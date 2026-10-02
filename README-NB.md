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
- `tools/pin_nb.py` — 19 FAIL-first pins, all GREEN (cycle refusal, memo
  cascade, receipt determinism, coverage, honest verdicts, witness law,
  mutant-battery spec grading).
- Legacy tree (open_notebook, api/, vessels) untouched on this branch.
- Queued seams: quilt-canvas-tui live board (read bridge/controller.mjs
  unix-socket protocol; render cell DAG + port verdicts as quilt blocks);
  pip packaging (`pyproject` + `pip install -e .` removes the PYTHONPATH
  shim in pins).

## The mutant op (spec-coverage as a first-class metric)

A `mutant` cell binds a SPEC cell (first dep) + defines `cand` (reference
impl) in code, and grades the SPEC: a deterministic battery of 9 output
corruptions (zero, const, negate, scale, offset, reverse, head_dup,
drop_last, nan_inj) + 3 input transforms (shift/scale/negate) is run,
each marked killed/survived under STRICT comparison (exact length + 1e-6).
`coverage = killed/total` moves with spec quality: the demo softmax spec
scores 0.9167; a degenerate one-vector spec scores 0.5833 with the
surviving mutants named (`weakest`). Honest boundaries, by design:
- coverage is a FLOOR, not a verdict — a survived input-transform can be a
  correct invariance of the function (softmax legitimately survives
  `shift_input`); the metric reports, humans interpret.
- `port_zip_holes` names mutants the port op's zip-compare would silently
  pass (`drop_last`: strict length catches it, zip truncates and passes).
  Booked as evidence; port semantics unchanged on this branch.
- a mutant that crashes or emits non-JSON-plain output is killed with the
  evidence booked (witness law applies to mutants too).
