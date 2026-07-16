# Changelog

All notable changes to LLMWiki are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- **AI Agent Integration**:
  - `llmwiki agent` — Enable/disable wiki-first agent behavior with `--enable`, `--disable`, `--status` flags
  - `llmwiki search` — Enhanced with `--json`, `--compact`, `--context` output modes for AI consumption
  - `llmwiki benchmark` — Token efficiency comparison between raw file access and wiki search
  - `llmwiki mcp` — MCP (Model Context Protocol) server for IDE integration via stdio JSON-RPC
  - `llmwiki setup-agent` — Generate MCP configs for VS Code, Cursor, JetBrains, Windsurf, GitHub Copilot CLI
  - Dashboard token stats widget showing raw tokens, wiki tokens, and compression percentage
  - [docs/token-efficiency.md](docs/token-efficiency.md) — Documentation on measuring and achieving 90%+ token savings
  - GitHub Copilot CLI extension generation (`--extension` flag)
  - Copilot CLI workspace config generation (`--cli` flag)
  - MCP tools: `wiki_search`, `wiki_get_page`, `wiki_list_categories`

---

## [0.1.0] — 2026-07-11

### Added

- **Core pipeline**: `init` → `ingest` → `build` → `serve` workflow
- **3-layer data model**: `raw/` (immutable extracted) → `wiki/` (generated intermediate) → `site/` (generated HTML)
- **6 built-in adapters**:
  - `source-code` — 30+ languages with language-specific parsing plus method/function extraction across Java, Python, and 16+ additional languages
  - `xml` — XML structure extraction with inline script detection
  - `pdf` — PDF-to-markdown conversion via `pymupdf` with font-based heading detection, table extraction via `find_tables()`, sub-bullet glyph handling, image extraction to `assets/`, and header/footer stripping
  - `markdown` — Pass-through with frontmatter extraction
  - `config` — Configuration file documentation (JSON, YAML, TOML, INI, etc.)
  - `generic` — Registered text adapter for explicit use (not auto-discovered)
- **Method tags**: extracted methods/functions are added as `method:*` tags for source pages
- **Knowledge graph**:
  - Cross-reference extraction from wiki links, Java imports, class references, SailPoint API refs, and connector names
  - **Title-based mention matching** — scans page bodies for other page titles to create `"mentions"` edges
  - Fuzzy reference resolution with partial slug matching
  - PageRank importance scoring (20 iterations, 0.85 damping factor)
  - Topic cluster detection via BFS connected components
- **Theme system**:
  - Swappable themes via CSS custom properties
  - Built-in themes: `emerald-dark` (default), `vodafone`
  - Custom themes: create a `.py` file in `llmwiki/render/themes/`
  - Config: `{"build": {"theme": "vodafone"}}` or `--theme` CLI flag
  - `llmwiki themes` command to list available themes
- **Three-panel UI layout**: sidebar + content + graph panel with responsive collapsing
- **Expandable sidebar navigation**: tier-2 subcategory drawers with inline page previews
- **Mini graph panel**: canvas-based force-directed graph on every detail page (2-hop neighborhood, spring simulation, color-coded nodes)
- **Full graph page**: vis-network force-directed view plus a neural-network layout
- **Graph tooltips**: hover cards surface page tags alongside importance and category data
- **Dual search**:
  - Client-side JSON search index with Cmd+K / Ctrl+K command palette
  - SQLite FTS5 full-text search database for AI agents and CLI queries
- **Inline category search**: listing pages can swap card grids for searchable result tables
- **Clickable method anchors**: method lists jump directly to highlighted declarations in code blocks
- **AI-consumable exports**:
  - `llms.txt` — page index per llmstxt.org specification
  - `llms-full.txt` — flattened text dump (≤5 MB)
  - `graph.jsonld` — JSON-LD knowledge graph (Schema.org)
  - `sitemap.xml` — standard sitemap
  - Per-page `.json` metadata files
- **Static site generation**:
  - Dashboard with stats, recent changes feed, category cards, and most-connected pages
  - Category index pages
  - Individual page detail views with backlink navigation and mini graph
  - Dark/light theme with system preference detection
- **Build history**: `build-history.json` written at the project root and copied into `site/`
- **CLI commands**: `init`, `ingest`, `clean`, `build`, `serve`, `search`, `graph`, `export`, `lint`, `stats`, `themes`, `all`
- **`llmwiki clean` command**: clean generated data (`--raw`, `--site`, `--all` flags)
- **`llmwiki ingest --force`**: force re-ingest all files by clearing state cache
- **`llmwiki build --theme`**: build with a specific theme override
- **Incremental ingestion**: SHA-256 content hashing, only changed files re-processed
- **Build state management**: `.llmwiki-state.json` tracks file hashes and build numbers
- **Quality checks**: `llmwiki lint` detects orphaned pages, broken wiki links, missing titles
- **Local development server**: built-in HTTP server with configurable port and host
- **Cross-platform support**: Windows, macOS, Linux
- **Minimal dependencies**: `markdown` + `pymupdf>=1.24.0` (all other functionality uses Python stdlib)
- **DESIGN.md**: full design system document
- **Comprehensive test suite**: unit tests for all modules plus end-to-end tests
