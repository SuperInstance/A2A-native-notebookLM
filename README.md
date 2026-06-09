# A2A-native-notebookLM

<div align="center">

### The Fleet's Cognitive Command Center

**An A2A-native, CORTEX-compliant research & synthesis agent — built on open-notebook v1.9.0**

[![I2I Protocol](https://img.shields.io/badge/protocol-I2I%20v2.1-blue?style=flat-square)](open_notebook/i2i/)
[![A2A Native](https://img.shields.io/badge/A2A-native-green?style=flat-square)](open_notebook/a2a/)
[![CORTEX](https://img.shields.io/badge/CORTEX-manifest-orange?style=flat-square)](CORTEX.json)
[![Forked from lfnovo/open-notebook](https://img.shields.io/badge/forked%20from-open--notebook%20v1.9.0-3776AB?style=flat-square)](https://github.com/lfnovo/open-notebook)

</div>

---

## What Is This?

This is a **fork** of [open-notebook](https://github.com/lfnovo/open-notebook) (v1.9.0, 19k+ ⭐) — the leading open-source alternative to Google NotebookLM — extended into an **A2A-native notebook that lives in your repository** and participates in the **SuperInstance fleet** as a cognitive command center.

**The repo is the mind. The notebook lives inside it.**

Instead of bringing your code to an AI tool, you bring the AI tool *into your repository*. Clone it, boot it, and it ingests your entire codebase — all source files, docs, READMEs, commit messages, PR descriptions — into a persistent, bootable, networked cognitive workspace that any agent (or human) can talk to.

### What's Different From Upstream

| Layer | open-notebook (upstream) | A2A-native-notebookLM |
|-------|------------------------|----------------------|
| **Core stack** | FastAPI + Next.js + SurrealDB + LangGraph | **Same** — unmodified upstream core |
| **Agent protocol** | None (standalone app) | **I2I vessel protocol** (`open_notebook/i2i/`) |
| **Fleet identity** | Local auth only | **CORTEX.json manifest**, SMP seed identity |
| **Agent hooks** | No agent awareness | **A2A hooks** in LangGraph graph nodes (`open_notebook/a2a/`) |
| **Repository boot** | Docker compose only | `python cli.py boot /path/to/repo` — boot from any repo |
| **Fleet integration** | None | Talks to Construct Coordination, Claw GPU, AI-Pasture, Pincher, Living Spreadsheet |
| **"Notebook in a Repo"** | N/A | One persistent notebook per repository, bootable, versionable |

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│              A2A-native-notebookLM                 │
│             (Cognitive Command Center)             │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌────────────────────────────────────────────┐   │
│  │       Upstream Core (v1.9.0, unmodified)   │   │
│  │                                             │   │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  │   │
│  │  │ FastAPI  │  │ LangGraph│  │ SurrealDB│  │   │
│  │  │ Backend  │  │Workflows │  │ Vector + │  │   │
│  │  │ (101 py) │  │ask/chat/ │  │  Graph   │  │   │
│  │  │          │  │transform │  │  Store   │  │   │
│  │  └─────────┘  └──────────┘  └──────────┘  │   │
│  │                                             │   │
│  │  ┌──────────────┐  ┌────────────────────┐  │   │
│  │  │   Next.js    │  │  Esperanto AI      │  │   │
│  │  │   Frontend   │  │  18+ AI Providers  │  │   │
│  │  └──────────────┘  └────────────────────┘  │   │
│  └────────────────────────────────────────────┘   │
│                                                    │
│  ┌────────────────────────────────────────────┐   │
│  │          A2A / I2I Extensions              │   │
│  │                                             │   │
│  │  ┌────────────┐  ┌────────────────────┐   │   │
│  │  │ I2I Vessel  │  │ A2A Hooks          │   │   │
│  │  │ (file-based │  │ (8 interception    │   │   │
│  │  │  bottle bus)│  │  points in graphs) │   │   │
│  │  └────────────┘  └────────────────────┘   │   │
│  │                                             │   │
│  │  ┌────────────┐  ┌────────────────────┐   │   │
│  │  │ CORTEX     │  │ SMP Seed           │   │   │
│  │  │ Manifest   │  │ Identity           │   │   │
│  │  └────────────┘  └────────────────────┘   │   │
│  │                                             │   │
│  │  ┌────────────┐  ┌────────────────────┐   │   │
│  │  │ CLI Boot   │  │ Repo Ingest        │   │   │
│  │  │ System     │  │ Pipeline           │   │   │
│  │  └────────────┘  └────────────────────┘   │   │
│  └────────────────────────────────────────────┘   │
│                         ↕                          │
│                  I2I BOTTLES                        │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Claw    │ │AI-Pasture│ │ Living           │   │
│  │  GPU     │ │ Farming  │ │ Spreadsheet      │   │
│  │  Engine  │ │ Sim      │ │ Ternary Cells    │   │
│  └──────────┘ └──────────┘ └──────────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  PLATO   │ │ Pincher  │ │ Construct        │   │
│  │  Rooms   │ │ Sandbox  │ │ Coordination     │   │
│  └──────────┘ └──────────┘ └──────────────────┘   │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Network Topology

```
                    ┌─────────────────┐
                    │   Fleet Agents  │
                    │  (Pincher, etc) │
                    └────────┬────────┘
                             │ I2I bottles
                             ▼
┌─────────────────────────────────────────────────────┐
│  A2A-native-notebookLM                              │
│                                                     │
│  I2I Vessel ⟷ A2A Dispatcher ⟷ LangGraph           │
│                   │                                  │
│         ┌─────────┼─────────┐                       │
│         ▼         ▼         ▼                       │
│    Research   Synthesis   Transform                  │
│    (ask.py)   (claw)     (transform.py)             │
│                                                     │
│         ┌──────────────────┐                        │
│         │  SurrealDB       │                        │
│         │  Vector Store    │                        │
│         └──────────────────┘                        │
└─────────────────────────────────────────────────────┘
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
  ┌──────────┐ ┌────────┐ ┌─────────┐
  │  Claw   │ │ PLATO  │ │ Fleet   │
  │  GPU    │ │ Rooms  │ │ Black-  │
  │  Engine │ │        │ │ board   │
  └──────────┘ └────────┘ └─────────┘
```

---

## The I2I Vessel Protocol

The **I2I (Inter-agent-to-Inter-agent) vessel protocol** is a file-based message bus. Any agent — in any environment, on any machine — can participate by writing **bottles** to a shared directory.

### Bottle Types

| Type | Purpose | Example |
|------|---------|---------|
| `I2I:BOTTLE` | Raw message — query, task, notification | "Research this code pattern" |
| `I2I:SYNTHESIS` | Combined findings — research results | "Found 3 circular dependencies" |
| `I2I:ACK` | Acknowledgment — handshake, progress | "Received, processing..." |
| `I2I:CHALLENGE` | Disagreement — reconsideration request | "This contradicts earlier findings" |
| `I2I:CHECKPOINT` | State snapshot — pause/resume point | "Saving progress at step 4 of 7" |

### How Agents Communicate

**1. An agent drops a bottle into the notebook's vessel:**
```json
{
  "type": "I2I:BOTTLE",
  "from": "agent:refactor-assistant",
  "to": "notebook:my-project",
  "payload": {
    "hook_point": "research.query",
    "query": "Map all circular dependencies between modules A, B, and C"
  }
}
```

**2. The notebook processes it** — runs vector search, generates insights, updates its memory.

**3. The notebook drops a response bottle back:**
```json
{
  "type": "I2I:SYNTHESIS",
  "from": "notebook:my-project",
  "to": "agent:refactor-assistant",
  "payload": {
    "findings": "Found 3 circular dependencies involving modules A, B, C",
    "artifacts": ["analysis/circular_deps.md"]
  }
}
```

**No API code written. No endpoint designed. No database schema planned.** The I2I endpoint **IS** the API. The bottle format **IS** the schema. The notebook's existing capabilities (vector search, source ingestion, insight generation, podcast creation) **ARE** the available functions.

### Why File-Based?

Because files are the universal interface. They survive reboots. They can be version-controlled (commit your bottles to git). They require no HTTP server, no port configuration, no auth infrastructure. They are the simplest possible substrate for agent-to-agent communication.

---

## The "Notebook in a Repo" Vision

Every Git repository gets **one persistent notebook instance** that lives alongside the code:

```
my-awesome-project/
├── src/
├── tests/
├── docs/
├── CORTEX.json          ← Fleet manifest (identity, capabilities, vessel path)
├── README.md
└── ...
```

A `python cli.py boot /path/to/repo` command:
1. **Ingests** the entire codebase — all source files, docs, READMEs, commit messages
2. **Indexes** everything into SurrealDB with semantic embeddings
3. **Persists** every interaction — every question, answer, and insight
4. **Boots** from its saved state — remembers everything it learned
5. **Speaks I2I** — any agent can send it bottles, and it responds

This means **any agent can pick up where any other agent left off**. Research starts in one session, hits a blocker, drops a CHECKPOINT bottle — days later, a different agent picks it up and continues. No handoff meeting. No context rebuild.

> **"Notebook in a Repo" is not a plugin. It's a cognitive agent that lives in your repo.**

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for SurrealDB) or an existing SurrealDB instance
- API key for at least one AI provider (OpenAI, Anthropic, Ollama, etc.)

### 1. Clone & Install

```bash
git clone <this-repo>
cd A2A-native-notebookLM
pip install -e ".[dev]"
```

### 2. Set Up SurrealDB

```bash
docker run -d --name surrealdb \
  -p 8000:8000 \
  surrealdb/surrealdb:v2 \
  start --log info --user root --pass root rocksdb:/mydata/mydatabase.db
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your AI provider credentials and SurrealDB connection
```

### 4. Boot From a Repository

```bash
# Scan a repo to preview what will be ingested
python cli.py scan /path/to/your/repo --verbose

# Boot the notebook server from the repo
python cli.py boot /path/to/your/repo --port 8080
```

The notebook will:
- Scan and ingest all source files, docs, and git history
- Start the I2I vessel (FS poller listening for inbound bottles)
- Launch the FastAPI server with the Next.js frontend at `http://localhost:8080`

### 5. Send a Bottle

```bash
# Drop a research bottle into the notebook's vessel
echo '{
  "type": "I2I:BOTTLE",
  "to": "notebook:self",
  "payload": {
    "hook_point": "research.query",
    "query": "Explain the module architecture of this codebase"
  }
}' > /tmp/i2i-vessel/inbox/research-bottle.json
```

### 6. Boot With Docker (Standalone)

If you just want to run the notebook as a standalone app (no fleet features):

```bash
docker compose up -d
# Open http://localhost:8502
```

---

## Fleet Integration

A2A-native-notebookLM is designed to be the **cognitive command center** for the SuperInstance fleet. Here's how it connects:

| Fleet Product | Integration | Status |
|---|---|---|
| **Construct Coordination** | CORTEX.json manifest, I2I vessel (bottle drop/beachcomb), SMP seed identity, A2A hooks in LangGraph | ✅ Active |
| **Claw GPU Engine** | Ternary compute backend for heavy synthesis (context ranking, vector reranking) | 🔄 In Progress |
| **AI-Pasture** | Each player's farm gets a notebook; NPC advisors research through vector store | 📋 Planned |
| **Living Spreadsheet** | Notes become spreadsheet cells; cross-notebook insight propagation | 📋 Planned |
| **PLATO Rooms** | Room-as-notebook-cells; ensign state persisted as notebook state | 📋 Planned |
| **Pincher/Sandbox** | Receives fleet research tasks, dispatches sub-tasks via I2I, synthesizes results | 🔄 In Progress |
| **Fleet Blackboard (OpenMind)** | Vector DB sync with fleet-wide knowledge base | 📋 Planned |

### CORTEX Manifest

Every notebook publishes a `CORTEX.json` manifest at the repo root that declares its identity, capabilities, and vessel address. Fleet agents discover notebooks by reading published manifests in the construct-coordination layer.

```json
{
  "identity": {
    "name": "a2a-native-notebooklm",
    "version": "1.0.0-a2a",
    "description": "Fleet cognitive command center",
    "agent_type": "notebook"
  },
  "capabilities": [
    {"name": "research", "description": "Research a topic with sources"},
    {"name": "transform", "description": "Transform content types"},
    {"name": "summarize", "description": "Summarize documents"},
    {"name": "podcast", "description": "Generate podcast from content"},
    {"name": "ai-query", "description": "Query notebook with any model"},
    {"name": "agent-chat", "description": "Agent-to-agent chat via I2I"}
  ],
  "endpoints": {
    "bottle": "/api/v1/a2a/bottle",
    "capabilities": "/api/v1/a2a/capabilities",
    "cortex": "/.well-known/cortex.json"
  }
}
```

### A2A Hooks

The original LangGraph workflows (ask, transform, source, chat) have **8 A2A interception points** — non-blocking hooks that broadcast/subscribe to I2I bottles at key graph boundaries:

```
ASK WORKFLOW:
  START → [A2A-1] strategy delegation
        → [A2A-2] sub-query routing to fleet
        → [A2A-3] fleet cache check / answer publish
        → [A2A-4] fleet synthesis broadcast → END

TRANSFORM: [A2A-5] delegation, [A2A-6] insight publish
SOURCE: [A2A-7] broadcast new source
CHAT: [A2A-8] fleet context injection
```

All hooks are **non-blocking** — if the fleet is unreachable, local logic proceeds normally. The notebook remains fully functional as a standalone app.

---

## Project Structure (A2A Extensions)

```
open_notebook/
├── a2a/                    ← A2A protocol package
│   ├── __init__.py         ← Models, client, hooks
│   ├── models.py           ← Bottle, CORTEX manifest models
│   ├── vessel.py           ← Vessel client
│   ├── hooks.py            ← A2A graph hooks (before/after)
│   └── ...
├── i2i/                    ← I2I vessel protocol package
│   ├── __init__.py         ← Package version, exports
│   ├── models.py           ← Bottle, envelope, vessel status models
│   ├── handlers.py         ← Dispatch, handler registry
│   ├── router.py           ← FastAPI router for bottle endpoints
│   ├── poller.py           ← FS poller (beachcomber)
│   └── ...
├── fleet/                  ← Fleet orchestration (planned)
├── repo_ingest.py          ← Repository scanning & ingestion
├── graphs/
│   └── a2a_hooks.py       ← A2A interception hooks
├── ternary/                ← Claw GPU bridge (planned)
├── ...
CORTEX.json                 ← Fleet manifest
cli.py                      ← CLI boot system
```

---

## Upstream Credit

This project is a **fork** of [open-notebook](https://github.com/lfnovo/open-notebook) by Luis Novo — a brilliant open-source alternative to Google NotebookLM. The upstream is MIT-licensed and has earned 19k+ GitHub stars through years of careful engineering.

**The entire core stack** (FastAPI backend, Next.js frontend, SurrealDB integration, LangGraph workflows, Esperanto AI factory for 18+ providers, podcast generation, content transformations) is unmodified upstream code. The A2A-native additions live in `open_notebook/a2a/`, `open_notebook/i2i/`, `cli.py`, and `CORTEX.json` — additive layers that don't alter the upstream's behavior.

If you want the standalone, non-fleet version of this tool, use the upstream: [github.com/lfnovo/open-notebook](https://github.com/lfnovo/open-notebook)

---

## License

This project is MIT licensed (inherited from upstream open-notebook). See [LICENSE](LICENSE).

---

## Contributing

The A2A-native additions in this fork are maintained as part of the SuperInstance fleet ecosystem. Contributions are welcome:

- **I2I protocol enhancements** — new bottle types, routing logic, vessel implementations
- **Fleet integrations** — Claw GPU bridge, PLATO MCP, Living Spreadsheet sync
- **Repository ingestion** — better codebase parsing, dependency graph extraction
- **A2A hooks** — new graph interception points, fleet collaboration patterns

For the upstream codebase, contribute directly to [lfnovo/open-notebook](https://github.com/lfnovo/open-notebook).

---

### Related Documents

- [HERMES-NOTEBOOK-VISION.md](./HERMES-NOTEBOOK-VISION.md) — The "Notebook in a Repo" white paper
- [IDEATION.md](./IDEATION.md) — Full fleet cognitive command center vision
- [CLAUDE.md](./CLAUDE.md) — Project identity for AI coding agents
- [CORTEX.json](./CORTEX.json) — Fleet manifest
- [open_notebook/i2i/](./open_notebook/i2i/) — I2I vessel protocol package
- [open_notebook/a2a/](./open_notebook/a2a/) — A2A integration package
