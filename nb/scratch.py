"""nb.scratch — the scratchpaper: a receipted sheet that thinks while you're away.

SELF-CONTAINED by choice: the port sheet (nb/engine.py) and the scratchpaper
share LAWS, not code — separate state files (.nb/scratch.json vs sheet.json),
no coupled evolution. Laws mirrored from the engine:
  - receipts are sha256 over JSON-plain content with NO timestamps inside the
    hash (bit-identical across reload); timestamps live in the receipt, OUTSIDE
    the hash
  - all state is JSON-plain (the witness law)
  - writes are atomic (temp file + os.replace)
  - the mutation log (.nb/scratch_log.jsonl) is append-only; never rewritten

Thinking op family (SCRATCHPAPER-VISION.md):
  note  -> RAW                      (sp add)
  ask   -> PENDING -> ANSWERED      (sp ask; answered via worker --apply)
  think -> OPEN -> THOUGHT         (sp think; filled via worker --apply)
  digest: pure consolidation of a cell's children — NO state change

Two edge kinds (the pinch0 lesson: similarity is NOT verified wiring):
  deps      hand-authored, causal. Promoted sim-links join these and
            participate in staleness.
  sim-links SUGGESTED by embedding similarity (bge-m3 via CF free tier,
            Jaccard fallback offline, marked). NEVER become deps until
            PROMOTED with a receipt saying why (promote --why / apply
            action=promote).

The brief (sp brief) is the attention contract: new answers, possible
contradictions (heuristic, marked), ripe threads, stale deps.
"""
import hashlib
import calendar
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "@cf/baai/bge-m3"
EMBED_BATCH = 32          # O(batch) memory: ~32 texts per CF request
LINK_THRESHOLD_BGE = 0.55  # cosine
LINK_THRESHOLD_JACCARD = 0.25
NEGATIONS = {"not", "no", "never", "cannot", "cant", "dont", "doesnt",
             "isnt", "arent", "wont", "wrong", "false", "actually",
             "contradicts", "incorrect", "nope", "without"}
STOP = {"the", "and", "for", "with", "this", "that", "from", "have", "has",
        "was", "are", "but", "not", "you", "its", "their", "they", "them",
        "will", "would", "could", "should", "what", "when", "where", "which",
        "into", "about", "than", "then", "them", "there", "here", "been",
        "being", "were", "does", "did", "done", "over", "under", "just"}


class ScratchError(Exception):
    """Refusal (fail-loud). CLI maps to rc=2."""


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def age_min(iso):
    try:
        t = calendar.timegm(time.strptime(iso, "%Y-%m-%dT%H:%M:%SZ"))
    except Exception:
        return 0.0
    return max(0.0, (time.time() - t) / 60.0)


def content_hash(cell):
    """Receipts-grade hash: JSON-plain content only. NO timestamps, NO status,
    NO rev — bit-identical across reloads and lifecycle changes."""
    payload = {"id": cell["id"], "kind": cell["kind"], "text": cell["text"],
               "deps": sorted(cell["deps"])}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def _atomic_write(path: Path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _tokens(text):
    return [w for w in re.findall(r"[a-z0-9']+", text.lower()) if len(w) >= 3]


def _content_words(text):
    return {w for w in _tokens(text) if w not in STOP}


def jaccard(a, b):
    A, B = _content_words(a), _content_words(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------- CF embed --
# Auth chain copied from the pinch0 pattern (quilt-gpu-lab scratch/pinch0/
# cf_embed.py): wrangler OAuth read at use-time, `wrangler whoami` auto-refresh
# on 401, legacy key.txt CF_API_TOKEN as LAST fallback (known DEAD 401 since
# 2026-10-02; kept only to mirror the pattern). Tokens are NEVER echoed,
# hardcoded, or committed; every error string is scrubbed against every
# credential read this run.

WRANGLER_CFG = os.path.expanduser("~/.wrangler/config/default.toml")
KEYFILE = "/mnt/c/Users/casey/key.txt"
_SEEN_SECRETS = []


def _read_kv(path):
    kv = {}
    try:
        with open(path, errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    kv[k.strip()] = v.strip().strip('"')
    except FileNotFoundError:
        pass
    return kv


def _remember_secret(tok):
    if tok and tok not in _SEEN_SECRETS:
        _SEEN_SECRETS.append(tok)


def _scrub(text):
    for s in list(_SEEN_SECRETS):
        if s in text:
            text = text.replace(s, "[scrubbed]")
    return text


def wrangler_token(refresh=False):
    if refresh:
        try:
            subprocess.run(["wrangler", "whoami"], capture_output=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired):
            pass
    tok = _read_kv(WRANGLER_CFG).get("oauth_token")
    _remember_secret(tok)
    return tok


def key_token():
    tok = _read_kv(KEYFILE).get("CF_API_TOKEN")
    _remember_secret(tok)
    return tok


def token_candidates(force_refresh=False):
    t = wrangler_token(refresh=force_refresh)
    if t:
        yield t
    k = key_token()  # legacy fallback, known-dead; mirrored from the pattern
    if k:
        yield k


def _cf_req(url, token, data=None, tries=3):
    body = json.dumps(data).encode() if data is not None else None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=body)
        req.add_header("Authorization", "Bearer " + token)
        if body:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return 200, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raw = _scrub(e.read().decode(errors="replace")[:300])
            if e.code == 401:
                return 401, raw
            ra = e.headers.get("Retry-After") if e.headers else None
            if e.code in (429, 500, 502, 503, 504, 522, 524) and attempt < tries - 1:
                wait = float(ra) if ra and re.fullmatch(r"\d+(\.\d+)?", ra) else min(2 ** attempt, 20)
                time.sleep(wait)
                continue
            return e.code, raw
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            if attempt < tries - 1:
                time.sleep(min(2 ** attempt, 10))
                continue
            return 0, _scrub(str(e))
    return 0, "retries exhausted"


class EmbedUnavailable(Exception):
    """No working embedding backend — caller falls back (marked) to Jaccard."""


def cf_account_id(token):
    c, j = _cf_req("https://api.cloudflare.com/client/v4/accounts", token)
    if c != 200 or not (isinstance(j, dict) and j.get("result")):
        raise EmbedUnavailable("no account id: " + _scrub(str(j)[:120]))
    return j["result"][0]["id"]


def cf_embed(texts):
    """Embed via CF Workers AI bge-m3 (free tier). Returns list of vectors.
    Raises EmbedUnavailable (scrubbed) when no credential / API refuses —
    the caller falls back to Jaccard and marks the output."""
    if os.environ.get("SP_DISABLE_CF"):
        raise EmbedUnavailable("SP_DISABLE_CF set — offline by request")
    last = "no credential candidates"
    for force in (False, True):
        for tok in token_candidates(force_refresh=force):
            try:
                acct = cf_account_id(tok)
            except EmbedUnavailable as e:
                last = str(e)
                continue
            url = "https://api.cloudflare.com/client/v4/accounts/%s/ai/run/%s" % (acct, MODEL)
            c, j = _cf_req(url, tok, {"text": list(texts)})
            if c == 200 and isinstance(j, dict) and j.get("success"):
                data = j["result"]["data"]
                if len(data) == len(texts):
                    return data
                last = "count mismatch %d != %d" % (len(data), len(texts))
            else:
                last = "http %s: %s" % (c, str(j)[:120])
    raise EmbedUnavailable(_scrub(last))


# ------------------------------------------------------------------ state --

class Scratch:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / ".nb" / "scratch.json"
        self.log_path = self.root / ".nb" / "scratch_log.jsonl"
        self.vec_path = self.root / ".nb" / "scratch_vectors.json"
        self.cells = {}
        self.links = []
        self.seq = 0
        self.seen = {}
        if self.path.exists():
            state = json.loads(self.path.read_text())
            self.cells = state["cells"]
            self.links = state.get("links", [])
            self.seq = state.get("seq", 0)
            self.seen = state.get("seen", {})

    # -- persistence ------------------------------------------------------
    def save(self):
        _atomic_write(self.path, json.dumps(
            {"version": 1, "seq": self.seq, "cells": self.cells,
             "links": self.links, "seen": self.seen}, indent=1))

    def log(self, op, detail):
        """Append-only mutation log. NEVER rewrites existing bytes."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as fh:
            fh.write(json.dumps({"ts": now_iso(), "op": op, "detail": detail},
                                sort_keys=True) + "\n")

    def save_vectors(self, cache):
        _atomic_write(self.vec_path, json.dumps(cache))

    def load_vectors(self):
        if self.vec_path.exists():
            try:
                return json.loads(self.vec_path.read_text())
            except json.JSONDecodeError:
                pass
        return {"backend": None, "vecs": {}}

    # -- cells -------------------------------------------------------------
    def _new_id(self):
        self.seq += 1
        return "c%03d" % self.seq

    def add_cell(self, kind, text, deps=None, actor="agent", op="add"):
        if not isinstance(text, str) or not text.strip():
            raise ScratchError("text must be a non-empty string")
        deps = list(deps or [])
        for d in deps:
            if d not in self.cells:
                raise ScratchError("unknown dep: %s" % d)
        status = {"note": "RAW", "ask": "PENDING", "think": "OPEN",
                  "thought": "THOUGHT", "answer": "THOUGHT"}[kind]
        ts = now_iso()
        cid = self._new_id()
        cell = {"id": cid, "kind": kind, "status": status, "text": text,
                "deps": deps, "created": ts, "built": ts, "rev": 0,
                "deps_added": {d: ts for d in deps},
                "receipt": {"h": None, "op": op, "ts": ts, "actor": actor,
                            "sources": list(deps)}}
        cell["receipt"]["h"] = content_hash(cell)
        self.cells[cid] = cell
        self.save()
        self.log(op, {"id": cid, "kind": kind, "deps": deps,
                      "h": cell["receipt"]["h"]})
        return cid

    # -- plan (pure) --------------------------------------------------------
    def plan(self, budget=4, think_threshold_min=45.0, link_threshold=None):
        """Pending work brief. PURE — no state change. PENDING asks oldest
        first, then RAW notes past the think-threshold (oldest first), then
        OPEN think cells, then SUGGESTED sim-links above threshold."""
        items = []
        asks = [c for c in self.cells.values()
                if c["kind"] == "ask" and c["status"] == "PENDING"]
        asks.sort(key=lambda c: c["created"])
        for c in asks:
            items.append({"item": c["id"], "type": "ask", "text": c["text"],
                          "age_min": round(age_min(c["created"]), 1),
                          "status": c["status"]})
        raws = [c for c in self.cells.values()
                if c["kind"] == "note" and c["status"] == "RAW"
                and age_min(c["created"]) >= think_threshold_min]
        raws.sort(key=lambda c: c["created"])
        for c in raws:
            items.append({"item": c["id"], "type": "think", "text": c["text"],
                          "age_min": round(age_min(c["created"]), 1),
                          "status": c["status"]})
        opens = [c for c in self.cells.values()
                 if c["kind"] == "think" and c["status"] == "OPEN"]
        opens.sort(key=lambda c: c["created"])
        for c in opens:
            items.append({"item": c["id"], "type": "think",
                          "text": "expansion pass on: " + ", ".join(c["deps"]),
                          "age_min": round(age_min(c["created"]), 1),
                          "status": c["status"]})
        lt = link_threshold if link_threshold is not None else (
            LINK_THRESHOLD_BGE if self.load_vectors().get("backend") == MODEL
            else LINK_THRESHOLD_JACCARD)
        for lnk in self.links:
            if lnk["status"] == "SUGGESTED" and lnk["score"] >= lt:
                items.append({"item": "%s->%s" % (lnk["from"], lnk["to"]),
                              "type": "link", "score": round(lnk["score"], 4),
                              "from_text": self.cells[lnk["from"]]["text"],
                              "to_text": self.cells[lnk["to"]]["text"],
                              "backend": lnk["backend"]})
        return {"generated": now_iso(),
                "budget": budget,
                "think_threshold_min": think_threshold_min,
                "link_threshold": lt,
                "n_open": len(items),
                "items": items[:budget]}

    # -- apply (the clerk writes the thinker's results) ---------------------
    def validate_results(self, doc):
        """Validate a results document BEFORE any mutation. Raises
        ScratchError on the first problem (fail-loud, rc=2 upstream)."""
        if not isinstance(doc, dict):
            raise ScratchError("results doc must be a JSON object")
        thinker = doc.get("thinker")
        if not isinstance(thinker, str) or not thinker.strip():
            raise ScratchError("results doc needs a non-empty 'thinker'")
        results = doc.get("results")
        if not isinstance(results, list) or not results:
            raise ScratchError("results doc needs a non-empty 'results' list")
        for i, r in enumerate(results):
            if not isinstance(r, dict):
                raise ScratchError("result[%d] must be an object" % i)
            item = r.get("item")
            action = r.get("action")
            if not isinstance(item, str) or not item:
                raise ScratchError("result[%d] missing 'item'" % i)
            if action not in ("answer", "thought", "promote"):
                raise ScratchError("result[%d] bad action: %r" % (i, action))
            if action == "promote":
                self._promote_target(item, r.get("why"))
            else:
                if item not in self.cells:
                    raise ScratchError("result[%d] unknown item: %s" % (i, item))
                text = r.get("text")
                if not isinstance(text, str) or not text.strip():
                    raise ScratchError("result[%d] needs non-empty 'text'" % i)
                cell = self.cells[item]
                if action == "answer" and cell["status"] != "PENDING":
                    raise ScratchError("result[%d]: %s is %s, not PENDING "
                                       "(only PENDING asks get answers)"
                                       % (i, item, cell["status"]))
                if action == "thought" and cell["status"] not in ("RAW", "OPEN"):
                    raise ScratchError("result[%d]: %s is %s (thoughts apply "
                                       "to RAW notes or OPEN think cells)"
                                       % (i, item, cell["status"]))
                sources = r.get("sources", [])
                if not isinstance(sources, list) or \
                        any(not isinstance(s, str) or s not in self.cells
                            for s in sources):
                    raise ScratchError("result[%d] 'sources' must be known "
                                       "cell ids" % i)
                nq = r.get("next_questions", [])
                if not isinstance(nq, list) or \
                        any(not isinstance(q, str) or not q.strip() for q in nq):
                    raise ScratchError("result[%d] 'next_questions' must be "
                                       "non-empty strings" % i)
        return thinker

    def _promote_target(self, item, why):
        if "->" not in item:
            raise ScratchError("promote item must be FROM->TO, got: %r" % item)
        src, dst = item.split("->", 1)
        if not isinstance(why, str) or not why.strip():
            raise ScratchError("promote %s->%s REFUSED: a promotion needs a "
                               "receipt ('why') — similarity is not verified "
                               "wiring" % (src, dst))
        if src not in self.cells or dst not in self.cells:
            raise ScratchError("promote: unknown cell in %s->%s" % (src, dst))
        if src in self.cells[dst]["deps"]:
            raise ScratchError("promote refused: %s is already a dep of %s"
                               % (src, dst))
        lnk = self.find_link(src, dst)
        if lnk is None or lnk["status"] != "SUGGESTED":
            raise ScratchError("promote refused: no SUGGESTED sim-link "
                               "%s->%s" % (src, dst))

    def apply_results(self, doc):
        """Validate-then-mutate. Every written child carries a receipt with
        the thinker id, source cells, and timestamp (outside the hash)."""
        thinker = self.validate_results(doc)
        written = []
        for r in doc["results"]:
            item, action = r["item"], r["action"]
            if action == "promote":
                cid = self.promote(item.split("->")[0], item.split("->")[1],
                                   r["why"], actor=thinker, via="worker")
                written.append({"item": item, "action": action, "cell": None,
                                "promoted": True})
                continue
            ts = now_iso()
            src_cell = self.cells[item]
            kind = "answer" if action == "answer" else "thought"
            deps = [item] + [s for s in r.get("sources", []) if s != item]
            cid = self._new_id()
            child = {"id": cid, "kind": kind, "status": "THOUGHT",
                     "text": r["text"], "deps": deps, "created": ts,
                     "built": ts, "rev": 0, "deps_added": {d: ts for d in deps},
                     "receipt": {"h": None, "op": "apply", "ts": ts,
                                 "actor": thinker, "sources": deps,
                                 "parent": item}}
            child["receipt"]["h"] = content_hash(child)
            self.cells[cid] = child
            src_cell["status"] = "ANSWERED" if action == "answer" else "THOUGHT"
            self.log("apply", {"thinker": thinker, "action": action,
                               "parent": item, "child": cid})
            written.append({"item": item, "action": action, "cell": cid})
            for q in r.get("next_questions", []):
                qid = self.add_cell("ask", q, deps=[cid], actor=thinker,
                                    op="apply-next-question")
                written.append({"item": q, "action": "next_question", "cell": qid})
        self.save()
        return written

    # -- sim-links -----------------------------------------------------------
    def find_link(self, src, dst):
        for lnk in self.links:
            if lnk["from"] == src and lnk["to"] == dst:
                return lnk
        return None

    def promote(self, src, dst, why, actor="agent", via="cli"):
        self._promote_target("%s->%s" % (src, dst), why)  # re-validate
        ts = now_iso()
        lnk = self.find_link(src, dst)
        lnk["status"] = "VERIFIED"
        lnk["receipt"] = {"ts": ts, "why": why, "actor": actor, "via": via}
        cell = self.cells[dst]
        cell["deps"].append(src)
        cell["deps_added"][src] = ts
        cell["rev"] += 1  # new upstream premise: downstream sees this as change
        cell["receipt"]["h"] = content_hash(cell)  # re-sign: deps are in the hash payload (wiring change = new content)
        self.save()
        self.log("promote", {"from": src, "to": dst, "why": why, "via": via})
        return lnk

    def embed_all(self, ids_texts, cache):
        """Embed missing vectors in ~32-text batches, checkpointing the cache
        after each batch (resume-safe, O(batch) memory). Returns backend used
        or raises EmbedUnavailable."""
        missing = [(i, t) for i, t in ids_texts if i not in cache["vecs"]]
        backend = cache.get("backend")
        if backend not in (None, MODEL):
            cache["vecs"] = {}  # backend switch: don't mix vector spaces
            missing = ids_texts
        for start in range(0, len(missing), EMBED_BATCH):
            batch = missing[start:start + EMBED_BATCH]
            vecs = cf_embed([t for _, t in batch])
            for (cid, _), v in zip(batch, vecs):
                cache["vecs"][cid] = v
            cache["backend"] = MODEL
            self.save_vectors(cache)  # checkpoint per batch
        if missing:
            self.log("embed", {"n": len(missing), "backend": MODEL})
        return MODEL

    def related(self, query, k=5, link_threshold=None):
        """Top-k cells by semantic similarity for an id or free text.
        Records SUGGESTED sim-links above threshold (never deps). Marks the
        backend; offline falls back to Jaccard, clearly marked."""
        qid = None
        if query in self.cells:
            qid, qtext = query, self.cells[query]["text"]
        else:
            for cid in self.cells:  # unique-prefix match
                if cid.startswith(query):
                    qid, qtext = cid, self.cells[cid]["text"]
                    break
            else:
                qtext = query
        try:
            cache = self.load_vectors()
            backend = self.embed_all(
                [(c["id"], c["text"]) for c in self.cells.values()], cache)
            qv = cf_embed([qtext])[0]
            scored = [(cosine(qv, cache["vecs"][c["id"]])
                       if c["id"] in cache["vecs"]
                       else jaccard(qtext, c["text"]),
                       c["id"], MODEL)
                      for c in self.cells.values() if c["id"] != qid]
            scored.sort(reverse=True)
            marked = "bge-m3"
        except EmbedUnavailable as e:
            reason = str(e)
            scored = sorted(
                [(jaccard(qtext, c["text"]), c["id"], "jaccard-fallback")
                 for c in self.cells.values() if c["id"] != qid],
                reverse=True)
            marked = "jaccard-fallback (offline: %s)" % reason[:80]
        top = scored[:k]
        lt = link_threshold if link_threshold is not None else (
            LINK_THRESHOLD_BGE if marked == "bge-m3" else LINK_THRESHOLD_JACCARD)
        new_links = []
        if qid is not None:
            for score, cid, be in top:
                if score < lt:
                    continue
                older, younger = sorted([qid, cid])
                if self.cells[younger]["kind"] in ("answer", "thought"):
                    continue  # content leaves don't take new upstream wiring
                if older in self.cells[younger]["deps"]:
                    continue  # already causal: nothing to suggest
                if self.find_link(older, younger):
                    continue
                self.links.append(
                    {"from": older, "to": younger, "score": round(score, 4),
                     "backend": be, "status": "SUGGESTED",
                     "created": now_iso(), "receipt": None})
                new_links.append((older, younger))
        if new_links:
            self.save()
            self.log("suggest_links", {"n": len(new_links),
                                       "backend": marked.split(" ")[0]})
        return {"query": qtext, "query_id": qid, "backend": marked,
                "link_threshold": lt,
                "related": [{"id": cid, "score": round(s, 4),
                             "kind": self.cells[cid]["kind"],
                             "status": self.cells[cid]["status"],
                             "text": self.cells[cid]["text"]}
                            for s, cid, be in top]}

    # -- digest (PURE) and brief ---------------------------------------------
    def digest(self, cid):
        """Consolidate a cell's children into a brief. PURE: reads state,
        mutates nothing (pinned)."""
        if cid not in self.cells:
            raise ScratchError("unknown cell: %s" % cid)
        c = self.cells[cid]
        children = [x for x in self.cells.values() if cid in x["deps"]
                    and x["kind"] in ("answer", "thought")]
        children.sort(key=lambda x: x["created"])
        return {"id": cid, "kind": c["kind"], "status": c["status"],
                "text": c["text"], "deps": c["deps"],
                "receipt": c["receipt"],
                "children": [{"id": x["id"], "kind": x["kind"],
                              "text": x["text"], "h": x["receipt"]["h"],
                              "thinker": x["receipt"]["actor"],
                              "ts": x["receipt"]["ts"]} for x in children]}

    def stale_cells(self):
        """Cells with a dep wired AFTER the cell's content was written —
        new upstream information they were not built with."""
        out = []
        for c in self.cells.values():
            for d, at in c.get("deps_added", {}).items():
                if at > c["built"]:
                    out.append({"id": c["id"], "stale_by": d,
                                "wired_at": at, "built_at": c["built"]})
                    break
        return out

    def _contradictions(self):
        """Heuristic only, and labelled as such: content-word overlap >=2 with
        negation tokens present on exactly one side."""
        found = []
        ids = [c["id"] for c in self.cells.values()
               if c["kind"] in ("note", "answer", "thought")]
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = self.cells[ids[i]], self.cells[ids[j]]
                wa, wb = _content_words(a["text"]), _content_words(b["text"])
                shared = wa & wb
                if len(shared) < 2:
                    continue
                na = bool(set(_tokens(a["text"])) & NEGATIONS)
                nb = bool(set(_tokens(b["text"])) & NEGATIONS)
                if na != nb:
                    found.append({"a": a["id"], "b": b["id"],
                                  "shared": sorted(shared)[:6],
                                  "negation_in": a["id"] if na else b["id"],
                                  "heuristic": True})
        return found

    def brief(self, mark_seen=True):
        """THE ATTENTION CONTRACT. What changed since last seen: new answers,
        contradictions between cells (heuristic, marked), ripe threads,
        stale deps. Updates the seen cursor unless mark_seen=False."""
        cursor = self.seen.get("answers_at")
        new_answers = []
        for c in self.cells.values():
            if c["kind"] == "answer":
                if cursor is None or c["created"] > cursor:
                    parent = c["receipt"].get("parent")
                    new_answers.append({
                        "ask": parent, "answer": c["id"],
                        "ask_text": self.cells[parent]["text"] if parent in self.cells else None,
                        "answer_text": c["text"],
                        "thinker": c["receipt"]["actor"]})
        ripe = self.plan(budget=10 ** 9)
        out = {"generated": now_iso(), "since": cursor,
               "new_answers": new_answers,
               "contradictions": self._contradictions(),
               "ripe": {"pending_asks": [i for i in ripe["items"] if i["type"] == "ask"],
                        "think_targets": [i for i in ripe["items"] if i["type"] == "think"],
                        "suggested_links": [i for i in ripe["items"] if i["type"] == "link"]},
               "stale": self.stale_cells()}
        if mark_seen:
            self.seen["answers_at"] = out["generated"]
            self.save()
            self.log("brief", {"new_answers": len(new_answers)})
        return out

    # -- graph ----------------------------------------------------------------
    def graph(self):
        return {"nodes": [{"id": c["id"], "kind": c["kind"], "status": c["status"],
                           "receipt": c["receipt"]["h"]}
                          for c in self.cells.values()],
                "dep_edges": [{"from": d, "to": c["id"]}
                              for c in self.cells.values() for d in c["deps"]],
                "sim_links": [{"from": l["from"], "to": l["to"],
                               "status": l["status"], "score": l["score"]}
                              for l in self.links]}
