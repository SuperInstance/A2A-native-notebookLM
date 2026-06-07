#!/usr/bin/env python3
"""
A2A-native-notebookLM CLI: boot a NotebookLM instance from a git repository.

Usage:
    python cli.py boot /path/to/repo --port 8080
    python cli.py boot /path/to/repo --port 8080 --host 0.0.0.0
    python cli.py scan /path/to/repo           # just print the scan summary
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path so imports work
_project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(_project_root))


def cmd_scan(args: argparse.Namespace) -> None:
    """Scan a repository and print the ingest summary."""
    from open_notebook.repo_ingest import scan_repo

    result = scan_repo(args.repo, max_file_bytes=args.max_size)
    print("=" * 60)
    print(result["summary"])
    print("=" * 60)
    print(f"\nKey files ({len(result['key_files'])}):")
    for kf in result["key_files"]:
        print(f"  [{_human_size(kf['size_bytes']):>8}] {kf['title']}")
    print(f"\nDirectories ({len(result['directories'])}):")
    for d in result["directories"]:
        files_in_dir = [s["title"] for s in result["sources"] if s["directory"] == d]
        print(f"  {d}/  ({len(files_in_dir)} files)")

    if args.verbose:
        print("\n--- Dependency Graph (outline) ---")
        _print_dep_graph(result["dependency_graph"])


def cmd_boot(args: argparse.Namespace) -> None:
    """
    Boot a NotebookLM server backed by the repository's code as sources.

    Steps:
        1. Scan the repo -> sources bundle
        2. Start the I2I vessel FS poller
        3. Launch uvicorn on the FastAPI app with sources injected
    """
    from open_notebook.repo_ingest import scan_repo

    print(f"Scanning repository: {args.repo}")
    result = scan_repo(args.repo, max_file_bytes=args.max_size)
    print(f"  Found {result['source_count']} sources ({_human_size(result['total_size_bytes'])})")
    print(f"  Languages: {', '.join(sorted(set(s['language'] for s in result['sources'])))}")

    # Store scan result in a well-known location so the FastAPI app can access it
    # without modifying the existing app startup code path
    _inject_into_app(result, args)

    # Load the I2I vessel-native package (same pattern as run_api.py)
    try:
        import open_notebook.i2i  # noqa: F401
        print("  I2I vessel-native package loaded")
    except ImportError as e:
        print(f"  Warning: I2I package not available ({e})")

    # Start the I2I vessel FS poller
    try:
        from open_notebook.i2i import start_poller as i2i_start_poller
        i2i_poller_task = i2i_start_poller()
        print(f"  I2I vessel FS poller started (task={i2i_poller_task})")
    except Exception as e:
        print(f"  Warning: I2I vessel poller failed to start: {e}")

    # Launch uvicorn
    import uvicorn

    host = args.host or os.getenv("API_HOST", "127.0.0.1")
    port = args.port or int(os.getenv("API_PORT", "8080"))
    reload_enabled = args.reload or (os.getenv("API_RELOAD", "false").lower() == "true")

    print(f"\n{'=' * 60}")
    print(f"  Notebook booted for {args.repo}")
    print(f"  Serving at http://{host}:{port}")
    print(f"  Sources loaded: {result['source_count']}")
    print(f"  Project: {result['project_name']}")
    print(f"{'=' * 60}\n")

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
        reload_dirs=[str(_project_root)] if reload_enabled else None,
    )


# ---------------------------------------------------------------------------
# Repository-scan injection
# ---------------------------------------------------------------------------
# We store the scan result as a module-level singleton so that the FastAPI app
# (which is already written and imported via ``api.main:app``) can fetch it.
# This avoids needing to modify the existing lifespan / startup code.

_SCAN_RESULT: dict | None = None


def _inject_into_app(result: dict, args: argparse.Namespace) -> None:
    """Make the scan result discoverable by the app at runtime."""
    global _SCAN_RESULT
    _SCAN_RESULT = {
        "result": result,
        "repo_path": str(Path(args.repo).resolve()),
    }

    # Also expose via the open_notebook package for easy import
    import open_notebook.repo_ingest as ri
    ri._BOOT_SCAN = _SCAN_RESULT


def _human_size(b: int) -> str:
    for unit in ("B", "KiB", "MiB"):
        if abs(b) < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} GiB"


def _print_dep_graph(graph: dict, indent: int = 0) -> None:
    """Pretty-print the dependency graph (outline)."""
    prefix = "  " * indent
    for key, val in graph.items():
        if isinstance(val, dict):
            files = val.pop("_files", 0) if "_files" in val else 0
            langs = val.pop("_language_tags", []) if "_language_tags" in val else []
            print(f"{prefix}{key}/  ({files} files, {', '.join(langs)})")
            _print_dep_graph(val, indent + 1)
        else:
            print(f"{prefix}{key}: {val}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="A2A-native-notebookLM — turn a git repo into a NotebookLM instance.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- boot ---
    boot = sub.add_parser("boot", help="Boot a full NotebookLM server from a repo")
    boot.add_argument("repo", type=str, help="Path to the git repository")
    boot.add_argument("--host", type=str, default=None, help="Bind host (default 127.0.0.1)")
    boot.add_argument("--port", type=int, default=8080, help="Bind port (default 8080)")
    boot.add_argument("--reload", action="store_true", help="Enable uvicorn auto-reload")
    boot.add_argument("--max-size", type=int, default=512 * 1024,
                      help="Max file size in bytes to include (default 512K)")
    boot.set_defaults(func=cmd_boot)

    # --- scan ---
    scan = sub.add_parser("scan", help="Scan a repo and print summary (no server)")
    scan.add_argument("repo", type=str, help="Path to the repository")
    scan.add_argument("--max-size", type=int, default=512 * 1024,
                      help="Max file size in bytes to include (default 512K)")
    scan.add_argument("--verbose", "-v", action="store_true", help="Show dependency graph")
    scan.set_defaults(func=cmd_scan)

    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
