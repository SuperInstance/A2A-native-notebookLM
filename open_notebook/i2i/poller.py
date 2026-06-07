"""
Background Vessel FS Poller.

Reads bottle JSON files from the I2I vessel's incoming directory, routes
them through the dispatch system, and writes the result envelopes to the
outgoing directory.

Designed to run as a FastAPI lifespan task — no cron, no systemd.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from open_notebook.i2i.handlers import dispatch
from open_notebook.i2i.models import Bottle, BottleEnvelope, BottleType

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_VESSEL_PATH = "/tmp/i2i-vessel"
_DEFAULT_POLL_INTERVAL = 5  # seconds
_MAX_RETRY_BACKOFF = 60  # maximum seconds between retries


def _vessel_path() -> Path:
    """Resolve the vessel path from environment or default."""
    return Path(os.environ.get("I2I_VESSEL_PATH", _DEFAULT_VESSEL_PATH))


def _poll_interval() -> int:
    """Return the configured poll interval in seconds."""
    return int(os.environ.get("I2I_POLL_INTERVAL", str(_DEFAULT_POLL_INTERVAL)))


def _ensure_dirs():
    """Ensure the vessel incoming and outgoing directories exist."""
    base = _vessel_path()
    (base / "incoming").mkdir(parents=True, exist_ok=True)
    (base / "outgoing").mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


async def _read_bottle_file(path: Path) -> Optional[BottleEnvelope]:
    """Read a single bottle JSON file and parse it into a BottleEnvelope."""
    try:
        data = json.loads(path.read_text())
        if "bottle" in data:
            return BottleEnvelope(**data)
        # If it's a bare bottle dict, wrap it
        return BottleEnvelope(bottle=Bottle(**data))
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        logger.error(f"Failed to parse bottle file {path.name}: {exc}")
        # Move malformed files to an error subdirectory
        error_dir = path.parent / "_errors"
        error_dir.mkdir(exist_ok=True)
        path.rename(error_dir / path.name)
        return None


async def _write_result(envelope: BottleEnvelope):
    """Write a result envelope as a JSON file to the outgoing directory."""
    out_dir = _vessel_path() / "outgoing"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{envelope.bottle.id}.json"
    # Atomically write via tempfile rename
    tmp = out_path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(envelope.model_dump_json(indent=2))
    tmp.rename(out_path)
    logger.debug(f"Wrote result to {out_path}")


# ---------------------------------------------------------------------------
# Polling loop
# ---------------------------------------------------------------------------

_running = False
_poller_task: Optional[asyncio.Task] = None
_processed_files: set = set()


async def _poll_once():
    """Scan the incoming directory and process any new bottles."""
    incoming = _vessel_path() / "incoming"
    if not incoming.exists():
        return

    for f in sorted(incoming.iterdir()):
        if f.suffix != ".json":
            continue
        if f.name in _processed_files:
            continue

        envelope = await _read_bottle_file(f)
        if envelope is None:
            continue

        logger.info(
            f"FS poller: processing bottle {envelope.bottle.id} "
            f"(type={envelope.bottle.type.value})"
        )

        try:
            result = await dispatch(envelope.bottle)
            await _write_result(result)
            _processed_files.add(f.name)
            # Remove the incoming file after successful processing
            f.unlink(missing_ok=True)
        except Exception as exc:
            logger.exception(
                f"FS poller: bottle {envelope.bottle.id} failed: {exc}"
            )
            # Write error result
            from open_notebook.i2i.models import Bottle as ResultBottle

            error_env = BottleEnvelope(
                bottle=ResultBottle(
                    sender=envelope.bottle.recipient,
                    recipient=envelope.bottle.sender,
                    type=BottleType.ERROR,
                    payload={"error": str(exc)},
                    context={"in_response_to": envelope.bottle.id},
                ),
                routing={"status": "error", "error": str(exc)},
            )
            await _write_result(error_env)
            # Move to _errors
            error_dir = f.parent / "_errors"
            error_dir.mkdir(exist_ok=True)
            f.rename(error_dir / f.name)
            _processed_files.add(f.name)
    logger.debug(f"FS poller: scanned {len(list(incoming.glob('*.json')))} files")


async def _poller_loop():
    """
    Main polling loop with exponential backoff on error.

    Runs continuously; stopped by cancelling the task.
    """
    global _running
    _running = True
    _ensure_dirs()

    backoff = 1
    interval = _poll_interval()

    logger.info(
        f"Vessel FS poller started: path={_vessel_path()} interval={interval}s"
    )

    while _running:
        try:
            await _poll_once()
            backoff = 1  # reset on success
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Vessel FS poller cancelled")
            break
        except Exception as exc:
            logger.error(f"Vessel FS poller error: {exc}, backing off {backoff}s")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, _MAX_RETRY_BACKOFF)

    _running = False
    logger.info("Vessel FS poller stopped")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def start_poller() -> asyncio.Task:
    """
    Start the background vessel poller as an asyncio task.

    Returns the Task so the caller can cancel it on shutdown.
    """
    global _poller_task
    if _poller_task is not None and not _poller_task.done():
        logger.warning("Vessel FS poller already running")
        return _poller_task
    _poller_task = asyncio.create_task(_poller_loop())
    return _poller_task


async def stop_poller():
    """Gracefully stop the background vessel poller."""
    global _running, _poller_task
    _running = False
    if _poller_task is not None and not _poller_task.done():
        _poller_task.cancel()
        try:
            await _poller_task
        except asyncio.CancelledError:
            pass
    _poller_task = None
    logger.info("Vessel FS poller stopped")
