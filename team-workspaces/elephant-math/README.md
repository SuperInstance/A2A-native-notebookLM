# Team Workspace — Elephant / Mathematician Discussion

Shared workspace for the elephant/mathematician foundation discussion
(Round 1, 2026-08-21). It ingests the discussion documents from the team
memory directory, snapshots them here, indexes them, and produces a digest
plus a cross-reference map so participants and fleet agents can load the
full state of the discussion without re-reading everything.

## Layout

```
team-workspaces/elephant-math/
├── README.md                  ← this guide
├── build.py                   ← the automation (stdlib-only Python 3.11+)
├── sources/                   ← verbatim snapshots of ingested docs (+ PROVENANCE.json)
├── index/
│   └── index.json             ← machine-readable index (entries, terms, code refs, stats)
└── digest/
    ├── DIGEST.md              ← team digest: roles, outlines, summaries, tensions, problem board
    └── cross-reference-map.md ← concept×doc matrix, code-ref map, problem↔response map,
                                 section affinities, statistic concordance
```

Generated artifacts (`index/`, `digest/`, `sources/PROVENANCE.json`) are
rebuildable at any time; the snapshots in `sources/` are committed so the
workspace stays hermetic even if the memory directory rotates.

## Usage

```bash
python3 team-workspaces/elephant-math/build.py
```

Options:

- `--source-dir DIR` — where discussion docs live
  (default: `~/.openclaw/workspace/memory`)
- `--pattern GLOB` — document glob, repeatable
  (default: `math-foundation-*.md`, `discussion-leader-round1-*.md`)
- `--quiet` — suppress the build report

## Adding future rounds

New rounds are picked up by adding patterns, e.g. when round 2 lands:

```bash
python3 team-workspaces/elephant-math/build.py \
    --pattern 'discussion-leader-round2-*.md' \
    --pattern 'math-foundation-round2-*.md'
```

Once a pattern is stable, add it to `DEFAULT_PATTERNS` in `build.py` so a
bare run picks it up.

## How the index is built

- Markdown headings (and bold-led list items like the Seams and Dissents)
  become addressable entries with stable ids (`algebraic::5.2`,
  `leader::2#p3`) recorded in `index/index.json`.
- Vocabulary terms are extracted from code spans, bold spans, and headings;
  terms shared across ≥2 docs feed the concept matrix.
- Code/artifact references (`vmf.py::edge`, `premise_band_movers.py::leg_A`,
  …) are collected with per-doc counts.
- Statistic-like values (e.g. `0.7714`, `0.9940`) are indexed with their
  surrounding context and concorded across docs.
- The Discussion Leader's `Problem N` headings are cosine-matched against
  foundation-doc sections to produce the problem↔response map; the two
  foundation docs are also cross-matched to surface section affinities and
  contested ground (both sides tension-flagged).

No AI provider, database, or network access is required — the build is
deterministic given the source documents.
