"""
repo_ingest — Scan a git repository and produce NotebookLM-ready sources.

Output format (each source entry):
{
    "id": str,
    "title": str,         # relative file path
    "source_type": str,   # "code" | "doc" | "config" | "data"
    "mime_type": str,     # e.g. "text/x-python"
    "content": str,       # full file text
    "language": str,      # programming language label
    "size_bytes": int,
    "directory": str,     # relative directory path
    "file_extension": str,
}

Top-level result:
{
    "project_name": str,
    "description": str,
    "summary": str,
    "source_count": int,
    "total_size_bytes": int,
    "directories": list[str],
    "sources": list[dict],
    "dependency_graph": dict,   # shallow outline
    "key_files": list[dict],   # most important files
}
"""

import os
import subprocess
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Extensions → metadata
# ---------------------------------------------------------------------------

LANGUAGE_MAP: dict[str, tuple[str, str, str]] = {
    ".py":   ("Python",   "text/x-python",    "code"),
    ".rs":   ("Rust",     "text/x-rust",      "code"),
    ".ts":   ("TypeScript","text/typescript",  "code"),
    ".tsx":  ("TSX",      "text/typescript-jsx","code"),
    ".js":   ("JavaScript","text/javascript",  "code"),
    ".jsx":  ("JSX",      "text/javascript-jsx","code"),
    ".go":   ("Go",       "text/x-go",        "code"),
    ".java": ("Java",     "text/x-java",      "code"),
    ".rb":   ("Ruby",     "text/x-ruby",      "code"),
    ".c":    ("C",        "text/x-c",         "code"),
    ".cpp":  ("C++",      "text/x-c++",       "code"),
    ".h":    ("C Header", "text/x-c",         "code"),
    ".hpp":  ("C++ Header","text/x-c++",      "code"),
    ".zig":  ("Zig",      "text/x-zig",       "code"),
    ".sh":   ("Shell",    "text/x-sh",        "code"),
    ".bash": ("Shell",    "text/x-sh",        "code"),
    ".zsh":  ("Zsh",      "text/x-sh",        "code"),
    ".sql":  ("SQL",      "text/x-sql",       "code"),
    ".r":    ("R",        "text/x-r",         "code"),
    ".swift":("Swift",    "text/x-swift",     "code"),
    ".kt":   ("Kotlin",   "text/x-kotlin",    "code"),
    ".scala":("Scala",    "text/x-scala",     "code"),
    ".ex":   ("Elixir",   "text/x-elixir",    "code"),
    ".exs":  ("Elixir",   "text/x-elixir",    "code"),
    ".clj":  ("Clojure",  "text/x-clojure",   "code"),
    ".lua":  ("Lua",      "text/x-lua",       "code"),
    ".pl":   ("Perl",     "text/x-perl",      "code"),
    ".pm":   ("Perl",     "text/x-perl",      "code"),
    ".dart": ("Dart",     "text/x-dart",      "code"),
    ".fs":   ("F#",       "text/x-fsharp",    "code"),
    ".cs":   ("C#",       "text/x-csharp",    "code"),
    # Docs
    ".md":   ("Markdown", "text/markdown",    "doc"),
    ".rst":  ("reST",     "text/x-rst",       "doc"),
    ".txt":  ("Text",     "text/plain",       "doc"),
    ".adoc": ("AsciiDoc", "text/asciidoc",    "doc"),
    ".org":  ("Org",      "text/x-org",       "doc"),
    # Config
    ".toml": ("TOML",     "text/x-toml",      "config"),
    ".yaml": ("YAML",     "text/x-yaml",      "config"),
    ".yml":  ("YAML",     "text/x-yaml",      "config"),
    ".json": ("JSON",     "application/json", "config"),
    ".ini":  ("INI",      "text/x-ini",       "config"),
    ".cfg":  ("Config",   "text/x-ini",       "config"),
    ".conf": ("Config",   "text/x-ini",       "config"),
    ".env":  ("Env",      "text/plain",       "config"),
    ".gradle":("Gradle",  "text/x-groovy",    "config"),
    # Data / other
    ".csv":  ("CSV",      "text/csv",         "data"),
    ".xml":  ("XML",      "text/xml",         "data"),
    ".lock": ("Lock",     "text/plain",       "data"),
}

# Extensions we also scan even if not in LANGUAGE_MAP (generic text fallback)
ALWAYS_INCLUDE: set[str] = {
    ".dockerfile", ".makefile", ".cmake",
    ".proto", ".graphql", ".gql",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git_root(path: str) -> str | None:
    """Return the repo root if *path* is inside a git repo."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _guess_project_name(path: str) -> str:
    return Path(path).resolve().name


def _guess_description(root: Path, sources: list[dict]) -> str:
    """Heuristic: look at README.md first lines."""
    for readme_candidate in ("README.md", "README.rst", "README.txt", "README"):
        candidate = root / readme_candidate
        if candidate.is_file():
            try:
                text = candidate.read_text("utf-8", errors="replace").strip()
                lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
                if lines:
                    return lines[0][:200]
                return text[:200]
            except OSError:
                pass
    return "No description available."


def _build_dependency_graph(root: Path, sources: list[dict]) -> dict:
    """Shallow dependency map keyed by directory."""
    directories: dict[str, list[str]] = {}
    for s in sources:
        d = s["directory"]
        directories.setdefault(d, []).append(s["title"])
    graph: dict[str, Any] = {}
    for d, files in sorted(directories.items()):
        parts = d.strip("/").split("/")
        target = graph
        for p in parts:
            target = target.setdefault(p, {})
        target["_files"] = len(files)
        target["_language_tags"] = sorted(
            set(s["language"] for s in sources if s["directory"] == d)
        )
    return graph


def _identify_key_files(sources: list[dict]) -> list[dict]:
    """Heuristic: README, package files, main entry points are key."""
    scoring: list[tuple[int, dict]] = []
    for s in sources:
        score = 0
        base = os.path.basename(s["title"]).lower()
        if base == "readme.md":
            score += 100
        if "package" in base:
            score += 50
        if "cargo.toml" == base or "go.mod" == base:
            score += 60
        if "pyproject.toml" == base:
            score += 60
        if "config" in base:
            score += 20
        if base.startswith("main.") or base.startswith("index."):
            score += 40
        # Penalize auto-generated/locale index files that are just data dumps
        if "locales" in s["title"] and base.startswith("index."):
            score -= 50
        # Penalize package-lock files (auto-generated)
        if base == "package-lock.json":
            score -= 100
        if s["size_bytes"] > 0:
            score += min(s["size_bytes"] // 500, 30)
        if s["source_type"] == "doc":
            score += 10
        scoring.append((score, s))
    scoring.sort(key=lambda x: -x[0])
    return [s for _, s in scoring[:10]]


def _is_text_file(path: Path) -> bool:
    """Quick heuristic: try reading as utf-8."""
    try:
        with open(path, "rb") as fh:
            chunk = fh.read(8192)
        chunk.decode("utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------

def scan_repo(repo_path: str, *, max_file_bytes: int = 512 * 1024) -> dict:
    """
    Scan *repo_path* and return a NotebookLM-ready source bundle.

    Parameters
    ----------
    repo_path : str
        Path to a directory (may or may not be a git repo).
    max_file_bytes : int
        Skip files larger than this (default 512 KiB).

    Returns
    -------
    dict with keys: project_name, description, summary, source_count,
                    total_size_bytes, directories, sources, dependency_graph,
                    key_files
    """
    root = Path(repo_path).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"{repo_path} is not a directory")

    git_root = _git_root(str(root))

    sources: list[dict] = []
    source_id = 0

    SKIP_DIRS: set[str] = {
        "node_modules", ".venv", "venv", "__pycache__", ".git",
        ".svn", ".hg", ".idea", ".vscode", ".nox", ".tox",
        "target", "build", "dist", "__pypackages__",
        "htmlcov", ".coverage", "__snapshots__",
        ".mypy_cache", ".pytest_cache", ".ruff_cache",
        ".terraform", "vendor", "bower_components",
        "egg-info", ".eggs", "lib", "deps",
        "site-packages", ".dart_tool", ".next",
        "__pycache__",
    }

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(root)
        parts = rel.parts
        # Skip files inside known artifact/vendor directories
        # Also skip hidden directories (.git, .venv, __pycache__, etc.)
        skip = False
        for p in parts[:-1]:
            if p in SKIP_DIRS or (
                p.startswith(".") and p != "."
            ) or p.endswith(".egg-info") or p.endswith(".dist-info"):
                skip = True
                break
        if skip:
            continue

        ext = file_path.suffix.lower()
        base_lower = file_path.name.lower()

        # Match extension or well-known non-extension files
        entry = LANGUAGE_MAP.get(ext)
        if entry is None:
            # Check whole-name files (Dockerfile, Makefile, etc.)
            if base_lower in ("dockerfile", "makefile", "cmakelists.txt", "justfile"):
                entry = (base_lower.capitalize(), "text/plain", "config")
            elif any(base_lower.endswith(e) for e in ALWAYS_INCLUDE):
                entry = (ext.lstrip(".").upper(), "text/plain", "config")
            else:
                continue

        # Size check
        try:
            size = file_path.stat().st_size
        except OSError:
            continue
        if size > max_file_bytes:
            continue
        if size == 0:
            continue

        # Read content
        try:
            content = file_path.read_text("utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            if not _is_text_file(file_path):
                continue
            try:
                content = file_path.read_text("latin-1", errors="replace")
            except OSError:
                continue

        language, mime, source_type = entry
        rel_str = str(rel)
        dir_str = str(rel.parent) if rel.parent != Path(".") else "."

        source_id += 1
        sources.append(
            {
                "id": f"src-{source_id:04d}",
                "title": rel_str,
                "source_type": source_type,
                "mime_type": mime,
                "content": content,
                "language": language,
                "size_bytes": size,
                "directory": dir_str,
                "file_extension": ext,
            }
        )

    project_name = _guess_project_name(repo_path)
    description = _guess_description(root, sources)

    directories = sorted(set(s["directory"] for s in sources))
    total_bytes = sum(s["size_bytes"] for s in sources)

    summary_parts = [
        f"Repository: {project_name}",
        f"Description: {description}",
        f"Total source files: {len(sources)} ({_human_size(total_bytes)})",
        f"Directories: {len(directories)}",
        f"Languages: {', '.join(sorted(set(s['language'] for s in sources)))}",
        f"Git root: {git_root or 'N/A'}",
    ]
    summary = "\n".join(summary_parts)

    return {
        "project_name": project_name,
        "description": description,
        "summary": summary,
        "source_count": len(sources),
        "total_size_bytes": total_bytes,
        "directories": directories,
        "sources": sources,
        "dependency_graph": _build_dependency_graph(root, sources),
        "key_files": _identify_key_files(sources),
    }


def _human_size(b: int) -> str:
    for unit in ("B", "KiB", "MiB"):
        if abs(b) < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} GiB"
