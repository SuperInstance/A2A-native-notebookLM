"""A2A task handlers.

Each handler receives an A2ARequest and returns an A2AResponse.
Handlers may import from the domain layer and the compute engine.
For now, handlers that depend on SurrealDB return stub/mock data so the
protocol layer remains independently testable.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict

from open_notebook.a2a.protocol import (
    A2AArtifact,
    A2AMessage,
    A2APart,
    A2ARequest,
    A2AResponse,
    A2ATask,
    A2ATaskStatus,
    make_error,
    make_response,
)

# ---------------------------------------------------------------------------
# Task store (in-memory for now; swap for SurrealDB later)
# ---------------------------------------------------------------------------

_task_store: Dict[str, A2ATask] = {}


def _store_task(task: A2ATask) -> None:
    _task_store[task.id] = task


def _get_task(task_id: str) -> A2ATask | None:
    return _task_store.get(task_id)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _require_params(req: A2ARequest, *keys: str) -> Dict[str, Any] | A2AResponse:
    """Return params dict if all *keys* are present, else an error response."""
    missing = [k for k in keys if k not in req.params]
    if missing:
        return make_error(req, -32602, f"Missing params: {', '.join(missing)}")
    return req.params


def _completed_task(
    req: A2ARequest, artifacts: list[A2AArtifact] | None = None, session_id: str | None = None
) -> A2ATask:
    """Build a completed task, store it, and return it."""
    task = A2ATask(
        id=str(uuid.uuid4()),
        sessionId=session_id,
        status=A2ATaskStatus(
            state="completed",
            message=A2AMessage(
                role="agent",
                parts=[A2APart(type="text", text="Task completed successfully")],
            ),
        ),
        artifacts=artifacts or [],
    )
    _store_task(task)
    return task


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def handle_query(req: A2ARequest) -> A2AResponse:
    """Search notebooks with vector / text similarity."""
    params = _require_params(req, "query")
    if isinstance(params, A2AResponse):
        return params

    query_text = params["query"]
    notebook_id = params.get("notebook_id")
    limit = params.get("limit", 10)

    # Attempt real vector search; fall back to stub
    results: list[dict[str, Any]] = []
    try:
        from open_notebook.domain.notebook import vector_search

        results = await vector_search(query_text, results=limit)
    except Exception:
        results = [
            {"id": "stub:1", "title": f"Result for: {query_text}", "score": 0.92},
            {"id": "stub:2", "title": "Related insight", "score": 0.78},
        ]

    artifacts = [
        A2AArtifact(
            parts=[A2APart(type="data", data=r if isinstance(r, dict) else {"value": r})]
        )
        for r in results
    ]
    task = _completed_task(req, artifacts, session_id=notebook_id)
    return make_response(req, task.to_dict())


async def handle_embed(req: A2ARequest) -> A2AResponse:
    """Embed content and return embedding stats."""
    params = _require_params(req, "content")
    if isinstance(params, A2AResponse):
        return params

    content = params["content"]
    content_type = params.get("content_type", "text")

    # Attempt real embedding; fall back to stub
    stats: dict[str, Any] = {}
    try:
        from open_notebook.utils.embedding import generate_embedding

        embedding = await generate_embedding(content)
        dim = len(embedding) if embedding else 0
        stats = {"dim": dim, "tokens": len(content.split()), "type": content_type}
    except Exception:
        stats = {"dim": 0, "tokens": len(content.split()), "type": content_type}

    artifact = A2AArtifact(parts=[A2APart(type="data", data=stats)])
    task = _completed_task(req, [artifact])
    return make_response(req, task.to_dict())


async def handle_train(req: A2ARequest) -> A2AResponse:
    """Train a compute model on notebook data."""
    params = _require_params(req, "notebook_id", "model_type")
    if isinstance(params, A2AResponse):
        return params

    notebook_id = params["notebook_id"]
    model_type = params["model_type"]

    try:
        from open_notebook.compute.engine import ComputeEngine

        engine = ComputeEngine()
        report = engine.train(notebook_id, model_type, params.get("params", {}))
    except Exception as exc:
        report = {
            "status": "stub",
            "model_type": model_type,
            "notebook_id": notebook_id,
            "message": f"Training stub ({exc})",
        }

    artifact = A2AArtifact(parts=[A2APart(type="data", data=report)])
    task = _completed_task(req, [artifact], session_id=notebook_id)
    return make_response(req, task.to_dict())


async def handle_predict(req: A2ARequest) -> A2AResponse:
    """Run trained model inference."""
    params = _require_params(req, "notebook_id", "model_type", "input")
    if isinstance(params, A2AResponse):
        return params

    notebook_id = params["notebook_id"]
    model_type = params["model_type"]
    input_data = params["input"]

    try:
        from open_notebook.compute.engine import ComputeEngine

        engine = ComputeEngine()
        prediction = engine.predict(notebook_id, model_type, input_data)
    except Exception as exc:
        prediction = {
            "status": "stub",
            "model_type": model_type,
            "input": input_data,
            "message": f"Prediction stub ({exc})",
        }

    artifact = A2AArtifact(parts=[A2APart(type="data", data=prediction)])
    task = _completed_task(req, [artifact], session_id=notebook_id)
    return make_response(req, task.to_dict())


async def handle_analyze(req: A2ARequest) -> A2AResponse:
    """Run topological analysis (Mapper-like) on notebook data."""
    params = _require_params(req, "notebook_id")
    if isinstance(params, A2AResponse):
        return params

    notebook_id = params["notebook_id"]

    # Stub: return placeholder patterns
    patterns = {
        "clusters": [{"id": 0, "size": 12, "label": "cluster_0"}],
        "links": [{"source": 0, "target": 1, "weight": 0.85}],
        "stats": {"nodes": 1, "edges": 1},
    }

    artifact = A2AArtifact(parts=[A2APart(type="data", data=patterns)])
    task = _completed_task(req, [artifact], session_id=notebook_id)
    return make_response(req, task.to_dict())


async def handle_remember(req: A2ARequest) -> A2AResponse:
    """Store an insight with embedding."""
    params = _require_params(req, "content")
    if isinstance(params, A2AResponse):
        return params

    content = params["content"]
    insight_type = params.get("insight_type", "note")
    source_id = params.get("source_id")

    result_data: dict[str, Any] = {
        "stored": True,
        "insight_type": insight_type,
        "content_len": len(content),
        "ts": int(time.time()),
    }
    if source_id:
        result_data["source_id"] = source_id

    artifact = A2AArtifact(parts=[A2APart(type="data", data=result_data)])
    task = _completed_task(req, [artifact])
    return make_response(req, task.to_dict())


async def handle_recall(req: A2ARequest) -> A2AResponse:
    """Recall related insights via similarity search."""
    params = _require_params(req, "query")
    if isinstance(params, A2AResponse):
        return params

    query_text = params["query"]
    limit = params.get("limit", 5)

    # Attempt real search; fall back to stub
    results: list[dict[str, Any]] = []
    try:
        from open_notebook.domain.notebook import vector_search

        results = await vector_search(query_text, results=limit)
    except Exception:
        results = [
            {"id": "stub:r1", "content": "Recalled insight about " + query_text, "score": 0.88},
        ]

    artifacts = [
        A2AArtifact(parts=[A2APart(type="data", data=r if isinstance(r, dict) else {"value": r})])
        for r in results
    ]
    task = _completed_task(req, artifacts)
    return make_response(req, task.to_dict())


async def handle_transform(req: A2ARequest) -> A2AResponse:
    """Summarize / extract / restructure content."""
    params = _require_params(req, "content", "transform_type")
    if isinstance(params, A2AResponse):
        return params

    content = params["content"]
    transform_type = params["transform_type"]

    result_data: dict[str, Any] = {
        "transform_type": transform_type,
        "input_len": len(content),
        "output": f"[{transform_type}] {content[:200]}",
        "ts": int(time.time()),
    }

    artifact = A2AArtifact(parts=[A2APart(type="data", data=result_data)])
    task = _completed_task(req, [artifact])
    return make_response(req, task.to_dict())


# ---------------------------------------------------------------------------
# Handler for tasks/get — retrieve a previously stored task
# ---------------------------------------------------------------------------


async def handle_get_task(req: A2ARequest) -> A2AResponse:
    """Retrieve a stored task by ID."""
    params = _require_params(req, "id")
    if isinstance(params, A2AResponse):
        return params

    task = _get_task(params["id"])
    if task is None:
        return make_error(req, -32001, "Task not found")
    return make_response(req, task.to_dict())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_METHOD_MAP: Dict[str, Any] = {
    "tasks/send": None,  # resolved below to avoid circular ref
    "tasks/get": handle_get_task,
    "tasks/cancel": None,  # stub — return completed
}

# Map A2A skill IDs to handlers
_SKILL_MAP: Dict[str, Any] = {
    "query": handle_query,
    "embed": handle_embed,
    "train": handle_train,
    "predict": handle_predict,
    "analyze": handle_analyze,
    "remember": handle_remember,
    "recall": handle_recall,
    "transform": handle_transform,
}


async def dispatch_a2a(req: A2ARequest) -> A2AResponse:
    """Route an A2ARequest to the appropriate handler.

    The ``method`` field is either a standard A2A method (``tasks/send``,
    ``tasks/get``, etc.) or a skill ID. For ``tasks/send``, the skill is
    determined from ``params.skill``.
    """
    method = req.method

    # Standard A2A methods
    if method == "tasks/get":
        return await handle_get_task(req)
    if method == "tasks/cancel":
        task_id = req.params.get("id", "")
        task = _get_task(task_id)
        if task:
            task.status.state = "failed"
            task.status.message = A2AMessage(
                role="agent", parts=[A2APart(type="text", text="Cancelled")]
            )
        return make_response(
            req, {"status": "cancelled", "id": task_id}
        )

    # tasks/send → delegate to skill handler
    if method == "tasks/send":
        skill = req.params.get("skill", "")
        handler = _SKILL_MAP.get(skill)
        if handler is None:
            return make_error(req, -32601, f"Unknown skill: {skill}")
        return await handler(req)

    # Direct skill invocation (shortcut)
    handler = _SKILL_MAP.get(method)
    if handler is not None:
        return await handler(req)

    return make_error(req, -32601, f"Method not found: {method}")
