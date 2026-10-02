#!/usr/bin/env python3
"""scratch_worker — the clerk, not the daemon (SCRATCHPAPER-VISION.md).

The THINKER is an agent lane (e.g. an OpenClaw cron clerk on an isolated
turn). The worker is only the ledger interface between that lane and the
paper:

  scratch_worker.py --plan [--budget 4] [--think-threshold 45]
      Emit pending work as a brief JSON: PENDING asks (oldest first),
      RAW notes past the think-threshold, OPEN think cells, and SUGGESTED
      sim-links above threshold. PURE — mutates nothing.

  scratch_worker.py --apply results.json
      Write the thinker's results as receipted child cells (thinker id,
      source cells, timestamp outside hashes). Refuses malformed input
      with rc=2 BEFORE any mutation.

Exit codes: 0 ok, 2 refused (malformed input, invalid transitions).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nb.scratch import Scratch, ScratchError  # noqa: E402


def main(argv=None):
    p = argparse.ArgumentParser(prog="scratch_worker", description="scratchpaper clerk (ledger interface)")
    p.add_argument("--root", default=".", help="paper root (default cwd)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true", help="emit pending work brief (pure)")
    g.add_argument("--apply", metavar="RESULTS_JSON", help="apply thinker results (receipted)")
    p.add_argument("--budget", type=int, default=4)
    p.add_argument("--think-threshold", type=float, default=45.0)
    p.add_argument("--link-threshold", type=float, default=None)
    p.add_argument("--out", default=None, help="write plan to file as well as stdout")
    args = p.parse_args(argv)
    sp = Scratch(Path(args.root))
    try:
        if args.plan:
            plan = sp.plan(budget=args.budget,
                           think_threshold_min=args.think_threshold,
                           link_threshold=args.link_threshold)
            text = json.dumps(plan, indent=1)
            if args.out:
                Path(args.out).write_text(text + "\n")
            print(text)
            return 0
        # --apply: read + validate BEFORE any mutation (fail-loud rc=2)
        try:
            doc = json.loads(Path(args.apply).read_text())
        except FileNotFoundError:
            raise ScratchError("results file not found: %s" % args.apply)
        except json.JSONDecodeError as e:
            raise ScratchError("results file is not valid JSON: %s" % e)
        if not isinstance(doc, dict):
            raise ScratchError("results doc must be a JSON object")
        written = sp.apply_results(doc)
        print(json.dumps({"applied": True, "thinker": doc.get("thinker"),
                          "written": written}, indent=1))
        return 0
    except ScratchError as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 2
    except KeyError as e:
        print("REFUSED: unknown id %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
