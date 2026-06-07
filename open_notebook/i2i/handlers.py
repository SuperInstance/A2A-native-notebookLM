"""
I2I Bottle Type Handlers.

Each handler receives a Bottle, processes it using the EXISTING notebook
code (no LangGraph modifications), and returns a result BottleEnvelope.

Handlers are pure functions: they take a Bottle, return a BottleEnvelope.
No hooks, no state mutation.
"""

from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from open_notebook.i2i.models import Bottle, BottleEnvelope, BottleType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_HANDLER_REGISTRY: Dict[BottleType, str] = {}


def _result_envelope(
    original: Bottle,
    payload: dict,
    status: str = "ok",
    error: Optional[str] = None,
) -> BottleEnvelope:
    """Build a result BottleEnvelope addressed from the handler back to the sender."""
    result_type = BottleType.ACK if status == "ok" else BottleType.ERROR
    result_bottle = Bottle(
        sender=original.recipient,
        recipient=original.sender,
        type=result_type,
        payload=payload,
        context={
            "in_response_to": original.id,
            "original_type": original.type.value,
            "status": status,
        },
        timestamp=datetime.now(timezone.utc),
    )
    env = BottleEnvelope(
        bottle=result_bottle,
        routing={"status": status},
    )
    if error:
        env.routing["error"] = error
    return env


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def handle_research(bottle: Bottle) -> BottleEnvelope:
    """
    Handle a RESEARCH bottle.

    Invokes the existing ask graph (open_notebook.graphs.ask.graph) with
    the question from the bottle payload.
    """
    question = bottle.payload.get("question") or bottle.payload.get("query", "")
    if not question:
        return _result_envelope(
            bottle,
            payload={"error": "No question or query in payload"},
            status="error",
            error="Missing question field",
        )

    try:
        from open_notebook.graphs.ask import graph as ask_graph

        config = {"configurable": {"thread_id": bottle.id}}
        state = {"question": question}

        result = await ask_graph.ainvoke(state, config)
        final_answer = result.get("final_answer", result.get("answer", ""))
        return _result_envelope(
            bottle,
            payload={
                "answer": final_answer,
                "sources": result.get("answers", []),
            },
        )
    except Exception as exc:
        logger.exception(f"Research handler failed for bottle {bottle.id}")
        return _result_envelope(
            bottle,
            payload={"error": str(exc)},
            status="error",
            error=traceback.format_exc(),
        )


async def handle_transform(bottle: Bottle) -> BottleEnvelope:
    """
    Handle a TRANSFORM bottle.

    Invokes the existing transformation graph (open_notebook.graphs.transformation)
    with input_text and optional transformation configuration from the payload.
    """
    input_text = bottle.payload.get("input_text") or bottle.payload.get("content", "")
    if not input_text:
        return _result_envelope(
            bottle,
            payload={"error": "No input_text or content in payload"},
            status="error",
            error="Missing input content",
        )

    try:
        from open_notebook.domain.transformation import Transformation

        transformation_config = bottle.payload.get("transformation", {})
        transformation_title = transformation_config.get("title", "I2I Transformation")

        # Resolve or create a transformation object
        transformation = None
        if transformation_config.get("id"):
            transformation = await Transformation.get(transformation_config["id"])
        if transformation is None:
            transformation = Transformation(title=transformation_title)
            if transformation_config.get("prompt"):
                transformation.prompt = transformation_config["prompt"]

        config = {
            "configurable": {
                "thread_id": bottle.id,
                "model_id": transformation_config.get("model", None),
            }
        }
        state = {
            "input_text": input_text,
            "source": None,
            "transformation": transformation,
        }

        from open_notebook.graphs.transformation import graph as transform_graph

        result = await transform_graph.ainvoke(state, config)
        output = result.get("output", "")
        return _result_envelope(
            bottle,
            payload={"output": output, "transformation": transformation_title},
        )
    except Exception as exc:
        logger.exception(f"Transform handler failed for bottle {bottle.id}")
        return _result_envelope(
            bottle,
            payload={"error": str(exc)},
            status="error",
            error=traceback.format_exc(),
        )


async def handle_podcast(bottle: Bottle) -> BottleEnvelope:
    """
    Handle a PODCAST bottle.

    Invokes the existing podcast commands to generate a podcast episode
    from the provided content and configuration.
    """
    content = bottle.payload.get("content") or bottle.payload.get("text", "")
    if not content:
        return _result_envelope(
            bottle,
            payload={"error": "No content or text in payload"},
            status="error",
            error="Missing podcast content",
        )

    try:
        from open_notebook.podcasts.models import EpisodeProfile, PodcastEpisode

        # Determine podcast configuration from payload
        podcast_config = bottle.payload.get("podcast_config", {})
        episode_title = podcast_config.get("title", "I2I Podcast Episode")

        # Resolve or create an episode profile
        profile_id = podcast_config.get("profile_id")
        episode_profile = None
        if profile_id:
            episode_profile = await EpisodeProfile.get(profile_id)

        # Build the episode
        episode = PodcastEpisode(
            title=episode_title,
            content=content,
            profile_id=episode_profile.id if episode_profile else None,
            status="pending",
        )

        # If a generate flag is set, try to invoke the podcast creator pipeline
        generate_audio = bottle.payload.get("generate_audio", False)
        audio_url = None
        if generate_audio:
            try:
                from commands.podcast_commands import run_podcast_creation

                output_dir = f"./data/podcasts/episodes/{bottle.id}"
                result_path = await run_podcast_creation(
                    content=content,
                    episode_profile=episode_profile,
                    output_dir=output_dir,
                )
                audio_url = result_path if isinstance(result_path, str) else str(result_path)
                episode.status = "completed"
            except Exception as audio_err:
                logger.warning(f"Audio generation skipped: {audio_err}")
                episode.status = "transcript_only"

        return _result_envelope(
            bottle,
            payload={
                "episode_title": episode_title,
                "status": episode.status,
                "audio_url": audio_url,
                "episode_id": episode.id if hasattr(episode, "id") else None,
            },
        )
    except Exception as exc:
        logger.exception(f"Podcast handler failed for bottle {bottle.id}")
        return _result_envelope(
            bottle,
            payload={"error": str(exc)},
            status="error",
            error=traceback.format_exc(),
        )


async def handle_status(bottle: Bottle) -> BottleEnvelope:
    """
    Handle a STATUS bottle.

    Returns the notebook's configuration and current status without
    invoking any LangGraph workflow.
    """
    try:
        import os

        from open_notebook.config import DATA_FOLDER
        from open_notebook.i2i import __version__

        status_info = {
            "name": "a2a-native-notebooklm",
            "version": __version__,
            "data_folder": DATA_FOLDER,
            "i2i_vessel_path": os.environ.get(
                "I2I_VESSEL_PATH", "/tmp/i2i-vessel"
            ),
            "i2i_poll_interval": int(os.environ.get("I2I_POLL_INTERVAL", "5")),
            "python_version": os.sys.version,
            "capabilities": [
                {"type": "RESEARCH", "description": "Research a topic with sources and AI synthesis"},
                {"type": "TRANSFORM", "description": "Transform content between formats"},
                {"type": "PODCAST", "description": "Generate audio podcast from content"},
                {"type": "STATUS", "description": "Return notebook status and capabilities"},
            ],
        }
        return _result_envelope(
            bottle,
            payload=status_info,
        )
    except Exception as exc:
        logger.exception(f"Status handler failed for bottle {bottle.id}")
        return _result_envelope(
            bottle,
            payload={"error": str(exc)},
            status="error",
            error=traceback.format_exc(),
        )


async def handle_synthesis(bottle: Bottle) -> BottleEnvelope:
    """
    Handle a SYNTHESIS bottle — multi-source research synthesis.

    Combines multiple research questions or source IDs, runs the ask graph
    for each, and synthesises the results.
    """
    questions = bottle.payload.get("questions", [])
    source_ids = bottle.payload.get("source_ids", [])
    if not questions and not source_ids:
        return _result_envelope(
            bottle,
            payload={"error": "No questions or source_ids in payload"},
            status="error",
            error="Missing synthesis input",
        )

    try:
        from open_notebook.graphs.ask import graph as ask_graph

        answers = []
        for q in questions:
            config = {"configurable": {"thread_id": f"{bottle.id}-{q[:32]}"}}
            state = {"question": q}
            result = await ask_graph.ainvoke(state, config)
            answers.append(
                {
                    "question": q,
                    "answer": result.get("final_answer", result.get("answer", "")),
                }
            )

        synthesis_payload = {
            "answers": answers,
            "source_count": len(source_ids) if source_ids else 0,
        }

        # Optionally run a final synthesis step
        if bottle.payload.get("synthesize", True) and len(answers) > 1:
            combined = "\n\n".join(
                f"Q: {a['question']}\nA: {a['answer']}" for a in answers
            )
            from open_notebook.graphs.ask import graph as ask_graph

            syn_config = {"configurable": {"thread_id": f"{bottle.id}-synthesis"}}
            syn_state = {
                "question": f"Synthesize the following multi-part research into a coherent summary:\n\n{combined}"
            }
            syn_result = await ask_graph.ainvoke(syn_state, syn_config)
            synthesis_payload["synthesis"] = syn_result.get(
                "final_answer", syn_result.get("answer", "")
            )

        return _result_envelope(bottle, payload=synthesis_payload)
    except Exception as exc:
        logger.exception(f"Synthesis handler failed for bottle {bottle.id}")
        return _result_envelope(
            bottle,
            payload={"error": str(exc)},
            status="error",
            error=traceback.format_exc(),
        )


# ---------------------------------------------------------------------------
# Router dispatch
# ---------------------------------------------------------------------------

_HANDLER_MAP = {
    BottleType.RESEARCH: handle_research,
    BottleType.TRANSFORM: handle_transform,
    BottleType.PODCAST: handle_podcast,
    BottleType.STATUS: handle_status,
    BottleType.SYNTHESIS: handle_synthesis,
}


def get_handler(bottle_type: BottleType):
    """Return the handler function for the given bottle type, or None."""
    return _HANDLER_MAP.get(bottle_type)


def registered_types() -> list[BottleType]:
    """Return the list of bottle types that have a registered handler."""
    return list(_HANDLER_MAP.keys())


async def dispatch(bottle: Bottle) -> BottleEnvelope:
    """
    Route a Bottle to the appropriate handler and return the result envelope.

    This is the main dispatch entry point. It is also used by the background
    vessel poller.
    """
    handler = get_handler(bottle.type)
    if handler is None:
        logger.warning(f"No handler registered for bottle type {bottle.type}")
        return _result_envelope(
            bottle,
            payload={"error": f"Unknown bottle type: {bottle.type}"},
            status="error",
            error=f"No handler for {bottle.type}",
        )
    logger.info(f"Dispatching bottle {bottle.id} (type={bottle.type.value})")
    return await handler(bottle)
