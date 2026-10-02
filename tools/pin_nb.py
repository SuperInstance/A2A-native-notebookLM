"""FAIL-first pins for the nb spreadsheet engine + the ML-porting demo.

L0 cycles are refused (RED before engine grew the check).
L1 spreadsheet memo cascade: touching one spec re-evals ONLY downstream.
L2 receipts are bit-identical across full sheet reload.
L3 every cell carries a receipt after eval.
L4 port cells book honest verdicts: correct port PASS, buggy port FAIL
    with mismatches (never hidden).
L5 the demo sheet's verdict row: softmax PASS, buggy-softmax FAIL.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from nb.engine import CycleError, Sheet  # noqa: E402

results = []


def pin(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f" - {detail}" if detail else ""))


def run_cli(root, *argv):
    import os
    env = dict(os.environ, PYTHONPATH=str(REPO))  # nb not yet pip-installed; honest seam
    return subprocess.run([sys.executable, "-m", "nb.cli", *argv],
                          cwd=root, capture_output=True, text=True, env=env)


def build_demo(root: Path):
    """ML/RL/NN/DL porting sheet: spec vectors -> impl -> port candidates."""
    s = Sheet(root)
    s.add("softmax_spec", [], "const", json.dumps([
        [[1.0, 2.0, 3.0], [0.09003057, 0.24472847, 0.66524096]],
        [[0.0, 0.0, 0.0], [0.33333333, 0.33333333, 0.33333333]],
        [[-1.0, 1.0], [0.11920292, 0.88079708]],
        [[1000.0, 1001.0, 1002.0], [0.09003057, 0.24472847, 0.66524096]]]))
    s.add("softmax_ref", [], "py",
          "import math\n"
          "v=[1.0,2.0,3.0]; m=max(v); e=[math.exp(x-m) for x in v]; t=sum(e)\n"
          "out={'probs':[x/t for x in e]}")  # JSON-plain data, not a function:
    # functions can't be witnessed between cells (the refusal law).
    s.add("softmax_py_impl", ["softmax_spec"], "py",
          "import math\n"
          "def f(v):\n"
          "    m=max(v); e=[math.exp(x-m) for x in v]; t=sum(e)\n"
          "    return [x/t for x in e]\n"
          "out={'n_pass': sum(1 for v,w in inputs['softmax_spec'] if all(abs(a-b)<=1e-6 for a,b in zip(f(v),w)))}")
    s.add("softmax_port_rust", ["softmax_spec"], "port",
          "def cand(v):\n"
          "    m=max(v); e=[2.718281828459045**(x-m) for x in v]; t=sum(e)\n"
          "    return [x/t for x in e]")
    s.add("softmax_port_buggy", ["softmax_spec"], "port",
          "def cand(v):\n"  # forgot max-subtraction: overflows/精度 mismatch on big values
          "    e=[2.718281828459045**x for x in v]; t=sum(e)\n"
          "    return [x/t for x in e]")
    s.add("linear_fwd", [], "py",
          "import math\n"
          "W=[[0.5,-0.25],[0.1,0.9]]; x=[1.0,2.0]\n"
          "h=[sum(W[i][j]*x[j] for j in range(2)) for i in range(2)]\n"
          "m=max(h); e=[math.exp(t-m) for t in h]; tot=sum(e)\n"
          "out={'pre_activation': h, 'probs': [t/tot for t in e]}")
    s.save()


def main():
    root = Path(tempfile.mkdtemp(prefix="nbpin-"))
    # ---- L0: cycle refused
    s = Sheet(root)
    s.add("a", ["b"], "const", "1"); s.add("b", ["a"], "const", "2")
    try:
        s.eval()
        pin("L0 cycles are refused with the path", False)
    except CycleError as e:
        pin("L0 cycles are refused with the path", "a -> b" in str(e), str(e))
    if (root / ".nb").exists():
        shutil.rmtree(root / ".nb")

    # demo sheet via CLI (headless path)
    build_demo(root)
    r = run_cli(root, "eval")
    pin("L1a CLI eval runs clean", r.returncode == 0, r.stderr.strip()[:80])
    s = Sheet(root)
    v = s.values
    pin("L4a correct port PASSES", v["softmax_port_rust"]["verdict"] == "PASS")
    pin("L4b buggy port FAILs with mismatches shown",
        v["softmax_port_buggy"]["verdict"] == "FAIL" and len(v["softmax_port_buggy"]["mismatches"]) > 0,
        f"n_failed={v['softmax_port_buggy']['n_failed']}")
    pin("L5 impl cell self-checks against spec", v["softmax_py_impl"]["n_pass"] == 4)
    pin("L5b composed cell (spreadsheet logic) resolves deps",
        abs(sum(v["linear_fwd"]["probs"]) - 1.0) < 1e-9)

    # L6 the refusal law: function-valued cells are refused with a clear error
    s3 = Sheet(root)
    s3.add("fn_cell", [], "py", "def g():\n    return 1\nout=g")
    try:
        s3.eval()
        pin("L6 function-valued cells refused (witness law)", False)
    except ValueError as e:
        pin("L6 function-valued cells refused (witness law)", "JSON-plain" in str(e))
    s3.cells.pop("fn_cell")

    # L1 memo cascade: touch spec -> only downstream re-evals
    log = []
    s2 = Sheet(root)
    s2.eval(eval_log=log)
    pin("L1b second eval is a no-op (all memoized)", log == [], f"re-evaled={log}")
    s2.cells["softmax_spec"].code = json.dumps(
        [[[1.0, 2.0, 3.0], [0.09003057, 0.24472847, 0.66524096]]])  # touch
    log = []
    s2.eval(eval_log=log)
    downstream = {"softmax_spec", "softmax_py_impl", "softmax_port_rust",
                  "softmax_port_buggy"}
    pin("L1c touching spec re-evals ONLY downstream", set(log) == downstream, str(sorted(log)))

    # L2 receipts survive full reload, bit-identical
    r1 = Sheet(root).receipts
    r2 = Sheet(root).receipts
    pin("L2 receipts deterministic across reload", r1 == r2)
    # L3 coverage
    pin("L3 every cell receipted", all(c in r2 for c in Sheet(root).cells))
    print(("GREEN: nb is a receipted spreadsheet engine" if all(r[1] for r in results)
           else "RED: pins failed"), f"({sum(r[1] for r in results)}/{len(results)})")
    return 0 if all(r[1] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
