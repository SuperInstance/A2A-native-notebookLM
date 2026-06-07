"""A2A JSON-RPC server integration with FastAPI.

Provides ``A2ARouter`` which adds:
* ``POST /a2a`` — JSON-RPC 2.0 endpoint
* ``GET /.well-known/agent.json`` — Agent Card
* ``POST /a2a/tasks/resubscribe`` — SSE streaming endpoint
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from open_notebook.a2a.agent_card import get_agent_card
from open_notebook.a2a.handlers import dispatch_a2a
from open_notebook.a2a.protocol import A2ARequest, parse_request
from open_notebook.a2a.streaming import stream_task_events


class A2ARouter:
    """Factory that creates a FastAPI ``APIRouter`` for A2A endpoints."""

    @staticmethod
    def create() -> APIRouter:
        router = APIRouter(prefix="/a2a", tags=["a2a"])

        @router.post("")
        async def a2a_endpoint(request: Request) -> JSONResponse:
            """Main A2A JSON-RPC 2.0 endpoint."""
            try:
                body = await request.json()
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    },
                )

            # Batch requests
            if isinstance(body, list):
                results = await asyncio.gather(
                    *[_handle_single(req_body) for req_body in body]
                )
                return JSONResponse(content=results)

            resp = await _handle_single(body)
            return JSONResponse(content=resp.to_dict())

        @router.get("/.well-known/agent.json")
        async def agent_card() -> Dict[str, Any]:
            """Return the Agent Card."""
            return get_agent_card()

        @router.post("/tasks/resubscribe")
        async def resubscribe(request: Request) -> StreamingResponse:
            """SSE streaming for long-running tasks."""
            try:
                body = await request.json()
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid JSON"},
                )

            task_id = body.get("id", "")
            return StreamingResponse(
                stream_task_events(task_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        return router


async def _handle_single(body: Dict[str, Any]):
    """Parse and dispatch a single JSON-RPC request."""
    try:
        req = parse_request(body)
    except ValueError as exc:
        return _jsonrpc_error(body.get("id"), -32600, str(exc))
    except Exception:
        return _jsonrpc_error(body.get("id"), -32700, "Parse error")

    try:
        return await dispatch_a2a(req)
    except Exception as exc:
        logger.error(f"A2A handler error: {exc}")
        return _jsonrpc_error(req.id, -32603, "Internal error")


def _jsonrpc_error(req_id, code: int, message: str):
    """Build a JSON-RPC error as an A2AResponse-like object."""
    from open_notebook.a2a.protocol import A2AResponse

    return A2AResponse(
        jsonrpc="2.0",
        id=str(req_id) if req_id else "",
        error={"code": code, "message": message},
    )


# Convenience module-level router instance
a2a_router = A2ARouter.create()
