"""
A2A (Agent-to-Agent) / I2I (Inter-agent-to-Inter-agent) integration package.

Provides the vessel protocol for bottle-based messaging between agents
in the SuperInstance fleet, including models, client, hooks, and API
endpoints.
"""

from open_notebook.a2a.models import (
    A2ACapability,
    Bottle,
    BottleEnvelope,
    BottleType,
    CORTEXManifest,
)
from open_notebook.a2a.vessel import VesselClient
from open_notebook.a2a.hooks import (
    after_ask,
    after_transformation,
    before_ask,
    before_transformation,
    setup_a2a_context,
)

__all__ = [
    # Models
    "A2ACapability",
    "Bottle",
    "BottleEnvelope",
    "BottleType",
    "CORTEXManifest",
    # Client
    "VesselClient",
    # Hooks
    "after_ask",
    "after_transformation",
    "before_ask",
    "before_transformation",
    "setup_a2a_context",
]
