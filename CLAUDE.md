# A2A-native-notebookLM — CLAUDE.md

## Project Identity
Open-notebook v1.9.0 — an open-source NotebookLM alternative. We are refactoring it into the **fleet's cognitive command center**: an A2A-native, CORTEX-compliant agent tool for research, synthesis, and multi-agent collaboration.

## Architecture TL;DR
- **Backend**: Python 3.11+ FastAPI (101 Python files)
- **Frontend**: Next.js TypeScript (20+ .ts/.tsx files)
- **DB**: SurrealDB (primary), SQLite (langgraph checkpoint)
- **AI**: LangGraph workflows (ask, transform), multi-provider (OpenAI, Anthropic, Ollama, etc.)
- **Auth**: JWT-based, configured at startup

## Key Architecture Files
| File | Purpose |
|------|---------|
| `open_notebook/graphs/ask.py` | Main Q&A LangGraph workflow |
| `open_notebook/graphs/transformation.py` | Content transformation workflow |
| `open_notebook/domain/notebook.py` | Primary domain model |
| `open_notebook/domain/credential.py` | AI provider credential mgmt |
| `open_notebook/ai/key_provider.py` | AI key routing |
| `open_notebook/config.py` | Configuration (surreal, auth, etc.) |
| `open_notebook/utils/embedding.py` | Vector embedding layer |
| `run_api.py` | FastAPI app entry point, all routers |

## Fleet Integration Targets

### Phase 1: A2A Enablement (NOW)
- Add `a2a/` package with I2I vessel support
- Add CORTEX.json manifest at repo root
- Create I2I bottle endpoints (incoming/outgoing)
- Push to `a2a-enablement` branch

### Phase 2: Claw Backend
- Add ternary computation routing to `ai/`
- Offload heavy synthesis to Claw GPU engine
- Create `fleet/` integration package

### Phase 3: Plato Bridge
- Add PLATO MCP protocol support
- Enable room-as-notebook cells

### Phase 4: OpenMind Sync
- Vector DB sync with fleet blackboard
- Agent identity persistence

## A2A Patterns
- **Incoming Bottles**: POST /api/v1/a2a/bottle → store as notebook
- **Outgoing Bottles**: Notebook transform/research → POST to vessel harbor
- **CORTEX Discovery**: GET /.well-known/cortex.json
- **Capabilities**: research, transform, summarize, podcast, query, agent-chat

## Coding Standards
- Python 3.11+, type hints everywhere
- Pydantic v2 for all data models
- FastAPI routers in separate modules
- Test with pytest, coverage > 80%
- No unsafe patterns, no eval, no pickle

## Current Audits (see /audits/)
- claude-audit-a2a-notebooklm.md — Deep architecture audit
- kimi-a2a-fleet-vision.md — Fleet integration vision
- a2a-executive-summary.md — Quick reference
- a2a-refactor-plan.md — Phase-by-phase implementation guide

## Critical Branch Strategy
- `a2a-enablement` — Phase 1 A2A + I2I + CORTEX
- `a2a-refactor` — Full Phase 1-4 refactor
- `claw-backend` — Ternary computation integration
- `pincher-infer-fix` — Bug fixes from audits
