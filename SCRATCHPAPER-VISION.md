# Scratchpaper — the nb sheet that thinks while you're away

Date: 2026-10-02. Author: Lucineer (directive: Casey 08:03 — "an agentic
scratch-paper that's far more than just keeping notes in a growing
collection of markdowns. the scratchpaper thinks while your attention is
elsewhere").

## The problem with markdowns

The fleet's scratch is a pile of `scratch/*.md` and `memory/YYYY-MM-DD.md`.
Notes are inert: they wait passively until someone re-reads them. Open
threads die in file bottoms. Nothing contradicts anything. Nothing ripens.

## The scratchpaper model

Same engine discipline as the port sheet — DAG of receipted cells, memoized
eval, honest verdicts — with a **thinking op family** and a **worker**:

| op | meaning | status path |
|----|---------|-------------|
| `note` | capture a thought in one line | RAW |
| `ask` | a question that wants an answer | PENDING → ANSWERED |
| `think` | expansion pass on parent cell(s): objections, consequences, designs, next questions | OPEN → THOUGHT |
| `digest` | consolidate a cell's children into a brief | (pure — no state change) |

State: `.nb/scratch.json` (cells) + `.nb/scratch_log.jsonl` (append-only
mutation log, pong-quilt draw-ledger discipline) + `.nb/scratch_vectors.json`
(embedding cache). Separate from the port sheet (`sheet.json`) so the two
instruments never interfere.

### Similarity ≠ wiring (the referral-graph lesson)

Pinch0 (2026-10-02, commit b639aea) proved: bge-m3 retrieves descriptions
near-perfectly (10/10 rank-1) but similarity is NOT verified wiring — edges
need their own receipts. So the scratchpaper has TWO edge kinds:

- **DAG deps** — hand-authored, causal (this thought builds on that one).
  Change the parent, the child is stale. Same memo-cascade law as ports.
- **sim-links** — SUGGESTED by embedding cosine (bge-m3 via CF free tier,
  Jaccard fallback offline). A sim-link NEVER becomes a dep until a worker
  or the agent PROMOTES it, with a receipt saying why. PENDING → VERIFIED,
  exactly the quilt-tools referral-graph discipline applied to my own
  thinking.

### The worker is a clerk, not a daemon

`tools/scratch_worker.py` is the ledger interface, not the thinker:

- `--plan` — emit pending work as a brief: PENDING asks (oldest first),
  RAW notes older than the think-threshold, SUGGESTED sim-links above
  threshold, budget-capped (default 4 items).
- `--apply results.json` — write a thinker's results as child cells with
  receipts (who thought it, from what, when). Refuses malformed input rc=2.

The THINKER is an agent lane (OpenClaw cron, isolated turn, every ~30 min):
run `--plan`, think each item, hand back results JSON via `--apply`. v1 the
clerk is a main-fleet lane; later slots can rotate to cheaper models. The
paper thinks while attention is elsewhere because the cron clerk shows up
when nobody's watching.

### Agent-first surfaces

- `sp add "text"` — capture in seconds, from chat, from a lane, from anywhere.
- `sp ask "question"` — hand a question to the paper, walk away.
- `sp plan` / `sp apply` — the clerk loop.
- `sp related <id|text>` — top-k cells by semantic similarity.
- `sp brief` — THE ATTENTION CONTRACT: what changed since last seen. New
  answers, contradictions between cells, threads gone ripe, stale deps.
  One screen. This is what you read when you come back.
- `sp show <id>` — cell + children + links + receipts.

## Why this beats a notes app

1. **Statuses make threads live.** A PENDING ask is work-in-queue, not a
   sentence in a file nobody opens.
2. **Receipts make thinking auditable.** Every answer carries its provenance
   (champion-integrity law: a ledger of receipts is not evidence the
   receipts are true — so answers cite what they're built from).
3. **Memoization makes thought cheap to revisit.** Touch one premise, only
   dependent conclusions restale. The paper knows what your new information
   actually invalidates.
4. **The witness law holds for thoughts.** Cells are JSON-plain text; the
   field stays provable.

## Build order

1. `nb/scratch.py` — ops + state + log (stdlib only, house laws).
2. CLI verbs in `nb/cli.py` (`add/ask/plan/apply/related/brief/show`).
3. `tools/scratch_worker.py` (--plan/--apply, budget, malformed-refusal).
4. FAIL-first pins in `tools/pin_scratch.py` (round-trip, budget cap,
   malformed apply refused, offline related fallback, sim-link promote
   requires receipt, digest purity).
5. Semantic `related` via bge-m3/urllib, wrangler-OAuth fallback chain
   (pattern: quilt-gpu-lab scratch/pinch0/cf_embed.py).
6. Cron clerk wiring + first live seed (fleet threads as cells) — the
   experiment: does handing notes to the paper replace holding them?

## Seeded experiment (2026-10-02)

First cells are real open threads, captured the moment this vision was
written — the paper's first job is thinking about its own gaps plus the
fleet's open questions while attention is on the build lanes.
