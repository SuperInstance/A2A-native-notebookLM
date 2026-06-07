"""
I2I Vessel Protocol — Pydantic v2 models.

Defines the core data types for the Inter-agent-to-Inter-agent (I2I) bottle
protocol used by the fleet cognitive command center.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class BottleType(str, Enum):
    """The type of bottle — maps one-to-one with notebook capabilities."""

    RESEARCH = "RESEARCH"
    TRANSFORM = "TRANSFORM"
    PODCAST = "PODCAST"
    STATUS = "STATUS"
    SYNTHESIS = "SYNTHESIS"
    SESSION = "SESSION"
    ACK = "ACK"
    ERROR = "ERROR"


class Bottle(BaseModel):
    """
    A single I2I bottle — the atomic unit of inter-agent communication.

    A bottle carries a payload and context from one vessel sender to
    a recipient vessel that knows how to handle the bottle's type.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = Field(description="Identity of the sending vessel/agent")
    recipient: str = Field(description="Identity of the intended recipient vessel/agent")
    type: BottleType = Field(description="The bottle type — determines which handler is invoked")
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="The business payload (query text, transform config, podcast params, etc.)",
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary context/metadata (trace id, priority, ttl, etc.)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the bottle was created (UTC)",
    )

    @field_validator("sender", "recipient")
    @classmethod
    def non_empty_string(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("sender and recipient must be non-empty strings")
        return v.strip()

    model_config = {"frozen": False, "extra": "ignore"}


class BottleEnvelope(BaseModel):
    """
    A bottle wrapped in an envelope with optional signature and routing info.

    This is the wire format — what is serialised to JSON for file-exchange
    and HTTP transport.
    """

    bottle: Bottle
    signature: Optional[str] = Field(
        default=None,
        description="Optional HMAC or JWT signature for integrity verification",
    )
    routing: Dict[str, Any] = Field(
        default_factory=dict,
        description="Routing metadata (hops, ttl, priority, delivery-guarantee, etc.)",
    )

    model_config = {"frozen": False, "extra": "ignore"}


class VesselStatus(BaseModel):
    """Status report for a vessel, returned by the /api/v1/i2i/status endpoint."""

    name: str = Field(description="Vessel name (e.g. 'a2a-native-notebooklm')")
    version: str = Field(description="Software version")
    uptime: float = Field(description="Seconds since vessel started")
    capabilities: List[Dict[str, str]] = Field(
        description="List of capability descriptors each with type and description"
    )
    active_bottles: int = Field(
        default=0, description="Number of bottles currently being processed"
    )

    model_config = {"frozen": False, "extra": "ignore"}
