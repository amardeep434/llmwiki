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
    p_init.add_argument("--source", default=None, help="Path to source codebase (prompted if not given)")
    p_init.add_argument("--name", help="Project name (auto-detected if not given)")
    p_init.add_argument("--output", default=None, help="Where to create the wiki (default: <source>/.llmwiki/)")

    # ingest
    p_ingest = sub.add_parser("ingest", help="Run adapters to populate raw/")
    p_ingest.add_argument("--adapter", help="Run only a specific adapter (e.g., pdf, xml, source-code)")
    p_ingest.add_argument("--force", action="store_true", help="Force re-ingest all files (ignore state cache)")
    p_ingest.add_argument("--config", default="llmwiki.json", help="Config file path")

    # clean
    p_clean = sub.add_parser("clean", help="Clean generated data and reset state")
    p_clean.add_argument("--raw", action="store_true", help="Clean raw/ only (forces full re-ingest)")
    p_clean.add_argument("--site", action="store_true", help="Clean site/ only (forces rebuild)")
    p_clean.add_argument("--all", action="store_true", help="Clean everything (raw + wiki + site + state)")
    p_clean.add_argument("--config", default="llmwiki.json", help="Config file path")

    # build
    p_build = sub.add_parser("build", help="Build wiki/ and site/ from raw/")
    p_build.add_argument("--full", action="store_true", help="Force full rebuild")
    p_build.add_argument("--theme", help="Theme name (e.g., emerald-dark, vodafone)")
    p_build.add_argument("--config", default="llmwiki.json", help="Config file path")

    # serve
    p_serve = sub.add_parser("serve", help="Serve site locally")
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.add_argument("--host", default="127.0.0.1")

    # search
    p_search = sub.add_parser("search", help="Search the knowledge base")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--config", default="llmwiki.json", help="Config file path")
    p_search.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON array")
    p_search.add_argument("--compact", action="store_true", help="Minimal output (lowest tokens)")
    p_search.add_argument("--context", action="store_true", help="Full context for LLM consumption")

    # graph
    p_graph = sub.add_parser("graph", help="Rebuild knowledge graph")
    p_graph.add_argument("--config", default="llmwiki.json", help="Config file path")

    # export
    p_export = sub.add_parser("export", help="Generate AI-consumable exports")
    p_export.add_argument("--config", default="llmwiki.json", help="Config file path")

    # lint
    p_lint = sub.add_parser("lint", help="Check for broken links and orphans")
    p_lint.add_argument("--config", default="llmwiki.json", help="Config file path")

    # stats
    p_stats = sub.add_parser("stats", help="Print inventory statistics")
    p_stats.add_argument("--config", default="llmwiki.json", help="Config file path")

    # themes
    sub.add_parser("themes", help="List available UI themes")

    # add-source
    p_add = sub.add_parser("add-source", help="Add a source directory or PDF folder to config")
    p_add.add_argument("path", help="Path to source directory or PDF file/folder")
    p_add.add_argument("--type", choices=["code", "pdf"], default="code", help="Source type (default: code)")
    p_add.add_argument("--label", default="docs", help="Category label for PDF sources (default: docs)")
    p_add.add_argument("--config", default="llmwiki.json", help="Config file path")

    # agent
    p_agent = sub.add_parser("agent", help="Enable/disable wiki-first agent behavior")
    p_agent.add_argument("--enable", action="store_true", help="Enable wiki-first agent assist")
    p_agent.add_argument("--disable", action="store_true", help="Disable agent assist")
    p_agent.add_argument("--status", action="store_true", help="Show current status")
    p_agent.add_argument("--config", default="llmwiki.json", help="Config file path")

    # benchmark
    p_bench = sub.add_parser("benchmark", help="Compare token usage: raw files vs wiki search")
    p_bench.add_argument("query", help="Search query to benchmark")
    p_bench.add_argument("--config", default="llmwiki.json", help="Config file path")

    # mcp
    p_mcp = sub.add_parser("mcp", help="Start MCP server (stdio mode for IDE integration)")
    p_mcp.add_argument("--config", default="llmwiki.json", help="Config file path")

    # setup-agent
    p_setup = sub.add_parser("setup-agent", help="Generate MCP configs for IDE integration")
    p_setup.add_argument("--mcp", action="store_true", help="Generate MCP configs for all detected IDEs")
    p_setup.add_argument("--vscode", action="store_true", help="VS Code Copilot (.vscode/mcp.json)")
    p_setup.add_argument("--cursor", action="store_true", help="Cursor (.cursor/mcp.json)")
    p_setup.add_argument("--jetbrains", action="store_true", help="JetBrains (.idea/ai-mcp.json)")
    p_setup.add_argument("--windsurf", action="store_true", help="Windsurf (.windsurf/mcp.json)")
    p_setup.add_argument("--extension", action="store_true", help="Copilot CLI extension (.github/extensions/)")
    p_setup.add_argument("--cli", action="store_true", help="CLI instructions in CLAUDE.md/AGENTS.md")
    p_setup.add_argument("--all", action="store_true", help="Install everything")
    p_setup.add_argument("--config", default="llmwiki.json", help="Config file path")

    # all
    p_all = sub.add_parser("all", help="Full pipeline: ingest → build → graph → export → lint")
    p_all.add_argument("--config", default="llmwiki.json", help="Config file path")
    p_all.add_argument("--full", action="store_true", help="Force full rebuild")

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
        "graph": _cmd_graph,
        "export": _cmd_export,
        "lint": _cmd_lint,
        "all": _cmd_all,
        "stats": _cmd_stats,
        "themes": _cmd_themes,
        "clean": _cmd_clean,
        "add-source": _cmd_add_source,
        "agent": _cmd_agent,
        "benchmark": _cmd_benchmark,
        "mcp": _cmd_mcp,
        "setup-agent": _cmd_setup_agent,
    }

    handler = dispatch.get(args.command)
    if handler:
        return handler(args)

    print(f"Command '{args.command}' not yet implemented.", file=sys.stderr)
    return 1


def _cmd_init(args) -> int:
    """Initialize a new llmwiki project with interactive setup."""
    from llmwiki.config import create_default_config, save_config
    from llmwiki.adapters import detect_adapters

    print("═" * 50)
    print("  LLMWiki Project Setup")
    print("═" * 50)

    # 1. Source code path
    if args.source:
        source = Path(args.source).resolve()
    else:
        print("\n📁 Source Code Path")
        print("   Enter the root directory of your codebase:")
        raw = input("   > ").strip()
        if not raw:
            print("Error: source path is required", file=sys.stderr)
            return 1
        source = Path(raw).expanduser().resolve()

    if not source.exists():
        print(f"Error: source path does not exist: {source}", file=sys.stderr)
        return 1

    # 2. Project name
    name = args.name
    if not name:
        default_name = source.name
        print(f"\n📝 Project Name (default: {default_name})")
        raw_name = input(f"   > ").strip()
        name = raw_name or default_name

    # 3. Additional source directories
    sources = [{"path": str(source), "type": "auto", "exclude": []}]
    print(f"\n📂 Additional Source Directories")
    print("   Add extra directories (e.g. shared libs, separate docs repos).")
    print("   Press Enter with empty path when done.")
    while True:
        extra = input("   Additional path (or Enter to skip): ").strip()
        if not extra:
            break
        extra_path = Path(extra).expanduser().resolve()
        if not extra_path.exists():
            print(f"   ⚠ Path does not exist: {extra_path}, skipping")
            continue
        sources.append({"path": str(extra_path), "type": "auto", "exclude": []})
        print(f"   ✓ Added: {extra_path}")

    # 4. PDF documentation
    pdf_sources = []
    print(f"\n📄 PDF Documentation")
    print("   Add PDF files or directories containing PDFs.")
    print("   Press Enter with empty path when done.")
    while True:
        pdf_path = input("   PDF path (or Enter to skip): ").strip()
        if not pdf_path:
            break
        pdf_resolved = Path(pdf_path).expanduser().resolve()
        if not pdf_resolved.exists():
            print(f"   ⚠ Path does not exist: {pdf_resolved}, skipping")
            continue
        label = input(f"   Category label for '{pdf_resolved.name}' (default: docs): ").strip() or "docs"
        pdf_sources.append({"path": str(pdf_resolved), "label": label})
        print(f"   ✓ Added: {pdf_resolved} → [{label}]")

    # 5. Output directory
    output = Path(args.output).resolve() if args.output else source / ".llmwiki"

    print(f"\n{'─' * 50}")
    print(f"  Project:  {name}")
    print(f"  Sources:  {len(sources)} director{'y' if len(sources) == 1 else 'ies'}")
    print(f"  PDFs:     {len(pdf_sources)} entr{'y' if len(pdf_sources) == 1 else 'ies'}")
    print(f"  Output:   {output}")
    print(f"{'─' * 50}")

    # Detect adapters for primary source
    print(f"\n🔍 Scanning {source}...")
    detected = detect_adapters(source)
    for adapter_name, files in detected.items():
        print(f"  Found {len(files)} files for adapter '{adapter_name}'")

    # Create directories
    for d in ["raw", "wiki", "site"]:
        (output / d).mkdir(parents=True, exist_ok=True)

    # Create config with all collected sources
    from llmwiki.config import DEFAULT_EXCLUDE
    config = create_default_config(name, str(source))
    # Replace sources with all collected entries
    for s in sources:
        if not s["exclude"]:
            s["exclude"] = list(DEFAULT_EXCLUDE)
    config["sources"] = sources
    config["pdf_sources"] = pdf_sources

    cfg_path = output / "llmwiki.json"
    save_config(config, cfg_path)
    print(f"\n✅ Created {cfg_path}")
    print(f"✅ Created raw/, wiki/, site/ in {output}")

    # Generate agent schema files
    from llmwiki.agent_schema import write_agent_schemas

    written = write_agent_schemas(
        source, str(output / "site"), name,
        {"total_pages": 0, "total_edges": 0, "total_clusters": 0},
    )
    for f in written:
        print(f"✅ Generated {f}")

    print(f"\n🚀 Next steps:")
    print(f"   cd {output}")
    print(f"   llmwiki ingest     # Extract content from sources")
    print(f"   llmwiki build      # Generate the static site")
    print(f"   llmwiki serve      # Preview at http://127.0.0.1:8765")
    print(f"   llmwiki all        # Or run everything at once")
    return 0


def _cmd_ingest(args) -> int:
    """Run ingestion pipeline."""
    from llmwiki.config import load_config, validate_config
    from llmwiki.ingest import ingest_all

    cfg_path = Path(args.config)
    config = load_config(cfg_path)
    errors = validate_config(config)
    if errors:
        for e in errors:
            print(f"Config error: {e}", file=sys.stderr)
        return 1
    raw_dir = cfg_path.parent / "raw"
    raw_dir.mkdir(exist_ok=True)
    state_path = cfg_path.parent / ".llmwiki-state.json"

    # --force: delete state to force re-processing of all files
    if getattr(args, 'force', False):
        if state_path.exists():
            state_path.unlink()
            print("🔄 Force mode: cleared state cache — all files will be re-processed")

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
    from llmwiki.build import build_site
    from llmwiki.config import load_config, validate_config

    cfg_path = Path(args.config)
    config = load_config(cfg_path)
    errors = validate_config(config)
    if errors:
        for e in errors:
            print(f"Config error: {e}", file=sys.stderr)
        return 1

    # CLI --theme overrides config
    if getattr(args, 'theme', None):
        config.setdefault("build", {})["theme"] = args.theme

    root = cfg_path.parent

    print("🔨 Building site...")
    result = build_site(root, config, full=args.full)
    print(f"  Pages: {result.get('total_pages', 0)}")
    print(f"  Categories: {result.get('total_categories', 0)}")

    # Update agent schemas with real stats
    from llmwiki.agent_schema import write_agent_schemas

    source_path = config["sources"][0]["path"] if config.get("sources") else str(root)
    site_dir = root / config.get("build", {}).get("out_dir", "site")
    write_agent_schemas(
        Path(source_path), str(site_dir),
        config.get("project", {}).get("name", ""),
        result,
    )

    return 0


def _cmd_serve(args) -> int:
    """Serve the site locally."""
    from llmwiki.serve import serve_site
    return serve_site("site", port=args.port, host=args.host)


def _cmd_search(args) -> int:
    """Search the knowledge base via SQLite FTS5."""
    from llmwiki.config import load_config
    from llmwiki.search import (
        search_pages, format_results_json, format_results_compact, format_results_context
    )

    cfg_path = Path(args.config)
    if cfg_path.exists():
        config = load_config(cfg_path)
        out_dir = config.get("build", {}).get("out_dir", "site")
    else:
        out_dir = "site"
    db_path = Path(cfg_path.parent if cfg_path.exists() else ".") / out_dir / "llmwiki.db"
    
    results = search_pages(db_path, args.query)
    
    if not results:
        print(f"No results for: {args.query}")
        return 0
    
    # Format output based on flags
    if args.json_output:
        print(format_results_json(results))
    elif args.compact:
        print(format_results_compact(results))
    elif args.context:
        print(format_results_context(results, db_path))
    else:
        # Default human-readable format
        print(f"Found {len(results)} results for: {args.query}\n")
        for r in results:
            print(f"  [{r.get('category', '')}] {r['title']}")
            if r.get("snippet"):
                print(f"    {r['snippet']}")
            print()
    
    return 0


def _cmd_all(args) -> int:
    """Run full pipeline."""
    for cmd_name, cmd_func in [
        ("ingest", lambda: _cmd_ingest(args)),
        ("build", lambda: _cmd_build(args)),
        ("graph", lambda: _cmd_graph(args)),
        ("export", lambda: _cmd_export(args)),
        ("lint", lambda: _cmd_lint(args)),
    ]:
        print(f"\n{'='*50}")
        print(f"  {cmd_name.upper()}")
        print(f"{'='*50}")
        ret = cmd_func()
        if ret != 0:
            return ret
    return 0


def _cmd_graph(args) -> int:
    """Build knowledge graph."""
    from llmwiki.config import load_config
    from llmwiki.graph import build_graph, save_graph

    cfg_path = Path(args.config)
    config = load_config(cfg_path)
    root = cfg_path.parent
    raw_dir = root / "raw"
    site_dir = root / config.get("build", {}).get("out_dir", "site")
    print("📊 Building knowledge graph...")
    graph = build_graph(raw_dir)
    save_graph(graph, site_dir / "cross-references.json")
    print(f"  Nodes: {graph['stats']['total_pages']}")
    print(f"  Edges: {graph['stats']['total_edges']}")
    print(f"  Clusters: {graph['stats']['total_clusters']}")
    return 0


def _cmd_export(args) -> int:
    """Generate AI-consumable exports."""
    from llmwiki.config import load_config
    from llmwiki.graph import _load_pages, build_graph
    from llmwiki.exporters import export_all

    cfg_path = Path(args.config)
    config = load_config(cfg_path)
    root = cfg_path.parent
    raw_dir = root / "raw"
    site_dir = root / config.get("build", {}).get("out_dir", "site")
    pages = _load_pages(raw_dir)
    # Build graph for edge data in graph.jsonld export
    graph = build_graph(raw_dir)
    for pid, pdata in pages.items():
        cat = (pdata.get("category", "") or "uncategorized").lower()
        slug = pid.split("/")[-1] if "/" in pid else pid
        pdata["url"] = pdata.get("url") or f"/categories/{cat}/{slug}.html"
    project_name = config.get("project", {}).get("name", "")
    project_description = config.get("project", {}).get("description", "")
    base_url = config.get("project", {}).get("base_url", "http://localhost:8765")
    print("📤 Exporting AI-consumable formats...")
    export_all(pages, site_dir, project_name, base_url, project_description, graph=graph)
    print("  Generated: llms.txt, llms-full.txt, graph.jsonld, sitemap.xml")
    return 0


def _cmd_lint(args) -> int:
    """Lint wiki for quality issues."""
    from llmwiki.config import load_config
    from llmwiki.graph import build_graph
    from llmwiki.lint import lint_wiki

    cfg_path = Path(args.config)
    config = load_config(cfg_path)
    root = cfg_path.parent
    raw_dir = root / "raw"
    print("🔍 Linting wiki...")
    graph = build_graph(raw_dir)
    issues = lint_wiki(raw_dir, graph)
    for issue in issues:
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue["severity"], "•")
        print(f"  {icon} [{issue['rule']}] {issue['page']}: {issue['message']}")
    if not issues:
        print("  ✅ No issues found.")
    return 1 if any(i["severity"] == "error" for i in issues) else 0


def _cmd_stats(args) -> int:
    """Print inventory statistics."""
    from llmwiki.config import load_config

    cfg_path = Path(args.config).resolve()
    root = cfg_path.parent
    if cfg_path.exists():
        config = load_config(cfg_path)
        out_dir = config.get("build", {}).get("out_dir", "site")
    else:
        out_dir = "site"
    raw = root / "raw"
    wiki = root / "wiki"
    site = root / out_dir
    print("📊 LLMWiki Statistics")
    for label, d in [("Raw", raw), ("Wiki", wiki), ("Site", site)]:
        if d.exists():
            count = len(list(d.rglob("*")))
            print(f"  {label}: {count} files")
        else:
            print(f"  {label}: not built")
    return 0


def _cmd_themes(args) -> int:
    """List available UI themes."""
    from llmwiki.render.themes import list_themes
    print("🎨 Available themes:\n")
    for t in list_themes():
        print(f"  {t['name']:20s} — {t['description']}")
    print(f"\nUsage: llmwiki build --theme <name>")
    print(f"   Or: set \"theme\" in llmwiki.json under \"build\"")
    return 0


def _cmd_clean(args) -> int:
    """Clean generated data and reset state."""
    import shutil

    cfg_path = Path(args.config).resolve()
    root = cfg_path.parent
    state_path = root / ".llmwiki-state.json"

    clean_all = getattr(args, 'all', False)
    clean_raw = getattr(args, 'raw', False) or clean_all
    clean_site = getattr(args, 'site', False) or clean_all

    # If no specific flag, default to cleaning site + state (most common need)
    if not clean_raw and not clean_site and not clean_all:
        clean_site = True

    cleaned = []

    if clean_raw:
        raw_dir = root / "raw"
        if raw_dir.exists():
            shutil.rmtree(raw_dir)
            raw_dir.mkdir()
            cleaned.append("raw/")

    if clean_site:
        site_dir = root / "site"
        if site_dir.exists():
            shutil.rmtree(site_dir)
            site_dir.mkdir()
            cleaned.append("site/")

    if clean_all:
        wiki_dir = root / "wiki"
        if wiki_dir.exists():
            shutil.rmtree(wiki_dir)
            wiki_dir.mkdir()
            cleaned.append("wiki/")

    # Always reset state when cleaning raw or all
    if clean_raw or clean_all:
        if state_path.exists():
            state_path.unlink()
            cleaned.append(".llmwiki-state.json")

    if cleaned:
        print(f"🧹 Cleaned: {', '.join(cleaned)}")
        if clean_raw:
            print("   Run `llmwiki ingest` to re-process all sources.")
        elif clean_site:
            print("   Run `llmwiki build` to regenerate the site.")
    else:
        print("Nothing to clean.")

    return 0


def _cmd_add_source(args) -> int:
    """Add a source directory or PDF folder to the config."""
    from llmwiki.config import load_config, save_config, DEFAULT_EXCLUDE

    cfg_path = Path(args.config).resolve()
    if not cfg_path.exists():
        print(f"Error: config not found at {cfg_path}. Run `llmwiki init` first.", file=sys.stderr)
        return 1

    source_path = Path(args.path).expanduser().resolve()
    if not source_path.exists():
        print(f"Error: path does not exist: {source_path}", file=sys.stderr)
        return 1

    config = load_config(cfg_path)
    source_type = args.type

    if source_type == "pdf":
        pdf_sources = config.get("pdf_sources", [])
        for existing in pdf_sources:
            if Path(existing["path"]).resolve() == source_path:
                print(f"⚠ Already configured: {source_path}")
                return 0
        label = args.label
        pdf_sources.append({"path": str(source_path), "label": label})
        config["pdf_sources"] = pdf_sources
        save_config(config, cfg_path)
        if source_path.is_dir():
            pdf_count = len(list(source_path.rglob("*.pdf")))
            print(f"✅ Added PDF source: {source_path} ({pdf_count} PDF files found)")
        else:
            print(f"✅ Added PDF source: {source_path}")
        print(f"   Category label: {label}")
    else:
        sources = config.get("sources", [])
        for existing in sources:
            if Path(existing["path"]).resolve() == source_path:
                print(f"⚠ Already configured: {source_path}")
                return 0
        sources.append({
            "path": str(source_path),
            "type": "auto",
            "exclude": list(DEFAULT_EXCLUDE),
        })
        config["sources"] = sources
        save_config(config, cfg_path)
        from llmwiki.adapters import detect_adapters
        detected = detect_adapters(source_path)
        total = sum(len(f) for f in detected.values())
        print(f"✅ Added source: {source_path} ({total} files detected)")
        for adapter_name, files in detected.items():
            if files:
                print(f"   {adapter_name}: {len(files)} files")

    print(f"\nRun `llmwiki ingest` to process the new source.")
    return 0


def _cmd_agent(args) -> int:
    """Enable/disable wiki-first agent behavior."""
    from llmwiki.agent_toggle import enable_agent, disable_agent, get_agent_status
    cfg_path = Path(args.config).resolve()
    if not cfg_path.exists():
        print(f"Error: config not found: {cfg_path}", file=sys.stderr)
        return 1
    if args.enable:
        enable_agent(cfg_path)
        print("✅ Agent assist ENABLED — agents will query LLMWiki first")
        print("   Run `llmwiki build` to regenerate agent schema files")
        return 0
    if args.disable:
        disable_agent(cfg_path)
        print("🚫 Agent assist DISABLED — agents use normal file reading")
        print("   Run `llmwiki build` to regenerate agent schema files")
        return 0
    if args.status:
        status = get_agent_status(cfg_path)
        print(f"Agent assist: {'ENABLED ✅' if status else 'DISABLED 🚫'}")
        return 0
    # Default: show status
    status = get_agent_status(cfg_path)
    print(f"Agent assist: {'ENABLED ✅' if status else 'DISABLED 🚫'}")
    print("\nUsage:")
    print("  llmwiki agent --enable   Enable wiki-first agent behavior")
    print("  llmwiki agent --disable  Disable agent assist")
    return 0


def _cmd_benchmark(args) -> int:
    """Run token efficiency benchmark."""
    from llmwiki.benchmark import run_benchmark, format_benchmark_report
    from llmwiki.config import load_config
    cfg_path = Path(args.config).resolve()
    if not cfg_path.exists():
        print(f"Error: config not found: {cfg_path}", file=sys.stderr)
        return 1
    config = load_config(cfg_path)
    root = cfg_path.parent
    out_dir = config.get("build", {}).get("out_dir", "site")
    wiki_dir = root / out_dir
    source_dirs = [Path(s["path"]) for s in config.get("sources", [])]
    if not wiki_dir.exists():
        print("Error: site not built yet. Run `llmwiki all` first.", file=sys.stderr)
        return 1
    result = run_benchmark(args.query, source_dirs=source_dirs, wiki_dir=wiki_dir)
    print(format_benchmark_report(result))
    return 0


def _cmd_mcp(args) -> int:
    """Start MCP server for IDE integration."""
    from llmwiki.mcp_server import run_server
    from llmwiki.config import load_config
    cfg_path = Path(args.config).resolve()
    if cfg_path.exists():
        config = load_config(cfg_path)
        out_dir = config.get("build", {}).get("out_dir", "site")
        wiki_dir = str(cfg_path.parent / out_dir)
    else:
        wiki_dir = "site"
    run_server(wiki_dir)
    return 0


def _cmd_setup_agent(args) -> int:
    """Generate IDE integration configs and agent extensions."""
    from llmwiki.setup_agent import detect_ides, setup_all
    from llmwiki.config import load_config

    cfg_path = Path(args.config).resolve()
    if not cfg_path.exists():
        print(f"Error: config file not found: {cfg_path}", file=sys.stderr)
        print("Run `llmwiki init` first to create a project.", file=sys.stderr)
        return 1

    config = load_config(cfg_path)
    project_root = cfg_path.parent.parent  # config is in .llmwiki/
    wiki_subdir = cfg_path.parent.name  # ".llmwiki"

    # Determine which targets to generate
    targets = []

    # If --all or --mcp: detect + generate for all
    if args.all or args.mcp:
        detected = detect_ides(project_root)
        print(f"🔍 Detected IDEs: {', '.join(detected) if detected else 'none'}")
        targets.extend(detected)
        # Also add explicitly requested ones
        if args.vscode:
            targets.append("vscode")
        if args.cursor:
            targets.append("cursor")
        if args.jetbrains:
            targets.append("jetbrains")
        if args.windsurf:
            targets.append("windsurf")
        if args.extension or args.all:
            targets.append("copilot_cli")
        # Remove duplicates, preserve order
        seen = set()
        targets = [t for t in targets if not (t in seen or seen.add(t))]
    else:
        # Only generate explicitly requested targets
        if args.vscode:
            targets.append("vscode")
        if args.cursor:
            targets.append("cursor")
        if args.jetbrains:
            targets.append("jetbrains")
        if args.windsurf:
            targets.append("windsurf")
        if args.extension:
            targets.append("copilot_cli")

    if not targets and not args.cli:
        print("No targets specified. Use --all, --mcp, or specific flags (--vscode, --cursor, etc.)")
        return 1

    # Generate configs
    if targets:
        created = setup_all(project_root, wiki_subdir, targets)
        print("\n✅ Generated IDE integration configs:\n")
        for path in created:
            print(f"   {path}")

    # Handle --cli flag
    if args.cli:
        print("\n📝 CLI Usage Instructions:\n")
        print("   To use llmwiki from the command line:")
        print(f"   cd {project_root}/{wiki_subdir}")
        print("   llmwiki search \"your query\" --compact")
        print("\n   For Copilot CLI extension:")
        print("   gh copilot extensions reload")
        print("   Then use: @llmwiki_search in your prompt")

    print("\n🎉 Setup complete! Restart your IDE to load MCP configs.\n")
    return 0

