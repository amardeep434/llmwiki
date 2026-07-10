"""CLI dispatcher for llmwiki."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from llmwiki import __version__


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="llmwiki",
        description="Generic codebase + documentation knowledge base pipeline",
    )
    parser.add_argument("--version", action="version", version=f"llmwiki {__version__}")

    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="Initialize a new llmwiki project")
    p_init.add_argument("--source", required=True, help="Path to source codebase")
    p_init.add_argument("--name", help="Project name (auto-detected if not given)")
    p_init.add_argument("--output", default=".", help="Where to create raw/wiki/site dirs")

    # ingest
    p_ingest = sub.add_parser("ingest", help="Run adapters to populate raw/")
    p_ingest.add_argument("--adapter", help="Run only a specific adapter")
    p_ingest.add_argument("--config", default="llmwiki.json", help="Config file path")

    # build
    p_build = sub.add_parser("build", help="Build wiki/ and site/ from raw/")
    p_build.add_argument("--full", action="store_true", help="Force full rebuild")
    p_build.add_argument("--config", default="llmwiki.json", help="Config file path")

    # serve
    p_serve = sub.add_parser("serve", help="Serve site locally")
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.add_argument("--host", default="127.0.0.1")

    # search
    p_search = sub.add_parser("search", help="Search the knowledge base")
    p_search.add_argument("query", help="Search query")

    # graph
    sub.add_parser("graph", help="Rebuild knowledge graph")

    # export
    sub.add_parser("export", help="Generate AI-consumable exports")

    # lint
    sub.add_parser("lint", help="Check for broken links and orphans")

    # stats
    sub.add_parser("stats", help="Print inventory statistics")

    # diff
    sub.add_parser("diff", help="Show changes since last build")

    # all
    p_all = sub.add_parser("all", help="Full pipeline: ingest → build → graph → export → lint")
    p_all.add_argument("--config", default="llmwiki.json", help="Config file path")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "init": _cmd_init,
        "ingest": _cmd_ingest,
        "build": _cmd_build,
        "serve": _cmd_serve,
        "search": _cmd_search,
        "all": _cmd_all,
        "stats": _cmd_stats,
    }

    handler = dispatch.get(args.command)
    if handler:
        return handler(args)

    print(f"Command '{args.command}' not yet implemented.", file=sys.stderr)
    return 1


def _cmd_init(args) -> int:
    """Initialize a new llmwiki project."""
    from llmwiki.config import create_default_config, save_config
    from llmwiki.adapters import detect_adapters

    source = Path(args.source).resolve()
    if not source.exists():
        print(f"Error: source path does not exist: {source}", file=sys.stderr)
        return 1

    output = Path(args.output).resolve()
    name = args.name or source.name

    # Detect adapters
    print(f"🔍 Scanning {source}...")
    detected = detect_adapters(source)
    for adapter_name, files in detected.items():
        print(f"  Found {len(files)} files for adapter '{adapter_name}'")

    # Create directories
    for d in ["raw", "wiki", "site"]:
        (output / d).mkdir(parents=True, exist_ok=True)

    # Create config
    config = create_default_config(name, str(source))
    cfg_path = output / "llmwiki.json"
    save_config(config, cfg_path)
    print(f"\n✅ Created llmwiki.json")
    print(f"✅ Created raw/, wiki/, site/ directories")
    print(f"\nRun `llmwiki ingest` to extract content, then `llmwiki build` to generate the site.")
    return 0


def _cmd_ingest(args) -> int:
    """Run ingestion pipeline."""
    from llmwiki.config import load_config
    from llmwiki.ingest import ingest_all

    cfg_path = Path(args.config)
    config = load_config(cfg_path)
    raw_dir = cfg_path.parent / "raw"
    raw_dir.mkdir(exist_ok=True)
    state_path = cfg_path.parent / ".llmwiki-state.json"

    print("📥 Ingesting sources...")
    result = ingest_all(config, raw_dir, state_path)
    print(f"  Added: {result['total_added']}")
    print(f"  Modified: {result['total_modified']}")
    print(f"  Unchanged: {result['total_unchanged']}")
    if result.get("total_errors"):
        print(f"  Errors: {result['total_errors']}")
    return 0


def _cmd_build(args) -> int:
    """Build wiki and site from raw."""
    try:
        from llmwiki.build import build_site
    except ImportError:
        print("Build module not yet implemented. Run `llmwiki ingest` first.", file=sys.stderr)
        return 1

    from llmwiki.config import load_config

    cfg_path = Path(args.config)
    config = load_config(cfg_path)
    root = cfg_path.parent

    print("🔨 Building site...")
    result = build_site(root, config, full=args.full)
    print(f"  Pages: {result.get('total_pages', 0)}")
    print(f"  Categories: {result.get('total_categories', 0)}")
    return 0


def _cmd_serve(args) -> int:
    """Serve the site locally."""
    try:
        from llmwiki.serve import serve_site
    except ImportError:
        print("Serve module not yet implemented.", file=sys.stderr)
        return 1
    return serve_site("site", port=args.port, host=args.host)


def _cmd_search(args) -> int:
    """Search the knowledge base via SQLite FTS5."""
    try:
        from llmwiki.search import cli_search
    except ImportError:
        print("Search module not yet implemented.", file=sys.stderr)
        return 1
    return cli_search(args.query, "site/llmwiki.db")


def _cmd_all(args) -> int:
    """Run full pipeline."""
    for cmd_name, cmd_func in [
        ("ingest", lambda: _cmd_ingest(args)),
        ("build", lambda: _cmd_build(args)),
    ]:
        print(f"\n{'='*50}")
        print(f"  {cmd_name.upper()}")
        print(f"{'='*50}")
        ret = cmd_func()
        if ret != 0:
            return ret
    return 0


def _cmd_stats(args) -> int:
    """Print inventory statistics."""
    raw = Path("raw")
    wiki = Path("wiki")
    site = Path("site")
    print("📊 LLMWiki Statistics")
    for label, d in [("Raw", raw), ("Wiki", wiki), ("Site", site)]:
        if d.exists():
            count = len(list(d.rglob("*")))
            print(f"  {label}: {count} files")
        else:
            print(f"  {label}: not built")
    return 0
