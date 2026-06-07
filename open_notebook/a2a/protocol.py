"""A2A protocol message types and parsing.

Defines the JSON-RPC 2.0 based A2A protocol data structures used for
agent-to-agent communication within the exocortex.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Core data types
# ---------------------------------------------------------------------------


@dataclass
class A2APart:
    """A single part of an A2A message – text or structured data."""

    type: str = "text"
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"type": self.type}
        if self.text is not None:
            d["text"] = self.text
        if self.data is not None:
            d["data"] = self.data
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> A2APart:
        return cls(type=d.get("type", "text"), text=d.get("text"), data=d.get("data"))


@dataclass
class A2AMessage:
    """An A2A message with a role and list of parts."""

    role: str = "user"
    parts: List[A2APart] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "parts": [p.to_dict() for p in self.parts]}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> A2AMessage:
        parts = [A2APart.from_dict(p) for p in d.get("parts", [])]
        return cls(role=d.get("role", "user"), parts=parts)


@dataclass
class A2ATaskStatus:
    """Status of an A2A task."""

    state: str = "submitted"  # submitted | working | input-required | completed | failed
    message: Optional[A2AMessage] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"state": self.state}
        if self.message is not None:
            d["message"] = self.message.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> A2ATaskStatus:
        msg = A2AMessage.from_dict(d["message"]) if "message" in d else None
        return cls(state=d.get("state", "submitted"), message=msg)


@dataclass
class A2AArtifact:
    """An artifact produced by an A2A task."""

    parts: List[A2APart] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"parts": [p.to_dict() for p in self.parts]}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> A2AArtifact:
        parts = [A2APart.from_dict(p) for p in d.get("parts", [])]
        return cls(parts=parts)


@dataclass
class A2ATask:
    """An A2A task representing a unit of work."""

    id: str = ""
    sessionId: Optional[str] = None
    status: A2ATaskStatus = field(default_factory=A2ATaskStatus)
    artifacts: List[A2AArtifact] = field(default_factory=list)
    history: List[A2AMessage] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "status": self.status.to_dict(),
            "artifacts": [a.to_dict() for a in self.artifacts],
            "history": [m.to_dict() for m in self.history],
        }
        if self.sessionId is not None:
            d["sessionId"] = self.sessionId
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> A2ATask:
        return cls(
            id=d.get("id", ""),
            sessionId=d.get("sessionId"),
            status=A2ATaskStatus.from_dict(d.get("status", {})),
            artifacts=[A2AArtifact.from_dict(a) for a in d.get("artifacts", [])],
            history=[A2AMessage.from_dict(m) for m in d.get("history", [])],
        )


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 request / response
# ---------------------------------------------------------------------------


@dataclass
class A2ARequest:
    """A JSON-RPC 2.0 request for the A2A protocol."""

    jsonrpc: str = "2.0"
    method: str = ""
    id: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "id": self.id,
            "params": self.params,
        }


@dataclass
class A2AResponse:
    """A JSON-RPC 2.0 response for the A2A protocol."""

    jsonrpc: str = "2.0"
    id: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            d["error"] = self.error
        elif self.result is not None:
            d["result"] = self.result
        return d


# ---------------------------------------------------------------------------
# Agent Card types
# ---------------------------------------------------------------------------


@dataclass
class A2AAgentSkill:
    """Describes a skill an A2A agent can perform."""

    id: str = ""
    name: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }
        if self.tags:
            d["tags"] = self.tags
        return d


@dataclass
class A2AAgentCard:
    """Agent Card describing the exocortex agent capabilities."""

    name: str = ""
    description: str = ""
    url: str = ""
    capabilities: Dict[str, bool] = field(default_factory=dict)
    skills: List[A2AAgentSkill] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "capabilities": self.capabilities,
            "skills": [s.to_dict() for s in self.skills],
        }


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def parse_request(raw: Dict[str, Any]) -> A2ARequest:
    """Parse a raw dict into an A2ARequest.

    Raises ValueError if required JSON-RPC fields are missing.
    """
    if raw.get("jsonrpc") != "2.0":
        raise ValueError("Invalid or missing jsonrpc version")
    method = raw.get("method")
    if not method or not isinstance(method, str):
        raise ValueError("Missing or invalid method")
    req_id = raw.get("id")
    if req_id is None:
        raise ValueError("Missing request id")
    return A2ARequest(
        jsonrpc="2.0",
        method=method,
        id=str(req_id),
        params=raw.get("params", {}),
    )


def make_response(req: A2ARequest, result: Dict[str, Any]) -> A2AResponse:
    """Create a success response for a given request."""
    return A2AResponse(jsonrpc="2.0", id=req.id, result=result)


def make_error(
    req: A2ARequest, code: int, message: str, data: Any = None
) -> A2AResponse:
    """Create an error response for a given request."""
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return A2AResponse(jsonrpc="2.0", id=req.id, error=err)
