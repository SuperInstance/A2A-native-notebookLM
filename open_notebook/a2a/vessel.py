"""
I2I Vessel Client — reads/writes bottles to a vessel directory and
discovers A2A-capable agents via CORTEX manifest introspection.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from open_notebook.a2a.models import Bottle, BottleEnvelope, CORTEXManifest

logger = logging.getLogger(__name__)


class VesselClient:
    """
    An I2I vessel client that exchanges bottles (messages) with other agents.

    Bottles are persisted to a local vessel directory structure:
        vessel_dir/
          incoming/     # Bottles received from other agents (read by us)
          outgoing/     # Bottles we've sent (our outgoing harbor)

    Args:
        base_url: Optional base URL of a remote vessel server.
        token: Optional auth token for the remote vessel server.
        vessel_dir: Path to the local vessel directory. Defaults to
                    ``./.vessel`` if not provided.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        vessel_dir: Optional[str] = None,
    ) -> None:
        self.base_url = base_url
        self.token = token
        self.vessel_dir = Path(vessel_dir or os.getenv("VESSEL_DIR", "./.vessel"))
        self._ensure_dirs()
        self._http_client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Directory helpers
    # ------------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        """Create the incoming/outgoing directory structure."""
        (self.vessel_dir / "incoming").mkdir(parents=True, exist_ok=True)
        (self.vessel_dir / "outgoing").mkdir(parents=True, exist_ok=True)

    def _incoming_dir(self) -> Path:
        return self.vessel_dir / "incoming"

    def _outgoing_dir(self) -> Path:
        return self.vessel_dir / "outgoing"

    # ------------------------------------------------------------------
    # HTTP helpers (async)
    # ------------------------------------------------------------------

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._http_client

    async def _close_http(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    # ------------------------------------------------------------------
    # Local vessel operations
    # ------------------------------------------------------------------

    def check_vessel(self) -> List[BottleEnvelope]:
        """
        Poll the local vessel for new bottles in the incoming directory.

        Returns a list of BottleEnvelope objects for all unprocessed
        bottles. Bottles are NOT removed after reading; consumers should
        call :meth:`mark_processed` when done.
        """
        envelopes: List[BottleEnvelope] = []
        incoming = self._incoming_dir()
        if not incoming.exists():
            return envelopes

        for filename in sorted(incoming.iterdir()):
            if not filename.is_file() or filename.suffix not in (".json",):
                continue
            try:
                data = json.loads(filename.read_text())
                bottle = Bottle.model_validate(
                    data["bottle"] if "bottle" in data else data
                )
                envelope = BottleEnvelope(
                    bottle=bottle,
                    signature=data.get("signature"),
                    routing=data.get("routing", {}),
                )
                envelopes.append(envelope)
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.warning("Failed to read bottle %s: %s", filename, exc)

        return envelopes

    def mark_processed(self, envelope: BottleEnvelope) -> None:
        """
        Remove a processed bottle file from the incoming directory.

        Args:
            envelope: The BottleEnvelope whose file should be removed.
        """
        bottle_id = envelope.bottle.id
        for f in self._incoming_dir().iterdir():
            if f.is_file() and bottle_id in f.name:
                f.unlink(missing_ok=True)
                return

    def _write_bottle_to(self, bottle: Bottle, directory: Path) -> bool:
        """Internal: write a bottle envelope to a specific directory."""
        try:
            envelope = BottleEnvelope(bottle=bottle)
            type_str = self._bottle_type_str(bottle)
            filename = f"{type_str}_{bottle.id}.json"
            out_path = directory / filename
            out_path.write_text(envelope.model_dump_json(indent=2))
            return True
        except OSError as exc:
            logger.error("Failed to write bottle %s: %s", bottle.id, exc)
            return False

    def send_bottle(self, bottle: Bottle) -> bool:
        """
        Write a bottle to the outgoing harbor directory.

        This is a local-only send; to deliver to a remote vessel server,
        use :meth:`send_bottle_remote`.

        Returns:
            True on success, False on error.
        """
        result = self._write_bottle_to(bottle, self._outgoing_dir())
        if result:
            logger.info("Bottle %s sent to outgoing harbor", bottle.id)
        return result

    def receive_bottle(self, bottle: Bottle) -> bool:
        """
        Write a received bottle to the incoming harbor directory.

        This is used by the A2A router to persist bottles received from
        other agents so they can be processed later.

        Returns:
            True on success, False on error.
        """
        result = self._write_bottle_to(bottle, self._incoming_dir())
        if result:
            logger.info("Bottle %s received into incoming harbor", bottle.id)
        return result

    async def send_bottle_remote(self, bottle: Bottle, target_url: str) -> bool:
        """
        Send a bottle to a remote agent's A2A endpoint.

        Args:
            bottle: The Bottle to send.
            target_url: The remote agent's bottle endpoint URL.

        Returns:
            True on success, False on error.
        """
        try:
            client = await self._get_http_client()
            envelope = BottleEnvelope(bottle=bottle).model_dump(mode="json")
            resp = await client.post(target_url, json=envelope)
            resp.raise_for_status()
            logger.info(
                "Bottle %s delivered to %s (status %d)",
                bottle.id,
                target_url,
                resp.status_code,
            )
            return True
        except httpx.HTTPError as exc:
            logger.error("Failed to send bottle %s to %s: %s", bottle.id, target_url, exc)
            return False

    @staticmethod
    def _bottle_type_str(bottle: Bottle) -> str:
        """Return the bottle type as a string, regardless of enum or string."""
        t = bottle.type
        if isinstance(t, str):
            return t
        return t.value if hasattr(t, 'value') else str(t)

    # ------------------------------------------------------------------
    # Bottle processing
    # ------------------------------------------------------------------

    def process_bottle(
        self, bottle: Bottle, reply_vessel: Optional[VesselClient] = None
    ) -> Optional[Bottle]:
        """
        Process an incoming bottle and optionally generate a reply bottle.

        This is a simple dispatcher that reads the bottle type and
        produces an appropriate ACK or response bottle.

        Args:
            bottle: The bottle to process.
            reply_vessel: If provided, the reply is sent through this vessel.

        Returns:
            A reply Bottle if one was generated, else None.
        """
        type_str = self._bottle_type_str(bottle)
        logger.info("Processing bottle %s (type=%s)", bottle.id, type_str)

        if type_str == "ACK":
            # ACKs are terminal — no reply needed
            return None

        if type_str == "TASK":
            # Acknowledge receipt
            ack = Bottle(
                sender=bottle.recipient,
                recipient=bottle.sender,
                type="ACK",
                payload={
                    "original_bottle_id": bottle.id,
                    "status": "received",
                    "message": "Task acknowledged",
                },
                context=bottle.context,
            )
            if reply_vessel:
                reply_vessel.send_bottle(ack)
            return ack

        if type_str == "STATUS":
            # Acknowledge status update
            ack = Bottle(
                sender=bottle.recipient,
                recipient=bottle.sender,
                type="ACK",
                payload={
                    "original_bottle_id": bottle.id,
                    "status": "status_acknowledged",
                },
            )
            if reply_vessel:
                reply_vessel.send_bottle(ack)
            return ack

        if type_str == "CHECKPOINT":
            # Acknowledge checkpoint
            ack = Bottle(
                sender=bottle.recipient,
                recipient=bottle.sender,
                type="ACK",
                payload={
                    "original_bottle_id": bottle.id,
                    "status": "checkpoint_received",
                },
            )
            if reply_vessel:
                reply_vessel.send_bottle(ack)
            return ack

        if type_str == "SESSION":
            # Session bottles are informational — acknowledge
            ack = Bottle(
                sender=bottle.recipient,
                recipient=bottle.sender,
                type="ACK",
                payload={
                    "original_bottle_id": bottle.id,
                    "status": "session_acknowledged",
                },
            )
            if reply_vessel:
                reply_vessel.send_bottle(ack)
            return ack

        # Unknown bottle types — send challenge
        challenge = Bottle(
            sender=bottle.recipient,
            recipient=bottle.sender,
            type="CHALLENGE",
            payload={
                "original_bottle_id": bottle.id,
                "message": f"Unrecognized bottle type: {type_str}",
            },
        )
        if reply_vessel:
            reply_vessel.send_bottle(challenge)
        return challenge

    # ------------------------------------------------------------------
    # A2A Agent discovery
    # ------------------------------------------------------------------

    async def discover_cortex(self, agent_url: str) -> Optional[CORTEXManifest]:
        """
        Discover an A2A agent's capabilities via CORTEX manifest.

        Attempts to fetch ``/.well-known/cortex.json`` from the agent's
        base URL.

        Args:
            agent_url: The base URL of the agent to discover.

        Returns:
            A CORTEXManifest if discovery succeeded, else None.
        """
        cortex_url = agent_url.rstrip("/") + "/.well-known/cortex.json"
        try:
            client = await self._get_http_client()
            resp = await client.get(cortex_url)
            resp.raise_for_status()
            data = resp.json()
            manifest = CORTEXManifest.model_validate(data)
            logger.info(
                "Discovered agent %s with %d capabilities",
                manifest.identity.get("name", agent_url),
                len(manifest.capabilities),
            )
            return manifest
        except httpx.HTTPError as exc:
            logger.warning("CORTEX discovery failed for %s: %s", agent_url, exc)
            return None
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse CORTEX manifest from %s: %s", agent_url, exc)
            return None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._close_http()
