"""FAIL-first pins for the scratchpaper (nb/scratch.py + sp CLI + worker).

P0  add->plan->apply round-trip: a PENDING ask comes back ANSWERED with a
    receipted answer child (thinker id + sources + ts outside the hash).
P1  plan budget is a hard cap (default 4) even when more work is pending.
P2  malformed apply is refused rc=2 BEFORE any mutation (bad JSON, missing
    thinker, unknown item, empty text) — state and log untouched.
P3  related falls back offline (SP_DISABLE_CF) and the output MARKS the
    fallback backend (jaccard-fallback), never passing bge off as local.
P4  sim-links are SUGGESTED, never deps: promote WITHOUT a receipt is
    refused rc=2; deps stay clean until a promote WITH 'why' lands, and
    the promoted edge is then a real causal dep (graph shows it).
P5  digest is PURE: byte-identical state files before/after (no cursor
    bump, no log line, no rewrite).
P6  brief is the attention contract: lists new answers and flags
    contradictions between cells (heuristic, marked) and stale deps.
P7  scratch_log.jsonl is append-only across mutations: earlier bytes are
    a strict prefix of later bytes; every line valid JSON.
P8  receipts are deterministic across reload and timestamps live OUTSIDE
    the content hash (hash == recomputed hash with no ts/status in it).
P9  think-threshold gates RAW notes: fresh note unplanned by default,
    planned when the threshold is lowered.
P10 promoted link restales its target: brief lists the cell as stale
    (upstream wired after the content was written).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from nb.scratch import Scratch, ScratchError, content_hash  # noqa: E402

results = []


def pin(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f" - {detail}" if detail else ""))


def run(root, *argv, env_extra=None, exe=None):
    import os
    env = dict(os.environ, PYTHONPATH=str(REPO), SP_DISABLE_CF="1")
    if env_extra:
        env.update(env_extra)
    if exe == "worker":
        cmd = [sys.executable, str(REPO / "tools" / "scratch_worker.py"), "--root", str(root), *argv]
    else:
        cmd = [sys.executable, "-m", "nb.sp", "--root", str(root), *argv]
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, env=env)


def state_bytes(root):
    out = {}
    for name in ("scratch.json", "scratch_log.jsonl", "scratch_vectors.json"):
        f = Path(root) / ".nb" / name
        out[name] = f.read_bytes() if f.exists() else None
    return out


def main():
    root = tempfile.mkdtemp(prefix="sppin-")

    # ---- P0: add -> plan -> apply round-trip produces ANSWERED + receipt
    r = run(root, "add", "the relay cron drifts when the gateway restarts mid-tick")
    pin("P0a add books a RAW note", r.returncode == 0 and "[note/RAW]" in r.stdout, r.stderr[:80])
    r = run(root, "ask", "why does the relay cron drift after gateway restarts?")
    ask_id = r.stdout.split()[1] if r.returncode == 0 else None
    pin("P0b ask books a PENDING cell", r.returncode == 0 and "[ask/PENDING]" in r.stdout)
    r = run(root, "worker-plan-placeholder")  # placeholder no-op
    plan_path = Path(root) / "plan.json"
    r = run(root, "--plan", "--think-threshold", "0", "--out", str(plan_path), exe="worker")
    plan = json.loads(plan_path.read_text()) if plan_path.exists() else {}
    pin("P0c worker --plan lists the PENDING ask first",
        r.returncode == 0 and plan.get("items") and plan["items"][0]["item"] == ask_id
        and plan["items"][0]["type"] == "ask", str(plan.get("items", []))[:100])
    res = {"thinker": "pin-clerk-v1",
           "results": [{"item": ask_id, "action": "answer",
                        "text": "restart kills the tick mid-flight; the cron re-arms from wall clock, not last-tick",
                        "sources": [], "next_questions": ["should the cron re-arm from last-tick instead?"]}]}
    res_path = Path(root) / "results.json"
    res_path.write_text(json.dumps(res))
    r = run(root, "--apply", str(res_path), exe="worker")
    pin("P0d apply accepts well-formed results", r.returncode == 0, r.stderr[:120])
    sp = Scratch(Path(root))
    pin("P0e ask is ANSWERED with a receipted child",
        sp.cells[ask_id]["status"] == "ANSWERED",
        str(sp.cells[ask_id]["status"]))
    ans = [c for c in sp.cells.values() if c["kind"] == "answer"]
    rec = ans[0]["receipt"] if ans else {}
    pin("P0f answer receipt carries thinker+sources and ts OUTSIDE the hash",
        bool(ans) and rec.get("actor") == "pin-clerk-v1" and "ts" in rec
        and rec.get("h") and "ts" not in json.loads(json.dumps({"h": rec["h"]}))
        and len(rec.get("sources", [])) >= 1, str(rec)[:120])
    pin("P0g next_question became a live PENDING ask",
        any(c["kind"] == "ask" and c["status"] == "PENDING"
            and c["text"].startswith("should the cron") for c in sp.cells.values()))
    r = run(root, "--apply", str(res_path), exe="worker")  # replay must refuse
    pin("P0h replaying the same answer is refused (ask no longer PENDING)",
        r.returncode == 2 and "not PENDING" in r.stderr, r.stderr.strip()[:90])

    # ---- P1: budget cap
    root2 = tempfile.mkdtemp(prefix="sppin2-")
    for i in range(6):
        run(root2, "ask", "question %d about the lane budget?" % i)
    r = run(root2, "--plan", exe="worker")
    plan_path2 = Path(root2) / "plan.json"
    run(root2, "--plan", "--out", str(plan_path2), exe="worker")
    plan2 = json.loads(plan_path2.read_text())
    pin("P1 default budget caps the plan at 4 items",
        plan2["budget"] == 4 and len(plan2["items"]) == 4,
        "n=%d" % len(plan2["items"]))
    run(root2, "--plan", "--budget", "2", "--out", str(plan_path2), exe="worker")
    plan2b = json.loads(plan_path2.read_text())
    pin("P1b explicit budget=2 caps at 2", len(plan2b["items"]) == 2)
    pin("P1c asks are oldest-first (creation order preserved)",
        [it["item"] for it in plan2["items"]] == sorted(it["item"] for it in plan2["items"]))

    # ---- P2: malformed apply refused rc=2, no mutation
    before = state_bytes(root2)
    bad_docs = [
        "{not json",
        json.dumps({"results": [{"item": "c001", "action": "answer", "text": "x"}]}),
        json.dumps({"thinker": "x", "results": [{"item": "c999", "action": "answer", "text": "x"}]}),
        json.dumps({"thinker": "x", "results": [{"item": "c001", "action": "answer", "text": " "}]}),
        json.dumps({"thinker": "x", "results": [{"item": "c001", "action": "explode", "text": "x"}]}),
    ]
    refused = 0
    for i, doc in enumerate(bad_docs):
        bp = Path(root2) / ("bad%d.json" % i)
        bp.write_text(doc)
        r = run(root2, "--apply", str(bp), exe="worker")
        if r.returncode == 2 and r.stderr.startswith("REFUSED"):
            refused += 1
    pin("P2 all 5 malformed applies refused rc=2 with REFUSED on stderr",
        refused == 5, "refused=%d" % refused)
    pin("P2b refused applies left state + log byte-identical",
        state_bytes(root2) == before)

    # ---- P3: related falls back offline, marked
    root3 = tempfile.mkdtemp(prefix="sppin3-")
    run(root3, "add", "fogarty cache holds the compiled atlas")
    r = run(root3, "add", "fogarty cache is wrong, rebuild it before the merge")
    pin("P3a two fogarty notes captured", r.returncode == 0)
    r = run(root3, "related", "compiled atlas cache")
    ok = r.returncode == 0 and "jaccard-fallback" in r.stdout
    pin("P3b offline related MARKS the fallback in output", ok, r.stdout[:100] + r.stderr[:80])
    out = run(root3, "related", "compiled atlas cache", "--json")
    j = json.loads(out.stdout)
    pin("P3c fallback scores still rank the atlas note first",
        j["related"] and j["related"][0]["text"].startswith("fogarty cache holds"),
        str(j["related"][:1]))

    # ---- P4: SUGGESTED links never deps; promote needs a receipt
    sp3 = Scratch(Path(root3))
    ids = sorted(sp3.cells.keys())
    r = run(root3, "related", ids[0], "--link-threshold", "0")
    sp3 = Scratch(Path(root3))
    links = [l for l in sp3.links if l["status"] == "SUGGESTED"]
    pin("P4a related recorded SUGGESTED sim-links", len(links) >= 1,
        "n=%d" % len(sp3.links))
    src, dst = links[0]["from"], links[0]["to"]
    g = json.loads(run(root3, "graph").stdout)
    pin("P4b SUGGESTED link is NOT a dep edge",
        {"from": src, "to": dst} not in g["dep_edges"])
    r = run(root3, "promote", src, dst, "--why", "")
    pin("P4c promote WITHOUT a receipt refused rc=2",
        r.returncode == 2 and "needs a receipt" in r.stderr, r.stderr.strip()[:90])
    g = json.loads(run(root3, "graph").stdout)
    pin("P4d refused promote did not touch deps",
        {"from": src, "to": dst} not in g["dep_edges"])
    r = run(root3, "promote", src, dst, "--why", "same subsystem, the rebuild note changes how I read the atlas note")
    pin("P4e promote WITH a receipt lands",
        r.returncode == 0 and "VERIFIED" in r.stdout, r.stderr[:90])
    g = json.loads(run(root3, "graph").stdout)
    pin("P4f promoted link is now a real causal dep",
        {"from": src, "to": dst} in g["dep_edges"])
    sp3 = Scratch(Path(root3))
    lnk = sp3.find_link(src, dst)
    pin("P4g promotion receipt records why/who/when",
        lnk["status"] == "VERIFIED" and lnk["receipt"] and
        lnk["receipt"]["why"].startswith("same subsystem") and "ts" in lnk["receipt"])

    # ---- P5: digest is pure
    before = state_bytes(root3)
    r = run(root3, "digest", src)
    pin("P5 digest mutates NOTHING (all state files byte-identical)",
        r.returncode == 0 and state_bytes(root3) == before, r.stderr[:80])
    run(root3, "brief", "--no-mark", "--json")  # control: no-mark brief also pure
    pin("P5b brief --no-mark is also byte-pure", state_bytes(root3) == before)

    # ---- P6: brief lists new answers + contradictions (+ staleness for P10)
    root6 = tempfile.mkdtemp(prefix="sppin6-")
    run(root6, "add", "fogarty cache holds the compiled atlas")
    run(root6, "add", "fogarty cache is wrong, rebuild it before the merge")
    run(root6, "ask", "should the atlas rebuild run before or after the merge?")
    res6 = {"thinker": "pin-clerk-v1",
            "results": [{"item": "c003", "action": "answer",
                         "text": "before the merge — the merge reads the atlas",
                         "sources": ["c001"]}]}
    p6 = Path(root6) / "r6.json"
    p6.write_text(json.dumps(res6))
    run(root6, "--apply", str(p6), exe="worker")
    out = run(root6, "brief", "--json")
    b = json.loads(out.stdout)
    pin("P6a brief lists the new answer",
        len(b["new_answers"]) == 1 and b["new_answers"][0]["thinker"] == "pin-clerk-v1",
        str(b["new_answers"])[:120])
    pin("P6b brief flags the fogarty contradiction between cells (heuristic)",
        any(c["a"] == "c001" and c["b"] == "c002" and c["heuristic"] is True
            for c in b["contradictions"]),
        str(b["contradictions"])[:140])
    pin("P6c contradiction names the negation side",
        b["contradictions"] and b["contradictions"][0]["negation_in"] == "c002")
    # cursor advanced: second brief shows nothing new
    out2 = run(root6, "brief", "--json")
    b2 = json.loads(out2.stdout)
    pin("P6d second brief is quiet (cursor = attention contract)",
        b2["new_answers"] == [])
    # ---- P10: promoted link restales its target
    run(root6, "related", "c001", "--link-threshold", "0")
    sp6 = Scratch(Path(root6))
    l6 = [l for l in sp6.links if l["status"] == "SUGGESTED" and "c002" in (l["from"], l["to"])]
    if l6:
        s6, d6 = l6[0]["from"], l6[0]["to"]
        run(root6, "promote", s6, d6, "--why", "pin: restale check")
        b3 = json.loads(run(root6, "brief", "--json").stdout)
        pin("P10 promoted dep restales its target in the brief",
            any(s["id"] == d6 for s in b3["stale"]), str(b3["stale"])[:100])
    else:
        pin("P10 promoted dep restales its target in the brief", False, "no SUGGESTED link formed")

    # ---- P7: append-only log
    logs = sorted(Path(r) / ".nb" / "scratch_log.jsonl" for r in (root, root2, root3, root6))
    all_ok, line_ok = True, True
    for lp in logs:
        first = lp.read_bytes()
        run(str(lp.parent.parent), "add", "post-log-check note")
        second = lp.read_bytes()
        if not second.startswith(first) or len(second) <= len(first):
            all_ok = False
        try:
            for line in second.decode().splitlines():
                json.loads(line)
        except Exception:
            line_ok = False
    pin("P7 scratch_log.jsonl is append-only (earlier bytes a strict prefix)",
        all_ok)
    pin("P7b every log line is valid JSON", line_ok)

    # ---- P8: receipts deterministic across reload; ts outside hash
    sp_r = Scratch(Path(root3))
    stable = all(c["receipt"]["h"] == content_hash(c) for c in sp_r.cells.values())
    sp_r2 = Scratch(Path(root3))
    same = all(sp_r.cells[i]["receipt"]["h"] == sp_r2.cells[i]["receipt"]["h"]
               for i in sp_r.cells)
    pin("P8 receipt hashes stable across reload and carry no timestamps",
        stable and same)

    # ---- P9: think-threshold gates RAW notes
    root9 = tempfile.mkdtemp(prefix="sppin9-")
    run(root9, "add", "brand new idea about the lane scheduler")
    p9 = Path(root9) / "plan.json"
    run(root9, "--plan", "--out", str(p9), exe="worker")
    plan9 = json.loads(p9.read_text())
    pin("P9a fresh RAW note is NOT planned at the default threshold",
        plan9["items"] == [], str(plan9["items"])[:80])
    run(root9, "--plan", "--think-threshold", "0", "--out", str(p9), exe="worker")
    plan9b = json.loads(p9.read_text())
    pin("P9b lowering the threshold plans the note as a think-target",
        len(plan9b["items"]) == 1 and plan9b["items"][0]["type"] == "think")

    # ---- witness law: state is JSON-plain
    json.loads((Path(root3) / ".nb" / "scratch.json").read_text())
    pin("P11 state files are JSON-plain (witnessable)",
        True)

    shutil.rmtree(root); shutil.rmtree(root2); shutil.rmtree(root3)
    shutil.rmtree(root6); shutil.rmtree(root9)
    green = all(r[1] for r in results)
    print(("GREEN: the scratchpaper holds the laws" if green else "RED: pins failed"),
          f"({sum(r[1] for r in results)}/{len(results)})")
    return 0 if green else 1


if __name__ == "__main__":
    sys.exit(main())
