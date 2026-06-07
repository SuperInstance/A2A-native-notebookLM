"""
A2A (Agent-to-Agent) / I2I (Inter-agent-to-Inter-agent) interception hooks.

These hooks allow A2A/I2I bottle (task/message) interception and delegation
within LangGraph workflows. They are designed to be optional — if the A2A
module is unavailable or a2a_context is not provided, all hooks become no-ops.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def before_ask(
    state: Dict[str, Any],
    a2a_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Hook invoked before the Q&A workflow begins reasoning.

    Checks the a2a_context for a pending bottle (task) and, if found,
    injects the bottle's question into the workflow state so the LLM
    can address it.

    Returns the (possibly modified) state.
    """
    if a2a_context is None:
        return state

    pending_task = a2a_context.get("pending_task")
    if pending_task is None:
        return state

    bottle_question = pending_task.get("query") or pending_task.get("question")
    if bottle_question:
        logger.info("A2A: injecting pending bottle question into ask workflow")
        state["question"] = (
            f"[A2A Bottle Request] {bottle_question}\n\n"
            f"Original context: {state.get('question', '')}"
        )
        state["_a2a_bottle_id"] = pending_task.get("id")
        state["_a2a_origin"] = pending_task.get("origin")

    return state


async def after_ask(
    state: Dict[str, Any],
    a2a_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Hook invoked after the Q&A workflow produces its final answer.

    If an A2A bottle was being processed, the final answer is packaged
    as a response bottle and emitted via the a2a_context callback.
    """
    if a2a_context is None:
        return state

    bottle_id = state.get("_a2a_bottle_id")
    if bottle_id is None:
        return state

    final_answer = state.get("final_answer", "")
    if not final_answer:
        return state

    emit_fn = a2a_context.get("emit_result")
    if emit_fn is None:
        logger.warning("A2A: emit_result callback not configured; bottle result not sent")
        return state

    logger.info(f"A2A: emitting result for bottle {bottle_id}")
    try:
        await emit_fn(
            bottle_id=bottle_id,
            result=final_answer,
            origin=state.get("_a2a_origin", "notebooklm"),
        )
    except Exception as exc:
        logger.error(f"A2A: failed to emit bottle result: {exc}")

    return state


async def setup_a2a_context(
    notebook_id: str,
    vessel: Optional["VesselClient"] = None,
) -> Dict[str, Any]:
    """
    Load relevant bottles for context and set up the A2A context dict.

    Polls the vessel for any pending bottles addressed to this notebook
    and returns a context dict with the pending task (if any) and an
    emit_result callback.

    Args:
        notebook_id: The ID of the notebook to load context for.
        vessel: An optional VesselClient instance.

    Returns:
        A dict with keys:
          - "pending_task": The first pending Bottle dict, or None.
          - "emit_result": An async callable to emit result bottles.
    """
    from open_notebook.a2a.models import Bottle, BottleType
    from open_notebook.a2a.vessel import VesselClient as _VesselClient

    if vessel is None:
        vessel = _VesselClient()

    # Check for pending bottles
    envelopes = vessel.check_vessel()
    pending_task = None

    for env in envelopes:
        bottle = env.bottle
        # Match by recipient or broadcast
        if bottle.recipient in (notebook_id, "broadcast"):
            if bottle.type == BottleType.TASK:
                pending_task = {
                    "id": bottle.id,
                    "origin": bottle.sender,
                    "query": bottle.payload.get("query") or bottle.payload.get("question"),
                    "question": bottle.payload.get("question") or bottle.payload.get("query"),
                    "content": bottle.payload.get("content"),
                    "input_text": bottle.payload.get("input_text"),
                    "transformation_prompt": bottle.payload.get("transformation_prompt") or bottle.payload.get("prompt"),
                    "prompt": bottle.payload.get("prompt"),
                    "bottle": bottle,
                    "envelope": env,
                }
                break

    async def emit_result(
        bottle_id: str,
        result: str,
        origin: str = "notebooklm",
    ) -> None:
        """Emit a DELIVERABLE bottle in response to a processed task."""
        response_bottle = Bottle(
            sender=origin,
            recipient=pending_task["origin"] if pending_task else "broadcast",
            type=BottleType.DELIVERABLE,
            payload={
                "original_bottle_id": bottle_id,
                "result": result,
            },
            context={"notebook_id": notebook_id},
        )
        vessel.send_bottle(response_bottle)

    return {
        "pending_task": pending_task,
        "emit_result": emit_result,
    }


async def before_transformation(
    state: Dict[str, Any],
    a2a_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Hook invoked before the content transformation workflow begins.

    Checks the a2a_context for a pending bottle payload and, if found,
    uses the bottle's content as the input_text for the transformation.
    """
    if a2a_context is None:
        return state

    pending_task = a2a_context.get("pending_task")
    if pending_task is None:
        return state

    bottle_payload = pending_task.get("content") or pending_task.get("input_text")
    if bottle_payload:
        logger.info("A2A: injecting bottle content into transformation workflow")
        state["input_text"] = bottle_payload
        state["_a2a_bottle_id"] = pending_task.get("id")
        state["_a2a_origin"] = pending_task.get("origin", "notebooklm")

    bottle_prompt = pending_task.get("transformation_prompt") or pending_task.get("prompt")
    if bottle_prompt and "transformation" in state:
        state["transformation"].prompt = (
            f"[A2A Bottle Instructions] {bottle_prompt}\n\n"
            f"{state['transformation'].prompt}"
        )

    return state


async def after_transformation(
    state: Dict[str, Any],
    a2a_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Hook invoked after the transformation workflow completes.

    If an A2A bottle was being processed, the transformation output is
    packaged as a response bottle and emitted.
    """
    if a2a_context is None:
        return state

    bottle_id = state.get("_a2a_bottle_id")
    if bottle_id is None:
        return state

    output = state.get("output", "")
    if not output:
        return state

    emit_fn = a2a_context.get("emit_result")
    if emit_fn is None:
        logger.warning("A2A: emit_result callback not configured; bottle result not sent")
        return state

    logger.info(f"A2A: emitting transformation result for bottle {bottle_id}")
    try:
        await emit_fn(
            bottle_id=bottle_id,
            result=output,
            origin=state.get("_a2a_origin", "notebooklm"),
        )
    except Exception as exc:
        logger.error(f"A2A: failed to emit transformation result: {exc}")

    return state
