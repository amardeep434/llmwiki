# Changelog

All notable changes to LLMWiki are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2026-07-11

### Added

- **Core pipeline**: `init` → `ingest` → `build` → `serve` workflow
- **3-layer data model**: `raw/` (immutable extracted) → `wiki/` (curated) → `site/` (generated HTML)
- **6 built-in adapters**:
  - `source-code` — 30+ languages with language-specific parsing (Java, Python, generic)
  - `xml` — XML structure extraction with inline script detection
  - `pdf` — PDF-to-markdown conversion via `pymupdf4llm`
  - `markdown` — Pass-through with frontmatter extraction
  - `config` — Configuration file documentation (JSON, YAML, TOML, INI, etc.)
  - `generic` — Fallback adapter for any text file
- **Knowledge graph**:
  - Cross-reference extraction from wiki links, Java imports, and class references
  - Fuzzy reference resolution with partial slug matching
  - PageRank importance scoring (configurable iterations, 0.85 damping factor)
  - Topic cluster detection via BFS connected components
- **Dual search**:
  - Client-side JSON search index with Cmd+K / Ctrl+K command palette
  - SQLite FTS5 full-text search database for AI agents and CLI queries
- **AI-consumable exports**:
  - `llms.txt` — page index per llmstxt.org specification
  - `llms-full.txt` — flattened text dump (≤5 MB)
  - `graph.jsonld` — JSON-LD knowledge graph (Schema.org)
  - `sitemap.xml` — standard sitemap
  - Per-page `.json` metadata files
- **Static site generation**:
  - Dashboard with stats, category cards, and most-connected pages
  - Category index pages
  - Individual page detail views with backlink navigation
  - Dark/light theme with system preference detection
- **Incremental builds**: SHA-256 content hashing, only changed files re-processed
- **Build state management**: `.llmwiki-state.json` tracks file hashes and build numbers
- **Quality checks**: `llmwiki lint` detects orphaned pages, broken wiki links, missing titles
- **CLI commands**: `init`, `ingest`, `build`, `serve`, `search`, `graph`, `export`, `lint`, `stats`, `diff`, `all`
- **Local development server**: built-in HTTP server with configurable port and host
- **Cross-platform support**: Windows, macOS, Linux
- **Minimal dependencies**: `markdown` + `pymupdf4llm` only (all other functionality uses Python stdlib)
- **Comprehensive test suite**: unit tests for all modules plus end-to-end tests
