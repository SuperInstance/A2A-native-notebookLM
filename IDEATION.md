# IDEATION.md: A2A-native-notebookLM — Fleet Cognitive Command Center

> **From open-source NotebookLM to the fleet's cognitive command center.**  
> This document is the north star — the unified vision synthesizing 27+ audit reports, architecture documents, and fleet integration plans.  
> It's not a specification. It's an invitation.

---

## 1. The Big Picture

### What This Becomes

**open-notebook** (v1.9.0) is a mature, production-grade open-source alternative to Google NotebookLM — 101 Python files, LangGraph workflows, SurrealDB-backed vector store, 18+ AI providers, and a beautiful Next.js frontend. It's earned 19k+ GitHub stars by being genuinely useful: a research assistant that respects your privacy.

But that's only the beginning.

This project is becoming the **Cognitive Command Center** for the SuperInstance fleet — the central nervous system that connects ternary GPU compute, educational simulations, living spreadsheets, and AI agents into a single coherent intelligence layer.

### How It Serves the Fleet

| Fleet Product | What open-notebook Becomes |
|---|---|
| **openConstruct** | The A2A-native vessel and CORTEX-compliant agent that all other fleet agents talk to |
| **Claw GPU Engine** | The research synthesis backend — heavy computation offloaded from Python to ternary GPU grids |
| **AI-Pasture** | The documentation/journal layer for every player's farm — NPCs research through notebook content |
| **Plato-as-Computer** | The native UI for PLATO room interactions — every room gets a notebook as its working memory |
| **Living Spreadsheet** | Sources and notes become spreadsheet cells — notebooks become the human-readable face of ternary computation |
| **OpenMind** | The long-term memory substrate — vector DB sync with fleet blackboard |
| **All Fleet Agents** | The collaboration platform — multi-agent research orchestration via I2I bottle protocol |

### The Core Thesis

> One notebook platform. Connected to every fleet agent.  
> Research tasks arrive as I2I bottles. Agents collaborate via the A2A protocol.  
> Heavy synthesis runs on the Claw GPU engine. Results persist as notebook sources, notes, and insights.  
> Every agent has a notebook. Every notebook is part of the fleet brain.

---

## 2. Architecture Vision

### Current State (v1.9.0)

```
┌─────────────────────────────────────────────┐
│  Frontend (Next.js 14 / TypeScript / Svelte) │
│  - i18n (15 locales), shadcn/ui components   │
│  - 20+ .ts/.tsx files                        │
└─────────────────┬───────────────────────────┘
                  │ HTTP REST (JSON/FormData)
                  ▼
┌─────────────────────────────────────────────┐
│  FastAPI Backend (Python 3.11+)             │
│  - 18 routers under /api/                   │
│  - PasswordAuthMiddleware (Bearer token)     │
│  - 101 Python files                         │
└─────────────────┬───────────────────────────┘
                  │ async Python
                  ▼
┌─────────────────────────────────────────────┐
│  LangGraph Workflows                        │
│  - ask.py: Multi-agent parallel RAG         │
│  - chat.py: Conversational with persistence │
│  - source.py: Content processing pipeline   │
│  - transformation.py: Content transforms    │
└──────┬──────────────────────┬───────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐ ┌──────────────────────────┐
│  SurrealDB   │ │  SQLite (LangGraph state) │
│  - Graph/doc │ │  - Chat session checkpts  │
│  - Vector    │ │                           │
│  - 14 migrations│                         │
└──────────────┘ └──────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  Esperanto AI Factory Layer                 │
│  - 18+ AI providers (OpenAI, Anthropic,     │
│    Ollama, DeepSeek, Groq, etc.)            │
│  - Model discovery & provisioning           │
│  - Encrypted credential management          │
└─────────────────────────────────────────────┘
```

This is already impressive. But it's a standalone app. It has no idea other agents exist.

### Target State (A2A-native, Fleet-Integrated)

```
┌────────────────────────────────────────────────────┐
│                  THE FLEET BRAIN                    │
├────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │         A2A-native-notebookLM                │  │
│  │         (Cognitive Command Center)           │  │
│  │                                              │  │
│  │  ┌──────────────────────────────────────┐   │  │
│  │  │  Existing Stack (v1.9.0 unchanged)   │   │  │
│  │  │  + A2A hooks at every graph node     │   │  │
│  │  │  + I2I vessel for bottle exchange    │   │  │
│  │  │  + CORTEX.json manifest              │   │  │
│  │  │  + SMP seed identity                 │   │  │
│  │  │  + Claw GPU bridge for heavy ops     │   │  │
│  │  │  + PLATO MCP bridge for rooms        │   │  │
│  │  └──────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────┘  │
│                    ↕ I2I BOTTLES ↕                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Claw    │ │AI-Pasture│ │ Living           │   │
│  │  GPU     │ │ Farming  │ │ Spreadsheet      │   │
│  │  Engine  │ │ Sim      │ │ Ternary Cells    │   │
│  └──────────┘ └──────────┘ └──────────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  PLATO   │ │ Pincher  │ │ OpenMind /       │   │
│  │  Rooms   │ │ Sandbox  │ │ Fleet Blackboard │   │
│  └──────────┘ └──────────┘ └──────────────────┘   │
│                    ↕ CORTEX / I2I ↕                │
│  ┌──────────────────────────────────────────────┐  │
│  │         Construct Coordination               │  │
│  │         (Oracle1, Forgemaster, Oracle2)      │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└────────────────────────────────────────────────────┘
```

### Network Topology

```
                    ┌─────────────────┐
                    │   Fleet Agents  │
                    │  (Pincher, etc) │
                    └────────┬────────┘
                             │ I2I bottles (TASK, DELIVERABLE, SYNTHESIS)
                             ▼
┌─────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────┐  │
│  │           A2A-native-notebookLM              │  │
│  │                                              │  │
│  │  I2I Vessel ⟷ A2A Dispatcher ⟷ LangGraph    │  │
│  │                   │                          │  │
│  │         ┌─────────┼─────────┐               │  │
│  │         ▼         ▼         ▼               │  │
│  │    Research   Synthesis   Transform          │  │
│  │    (ask.py)   (claw)     (transform.py)     │  │
│  │                                              │  │
│  │         ┌──────────────────┐                │  │
│  │         │  SurrealDB       │                │  │
│  │         │  Vector Store    │                │  │
│  │         └──────────────────┘                │  │
│  └──────────────────────────────────────────────┘  │
│                    │                                │
│         ┌──────────┼──────────┐                    │
│         ▼          ▼          ▼                    │
│  ┌──────────┐ ┌────────┐ ┌─────────┐              │
│  │  Claw   │ │ PLATO  │ │ Fleet   │              │
│  │  GPU    │ │ Rooms  │ │ Black-  │              │
│  │  Engine │ │        │ │ board   │              │
│  └──────────┘ └────────┘ └─────────┘              │
└─────────────────────────────────────────────────────┘
```

---

## 3. Fleet Integration Map

| Fleet Product | Integration | Priority | Timeline |
|---|---|---|---|
| **openConstruct** | Full A2A protocol: CORTEX.json manifest, I2I vessel (bottle drop/beachcomb), SMP seed identity, A2A hooks in LangGraph graph nodes | **P0** | **Week 1** |
| **Claw GPU Engine** | Ternary compute backend for heavy synthesis: context ranking as ternary cellgrid, vector search reranking via tissue consensus, SMP-seeded deterministic context assembly | **P1** | **Week 2-3** |
| **AI-Pasture** | Educational agent notebook: each player gets a notebook, NPC advisors research through vector store, farm state written as notebook sources, A2A-queryable game state | **P2** | **Week 3-4** |
| **Living Spreadsheet** | Dynamic document as spreadsheet cells: notes become cells, sources become cellgrids, cross-notebook rigging for insight propagation, insight-to-mutation loop | **P3** | **Month 2** |
| **Plato-as-Computer** | AI notebook as OS interface: room-as-notebook, ensign state persisted as notebook state, construct-core integration via credential checks | **P4** | **Month 3** |
| **Pincher/Sandbox** | Receive fleet research tasks, dispatch sub-tasks via I2I, synthesize results, broadcast back | **P1** | **Week 2** |
| **Fleet Blackboard** | Vector DB sync with fleet-wide knowledge base, agent identity persistence | **P2** | **Week 4** |
| **OpenMind** | Long-term memory substrate — notebooks as agent memory, cross-session state persistence | **P3** | **Month 2** |

### Integration Depth per Product

| Product | Vessel | CORTEX | Hooks | Store | UI |
|---------|--------|--------|-------|-------|----|
| openConstruct | ✅ I2I bottle | ✅ CORTEX.json | ✅ A2A hooks | ✅ Fleet metadata | ⬜ |
| Claw GPU | ✅ Client | ⬜ | ✅ Ternary offload | ⬜ | ⬜ |
| AI-Pasture | ✅ Bridge | ⬜ | ⬜ | ✅ Notebook-as-journal | ✅ NPC UI |
| Living Spreadsheet | ⬜ | ⬜ | ✅ Mutation loop | ✅ Cell mapping | ✅ Sheet UI |
| Plato | ✅ Bridge | ⬜ | ⬜ | ✅ Room state | ✅ Room UI |
| Pincher | ✅ Vessel | ✅ CORTEX | ⬜ | ⬜ | ⬜ |

---

## 4. Implementation Roadmap

### Phase 1: A2A Enablement (Week 1)

**Goal:** Make the notebook speak the fleet's protocol. By end of week, any fleet agent can send a research task to the notebook and get a result back.

**New Files (10):**
```
open_notebook/i22/__init__.py      ← I2I protocol package
open_notebook/i2i/vessel.py         ← Bottle drop, beachcomb, harbor
open_notebook/i2i/bottle.py         ← Pydantic models (TASK, STATUS, DELIVERABLE, etc.)
open_notebook/i2i/harbor.py         ← Async harbor listener
open_notebook/i2i/router.py         ← Bottle type → handler mapping
open_notebook/i2i/beachcomber.py    ← Periodic scan cycle
open_notebook/fleet/__init__.py     ← Fleet orchestration package
open_notebook/fleet/cortex.py       ← CORTEX manifest loader
open_notebook/fleet/identity.py     ← SMP seed identity
open_notebook/fleet/registry.py     ← Capability registry
open_notebook/graphs/a2a_hooks.py   ← A2A interception hooks for LangGraph
open_notebook/a2a/__init__.py       ← A2A protocol package
open_notebook/a2a/interceptor.py    ← Graph node wrapper
open_notebook/a2a/dispatcher.py     ← Cross-notebook dispatch
open_notebook/a2a/contract.py       ← A2A contract enforcement
CORTEX.json                         ← Manifest at repo root
scripts/init-fleet.sh               ← Fleet init script
```

**Modified Files (12+):**
```
open_notebook/graphs/ask.py          ← 4 A2A hook points (strategy, query, answer, synthesis)
open_notebook/graphs/transformation.py ← 2 A2A hook points
open_notebook/graphs/source.py       ← I2I bottle after source processing
open_notebook/graphs/chat.py         ← A2A context injection
open_notebook/domain/notebook.py     ← SMP identity, fleet context
open_notebook/ai/provision.py        ← Ternary offload parameter
open_notebook/domain/base.py         ← fleet_metadata field
open_notebook/config.py              ← I2I paths, SMP seed path, Claw endpoint
api/main.py                          ← I2I lifecycle in lifespan()
api/routers/notebooks.py             ← Fleet-aware endpoints
pyproject.toml                       ← New dependencies
CLAUDE.md / README.md                ← Fleet mode docs
```

**New REST Endpoints (10):**
```
GET  /api/fleet/status       ← Fleet health & connected agents
GET  /api/fleet/cortex        ← Return CORTEX manifest
GET  /api/fleet/identity      ← SMP identity (public seed hash)
POST /api/fleet/broadcast     ← Drop I2I bottle
GET  /api/fleet/messages      ← Poll inbound harbor
POST /api/notebooks/{id}/fleet-broadcast
GET  /api/notebooks/{id}/fleet-status
POST /api/transformations/{id}/delegate
POST /api/a2a/dispatch
GET  /api/ternary/status     ← Claw GPU connectivity
```

**A2A Interception Points in LangGraph (8 total):**

```
ASK WORKFLOW:
  START → agent → [A2A-1] strategy generation delegation
        → trigger_queries → [A2A-2] sub-query routing to fleet
        → provide_answer → [A2A-3] fleet cache check / answer publish
        → write_final_answer → [A2A-4] fleet synthesis broadcast
        → END

TRANSFORM WORKFLOW:
  START → run_transformation → [A2A-5] delegation to fleet specialist
                              → [A2A-6] insight publish → END

SOURCE WORKFLOW:
  [A2A-7] broadcast new source availability → END

CHAT WORKFLOW:
  [A2A-8] fleet context injection before model call → END
```

**Key Design Decision:** All A2A hooks are **non-blocking**. If the fleet peer is unreachable, local logic proceeds normally. The notebook remains fully functional as a standalone app.

**Dependencies:** None (pure Python — standard library + existing deps)

### Phase 2: Claw Backend Integration (Week 2-3)

**Goal:** Heavy research synthesis runs on the Claw GPU engine instead of Python threads. The notebook becomes the smartest research tool in the fleet.

**New Files (5):**
```
open_notebook/ternary/__init__.py  ← Ternary bridge package
open_notebook/ternary/client.py    ← Async HTTP client to Claw
open_notebook/ternary/operations.py ← Offload-eligible op registry
open_notebook/ternary/synthesis.py  ← Heavy synthesis offloader
open_notebook/ternary/embed.py      ← GPU-accelerated embedding
```

**Key Integration Patterns:**

1. **Context Ranking as Ternary Computation:** The `ContextBuilder` that prioritizes sources/notes/insights becomes a ternary cell grid. Each context item maps to a cell whose `fitness` determines inclusion. Instead of Python-level sorting, we run `tick_all()` on a `CellGrid` and read the `consensus()`.

2. **Vector Search Reranking:** Raw embedding results populate a `Tissue` that runs consensus. Only cells that converge on `Choose` (+1) are surfaced. This eliminates low-signal results without arbitrary thresholding.

3. **SMP Seeds for Context Assembly:** Randomness in context selection (which sources when token budget is tight) adopts SMP seeding — producing deterministic, reproducible context assembly across runs.

4. **Heavy Synthesis Offload:** Large-context research queries (>100K tokens) are routed to the Claw GPU engine's `/synthesize` endpoint. Results stream back into the LangGraph pipeline.

**Modified:**
```python
# open_notebook/ternary/client.py
class ClawContextReranker:
    """Replace Python-level context priority with ternary tissue consensus."""
    
    async def rank_context_items(self, items) -> list[ContextItem]:
        # Map each item to a cell, run tick cycles, read consensus
        # Items with cell.ternary_value == +1 (Choose) are kept
```

### Phase 3: Fleet Intelligence (Week 3-4)

**Goal:** The notebook is no longer just a tool — it's an active participant in the fleet knowledge ecosystem.

**Key Deliverables:**

- **AI-Pasture Bridge:** Each player's farm gets a notebook. NPC advisors (SMP-seeded LLMs) research through the notebook's vector store before answering kids' questions. Farm state (crops, weather, market prices) written as notebook sources.

- **Multi-Agent Research Collaboration:** Implement the `ResearchCollaborator` pattern:
  ```
  Coordinator sends TASK to each specialist notebook
  → Specialist runs vector search, creates insights
  → Specialist sends DELIVERABLE back
  → Coordinator synthesizes all DELIVERABLEs → final answer
  ```

- **Fleet Context Injection:** Chat sessions can pull enriched context from fleet-wide knowledge. When a user asks a question, the notebook checks: "Has any fleet agent already answered something like this?"

- **PLATO MCP Protocol:** Add PLATO MCP support for room-as-notebook-cells. PLATO rooms can write state directly to notebooks.

### Phase 4: Convergence (Month 2-3)

**Goal:** The notebook is fully merged with the Living Spreadsheet, the Fleet Blackboard, and Plato-as-Computer.

**Key Deliverables:**

- **Living Spreadsheet Cells → Notebook Notes:** Every note becomes a spreadsheet cell. Every source becomes a cell grid. Cross-notebook connections create rigging networks. "Shaking" a notebook's consensus propagates through the fleet.

- **The Insight→Mutation Loop:** When a notebook generates an insight, it mutates the Living Spreadsheet:
  - Contradiction → OSCILLATE the target cell
  - Confirmation → STABILIZE
  - Novelty → SEED (inject new SMP seed)

- **Fleet Blackboard Sync:** Vector DB syncs bidirectionally with the fleet blackboard (OpenMind). Notebook content is queryable by any fleet agent.

- **Plato-as-Computer UI:** Room conversations, file uploads, and analysis results recorded as notebook sources and notes. Ensign state persisted across room sessions.

---

## 5. Strategic Significance

### Why This Matters for the Fleet

The ternary fleet has 195+ Rust crates, a GPU engine, educational simulations, and a new form of spreadsheet programming. What it doesn't have is a **human-friendly, general-purpose research interface**. open-notebook fills that gap perfectly:

- **It already works.** 19k GitHub stars, production-tested, 18 AI providers, beautiful UI. We're not building from scratch.
- **It's vector-native.** SurrealDB with full-text + vector search makes it a natural fleet knowledge substrate.
- **It has LangGraph.** The most sophisticated agent graph framework — and we can inject A2A hooks at every node boundary.
- **It's self-hosted.** Every fleet agent can run its own notebook instance. Privacy + sovereignty.

### What Makes It Unique

**The Cognitive Command Center is not just a "chat with your docs" tool.** It's:

1. **A research collaborator** — Fleet agents send each other tasks, delegate sub-queries, synthesize results, and learn from each other's answers.

2. **A memory substrate** — SMP seed identity persists across sessions. The notebook remembers who you are, what you've researched, and which fleet agents contributed.

3. **A ternary gateway** — Behind the familiar notebook UI, your research is processed by a GPU-accelerated ternary cell grid. You don't need to know what a `TernaryCell` is to benefit from it.

4. **A learning journal** — Every AI-Pasture player gets one. Every PLATO room gets one. Every OpenMind agent gets one. The notebook is the universal memory layer.

5. **A convergence point** — This is where the Living Spreadsheet, ternary physics, and human-readable research meet. Insights from the ternary grid become notebook insights. Notebook notes become spreadsheet cells.

### Competitive Advantage

| Aspect | NotebookLM (Google) | Other Open-Source | A2A-native-notebookLM |
|--------|-------------------|-------------------|----------------------|
| **AI Providers** | Gemini only | Usually 1-3 | **18+** |
| **Data Sovereignty** | Google servers | Self-hosted | Self-hosted + fleet-aware |
| **Multi-Agent** | None | None | **Full A2A/I2I protocol** |
| **GPU Acceleration** | Google internal | None | **Claw ternary GPU engine** |
| **Living Documents** | Static notes | Static notes | **Spreadsheet cells that predict/evolve** |
| **Educational** | None | None | **AI-Pasture bridge** |
| **Room Integration** | None | None | **PLATO MCP bridge** |
| **Fleet Identity** | Google account | Local auth | **SMP seed identity (portable across agents)** |

---

## 6. Developer Onboarding

### How to Start Contributing

You don't need to understand the entire ternary fleet to contribute to the Cognitive Command Center. Start here:

1. **Read the existing codebase:** `open_notebook/graphs/ask.py` is the heart of the research workflow. `open_notebook/domain/notebook.py` is the primary domain model. `run_api.py` is the FastAPI entry point.

2. **Understand the A2A hook pattern:** Look at `open_notebook/graphs/a2a_hooks.py` (Phase 1 deliverable). Each hook is a pre/post wrapper around a LangGraph node. The pattern is:
   ```python
   async def my_node(state, config):
       result = await a2a_pre_hook("POINT-ID", state)
       if result.is_handled:
           return result.payload
       # ... original logic ...
       await a2a_post_hook("POINT-ID", state, result)
       return result
   ```

3. **Pick a starting point:**

| Interest | Entry Point | Files to Read |
|----------|-------------|---------------|
| RAG pipelines | Ask workflow | `graphs/ask.py`, `domain/notebook.py` (vector_search) |
| Frontend | Notebook chat | `frontend/src/app/(dashboard)/notebooks/[id]/` |
| I2I protocol | Fleet messaging | `open_notebook/i2i/vessel.py`, `bottle.py` |
| GPU acceleration | Claw bridge | `open_notebook/ternary/client.py`, `synthesis.py` |
| CORTEX compliance | Fleet identity | `open_notebook/fleet/cortex.py`, `identity.py` |
| Testing | All of the above | `tests/test_i2i/`, `tests/test_a2a/` |

### Key Architectural Decisions to Know

1. **A2A hooks are non-blocking by default.** If the fleet is unreachable, the notebook works perfectly as a standalone app. This is inviolable.

2. **I2I uses file-based bottles.** Messages are JSON files in a shared vessel directory. No message broker, no pub-sub, no network dependency for basic operation.

3. **SMP seeds are optional.** The notebook assigns a random seed on init if none is configured. Fleet identity is an opt-in enhancement, not a requirement.

4. **The existing LangGraph workflow is preserved.** A2A hooks intercept at well-defined boundaries but never modify the internal graph logic. Every hook can be removed by deleting the decorator.

5. **Backward compatibility is paramount.** Existing users upgrading from v1.9.0 should see zero changes to their workflow. Fleet features are additive.

### Testing Strategy

| Layer | Approach | Coverage Target |
|-------|----------|----------------|
| **I2I protocol** | Unit tests for bottle model serialization, vessel read/write, harbor dispatch | 90%+ |
| **A2A hooks** | Integration tests: mock fleet agent, verify hook interception, test fallback behavior | 85%+ |
| **CORTEX manifest** | Validate CORTEX.json against schema, test discovery flow | 100% critical |
| **Claw bridge** | Integration: mock Claw GPU endpoint, verify offload/fallback logic | 80%+ |
| **Full workflow** | E2E: start notebook + mock fleet, send research task, verify result | 1 happy path + 3 edge cases |
| **Standalone mode** | All existing pytest tests must pass unchanged | 100% (no regressions) |

**Existing test base:** `tests/` directory (13 test files). Our goal: **no existing test breaks**, then add new tests for all new modules.

### Quick Start Development

```bash
# Clone and setup
git clone https://github.com/lfnovo/open-notebook
cd open-notebook

# Fleet mode (development)
cp .env.example .env
# Set: FLEET_MODE=true, I2I_BOTTLE_DIR=/tmp/i2i-vessel
docker compose up -d

# Standalone mode (production)
docker compose -f docker-compose.standalone.yml up -d
```

---

## Appendix: Reference Audit Documents

This IDEATION.md synthesizes the following audits and vision documents:

| Document | Focus |
|----------|-------|
| `audits/claude-audit-a2a-notebooklm.md` | Deep architecture audit (101 Python files, LangGraph, SurrealDB, security) |
| `audits/kimi-a2a-fleet-vision.md` | Fleet integration vision (Claw, AI-Pasture, Living Spreadsheet, PLATO) |
| `audits/a2a-executive-summary.md` | Quick reference (what it is, stack, data model, AI providers) |
| `audits/a2a-refactor-plan.md` | Phase-by-phase implementation guide (file list, API changes, hook points) |
| `audits/kimi-cortex-synthesis.md` | Unified CORTEX spec (manifest schema, skill types, discovery flow) |
| `audits/kimi-product-convergence.md` | The Construct product vision (Claw + AI-Pasture + Living Spreadsheet) |
| `audits/fleet-improvement-roadmap.md` | Fleet health dashboard (critical fixes, priorities, grades) |
| `audits/kimi-remaining-docs.md` | Deep architecture papers (FLEET-NEURO, SMP, RECURSION, ZERO-SPINDLE, SPECULATIVE-SYNC) |

---

*This document is a living artifact. As the project evolves, update it. As new audits are produced, absorb them. As the fleet grows, extend the map.*

*The Cognitive Command Center is not a destination. It's how we research together.*
