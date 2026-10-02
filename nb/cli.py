"""nb.cli — headless agent runs: python3 -m nb.cli <cmd> in a repo."""
import argparse
import json
import sys
from pathlib import Path

from nb.engine import CycleError, Sheet


def main(argv=None):
    p = argparse.ArgumentParser(prog="nb", description="spreadsheet-logic notebook (headless)")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("id"); a.add_argument("--deps", default="")
    a.add_argument("--op", required=True, choices=["const", "py", "port", "mutant"])
    a.add_argument("--code", required=True, help="JSON literal (const) or python source (py/port)")
    sub.add_parser("eval"); sub.add_parser("get").add_argument("id")
    sub.add_parser("graph"); sub.add_parser("receipts")
    args = p.parse_args(argv)
    sheet = Sheet(Path.cwd())
    try:
        if args.cmd == "add":
            sheet.add(args.id, [d for d in args.deps.split(",") if d], args.op, args.code)
            sheet.save(); print(f"added {args.id} op={args.op}")
        elif args.cmd == "eval":
            log = []
            sheet.eval(eval_log=log)
            print(json.dumps({"evaled": log, "cells": len(sheet.cells)}))
        elif args.cmd == "get":
            print(json.dumps(sheet.values[args.id]))
        elif args.cmd == "graph":
            print(json.dumps(sheet.graph(), indent=1))
        elif args.cmd == "receipts":
            print(json.dumps(sheet.receipts, indent=1))
    except CycleError as e:
        print(f"CYCLE REFUSED: {e}", file=sys.stderr); sys.exit(2)


if __name__ == "__main__":
    main()
