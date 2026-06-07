"""
I2I Vessel-Native Package for A2A-Native-NotebookLM.

This package implements the Inter-agent-to-Inter-agent (I2I) vessel protocol
for the notebook. Instead of hooking into LangGraph, the notebook becomes
a proper I2I endpoint that can receive, process, and respond to bottles.

Architecture:
    ┌─────────────────────────────────┐
    │   I2I Vessel (HTTP + FS)        │
    │  ┌─────────┐  ┌──────────────┐  │
    │  │ Router  │  │ FS Poller    │  │
    │  │(FastAPI)│  │(Background)  │  │
    │  └────┬────┘  └──────┬───────┘  │
    │       │              │          │
    │  ┌────▼──────────────▼───────┐  │
    │  │     Dispatcher            │  │
    │  │  → handle_research        │  │
    │  │  → handle_transform       │  │
    │  │  → handle_podcast         │  │
    │  │  → handle_status          │  │
    │  └────────────┬──────────────┘  │
    │               │                 │
    │  ┌────────────▼──────────────┐  │
    │  │  LangGraph (internal)     │  │
    │  │  (NOT modified)          │  │
    │  └──────────────────────────┘  │
    └────────────────────────────────┘
"""

from __future__ import annotations

__version__ = "1.0.0-i2i"

from open_notebook.i2i.models import Bottle, BottleEnvelope, BottleType, VesselStatus
from open_notebook.i2i.handlers import dispatch, get_handler, registered_types
from open_notebook.i2i.router import router, _well_known_router
from open_notebook.i2i.poller import start_poller, stop_poller

__all__ = [
    # Version
    "__version__",
    # Models
    "Bottle",
    "BottleEnvelope",
    "BottleType",
    "VesselStatus",
    # Handlers / Dispatch
    "dispatch",
    "get_handler",
    "registered_types",
    # Router
    "router",
    "_well_known_router",
    # Poller
    "start_poller",
    "stop_poller",
]
