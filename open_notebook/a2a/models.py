"""
Pydantic v2 models for the I2I vessel protocol.

Defines the core data structures used for Agent-to-Agent communication
via the Inter-agent-to-Inter-agent (I2I) vessel protocol.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_serializer


class BottleType(str, Enum):
    """The type of a bottle (message) exchanged between agents."""

    TASK = "TASK"
    STATUS = "STATUS"
    CHECKPOINT = "CHECKPOINT"
    BLOCKER = "BLOCKER"
    DELIVERABLE = "DELIVERABLE"
    BOTTLE = "BOTTLE"
    ACK = "ACK"
    SYNTHESIS = "SYNTHESIS"
    CHALLENGE = "CHALLENGE"
    SESSION = "SESSION"


class Bottle(BaseModel):
    """
    A single bottle (message) in the I2I vessel protocol.

    Attributes:
        id: Unique identifier for this bottle.
        sender: Agent ID / name of the sender.
        recipient: Agent ID / name of the intended recipient (or "broadcast").
        type: The bottle type (TASK, STATUS, CHECKPOINT, etc.).
        payload: The actual message / data payload.
        context: Optional metadata / context dictionary.
        timestamp: ISO-8601 timestamp of creation (default: now).
    """

    model_config = {"extra": "allow", "use_enum_values": False}

    id: str = Field(default_factory=lambda: f"bottle-{uuid.uuid4().hex[:12]}")
    sender: str
    recipient: str = "broadcast"
    type: BottleType = BottleType.TASK
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer("type")
    def serialize_type(self, value: BottleType) -> str:
        return value.value if isinstance(value, BottleType) else str(value)


class BottleEnvelope(BaseModel):
    """
    An envelope wrapping a bottle with signature and routing info.

    Attributes:
        bottle: The Bottle being transported.
        signature: Optional cryptographic or HMAC signature.
        routing: Optional routing metadata (hops, ttl, path).
    """

    model_config = {"extra": "allow"}

    bottle: Bottle
    signature: Optional[str] = None
    routing: Dict[str, Any] = Field(default_factory=dict)


class A2ACapability(BaseModel):
    """
    Describes a single capability exposed by an A2A agent.

    Attributes:
        name: Short name / identifier for the capability.
        version: Version string for this capability.
        description: Human-readable description.
        input_schema: Optional JSON Schema dict describing expected input.
        output_schema: Optional JSON Schema dict describing expected output.
    """

    name: str
    version: str = "1.0"
    description: str = ""
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None


class CORTEXManifest(BaseModel):
    """
    A2A / CORTEX agent manifest for standards-based agent discovery.

    Follows the CORTEX (Cognitive Orchestration Runtime for Task EXchange)
    discovery specification.

    Attributes:
        api_version: Version of the CORTEX API (e.g. "v1").
        identity: Agent identity information.
        capabilities: List of A2ACapability objects.
        endpoints: Dictionary of named endpoint paths.
        schemas: Optional dictionary of named JSON Schemas.
    """

    model_config = {"extra": "allow"}

    api_version: str = "v1"
    identity: Dict[str, Any] = Field(default_factory=dict)
    capabilities: List[A2ACapability] = Field(default_factory=list)
    endpoints: Dict[str, str] = Field(default_factory=dict)
    schemas: Optional[Dict[str, Any]] = None
