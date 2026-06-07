"""
FastAPI router for A2A (Agent-to-Agent) endpoints.

Provides bottle reception, listing, capability exposure, and standards-based
CORTEX agent discovery.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from open_notebook.a2a.models import (
    A2ACapability,
    Bottle,
    BottleEnvelope,
    CORTEXManifest,
)
from open_notebook.a2a.vessel import VesselClient

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Router setup
# ------------------------------------------------------------------

router = APIRouter(tags=["a2a"])


def _get_default_manifest() -> CORTEXManifest:
    """Load the CORTEX manifest, falling back to defaults."""
    cortex_path = Path(__file__).parent.parent.parent / "CORTEX.json"
    if cortex_path.exists():
        try:
            data = json.loads(cortex_path.read_text())
            return CORTEXManifest.model_validate(data)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to load CORTEX.json: %s", exc)

    return CORTEXManifest(
        api_version="v1",
        identity={
            "name": "a2a-native-notebooklm",
            "version": "1.0.0-a2a",
            "description": "Fleet cognitive command center",
            "agent_type": "notebook",
        },
        capabilities=[
            A2ACapability(
                name="research",
                version="1.0",
                description="Research a topic with sources",
            ),
            A2ACapability(
                name="transform",
                version="1.0",
                description="Transform content types",
            ),
            A2ACapability(
                name="summarize",
                version="1.0",
                description="Summarize documents",
            ),
            A2ACapability(
                name="podcast",
                version="1.0",
                description="Generate podcast from content",
            ),
            A2ACapability(
                name="ai-query",
                version="1.0",
                description="Query notebook with any model",
            ),
            A2ACapability(
                name="agent-chat",
                version="1.0",
                description="Agent-to-agent chat via I2I",
            ),
        ],
        endpoints={
            "bottle": "/api/v1/a2a/bottle",
            "capabilities": "/api/v1/a2a/capabilities",
            "cortex": "/.well-known/cortex.json",
        },
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post("/api/v1/a2a/bottle")
async def receive_bottle(request: Request) -> Dict[str, Any]:
    """
    Receive a bottle from another agent.

    Accepts a JSON BottleEnvelope, validates it, and writes the bottle
    to the vessel's incoming directory for processing.

    Returns an ACK with the bottle ID.
    """
    try:
        body = await request.json()
        envelope = BottleEnvelope.model_validate(body)
    except Exception as exc:
        logger.warning("Invalid bottle envelope received: %s", exc)
        raise HTTPException(status_code=422, detail=f"Invalid bottle envelope: {exc}")

    # Get from app state or create a default vessel
    vessel: VesselClient = getattr(request.app.state, "a2a_vessel", None)
    if vessel is None:
        vessel = VesselClient()
        request.app.state.a2a_vessel = vessel

    # Write to incoming directory
    bottle_id = envelope.bottle.id
    vessel.receive_bottle(envelope.bottle)

    logger.info("Received bottle %s from %s", bottle_id, envelope.bottle.sender)

    return {
        "status": "ok",
        "bottle_id": bottle_id,
        "message": f"Bottle {bottle_id} received and queued",
    }


@router.get("/api/v1/a2a/bottles")
async def list_bottles(
    request: Request,
    limit: int = Query(10, ge=1, le=100, description="Max bottles to return"),
) -> List[Dict[str, Any]]:
    """
    List bottles for this notebook's vessel.

    Returns the most recent bottles from the incoming directory.
    """
    vessel: VesselClient = getattr(request.app.state, "a2a_vessel", None)
    if vessel is None:
        return []

    envelopes = vessel.check_vessel()
    # Return as dicts sorted by timestamp descending
    result = []
    for env in envelopes[:limit]:
        result.append(env.model_dump(mode="json"))

    return result


@router.get("/api/v1/a2a/capabilities")
async def get_capabilities(request: Request) -> Dict[str, Any]:
    """
    Expose this notebook's capabilities as an A2A agent.

    Returns the full CORTEXManifest data, suitable for agent-to-agent
    capability discovery.
    """
    manifest = _get_default_manifest()

    # Allow app-level override via state
    app_manifest: Optional[CORTEXManifest] = getattr(
        request.app.state, "a2a_manifest", None
    )
    if app_manifest is not None:
        manifest = app_manifest

    return manifest.model_dump(mode="json")


@router.get("/.well-known/cortex.json")
async def cortex_discovery(request: Request) -> JSONResponse:
    """
    Standards-based agent discovery endpoint.

    Returns a CORTEXManifest JSON describing this agent's identity,
    capabilities, and endpoints. This follows the CORTEX discovery
    specification for the SuperInstance fleet.
    """
    manifest = _get_default_manifest()

    # Allow app-level override
    app_manifest: Optional[CORTEXManifest] = getattr(
        request.app.state, "a2a_manifest", None
    )
    if app_manifest is not None:
        manifest = app_manifest

    return JSONResponse(
        content=manifest.model_dump(mode="json"),
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    )
