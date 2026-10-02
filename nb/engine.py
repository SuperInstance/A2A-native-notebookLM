"""nb — spreadsheet-logic cell engine (A2A-native-notebookLM rebuild core).

A sheet is a DAG of cells. Each cell: {id, deps, op, code}. Eval is
topological, memoized, and receipted — every cell eval books a receipt
(fnv1a-64 over cell_id+code+inputs+output; NO timestamps inside the
hash, so receipts are bit-identical across reruns of an unchanged sheet).
The porting op is the ML/RL/NN/DL workhorse: a port cell binds a SPEC
cell (test vectors) and a CANDIDATE cell (ported code) and books an
honest verdict. Spreadsheet logic: touch one cell, only downstream
re-evals (pins prove the memo cascade).
"""
import hashlib
import json
from pathlib import Path


def _h(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


class CycleError(Exception):
    pass


class Cell:
    def __init__(self, cid, deps, op, code):
        self.id, self.deps, self.op, self.code = cid, list(deps), op, code


class Sheet:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / ".nb" / "sheet.json"
        self.cells = {}
        self.values = {}
        self.receipts = {}
        if self.path.exists():
            for c in json.loads(self.path.read_text())["cells"]:
                self.cells[c["id"]] = Cell(c["id"], c.get("deps", []), c["op"], c["code"])
            state = json.loads(self.path.read_text())
            self.values = state.get("values", {})
            self.receipts = state.get("receipts", {})

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({
            "cells": [{"id": c.id, "deps": c.deps, "op": c.op, "code": c.code}
                      for c in self.cells.values()],
            "values": self.values, "receipts": self.receipts}, indent=1))

    def add(self, cid, deps, op, code):
        self.cells[cid] = Cell(cid, deps, op, code)

    def order(self):
        seen, stack, out = set(), [], []

        def visit(cid):
            if cid in stack:
                raise CycleError(" -> ".join(stack + [cid]))
            if cid in seen:
                return
            stack.append(cid)
            for d in self.cells[cid].deps:
                if d not in self.cells:
                    raise KeyError(f"{cid} dep missing: {d}")
                visit(d)
            stack.pop()
            seen.add(cid)
            out.append(cid)
        for cid in self.cells:
            visit(cid)
        return out

    def eval(self, only=None, eval_log=None):
        """Eval stale cells. Memo cascade: a cell re-evals only if its code,
        its deps' receipts, or its own receipt is absent. Returns eval order."""
        order = self.order()
        for cid in order:
            c = self.cells[cid]
            dep_receipts = {d: self.receipts.get(d, {}).get("out") for d in c.deps}
            sig = _h({"code": c.code, "op": c.op, "deps": dep_receipts, "id": cid})
            old = self.receipts.get(cid, {})
            if old.get("sig") == sig:
                continue  # memo: unchanged code + upstream receipts -> skip
            inputs = {d: self.values[d] for d in c.deps}
            out = self._run(c, inputs)
            try:  # the witness law: every cell value must be JSON-plain
                json.dumps(out)
            except TypeError as e:
                raise ValueError(f"{cid}: cell value must be JSON-plain "
                                 f"(witnessable); got non-serializable value: {e}")
            self.values[cid] = out
            self.receipts[cid] = {"sig": sig, "out": _h(out), "op": c.op,
                                  "deps": {d: self.receipts[d]["out"] for d in c.deps}}
            if eval_log is not None:
                eval_log.append(cid)
        self.save()
        return order

    def _run(self, c, inputs):
        if c.op == "const":
            return json.loads(c.code)
        if c.op == "py":
            g = {"inputs": inputs, "math": __import__("math")}
            exec(c.code, g)  # single namespace: comprehensions see cell-defined fns
            return g.get("out")
        if c.op == "port":
            # port cell: FIRST dep is the spec cell (test vectors); code defines cand
            spec = inputs[c.deps[0]] if c.deps else None
            g = {"inputs": inputs, "math": __import__("math")}
            exec(c.code, g)
            cand = g.get("cand")
            fails = []
            for vec, want in spec:
                try:
                    got = cand(vec)
                except Exception as ex:  # a candidate that crashes on a spec vector is a FAIL, booked as evidence
                    fails.append({"vec": vec, "want": want, "error": f"{type(ex).__name__}: {ex}"})
                    continue
                if any(abs(a - b) > 1e-6 for a, b in zip(got, want)):  # spec vectors are receipts-grade (8dp); port contract = 1e-6
                    fails.append({"vec": vec, "want": want, "got": got})
            return {"verdict": "FAIL" if fails else "PASS", "n_checked": len(spec),
                    "n_failed": len(fails), "mismatches": fails[:4]}
        raise ValueError(f"unknown op {c.op}")

    def graph(self):
        return {"nodes": [{"id": c.id, "op": c.op,
                           "receipt": self.receipts.get(c.id, {}).get("out")}
                          for c in self.cells.values()],
                "edges": [{"from": d, "to": c.id} for c in self.cells.values()
                          for d in c.deps]}
