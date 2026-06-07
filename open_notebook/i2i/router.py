"""
I2I FastAPI Router.

Exposes the I2I vessel protocol over HTTP so that other agents in the fleet
can discover capabilities and exchange bottles via the well-known endpoints.
"""

from __future__ import annotations

import os
import time
from typing import List

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from open_notebook.i2i import __version__
from open_notebook.i2i.handlers import dispatch, registered_types
from open_notebook.i2i.models import Bottle, BottleEnvelope, BottleType, VesselStatus

router = APIRouter(prefix="/api/v1/i2i", tags=["i2i"])

# Keep a bounded in-memory ring buffer of recent bottles for debugging
_MAX_RECENT = 100
_recent_bottles: List[dict] = []

# Track start time for uptime reporting
_start_time = time.time()


def _record_bottle(bottle: Bottle, envelope: BottleEnvelope, direction: str):
    """Append a bottle to the recent-bottles ring buffer."""
    entry = {
        "id": bottle.id,
        "type": bottle.type.value,
        "sender": bottle.sender,
        "recipient": bottle.recipient,
        "direction": direction,
        "status": envelope.routing.get("status", "unknown"),
        "timestamp": bottle.timestamp.isoformat() if bottle.timestamp else None,
    }
    _recent_bottles.append(entry)
    if len(_recent_bottles) > _MAX_RECENT:
        _recent_bottles.pop(0)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/bottle", response_model=BottleEnvelope)
async def accept_bottle(request: Request, envelope: BottleEnvelope) -> BottleEnvelope:
    """
    Accept an incoming I2I bottle, route it to the appropriate handler,
    and return the result envelope.

    This is the primary HTTP entry point for the I2I protocol. Other fleet
    agents POST bottles here.
    """
    bottle = envelope.bottle
    logger.info(
        f"I2I bottle received: id={bottle.id} type={bottle.type.value} "
        f"sender={bottle.sender} recipient={bottle.recipient}"
    )

    # Check if this vessel is the intended recipient
    vessel_name = os.environ.get("I2I_VESSEL_NAME", "a2a-native-notebooklm")
    if bottle.recipient != "*" and bottle.recipient != vessel_name:
        logger.warning(
            f"Bottle {bottle.id} addressed to '{bottle.recipient}' "
            f"but this vessel is '{vessel_name}'"
        )
        return BottleEnvelope(
            bottle=Bottle(
                sender=bottle.recipient,
                recipient=bottle.sender,
                type=BottleType.ERROR,
                payload={"error": f"Not addressed to this vessel"},
                context={"in_response_to": bottle.id},
            ),
            routing={"status": "error", "error": "Wrong recipient"},
        )

    try:
        result = await dispatch(bottle)
        _record_bottle(bottle, result, "in")
        return result
    except Exception as exc:
        logger.exception(f"Unhandled error processing bottle {bottle.id}")
        error_env = BottleEnvelope(
            bottle=Bottle(
                sender=bottle.recipient,
                recipient=bottle.sender,
                type=BottleType.ERROR,
                payload={"error": str(exc)},
                context={"in_response_to": bottle.id},
            ),
            routing={"status": "error", "error": str(exc)},
        )
        _record_bottle(bottle, error_env, "in")
        return error_env


@router.get("/bottles", response_model=List[dict])
async def list_recent_bottles(limit: int = 20):
    """
    Return the most recent bottles processed by this vessel.

    Useful for debugging and observability.
    """
    return list(reversed(_recent_bottles[-limit:]))


@router.get("/status", response_model=VesselStatus)
async def vessel_status():
    """
    Return the vessel's current operational status, including uptime,
    capabilities, and active bottle count.

    Used by fleet orchestration to determine readiness.
    """
    active = sum(
        1
        for b in _recent_bottles
        if b.get("status") not in ("completed", "error", "ok")
    )
    return VesselStatus(
        name="a2a-native-notebooklm",
        version=__version__,
        uptime=time.time() - _start_time,
        capabilities=[
            {"type": "RESEARCH", "description": "Research a topic with sources and AI synthesis"},
            {"type": "TRANSFORM", "description": "Transform content between formats"},
            {"type": "PODCAST", "description": "Generate audio podcast from content"},
            {"type": "STATUS", "description": "Return notebook status and capabilities"},
        ],
        active_bottles=active,
    )


# ---------------------------------------------------------------------------
# Well-known endpoints (no I2I prefix)
# ---------------------------------------------------------------------------

_well_known_router = APIRouter(tags=["i2i-well-known"])


@_well_known_router.get("/.well-known/cortex.json")
async def cortex_manifest():
    """
    Return the CORTEX discovery manifest.

    Other agents in the fleet hit this to discover what bottle types this
    vessel can handle and how to send bottles to it.
    """
    return {
        "api_version": "v1",
        "identity": {
            "name": "a2a-native-notebooklm",
            "version": __version__,
            "description": "I2I-native fleet cognitive command center",
            "agent_type": "notebook",
            "vessel_protocol": "i2i-v2",
        },
        "endpoints": {
            "bottle": "/api/v1/i2i/bottle",
            "status": "/api/v1/i2i/status",
            "cortex": "/.well-known/cortex.json",
            "vessel": os.environ.get("I2I_VESSEL_PATH", "/tmp/i2i-vessel"),
        },
        "capabilities": [
            {"type": bt.value, "description": f"Handle {bt.value} bottles"}
            for bt in registered_types()
        ],
    }


# Export both routers so the main app can mount both
__all__ = ["router", "_well_known_router"]
