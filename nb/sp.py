"""sp — the scratchpaper CLI (agent-first surfaces).

Thin direct entry:  python3 -m nb.sp <verb> ...
Also wired into the main CLI:  python3 -m nb.cli sp <verb> ...

Verbs: add / ask / think / plan / apply / related / brief / show /
       digest / promote

House rules: stdlib only, fail-loud rc=2 on refusals, receipts on every
mutation, timestamps live in receipts (never inside hashes).
"""
import argparse
import json
import sys
from pathlib import Path

from nb.scratch import Scratch, ScratchError


def _cell_line(c):
    return "%s [%s/%s] deps=%s %r" % (c["id"], c["kind"], c["status"],
                                      ",".join(c["deps"]) or "-", c["text"][:70])


def _print_plan(p):
    print("plan @ %s  budget=%d (open=%d, threshold>=%smin, links>=%s)" % (
        p["generated"], p["budget"], p["n_open"],
        p["think_threshold_min"], p["link_threshold"]))
    if not p["items"]:
        print("  (nothing pending — the paper is quiet)")
    for it in p["items"]:
        if it["type"] == "link":
            print("  LINK  %s  score=%.3f [%s]" % (it["item"], it["score"], it["backend"]))
            print("        from: %r" % it["from_text"][:66])
            print("        to:   %r" % it["to_text"][:66])
        else:
            print("  %-5s %s  age=%.0fmin  %r" % (
                it["type"].upper(), it["item"], it["age_min"], it["text"][:64]))


def _print_brief(b):
    print("== scratchpaper brief @ %s (since %s) ==" % (b["generated"], b["since"] or "forever"))
    if b["new_answers"]:
        print("new answers:")
        for a in b["new_answers"]:
            print("  %s ANSWERED %r -> %s %r (by %s)" % (
                a["ask"], (a["ask_text"] or "")[:48], a["answer"],
                a["answer_text"][:56], a["thinker"]))
    else:
        print("new answers: none since last brief")
    if b["contradictions"]:
        print("possible contradictions (HEURISTIC, verify before acting):")
        for c in b["contradictions"]:
            print("  %s <-> %s share %s (negation in %s)" % (
                c["a"], c["b"], c["shared"], c["negation_in"]))
    r = b["ripe"]
    threads = (r["pending_asks"] or r["think_targets"] or r["suggested_links"])
    if threads:
        print("ripe threads:")
        for it in r["pending_asks"]:
            print("  PENDING ask %s age=%.0fmin %r" % (it["item"], it["age_min"], it["text"][:56]))
        for it in r["think_targets"]:
            print("  think-target %s age=%.0fmin %r" % (it["item"], it["age_min"], it["text"][:56]))
        for it in r["suggested_links"]:
            print("  SUGGESTED link %s score=%.3f" % (it["item"], it["score"]))
    else:
        print("ripe threads: none")
    if b["stale"]:
        print("stale deps (upstream wired after this was written):")
        for s in b["stale"]:
            print("  %s (dep %s wired %s > built %s)" % (
                s["id"], s["stale_by"], s["wired_at"], s["built_at"]))


def build_parser():
    p = argparse.ArgumentParser(prog="sp", description="the scratchpaper: notes that think")
    p.add_argument("--root", default=".", help="paper root (default cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="capture a thought (note, RAW)")
    a.add_argument("text"); a.add_argument("--dep", default="", help="comma-separated dep ids")
    q = sub.add_parser("ask", help="hand a question to the paper (PENDING)")
    q.add_argument("text"); q.add_argument("--dep", default="")
    t = sub.add_parser("think", help="open an expansion pass on parent cell(s) (OPEN)")
    t.add_argument("ids", nargs="+")
    pl = sub.add_parser("plan", help="pending work brief (pure)")
    pl.add_argument("--budget", type=int, default=4)
    pl.add_argument("--think-threshold", type=float, default=45.0,
                    help="minutes before a RAW note is a think-target")
    pl.add_argument("--link-threshold", type=float, default=None)
    pl.add_argument("--json", action="store_true")
    ap = sub.add_parser("apply", help="write a thinker's results (receipted)")
    ap.add_argument("results_json")
    r = sub.add_parser("related", help="top-k cells by similarity (suggests sim-links)")
    r.add_argument("id_or_text"); r.add_argument("-k", type=int, default=5)
    r.add_argument("--link-threshold", type=float, default=None)
    r.add_argument("--json", action="store_true")
    b = sub.add_parser("brief", help="THE ATTENTION CONTRACT: what changed since last seen")
    b.add_argument("--json", action="store_true")
    b.add_argument("--no-mark", action="store_true", help="don't update the seen cursor")
    s = sub.add_parser("show", help="cell + children + links + receipts")
    s.add_argument("id")
    d = sub.add_parser("digest", help="consolidate a cell's children (pure)")
    d.add_argument("id")
    pr = sub.add_parser("promote", help="SUGGESTED sim-link -> verified dep (needs a receipt)")
    pr.add_argument("src"); pr.add_argument("dst"); pr.add_argument("--why", required=True)
    g = sub.add_parser("graph", help="cells, dep edges, sim-links")
    return p


def main(argv=None):
    p = build_parser()
    args = p.parse_args(argv)
    sp = Scratch(Path(args.root))
    try:
        if args.cmd == "add":
            deps = [d for d in args.dep.split(",") if d]
            cid = sp.add_cell("note", args.text, deps=deps)
            print("added %s [note/RAW]" % cid)
        elif args.cmd == "ask":
            deps = [d for d in args.dep.split(",") if d]
            cid = sp.add_cell("ask", args.text, deps=deps)
            print("asked %s [ask/PENDING]" % cid)
        elif args.cmd == "think":
            cid = sp.add_cell("think", "expansion pass on: " + ", ".join(args.ids),
                              deps=args.ids, op="think")
            print("thinking %s [think/OPEN]" % cid)
        elif args.cmd == "plan":
            out = sp.plan(budget=args.budget, think_threshold_min=args.think_threshold,
                          link_threshold=args.link_threshold)
            print(json.dumps(out, indent=1) if args.json else "")
            if not args.json:
                _print_plan(out)
        elif args.cmd == "apply":
            try:
                doc = json.loads(Path(args.results_json).read_text())
            except FileNotFoundError:
                raise ScratchError("results file not found: %s" % args.results_json)
            except json.JSONDecodeError as e:
                raise ScratchError("results file is not valid JSON: %s" % e)
            written = sp.apply_results(doc)
            print(json.dumps({"applied": True, "thinker": doc.get("thinker"),
                              "written": written}, indent=1))
        elif args.cmd == "related":
            out = sp.related(args.id_or_text, k=args.k,
                             link_threshold=args.link_threshold)
            if args.json:
                print(json.dumps(out, indent=1))
            else:
                print("related to %r  backend=%s" % (out["query"][:60], out["backend"]))
                for rrow in out["related"]:
                    print("  %.3f  %s [%s/%s] %r" % (rrow["score"], rrow["id"],
                                                     rrow["kind"], rrow["status"],
                                                     rrow["text"][:56]))
        elif args.cmd == "brief":
            out = sp.brief(mark_seen=not args.no_mark)
            if args.json:
                print(json.dumps(out, indent=1))
            else:
                _print_brief(out)
        elif args.cmd == "show":
            out = sp.digest(args.id)
            print(_cell_line(sp.cells[args.id]))
            print("  receipt: h=%s op=%s actor=%s ts=%s sources=%s" % (
                out["receipt"]["h"], out["receipt"]["op"],
                out["receipt"]["actor"], out["receipt"]["ts"],
                out["receipt"]["sources"]))
            if out["children"]:
                print("  children:")
                for ch in out["children"]:
                    print("    %s [%s] by %s @ %s h=%s %r" % (
                        ch["id"], ch["kind"], ch["thinker"], ch["ts"],
                        ch["h"], ch["text"][:64]))
            links = [l for l in sp.links if args.id in (l["from"], l["to"])]
            if links:
                print("  sim-links:")
                for l in links:
                    print("    %s->%s %s score=%.3f %s" % (
                        l["from"], l["to"], l["status"], l["score"],
                        ("why: " + l["receipt"]["why"]) if l["receipt"] else "(unverified)"))
        elif args.cmd == "digest":
            print(json.dumps(sp.digest(args.id), indent=1))
        elif args.cmd == "promote":
            lnk = sp.promote(args.src, args.dst, args.why)
            print("promoted %s->%s VERIFIED; %s now deps on %s" % (
                args.src, args.dst, args.dst, args.src))
            print("  receipt: why=%r via=cli actor=agent" % lnk["receipt"]["why"])
        elif args.cmd == "graph":
            print(json.dumps(sp.graph(), indent=1))
    except ScratchError as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 2
    except KeyError as e:
        print("REFUSED: unknown id %s" % e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
