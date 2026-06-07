"""Agent Card definition for the exocortex A2A agent.

Exposes the agent's identity and capabilities at
``/.well-known/agent.json`` as defined by the A2A specification.
"""

from __future__ import annotations

from typing import Any, Dict

from open_notebook.a2a.protocol import A2AAgentCard, A2AAgentSkill

# ---------------------------------------------------------------------------
# Static Agent Card
# ---------------------------------------------------------------------------

EXOCORTEX_AGENT_CARD = A2AAgentCard(
    name="Exocortex",
    description="A2A-native knowledge engine: vector search, embeddings, ML training, "
    "prediction, topological analysis, insight management, and content transformation.",
    url="http://localhost:8000/a2a",
    capabilities={
        "streaming": True,
        "pushNotifications": False,
        "stateTransitionHistory": True,
    },
    skills=[
        A2AAgentSkill(
            id="query",
            name="Query",
            description="Search notebooks with vector and text similarity",
            tags=["search", "vector", "semantic"],
        ),
        A2AAgentSkill(
            id="embed",
            name="Embed",
            description="Embed content (source or note) and return embedding stats",
            tags=["embedding", "vectorize"],
        ),
        A2AAgentSkill(
            id="train",
            name="Train",
            description="Train a compute model on notebook data",
            tags=["ml", "training", "model"],
        ),
        A2AAgentSkill(
            id="predict",
            name="Predict",
            description="Run trained model inference on input data",
            tags=["ml", "inference", "prediction"],
        ),
        A2AAgentSkill(
            id="analyze",
            name="Analyze",
            description="Topological analysis (Mapper-like) of notebook data",
            tags=["analysis", "topology", "patterns"],
        ),
        A2AAgentSkill(
            id="remember",
            name="Remember",
            description="Store an insight with embedding for future recall",
            tags=["insight", "store", "memory"],
        ),
        A2AAgentSkill(
            id="recall",
            name="Recall",
            description="Recall related insights via similarity search",
            tags=["insight", "search", "recall"],
        ),
        A2AAgentSkill(
            id="transform",
            name="Transform",
            description="Summarize, extract, or restructure content",
            tags=["transform", "summarize", "extract"],
        ),
    ],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_agent_card() -> Dict[str, Any]:
    """Return the Agent Card as a plain dictionary."""
    return EXOCORTEX_AGENT_CARD.to_dict()


def register_agent_card(app: Any) -> None:
    """Add the ``GET /.well-known/agent.json`` endpoint to a FastAPI app."""

    @app.get("/.well-known/agent.json")
    async def _agent_card() -> Dict[str, Any]:
        return get_agent_card()
