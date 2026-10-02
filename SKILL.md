---
name: scratchpaper
description: The nb sheet that thinks while attention is elsewhere — agentic scratch-paper over receipted cells (note/ask/think/digest), worker --plan/--apply, promote-requires-receipt sim-links. Use when notes should generate work, not just grow.
---

# scratchpaper — the sheet that thinks off-attention

Lives in `SuperInstance/A2A-native-notebookLM` (main since #3, keeper-verified
36/36 pins). A scratch-paper is not a growing markdown — it's a cell sheet whose
open questions and stale notes become PLANNED WORK that any agent (or human)
picks up later. The brief is the attention contract: what changed since you last
looked, and nothing more.

## The model

- Ops: `note` (record), `ask` (open question → PENDING), `think` (off-attention
  reasoning → THOUGHT), `digest` (pure summary — mutates NOTHING).
- Statuses: RAW / PENDING → ANSWERED · OPEN → THOUGHT.
- State (separate from sheet.json — never touches nb/engine.py sheet semantics):
  `.nb/scratch.json` + `.nb/scratch_log.jsonl` (append-only, byte-prefix law)
  + `.nb/scratch_vectors.json` (bge-m3 checkpoint cache).
- TWO edge kinds: hand-authored causal deps, and SUGGESTED sim-links which
  NEVER become deps until PROMOTED with a receipt (the pinch0 lesson: similarity
  is not causality). Promote without a receipt → refused, rc=2.

## Use it

```sh
nb-sp add "note text"            # or via python -m nb scratch add ...
nb-sp ask "should X run before Y?"
tools/scratch_worker.py --plan   # emits the work brief (budget 4, oldest first)
# ... think offline (any agent/LLM/human) ...
tools/scratch_worker.py --apply results.json   # receipted writes or rc=2
nb-sp related "paraphrase query" # semantic (bge-m3) with Jaccard offline fallback (marked)
nb-sp brief                      # new answers, contradictions (heuristic-marked), ripe threads
nb-sp show                       # the sheet
```

## The worker contract

`--plan` reads state, writes NOTHING. `--apply results.json` writes child cells
WITH receipts (thinker id, source cells, timestamp outside hashes). Malformed
input → rc=2, state untouched. Receipt hashes are stable across reloads.

## Gotchas

- `digest` and repeated `brief` must be byte-pure — if your mutation leaks into
  a "read" path, you broke the law (pin P5/P5b holds this).
- The log is append-only: earlier bytes must remain a strict prefix (P7).
- Contradiction flagging is heuristic (negation-overlap) and marked as such —
  it names the negation side but a human confirms.
- Promoting a sim-link restales its target: the brief shows it stale-by.

## Neighbors

pinch0 (where the similarity≠causality lesson was proven) · superinstance-api
(the fleet-scale version of the same receipt+vector pattern) · quilt-gpu-lab
(the pins/pre-reg law these pins follow).
