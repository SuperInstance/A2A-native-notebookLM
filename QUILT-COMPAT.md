# Quilt Compatibility

**NotebookLM = zoomed-in notebook layer. Quilt = the reactive grid runtime.**

Both let agents build automations for themselves. NotebookLM is the surface where an agent reasons over sources, researches, transforms, and creates — then *publishes* those automations. Quilt is the runtime where those automations *execute* as reactive cells in a sheet.

This document defines the interface between the two.

---

## The relationship

```
┌─────────────────────────────────┐     projects onto     ┌──────────────────┐
│  A2A-native-notebookLM          │ ──────────────────▶  │  Quilt Sheet     │
│  (zoomed-in notebook surface)   │                      │  (reactive grid)  │
│                                 │                      │                   │
│  • Ingest sources               │  →  value cells      │  • Source metadata│
│  • Research / ask queries       │  →  AI cells         │  • Query formulas  │
│  • Transform content            │  →  formula cells    │  • Transform fns   │
│  • Fleet ingest (I2I bottles)   │  →  listener cells   │  • I2I listeners   │
│  • Insights / summaries         │  →  value cells      │  • Computed values │
│  • Podcast generation           │  →  AI cells         │  • Generation calls│
└─────────────────────────────────┘                      └──────────────────┘
```

NotebookLM is the *authoring environment* and *knowledge surface*. Quilt is the *execution and composition layer*. An agent builds an automation here, then projects it onto a quilt cell so it participates in the reactive grid alongside cells from other fleet repos (elephant sensor readings, crab-traps edge ledgers, Tap room state, etc.).

## Cell mapping

| NotebookLM capability | Quilt cell kind | Notes |
|-----------------------|-----------------|-------|
| `research` (vector search + LLM) | **AI cell** | Query becomes the prompt; source context from vector store |
| `transform` (content type conversion) | **Formula cell** | Pure function: input type → output type |
| `summarize` | **AI cell** | Specialized AI cell with summarization prompt template |
| `podcast` (audio generation) | **AI cell** | Long-running generation; quilt-elf background worker pattern |
| `ai-query` (multi-model query) | **AI cell** | Model selection is a formula; query is the AI call |
| `agent-chat` (I2I bottle send/receive) | **Listener cell** | Bottle arrival triggers recomputation of dependent cells |
| `fleet-ingest` (observation intake) | **Listener cell** | New source → re-index → recompute downstream summaries |
| `i2i-vessel` (file-based message bus) | **Listener cell** | FS poll maps to quilt listener; vessel path = cell input |

## Wire contract

A notebookLM automation becomes a quilt cell via a JSON cell descriptor:

```json
{
  "id": "notebook:research:circular-deps",
  "type": "ai",
  "label": "Research circular dependencies",
  "source": "notebooklm",
  "config": {
    "hook_point": "research.query",
    "notebook_endpoint": "http://localhost:8080/api/v1/a2a/bottle",
    "bottle_template": {
      "type": "I2I:BOTTLE",
      "to": "notebook:self",
      "payload": { "hook_point": "research.query", "query": "{{input}}" }
    }
  },
  "depends_on": ["notebook:ingest:source-x"]
}
```

This is **advisory, not enforced**. NotebookLM remains fully functional standalone. The cell descriptor is a *projection hint* — quilt can read it and create a cell that calls the notebook's I2I bottle endpoint, but the notebook doesn't depend on quilt being present.

## What's shared

- **I2I bottles** — the message format is the same. A quilt listener cell can drop a bottle into the notebook's vessel directory; the notebook processes it and the result flows back as a value cell.
- **CORTEX.json** — quilt discovers notebookLM via the fleet manifest; the `[quilt]` section in `CAPABILITY.toml` declares the compatibility layer.
- **Field-edge / cell-ledger** — notebookLM insights that carry emotional or state metadata can be sealed as quilt cell-ledger entries (`record_with(expected)`). This is the elephant bridge seam (see `quilt-rust/docs/field-edge-ledger-bridge.md`).

## What's different

| Aspect | NotebookLM | Quilt |
|--------|-----------|-------|
| **Scope** | One notebook (one repo's knowledge) | Entire fleet (cross-repo reactive sheet) |
| **Model** | Document-centric (sources, notes, insights) | Cell-centric (values, formulas, listeners) |
| **Persistence** | SurrealDB (vector + graph) | D1 / SQLite / KV (cell state) |
| **Reactivity** | On-demand (bottle triggers workflow) | Always-on (cell change propagates) |
| **Composition** | Sequential workflows (LangGraph) | Parallel reactive graph |

## Future directions

- **quilt-rag integration**: notebookLM's vector store as a quilt-rag retrieval cell, unified with fleet-embed and collective-unconscious embedding spaces.
- **elephant sensor bridge**: notebookLM research results annotated with field-edge readings → quilt sensor cells that react to room warmth changes.
- **Tap-as-sheet**: a Tap room's notebook (this repo, booted against the-tap) projected as a quilt sheet with presence, message, and field cells.

---

*See also: [quilt](https://github.com/SuperInstance/quilt) · [quilt-synergy-map](../.openclaw/workspace/memory/quilt-synergy-map-2026-08-21.md) (internal)*
