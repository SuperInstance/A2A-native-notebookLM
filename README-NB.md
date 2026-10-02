# nb — spreadsheet-logic notebook core (rebuild track)

The rebuild of A2A-native-notebookLM as Kimi scoped it (2026-10-02): a
spreadsheet-logic engine for porting ML/RL/NN/DL functions, drivable three
ways by the same sheet state (`.nb/sheet.json`):

| mode | surface | use |
|---|---|---|
| headless agent runs | `python3 -m nb.cli add/eval/get/graph/receipts` | agents work alone, receipts in-repo |
| deployment | `python3 -m nb.mcp_server` (stdio MCP, 5 tools) | any MCP client drives the sheet |
| human watching | `nb graph` JSON → quilt-canvas-tui board payload (seam queued) | live port review next to the quilt |

## The model

A sheet is a DAG of cells. Each cell: `{id, deps, op, code}` with
`op ∈ {const, py, port}`.

- **Spreadsheet logic**: eval is topological + memoized by content sig
  (code + upstream receipts). Touch one spec cell → ONLY downstream cells
  re-eval (pin L1c proves the cascade set exactly).
- **Porting**: a `port` cell binds its FIRST dep as a SPEC cell (test
  vectors) and its code defines `cand`. The verdict is honest: candidate
  crashes (e.g. `OverflowError` from a missing max-subtraction) are booked
  as FAIL evidence, never hidden. Port contract tolerance 1e-6 (spec
  vectors are receipts-grade, 8dp).
- **Witness law**: every cell value must be JSON-plain — functions cannot
  flow between cells because functions cannot be witnessed (refusal policy
  keeps the field provable; exoj doctrine). Refused with a clear error
  (pin L6).
- **Receipts**: per-cell sha256 sigs of {id, op, code, upstream receipts,
  output}; bit-identical across reloads (pin L2). Timestamps appear in
  commit messages, never inside receipt hashes.

## Why this design (porting ML functions)

The demo in `tools/pin_nb.py` is the proof of value: the softmax spec
started with 3 small vectors and the mutant (no max-subtraction) PASSED —
softmax is shift-invariant, small vectors can't kill it. The sheet caught
this the way a good reviewer would: the spec grew a `[1000,1001,1002]`
vector, the mutant overflowed, verdict flipped to FAIL with the error
booked as evidence. **The spec is the product; cells are its editors.**

## Status

- `nb/engine.py` + `nb/cli.py` + `nb/mcp_server.py` — stdlib only.
- `tools/pin_nb.py` — 11 FAIL-first pins, all GREEN (cycle refusal, memo
  cascade, receipt determinism, coverage, honest verdicts, witness law).
- Legacy tree (open_notebook, api/, vessels) untouched on this branch.
- Queued seams: quilt-canvas-tui live board (read bridge/controller.mjs
  unix-socket protocol; render cell DAG + port verdicts as quilt blocks);
  pip packaging (`pyproject` + `pip install -e .` removes the PYTHONPATH
  shim in pins); a `mutant` op (auto-generate port mutants to grade spec
  strength — spec-coverage as a first-class metric).
