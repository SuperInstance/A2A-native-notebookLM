"""SSE streaming for long-running A2A tasks.

Provides an async generator that yields Server-Sent Events for task
progress updates, compatible with FastAPI's ``StreamingResponse``.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import AsyncGenerator, Dict, Optional

from open_notebook.a2a.protocol import (
    A2AMessage,
    A2APart,
    A2ATask,
    A2ATaskStatus,
)


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------


def _sse_event(event: str, data: Dict) -> str:
    """Format a single SSE event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_task_events(
    task_id: str,
    *,
    max_iterations: int = 100,
    tick: float = 0.5,
) -> AsyncGenerator[str, None]:
    """Yield SSE events for a task's lifecycle.

    This is a simplified implementation that emits a ``working`` event
    periodically and then a ``completed`` event. In production this would
    integrate with a real task runner / job queue.

    Parameters
    ----------
    task_id:
        The ID of the task to stream.
    max_iterations:
        Safety limit on the number of working ticks.
    tick:
        Seconds between working events.
    """
    # Emit initial working event
    yield _sse_event(
        "working",
        {
            "id": task_id,
            "status": {"state": "working"},
        },
    )

    for i in range(max_iterations):
        await asyncio.sleep(tick)

        # For now, emit one working tick then complete
        if i >= 1:
            break

        yield _sse_event(
            "working",
            {
                "id": task_id,
                "status": {"state": "working"},
                "progress": i + 1,
            },
        )

    # Final event
    yield _sse_event(
        "completed",
        {
            "id": task_id,
            "status": {"state": "completed"},
        },
    )
