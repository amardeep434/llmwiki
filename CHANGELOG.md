# Changelog

All notable changes to LLMWiki are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added — synthesis layer (Phase S)

- **Curated knowledge layer**: a new `curated/**/*.md` tree (sibling of `raw/`)
  holds hand/agent-written pages — cross-file explanations, architecture,
  provisioning flows, saved Q&A — that llmwiki never generates or deletes.
  Curated pages carry `type` (module/concept/entity/note), `sources:` (page
  ids they derive from), and a `synthesized_at` timestamp; they merge into the
  graph with `cites` edges, are floored to importance ≥ 0.5 so they outrank
  extracted pages, and flow through the DB, search index, and exports.
  `llmwiki search --agent` marks them `[curated]`.
- **`llmwiki init` writes `SCHEMA.md`** — the conventions for writing curated
  pages (page types, required frontmatter, the "cite every claim" rule, the
  150-line limit, `[[page-id]]` linking, `> CONTRADICTION:` blockquotes).
  Re-running `init` never overwrites an edited `SCHEMA.md`.
- **`llmwiki synthesize`**: computes a prioritised work order — `refresh` items
  for curated pages whose cited sources changed since `synthesized_at`, then
  `create` items for the highest-importance extracted pages no curated page
  covers yet. Honours `--budget` (refresh first), prints a manifest (or
  `--json`), and writes per-item instructions to `synthesis-todo.md`.
- **Curated-aware lint**: new rules `stale-claim` (error), `uncited` (warning),
  `bad-source` (error), and `missing-type` (warning) validate the curated layer.

### Added — security hardening

- **Sensitive-file exclusion floor**: secret-bearing files (`.env`, `*.pem`,
  `*.key`, `id_rsa*`, `*credentials*`, `*secret*`, `.ssh`/`.aws`/`.gnupg`, and
  more) are now refused at config-load time regardless of a config's own
  `exclude` lists, protecting legacy/frozen configs without migration. Opt out
  with `"security": {"allow_sensitive_files": true}`. `.env` also removed from
  the config adapter's handled extensions (defence in depth).
- **Ingest-time redaction**: new `llmwiki/redact.py` scrubs high-confidence
  secrets (AWS access keys, Google API keys, PEM private-key blocks, JWTs, URL
  credentials, and gated `password=`/`token=`/`secret=` assignments with
  placeholder filtering) from every page body before it reaches `raw/`, the DB,
  the search index, or exports. Ingest reports `⚠ redacted N suspected
  credentials across M pages`. Extra patterns via `security.redact_patterns`;
  disable via `security.redact: false`.
- **Lint `secret-suspect` rule**: flags secrets still present in pages built
  before redaction existed (severity `error`, message names the kind).
- **Export gate**: `llms-full.txt` is re-scrubbed at export time with a
  prominent stderr warning — suspected secrets never ship in exports.

### Fixed — data correctness

- **Deleted/renamed sources are pruned end-to-end**: a full `llmwiki ingest`
  (or `all`) now detects source files that disappeared since the last run and
  removes their `raw/` pages and state entries; `llmwiki build` drops matching
  rows from `llmwiki.db` (and its FTS index) so a deleted or renamed file no
  longer lingers forever in `raw/`, search results, and exports. Ingest reports
  `Removed: N`. Pruning only runs on full ingests — a filtered `--adapter` run
  never prunes, since it sees only a subset of files. Legacy databases with
  pre-existing ghost rows self-heal on the next build.
- **Silent slug collisions fixed**: two files sharing a stem whose pages fell
  in the same category (e.g. `a/utils.py` and `b/utils.py`) previously
  overwrote each other, silently dropping one page. Page ids are now derived
  from the path *relative to the source root* (shared `adapters.base.make_slug`
  helper, used by the source/xml/markdown/config/generic adapters), guaranteeing
  uniqueness within a source. As a second safety net, ingest disambiguates any
  raw output filename that would collide within a run (appends a short content
  hash and logs a warning).
- **Atomic search-DB rebuild**: `llmwiki.db` is now built in a temp file and
  swapped in via `os.replace`, so agents querying mid-build never hit a locked
  or half-populated database. On Windows a locked target is retried, then falls
  back to the previous in-place write with a warning.

### Changed (breaking)

- **Page ids for nested files changed**: with path-aware slugs, files below the
  source root now carry directory context in their id (`svc/src/billing/utils`
  instead of `svc/utils`). Ids for files directly at the source root are
  unchanged. After upgrading, run `llmwiki clean && llmwiki all` once to
  regenerate under the new ids (build-time DB pruning clears the old-id rows
  automatically).

### Changed — credibility & CLI-first overhaul

- **Honest benchmark**: `llmwiki benchmark` now compares against a realistic
  grep-and-read agent baseline (top-5 term-ranked files) instead of summing
  every keyword-matching file in the tree; methodology is printed with every
  report, and negative savings are reported plainly.
- **Staleness detection**: new `llmwiki status` command plus automatic
  `⚠ index is STALE` warnings prepended to `search`/`get`/MCP responses when
  source files changed since the last ingest (stat-based check with hash
  confirmation; state now records mtime/size).
- **FTS5 query sanitization**: natural-language queries with colons, hyphens,
  or question marks no longer raise silent `OperationalError` → "no results";
  `method:<name>` queries route to method search (the documented agent
  workflow previously errored); substring fallback on residual FTS errors.
- **MCP server unified on FTS5**: MCP tools now query `llmwiki.db` (BM25)
  instead of naive substring matching over `search-index.json`, and
  `llmwiki_get_page` returns full source-stripped page content instead of a
  1200-char truncation (JSON index remains a fallback when no DB exists).
- **`--context` output fixed**: no longer embeds the full source file per
  result — returns the structured summary layer only.
- **Generic by default**: SailPoint/connector regexes removed from cross-ref
  extraction (now config-driven via `cross_references.custom_patterns`);
  BeanShell-in-XML extraction is opt-in per source.
- **Agent instruction files**: first write now includes idempotency markers
  (fixes duplicate sections on rebuild); generated guide compacted to ~15
  lines, CLI-first with `python -m llmwiki` fallback and file-based last
  resort; `llmwiki build` only refreshes existing marked sections — creating
  files is opt-in via `llmwiki setup-agent`.
- **Read-only SQL enforced**: `llmwiki query` opens the DB with
  `mode=ro` — the SELECT prefix check is no longer the security boundary.
- **Build performance**: search DB population batched into one
  connection/transaction instead of one per page.
- **CI**: GitHub Actions test matrix (Ubuntu/Windows/macOS × Python 3.9/3.13).
- **Docs**: repositioned around un-greppable knowledge (PDFs, vendor XML,
  architecture); removed unconditional "90%+ savings" claims.

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
