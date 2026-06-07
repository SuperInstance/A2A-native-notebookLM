"""Convert domain objects to/from A2A artifacts.

All converters produce **compact** payloads:
* Null / None values are stripped
* Timestamps are converted to epoch seconds (int)
* Short keys are used where possible
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Sequence

from open_notebook.a2a.protocol import A2AArtifact, A2AMessage, A2APart


# ---------------------------------------------------------------------------
# Compact serialisation helpers
# ---------------------------------------------------------------------------


def _strip_nulls(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys whose values are None."""
    return {k: v for k, v in d.items() if v is not None}


def _to_epoch(ts: Optional[datetime]) -> Optional[int]:
    """Convert a datetime to epoch seconds, or return None."""
    if ts is None:
        return None
    return int(ts.timestamp())


def _compact(obj: Any) -> Any:
    """Recursively compact a value: strip nulls, convert datetimes."""
    if isinstance(obj, datetime):
        return int(obj.timestamp())
    if isinstance(obj, dict):
        return _strip_nulls({k: _compact(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [_compact(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


# ---------------------------------------------------------------------------
# Domain → A2A converters
# ---------------------------------------------------------------------------


def insight_to_artifact(insight: Any) -> A2AArtifact:
    """Convert a SourceInsight domain object to a compact A2AArtifact."""
    data = _compact(
        {
            "id": getattr(insight, "id", None),
            "type": getattr(insight, "insight_type", None),
            "content": getattr(insight, "content", None),
            "created": _to_epoch(getattr(insight, "created", None)),
            "updated": _to_epoch(getattr(insight, "updated", None)),
        }
    )
    return A2AArtifact(parts=[A2APart(type="data", data=data)])


def notebook_to_artifact(nb: Any) -> A2AArtifact:
    """Convert a Notebook domain object to a compact A2AArtifact."""
    data = _compact(
        {
            "id": getattr(nb, "id", None),
            "name": getattr(nb, "name", None),
            "desc": getattr(nb, "description", None),
            "archived": getattr(nb, "archived", None),
            "created": _to_epoch(getattr(nb, "created", None)),
            "updated": _to_epoch(getattr(nb, "updated", None)),
        }
    )
    return A2AArtifact(parts=[A2APart(type="data", data=data)])


def source_to_artifact(source: Any) -> A2AArtifact:
    """Convert a Source domain object to a compact A2AArtifact."""
    asset = getattr(source, "asset", None)
    asset_data = None
    if asset:
        asset_data = _compact(
            {
                "fp": getattr(asset, "file_path", None),
                "url": getattr(asset, "url", None),
            }
        )
    data = _compact(
        {
            "id": getattr(source, "id", None),
            "title": getattr(source, "title", None),
            "topics": getattr(source, "topics", None) or None,
            "asset": asset_data,
            "created": _to_epoch(getattr(source, "created", None)),
            "updated": _to_epoch(getattr(source, "updated", None)),
        }
    )
    return A2AArtifact(parts=[A2APart(type="data", data=data)])


def note_to_artifact(note: Any) -> A2AArtifact:
    """Convert a Note domain object to a compact A2AArtifact."""
    data = _compact(
        {
            "id": getattr(note, "id", None),
            "title": getattr(note, "title", None),
            "type": getattr(note, "note_type", None),
            "content": getattr(note, "content", None),
            "created": _to_epoch(getattr(note, "created", None)),
            "updated": _to_epoch(getattr(note, "updated", None)),
        }
    )
    return A2AArtifact(parts=[A2APart(type="data", data=data)])


def chat_message_to_a2a(msg: Any) -> A2AMessage:
    """Convert a chat message (dict or object) to an A2AMessage."""
    if isinstance(msg, dict):
        role = msg.get("role", "user")
        content = msg.get("content", "")
    else:
        role = getattr(msg, "role", "user")
        content = getattr(msg, "content", "")
    return A2AMessage(
        role=role,
        parts=[A2APart(type="text", text=str(content) if content else None)],
    )


# ---------------------------------------------------------------------------
# A2A → Domain converters
# ---------------------------------------------------------------------------


def artifact_to_insight(artifact: A2AArtifact) -> Dict[str, Any]:
    """Extract insight fields from an A2AArtifact for domain creation."""
    for part in artifact.parts:
        if part.type == "data" and part.data:
            return dict(part.data)
    return {}


# ---------------------------------------------------------------------------
# Batch helpers
# ---------------------------------------------------------------------------


def batch_to_artifacts(
    objs: Sequence[Any], converter: Callable[[Any], A2AArtifact]
) -> List[A2AArtifact]:
    """Convert a sequence of domain objects using *converter*."""
    return [converter(obj) for obj in objs]
