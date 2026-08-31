#!/usr/bin/env python3
"""Build the elephant/mathematician discussion workspace.

Ingests discussion-round documents (math-foundation-*.md,
discussion-leader-round*.md) from the team memory directory, snapshots them
into sources/, builds a structured machine-readable index
(index/index.json), and generates a team digest plus a cross-reference map
(digest/DIGEST.md, digest/cross-reference-map.md).

Usage:
    python3 team-workspaces/elephant-math/build.py [--source-dir DIR]
        [--pattern GLOB ...] [--quiet]

New discussion rounds are picked up by adding patterns, e.g.:
    python3 team-workspaces/elephant-math/build.py \
        --pattern 'discussion-leader-round2-*.md'
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SOURCE_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
DEFAULT_PATTERNS = ["math-foundation-*.md", "discussion-leader-round1-*.md"]

ROLE_BY_PREFIX = [
    ("discussion-leader", "leader", "Leader", "Discussion Leader",
     "facilitator — frames the unifying vision, seams, and round agenda"),
    ("math-foundation-algebraic", "algebraic", "Algebraic", "Mathematician (algebraic arm)",
     "category-theoretic / structural foundation"),
    ("math-foundation-probabilistic", "probabilistic", "Probabilistic",
     "Mathematician (probabilistic arm)",
     "measure-theoretic / estimation-theoretic foundation"),
    ("math-foundation-creative", "creative", "Creative",
     "Mathematician (creative-analogical arm)",
     "generative analogy foundation (tide table)"),
    ("math-foundation-dissertation", "zeroclaw", "ZeroClaw",
     "ZeroClaw — dissertation keeper",
     "keeper's ruling over the dissertation claims (R1-R5, registrations)"),
    ("math-foundation-wesley-localgpu", "wesley", "Wesley",
     "Wesley (local GPU ensign)",
     "granite3.1-dense:2b position, advised by Lucineer"),
    ("math-foundation", "mathematician", "Mathematician", "Mathematician",
     "foundation analysis"),
]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
POINT_RE = re.compile(r"^(?:\s*\d+\.\s+|\s*[-*]\s+)?\*\*(.+?)\*\*\s*[:.\u2014-]?\s*(.*)$")
NUMBERED_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")
PROBLEM_RE = re.compile(r"^Problem\s+(\d+)\b[:.]?\s*(.*)", re.IGNORECASE)
CODESPAN_RE = re.compile(r"`([^`\n]+)`")
BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
FILEREF_RE = re.compile(
    r"(?<![\w./-])([\w./\-]+\.(?:py|md|jsonl|json|toml|yaml|yml|ts|tsx))(?:::[\w_()]+)?"
)
STAT_RE = re.compile(r"(?<![\d.])(\d+\.\d{2,4})(?![\d.])")
WORD_RE = re.compile(r"[a-z0-9_]+")
TENSION_RE = re.compile(
    r"dissent|risk|seam|strain|problem|agenda|challenge|disagree|"
    r"tautolog|unfalsifiab|not.*natural|sink the thesis|mislead",
    re.IGNORECASE,
)
META_TITLE_RE = re.compile(r"^(date|author|filed|scope|status|code|written)\b", re.IGNORECASE)
CROSSCUT_RE = re.compile(r"summary|index|mappings|formula", re.IGNORECASE)

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "in", "on", "for", "to", "is", "are",
    "not", "it", "its", "this", "that", "these", "those", "with", "from", "by",
    "as", "at", "be", "was", "were", "been", "has", "have", "had", "which",
    "where", "when", "how", "what", "why", "all", "any", "because", "but",
    "if", "then", "than", "so", "no", "nor", "only", "also", "more", "most",
    "some", "such", "can", "cannot", "could", "would", "should", "must",
    "may", "might", "will", "shall", "do", "does", "did", "each", "every",
    "one", "two", "three", "four", "five", "six", "seven", "see", "via",
    "per", "etc", "eg", "ie", "sec", "section", "sections", "chapter",
    "code", "note", "notes", "doc", "docs", "file", "files", "line", "lines",
    "table", "tables", "example", "examples", "definition", "proposition",
    "conjecture", "lemma", "theorem", "proof", "corollary", "statement",
    "statements", "solution", "outcome", "matter", "matters", "over",
    "under", "between", "into", "onto", "both", "same", "other", "another",
    "new", "old", "current", "existing", "original", "formal", "formally",
    "written", "read", "only", "exact", "exactly", "already", "just", "there",
    "they", "them", "their", "we", "you", "your", "uses", "used", "using",
    "against", "about", "instead", "rather", "since", "while", "during",
    "after", "before", "above", "below", "up", "down", "out", "off", "again",
    "further", "once", "here", "who", "whom", "everything", "nothing",
    "something", "anything", "consequence", "consequences",
}


@dataclass
class Entry:
    doc: str
    kind: str
    title: str
    label: str
    eid: str
    level: int
    body: str = ""
    lines: tuple[int, int] = (0, 0)
    terms: Counter = field(default_factory=Counter)
    tf: Counter = field(default_factory=Counter)
    tension: bool = False


@dataclass
class Doc:
    name: str
    slug: str
    short: str
    role: str
    role_note: str
    date: str
    sha256: str
    title: str
    text: str
    entries: list[Entry] = field(default_factory=list)
    stats: list[dict] = field(default_factory=list)
    filerefs: Counter = field(default_factory=Counter)
    display: dict[str, Counter] = field(default_factory=dict)


def role_for(stem: str) -> tuple[str, str, str, str, str]:
    for prefix, slug, short, role, note in ROLE_BY_PREFIX:
        if stem.startswith(prefix):
            return slug, short, role, note, prefix
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return slug, slug.capitalize(), "Contributor", "discussion document", prefix


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def ingest(source_dir: Path, patterns: list[str]) -> list[Path]:
    found: dict[str, Path] = {}
    for pattern in patterns:
        for path in sorted(source_dir.glob(pattern)):
            if path.is_file():
                found[path.name] = path
    return [found[k] for k in sorted(found)]


def snapshot(doc_paths: list[Path], sources_dir: Path, quiet: bool) -> list[dict]:
    sources_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for path in doc_paths:
        digest = sha256_of(path)
        dest = sources_dir / path.name
        action = "kept"
        if not dest.exists() or sha256_of(dest) != digest:
            shutil.copy2(path, dest)
            action = "copied"
        records.append({
            "name": path.name,
            "source_path": str(path),
            "sha256": digest,
            "source_mtime": datetime.fromtimestamp(
                path.stat().st_mtime, timezone.utc
            ).isoformat(timespec="seconds"),
            "snapshot_action": action,
        })
        if not quiet:
            print(f"  [{action}] {path.name} ({digest[:12]})")
    prov = sources_dir / "PROVENANCE.json"
    prov.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return records


def parse_doc(path: Path) -> Doc:
    stem = path.stem
    slug, short, role, role_note, _ = role_for(stem)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = next((m.group(2).strip() for m in map(HEADING_RE.match, lines) if m), stem)
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", stem)
    doc = Doc(
        name=path.name, slug=slug, short=short, role=role, role_note=role_note,
        date=date_match.group(1) if date_match else "",
        sha256=sha256_of(path), title=title, text=text,
    )

    entries: list[Entry] = []
    heading_seq: dict[str, int] = defaultdict(int)
    current: Entry | None = None
    current_heading: Entry | None = None
    in_fence = False
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        if current is not None:
            current.body = "\n".join(buffer).strip()
        buffer = []

    for lineno, raw in enumerate(lines, 1):
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            if current is not None:
                buffer.append(raw)
            continue
        if in_fence:
            if current is not None:
                buffer.append(raw)
            continue

        hm = HEADING_RE.match(raw)
        if hm:
            flush()
            level = len(hm.group(1))
            htitle = hm.group(2).strip()
            nm = NUMBERED_RE.match(htitle)
            pm = PROBLEM_RE.match(htitle)
            if nm:
                number, clean, label = nm.group(1), nm.group(2), f"§{nm.group(1)}"
            elif pm and pm.group(2):
                number = f"P{pm.group(1)}"
                clean, label = pm.group(2), f"Problem {pm.group(1)}"
            else:
                number = _assign_number(entries, level, heading_seq, slug)
                clean, label = htitle, ""
            eid = f"{slug}::{number}"
            current = Entry(doc=slug, kind="heading", title=clean, label=label,
                            eid=eid, level=level, lines=(lineno, lineno))
            current.tension = bool(TENSION_RE.search(htitle))
            entries.append(current)
            current_heading = current
            continue

        if current_heading is None:
            continue
        pm2 = POINT_RE.match(raw)
        if pm2 and not META_TITLE_RE.match(pm2.group(1)):
            flush()
            ptitle = pm2.group(1).strip().rstrip(".:")
            parent = current_heading
            n_prev = sum(1 for e in entries
                         if e.kind == "point" and e.eid.startswith(parent.eid + "#"))
            pe = Entry(doc=slug, kind="point", title=ptitle,
                       label=f"{parent.label}\u00b6{n_prev + 1}" if parent.label else "",
                       eid=f"{parent.eid}#p{n_prev + 1}",
                       level=parent.level + 1, lines=(lineno, lineno))
            pe.tension = bool(TENSION_RE.search(ptitle))
            entries.append(pe)
            current = pe
            if pm2.group(2).strip():
                buffer.append(pm2.group(2))
            continue

        buffer.append(raw)
    flush()

    doc.entries = entries
    _extract_features(doc, lines)
    return doc


def _assign_number(entries: list[Entry], level: int, seq: dict[str, int], slug: str) -> str:
    parent = None
    for e in reversed(entries):
        if e.kind == "heading" and e.level < level:
            parent = e
            break
    if parent is None:
        seq["root"] += 1
        return str(seq["root"])
    base = parent.label.lstrip("§") or parent.label
    key = f"under:{parent.eid}"
    seq[key] += 1
    return f"{base}.{seq[key]}"


def norm_term(term: str) -> str | None:
    key = re.sub(r"\s+", " ", term.strip().lower()).strip("`*")
    if not key or len(key) < 3:
        return None
    if re.search(r"[.?!\u2014:;]", key):
        return None
    if re.fullmatch(r"[\d.\s%\-]+", key):
        return None
    words = key.split()
    if len(words) > 5:
        return None
    if all(w in STOPWORDS or len(w) < 2 for w in words):
        return None
    return key


def extract_terms_from_line(line: str) -> list[str]:
    raws: list[str] = []
    for m in CODESPAN_RE.finditer(line):
        raws.append(m.group(1))
    stripped = CODESPAN_RE.sub(" ", line)
    for m in BOLD_RE.finditer(stripped):
        raws.append(m.group(1))
    return [r for r in raws if norm_term(r)]


def tf_of(text: str) -> Counter:
    words = [w for w in WORD_RE.findall(text.lower())
             if len(w) >= 3 and w not in STOPWORDS and not w.isdigit()]
    return Counter(words)


def _extract_features(doc: Doc, lines: list[str]) -> None:
    for e in doc.entries:
        raw_title_terms = extract_terms_from_line(e.title) if e.kind == "heading" else []
        for r in raw_title_terms:
            k = norm_term(r)
            if k:
                e.terms[k] += 1
                doc.display.setdefault(k, Counter())[r] += 1
        e.tf = tf_of(e.title + "\n" + e.body)

    spans = _entry_line_spans(doc, len(lines))
    seen_stats: set[str] = set()
    for lineno, raw in enumerate(lines, 1):
        owner = spans.get(lineno)
        if owner is None or HEADING_RE.match(raw):
            continue
        if raw.lstrip().startswith(("```", "|")):
            continue
        for r in extract_terms_from_line(raw):
            k = norm_term(r)
            if k:
                owner.terms[k] += 1
                doc.display.setdefault(k, Counter())[r] += 1
        for m in FILEREF_RE.finditer(raw):
            doc.filerefs[m.group(1)] += 1
        for m in STAT_RE.finditer(raw):
            value = m.group(1)
            ctx = raw.strip()
            if len(ctx) > 110:
                ctx = ctx[:107] + "..."
            key = f"{value}@{owner.eid}"
            if key not in seen_stats:
                seen_stats.add(key)
                doc.stats.append({"value": value, "context": ctx,
                                  "where": owner.label or owner.title, "eid": owner.eid})


def _entry_line_spans(doc: Doc, n_lines: int) -> dict[int, Entry]:
    spans: dict[int, Entry] = {}
    ordered = sorted(doc.entries, key=lambda e: e.lines[0])
    for i, e in enumerate(ordered):
        end = ordered[i + 1].lines[0] - 1 if i + 1 < len(ordered) else n_lines
        for lineno in range(e.lines[0], end + 1):
            spans[lineno] = e
    return spans


def cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    if dot == 0:
        return 0.0
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb)


def label_title(e: Entry | dict) -> str:
    if isinstance(e, Entry):
        label, title = e.label, e.title
    else:
        label, title = e["label"], e["title"]
    return f"{label} {title}".strip()


def display_for(doc: Doc, key: str) -> str:
    variants = doc.display.get(key)
    if variants:
        return variants.most_common(1)[0][0]
    return key


def first_prose(body: str, limit: int = 300) -> str:
    for raw in body.splitlines():
        s = raw.strip()
        if not s or s.startswith(("|", ">", "```", "#")):
            continue
        if re.fullmatch(r"[-=_*~]{3,}", s):
            continue
        s = re.sub(r"`([^`]+)`", r"\1", s)
        if len(s) > limit:
            s = s[: limit - 3].rstrip() + "..."
        return s
    return ""


def esc(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def build_index(docs: list[Doc], records: list[dict], source_dir: Path,
                patterns: list[str]) -> dict:
    shared: dict[str, dict[str, int]] = defaultdict(dict)
    displays: dict[str, dict[str, str]] = defaultdict(dict)
    for d in docs:
        agg: Counter = Counter()
        for e in d.entries:
            agg += e.terms
        for term, n in agg.items():
            shared[term][d.slug] = n
            displays[term][d.slug] = display_for(d, term)
    shared = {t: v for t, v in shared.items() if len(v) >= 2}

    code_refs: dict[str, dict[str, int]] = defaultdict(dict)
    for d in docs:
        for ref, n in d.filerefs.items():
            code_refs[ref][d.slug] = n

    doc_tf: dict[str, Counter] = {}
    for d in docs:
        agg = Counter()
        for e in d.entries:
            agg += e.tf
        doc_tf[d.slug] = agg
    shared_topics = {w: per for w, per in
                     ((w, {s: c for s, c in
                       ((s, doc_tf[s].get(w, 0)) for s in doc_tf) if c})
                      for w in set().union(*doc_tf.values()))
                     if len(per) >= 3}
    shared_topics = dict(sorted(shared_topics.items(),
                                key=lambda kv: (-len(kv[1]), -sum(kv[1].values()), kv[0]))[:18])

    stat_index: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for d in docs:
        for s in d.stats:
            stat_index[s["value"]][d.slug].append(s)

    return {
        "workspace": "elephant-math",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_dir": str(source_dir),
        "patterns": patterns,
        "documents": [
            {
                "name": d.name,
                "slug": d.slug,
                "title": d.title,
                "role": d.role,
                "role_note": d.role_note,
                "date": d.date,
                "sha256": d.sha256,
                "provenance": next(r for r in records if r["name"] == d.name),
                "entries": [
                    {
                        "eid": e.eid,
                        "kind": e.kind,
                        "label": e.label,
                        "title": e.title,
                        "level": e.level,
                        "lines": list(e.lines),
                        "tension": e.tension,
                        "terms": dict(e.terms.most_common(20)),
                    }
                    for e in d.entries
                ],
                "top_terms": dict(sum((e.terms for e in d.entries), Counter()).most_common(40)),
                "file_refs": dict(d.filerefs.most_common()),
                "stats": d.stats,
            }
            for d in docs
        ],
        "shared_terms": {t: v for t, v in sorted(
            shared.items(), key=lambda kv: (-len(kv[1]), -sum(kv[1].values()), kv[0]))[:200]},
        "term_displays": {t: v for t, v in displays.items() if t in shared},
        "shared_topics": shared_topics,
        "code_refs": dict(sorted(code_refs.items())),
        "statistics_index": {v: dict(per) for v, per in sorted(stat_index.items())},
    }


def problem_response_map(docs: list[Doc], cap: int = 5) -> list[dict]:
    leaders = [d for d in docs if d.slug == "leader"] or [docs[0]]
    foundations = [d for d in docs if d not in leaders]
    problems = [e for d in leaders for e in d.entries
                if e.kind == "heading" and e.eid.split("::")[1].startswith("P")]
    out = []
    for p in problems:
        candidates = []
        for f in foundations:
            for e in f.entries:
                if e.kind != "heading" or e.level < 2 or e.level > 3:
                    continue
                if CROSSCUT_RE.search(e.title):
                    continue
                s = cosine(p.tf, e.tf)
                if s >= 0.04:
                    candidates.append({
                        "doc": f.short, "label": e.label, "title": e.title,
                        "eid": e.eid, "score": round(s, 3), "tension": e.tension,
                    })
        candidates.sort(key=lambda m: (-m["score"], m["eid"]))
        out.append({
            "problem": p.title, "label": p.label, "eid": p.eid,
            "summary": first_prose(p.body, 260),
            "best_score": candidates[0]["score"] if candidates else 0.0,
            "matches": candidates[:cap],
        })
    return out


def section_affinities(docs: list[Doc], min_score: float = 0.14,
                       top: int = 10) -> list[dict]:
    heads = {d.slug: [e for e in d.entries if e.kind == "heading" and 2 <= e.level <= 3
                      and not CROSSCUT_RE.search(e.title)] for d in docs}
    slugs = [d.slug for d in docs]
    pairs = []
    for i, a in enumerate(slugs):
        for b in slugs[i + 1:]:
            for ea in heads[a]:
                for eb in heads[b]:
                    s = cosine(ea.tf, eb.tf)
                    if s >= min_score:
                        pairs.append((s, ea, eb))
    pairs.sort(key=lambda t: (-t[0], t[1].eid, t[2].eid))
    return [
        {"score": round(s, 3),
         "a": {"doc": ea.doc, "label": ea.label, "title": ea.title,
               "eid": ea.eid, "tension": ea.tension},
         "b": {"doc": eb.doc, "label": eb.label, "title": eb.title,
               "eid": eb.eid, "tension": eb.tension}}
        for s, ea, eb in pairs[:top]
    ]


def render_digest(docs: list[Doc], records: list[dict], index: dict,
                  problems: list[dict]) -> str:
    now = index["generated_at"]
    out: list[str] = []
    out.append("# Elephant / Mathematician Discussion — Team Digest")
    out.append("")
    out.append(f"*Auto-generated by `team-workspaces/elephant-math/build.py` at {now}.*")
    out.append("")
    out.append(f"Source: `{index['source_dir']}` (patterns: "
               + ", ".join(f"`{p}`" for p in index["patterns"]) + "). "
               "Snapshots live in [`sources/`](../sources/); regenerate with the build command above.")
    out.append("")

    out.append("## 1. Reading Order & Roles")
    out.append("")
    out.append("| Doc | Participant | Filed | Snapshot | Sections |")
    out.append("|---|---|---|---|---|")
    for d in docs:
        r = next(x for x in records if x["name"] == d.name)
        n_head = sum(1 for e in d.entries if e.kind == "heading" and e.level > 1)
        out.append(f"| [`{d.name}`](../sources/{d.name}) | {d.role} — {d.role_note} | "
                   f"{d.date or '—'} | `{r['sha256'][:12]}` | {n_head} |")
    out.append("")
    out.append("Suggested reading order: Discussion Leader round first (vision, seams, agenda), "
               "then the foundation positions, then the keeper's ruling.")
    out.append("")

    children: dict[str, list[Entry]] = defaultdict(list)
    for d in docs:
        stack: list[Entry] = []
        for e in d.entries:
            if e.kind != "heading":
                continue
            while stack and stack[-1].level >= e.level:
                stack.pop()
            if stack:
                children[stack[-1].eid].append(e)
            stack.append(e)

    for d in docs:
        out.append(f"## 2.{docs.index(d) + 1} {d.title}")
        out.append("")
        out.append(f"**{d.role}** ({d.role_note}) · filed {d.date or '—'} · "
                   f"snapshot `{d.sha256[:12]}`")
        out.append("")
        out.append("### Outline")
        out.append("")
        has_headings = any(e.kind == "heading" and e.level >= 2 for e in d.entries)
        if has_headings:
            points_shown = 0
            under_tension = False
            for e in d.entries:
                if e.kind == "heading" and 2 <= e.level <= 3:
                    indent = "  " * (e.level - 2)
                    flag = " \u26a0️" if e.tension else ""
                    out.append(f"{indent}- **{label_title(e)}**{flag}")
                    under_tension = e.tension
                    points_shown = 0
                elif e.kind == "point" and (
                        e.tension or (under_tension and points_shown < 8
                                      and len(e.title) >= 20)):
                    out.append(f"    - {'⚠️ ' if e.tension else '· '}{esc(e.title)}")
                    points_shown += 1
        else:
            for e in d.entries:
                if e.kind == "point":
                    flag = " \u26a0️" if e.tension else ""
                    out.append(f"- **{esc(e.title)}**{flag}")
        out.append("")
        out.append("### Section summaries")
        out.append("")
        any_summary = False
        for e in d.entries:
            if e.kind != "heading" or e.level != 2:
                continue
            s = first_prose(e.body)
            if not s:
                for child in children.get(e.eid, []):
                    s = first_prose(child.body)
                    if s:
                        s = f"*(via {label_title(child)})* " + s
                        break
            if s:
                any_summary = True
                out.append(f"- **{label_title(e)}** — {esc(s)}")
        if not any_summary:
            body = next((e.body for e in d.entries if e.kind == "heading"), "")
            s = first_prose(body, 400)
            if s:
                out.append(f"- **(whole document)** — {esc(s)}")
        out.append("")
        vals: list[str] = []
        for s in d.stats:
            if s["value"] not in vals:
                vals.append(s["value"])
            if len(vals) == 8:
                break
        if vals:
            out.append("### Key figures (first appearance)")
            out.append("")
            for s in d.stats:
                if s["value"] in vals:
                    out.append(f"- `{s['value']}` ({s['where']}) — {esc(s['context'])}")
                    vals.remove(s["value"])
            out.append("")
        out.append("---")
        out.append("")

    out.append("## 3. Tensions, Dissents & Open Problems")
    out.append("")
    for d in docs:
        flagged = [e for e in d.entries if e.tension]
        if not flagged:
            continue
        out.append(f"### {d.short} ({d.role})")
        out.append("")
        for e in flagged:
            s = first_prose(e.body, 240)
            out.append(f"- **{label_title(e)}**" + (f" — {esc(s)}" if s else ""))
        out.append("")

    out.append("## 4. Round 1 Problem Board")
    out.append("")
    if problems:
        for p in problems:
            status = ("strong response" if p["best_score"] >= 0.15 else
                      "partial response" if p["best_score"] >= 0.07 else
                      "**no substantial response yet**")
            out.append(f"### {p['label']} — {esc(p['problem'])}")
            out.append("")
            if p["summary"]:
                out.append(f"> {esc(p['summary'])}")
                out.append("")
            out.append(f"Foundation responses: {status} (best similarity {p['best_score']}).")
            out.append("")
            if p["matches"]:
                out.append("| Foundation doc | Section | Similarity |")
                out.append("|---|---|---|")
                for m in p["matches"]:
                    flag = " \u26a0️" if m["tension"] else ""
                    out.append(f"| {m['doc']} | {esc(label_title(m))}{flag} | {m['score']} |")
                out.append("")
        out.append("See [cross-reference-map.md](cross-reference-map.md) for the full map.")
        out.append("")
    else:
        out.append("_No `Problem N` headings found in the leader document._")
        out.append("")
    return "\n".join(out) + "\n"


def render_xref(docs: list[Doc], index: dict, problems: list[dict],
                affinities: list[dict]) -> str:
    now = index["generated_at"]
    short_of = {d.slug: d.short for d in docs}
    out: list[str] = []
    out.append("# Cross-Reference Map — Elephant / Mathematician Round 1")
    out.append("")
    out.append(f"*Auto-generated at {now}. Every cell below is traceable to "
               "`index/index.json`.*")
    out.append("")

    out.append("## 1. Concept × Document Matrix")
    out.append("")
    out.append("Shared vocabulary across two or more docs, ranked by spread then "
               "frequency. Cells show occurrences and the densest sections.")
    out.append("")
    out.append("| Concept | " + " | ".join(d.short for d in docs) + " |")
    out.append("|" + "---|" * (len(docs) + 1))
    shared = index["shared_terms"]
    displays = index["term_displays"]
    for term, per_doc in list(shared.items())[:25]:
        shown: set[str] = set()
        cells = []
        for d in docs:
            n = per_doc.get(d.slug)
            if not n:
                cells.append("—")
                continue
            locs = Counter()
            for e in d.entries:
                c = e.terms.get(term)
                if c:
                    locs[e.label or e.title.split(":")[0][:24]] += c
            top = ", ".join(f"{lbl} ({c})" for lbl, c in locs.most_common(2))
            cells.append(f"{n} — {top}" if top else str(n))
        display = displays.get(term, {}).get(next(iter(per_doc)), term)
        if display in shown:
            continue
        shown.add(display)
        out.append(f"| `{esc(display)}` | " + " | ".join(cells) + " |")
    out.append("")

    topics = index.get("shared_topics", {})
    if topics:
        out.append("### Topical vocabulary (body-text frequency)")
        out.append("")
        out.append("Words used across three or more docs — the discussion's shared "
                   "working language (counts are body-text occurrences).")
        out.append("")
        out.append("| Term | " + " | ".join(d.short for d in docs) + " |")
        out.append("|" + "---|" * (len(docs) + 1))
        for w, per in topics.items():
            cells = [str(per.get(d.slug, "—")) for d in docs]
            out.append(f"| `{w}` | " + " | ".join(cells) + " |")
        out.append("")

    out.append("## 2. Code & Artifact Reference Map")
    out.append("")
    out.append("Which discussion docs cite which code artifacts "
               "(aggregated by file; `::function` calls listed where cited).")
    out.append("")
    out.append("| Artifact | Cited by | Functions cited |")
    out.append("|---|---|---|")
    by_base: dict[str, dict] = defaultdict(lambda: {"docs": Counter(), "funcs": set()})
    for ref, per_doc in index["code_refs"].items():
        base = ref.split("::")[0]
        by_base[base]["docs"].update(per_doc)
        if "::" in ref:
            by_base[base]["funcs"].add(ref.split("::", 1)[1])
    for base in sorted(by_base, key=lambda b: (-sum(by_base[b]["docs"].values()), b)):
        info = by_base[base]
        cited = ", ".join(f"{short_of.get(s, s)} ×{n}" for s, n in info["docs"].most_common())
        funcs = ", ".join(f"`{f}`" for f in sorted(info["funcs"])) or "—"
        out.append(f"| `{esc(base)}` | {cited} | {funcs} |")
    out.append("")

    out.append("## 3. Round 1 Problems ↔ Foundation Responses")
    out.append("")
    for p in problems:
        out.append(f"### {p['label']} — {esc(p['problem'])}")
        out.append("")
        if not p["matches"]:
            out.append("_No matching foundation section found (similarity below floor) — "
                       "open ground for round 2._")
            out.append("")
            continue
        for m in p["matches"]:
            flag = " \u26a0️ tension" if m["tension"] else ""
            out.append(f"- **{m['doc']} {esc(label_title(m))}** (sim {m['score']}){flag}")
        out.append("")

    out.append("## 4. Section Affinities Across Foundation Docs")
    out.append("")
    out.append("High-similarity section pairs — the same ground treated by multiple "
               "positions (tension markers show where they disagree).")
    out.append("")
    if affinities:
        out.append("| A | B | Similarity |")
        out.append("|---|---|---|")
        for a in affinities:
            ea, eb = a["a"], a["b"]
            flag = " \u26a0️" if (ea["tension"] or eb["tension"]) else ""
            out.append(f"| {short_of.get(ea['doc'], ea['doc'])} {esc(label_title(ea))} | "
                       f"{short_of.get(eb['doc'], eb['doc'])} {esc(label_title(eb))} | "
                       f"{a['score']}{flag} |")
        out.append("")
        contested = [a for a in affinities if a["a"]["tension"] and a["b"]["tension"]]
        if contested:
            out.append("**Contested ground (both sides flagged as tension/risk):**")
            out.append("")
            for a in contested:
                out.append(f"- {esc(label_title(a['a']))} ↔ {esc(label_title(a['b']))} "
                           f"(sim {a['score']})")
            out.append("")
    else:
        out.append("_No section pairs above the similarity floor._")
        out.append("")

    out.append("## 5. Statistic Concordance")
    out.append("")
    out.append("Numeric values appearing in two or more docs (shared evidence — "
               "or shared artifact).")
    out.append("")
    stat_index = index["statistics_index"]
    rows = [(v, per) for v, per in stat_index.items() if len(per) >= 2]
    rows.sort(key=lambda t: (-len(t[1]), t[0]))
    if rows:
        out.append("| Value | Docs | First context per doc |")
        out.append("|---|---|---|")
        for v, per in rows[:30]:
            ctxs = []
            for s in per:
                first = per[s][0]
                ctxs.append(f"**{short_of.get(s, s)}** ({first['where']}): "
                            f"{esc(first['context'][:90])}")
            out.append(f"| `{v}` | {len(per)} | " + "<br>".join(ctxs) + " |")
        out.append("")
    else:
        out.append("_No statistic appears in two or more docs yet._")
        out.append("")

    out.append("## 6. Open Threads for Round 2")
    out.append("")
    unhandled = [p for p in problems if p["best_score"] < 0.07]
    if unhandled:
        for p in unhandled:
            out.append(f"- {p['label']} — {esc(p['problem'])}: no substantial foundation "
                       "response yet.")
        out.append("")
    else:
        out.append("- All leader problems have at least a partial foundation response; "
                   "adjudicate the contested ground in §4 next.")
        out.append("")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR,
                    help=f"discussion docs directory (default: {DEFAULT_SOURCE_DIR})")
    ap.add_argument("--pattern", action="append", default=None,
                    help="glob for docs to ingest (repeatable; "
                         f"default: {DEFAULT_PATTERNS})")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    patterns = args.pattern or DEFAULT_PATTERNS
    root = Path(__file__).resolve().parent
    sources_dir = root / "sources"
    index_dir = root / "index"
    digest_dir = root / "digest"
    for d in (index_dir, digest_dir):
        d.mkdir(parents=True, exist_ok=True)

    if not args.quiet:
        print(f"Ingesting from {args.source_dir} ({', '.join(patterns)})")
    doc_paths = ingest(args.source_dir, patterns)
    if not doc_paths:
        print(f"ERROR: no documents matched {patterns} in {args.source_dir}",
              file=sys.stderr)
        return 2

    records = snapshot(doc_paths, sources_dir, args.quiet)
    docs = [parse_doc(sources_dir / p.name) for p in doc_paths]
    slugs = [d.slug for d in docs]
    if len(slugs) != len(set(slugs)):
        print(f"ERROR: duplicate role slugs after mapping: {slugs}", file=sys.stderr)
        return 3

    index = build_index(docs, records, args.source_dir, patterns)
    problems = problem_response_map(docs)
    affinities = section_affinities(docs)

    (index_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (digest_dir / "DIGEST.md").write_text(
        render_digest(docs, records, index, problems), encoding="utf-8")
    (digest_dir / "cross-reference-map.md").write_text(
        render_xref(docs, index, problems, affinities), encoding="utf-8")

    n_entries = sum(len(d.entries) for d in docs)
    if not args.quiet:
        print(f"Indexed {len(docs)} docs, {n_entries} entries, "
              f"{len(index['shared_terms'])} shared terms, "
              f"{len(index['code_refs'])} code refs")
        print(f"Wrote {index_dir / 'index.json'}")
        print(f"Wrote {digest_dir / 'DIGEST.md'}")
        print(f"Wrote {digest_dir / 'cross-reference-map.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
