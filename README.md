# LLMWiki

**Make your un-greppable knowledge — PDFs, vendor docs, XML config, architecture — searchable by any AI coding agent. No MCP required.**

AI agents are good at grepping source code. They cannot grep a 400-page PDF, a vendor's XML configuration, or the architectural picture spread across both. LLMWiki ingests source code (30+ languages), XML, PDFs, Markdown, and config files into one FTS5-searchable knowledge base with a cross-reference graph, then exposes it three ways — plain CLI (works in any locked-down environment), static files (`llms.txt`, JSON index), and optionally MCP. Just 2 pip dependencies.

**Honesty note on token savings:** for questions answered by docs/PDFs/config, searching the wiki is dramatically cheaper than an agent flailing through raw files (which it often can't read at all). For plain source-code questions, modern agents' own grep-and-read is already efficient — the wiki helps with navigation (method → file lookup, cross-references) rather than replacing file reads. `llmwiki benchmark "<query>"` measures your actual numbers against a realistic grep-and-read baseline and will honestly tell you when the wiki is *not* cheaper.

---

## Quick Start

### macOS / Linux

```bash
pip install -e .
llmwiki init --source /path/to/your/project
cd /path/to/your/project/.llmwiki
llmwiki all
llmwiki serve
# Open http://127.0.0.1:8765
```

### Windows

```batch
python -m pip install -e .
llmwiki init --source C:\path\to\your\project
cd C:\path\to\your\project\.llmwiki
llmwiki all
llmwiki serve
```

Or run the setup script:

```batch
setup.bat
llmwiki init --source C:\path\to\your\project
```

---

## How It Works

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Sources    │    │    raw/      │    │    wiki/     │
│              │    │  (immutable  │    │  (generated  │
│  Code, PDFs, ├───►│   extracted  ├───►│   markdown)  │
│  XML, Docs   │    │   markdown)  │    │              │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                          ┌────────────────────┘
                          ▼
                    ┌──────────────┐
                    │    site/     │
                    │  (static    │
                    │   HTML +    │
                    │   search +  │
                    │   AI files) │
                    └──────────────┘
```

**3-layer data model:**

| Layer | Path      | Purpose                               | Mutable? |
| ----- | --------- | ------------------------------------- | -------- |
| Raw   | `raw/`  | Adapter output, never hand-edited     | No       |
| Wiki  | `wiki/` | Generated intermediate markdown       | No       |
| Site  | `site/` | Generated HTML, search index, exports | No       |

---

## CLI Reference

| Command                          | Description                                               |
| -------------------------------- | --------------------------------------------------------- |
| `llmwiki init`                 | Initialize project — scan source, create config          |
| `llmwiki ingest`               | Run adapters to populate`raw/`                          |
| `llmwiki ingest --force`       | Force re-ingest all files (ignore state cache)            |
| `llmwiki clean`                | Clean generated data and reset state                      |
| `llmwiki build`                | Build`wiki/` and `site/` from `raw/`                |
| `llmwiki build --theme <name>` | Build with a specific UI theme                            |
| `llmwiki serve`                | Start local HTTP server (default port 8765)               |
| `llmwiki search`               | Full-text search via SQLite FTS5                          |
| `llmwiki graph`                | Rebuild the knowledge graph                               |
| `llmwiki export`               | Generate AI-consumable exports                            |
| `llmwiki lint`                 | Check for broken links and orphaned pages                 |
| `llmwiki stats`                | Print inventory statistics                                |
| `llmwiki status`               | Check index freshness vs the source tree                  |
| `llmwiki themes`               | List available UI themes                                  |
| `llmwiki add-source <path>`    | Add a source directory or PDF folder to config            |
| `llmwiki all`                  | Full pipeline: ingest → build → graph → export → lint |
| `llmwiki agent`                | Enable/disable wiki-first agent behavior                  |
| `llmwiki search --context`     | Search with full LLM-ready context output                 |
| `llmwiki benchmark`            | Compare token usage: raw files vs wiki search             |
| `llmwiki mcp`                  | Start MCP server for IDE integration                      |
| `llmwiki setup-agent`          | Generate MCP configs for VS Code, Cursor, etc.            |

See [docs/cli-reference.md](docs/cli-reference.md) for flags and examples.

---

## Feature Highlights

- **6 built-in adapters**: source-code (30+ languages), XML, PDF, Markdown, config files, generic text (registered but not auto-discovered)
- **Method/function extraction**: Java, Python, and 16+ additional languages emit method/function lists plus `method:*` tags
- **PDF conversion**: pymupdf with font-based heading detection, table extraction, image extraction, header/footer stripping
- **Knowledge graph**: PageRank importance scoring, title-based cross-references, cluster detection
- **Cross-references**: wiki links, Java imports, class references, and title-mention matching
- **Mini graph panel**: canvas-based force-directed graph on every detail page (2-hop neighborhood)
- **Full graph explorer**: vis-network force-directed + neural-network views with hover tooltips that include page tags
- **Three-panel UI**: sidebar + content + graph panel with responsive collapsing
- **Sidebar navigation**: expandable tier-2 content-type tree with inline page previews
- **Theme system**: swappable themes via CSS variables (built-in: `emerald-dark`, `vodafone`)
- **Dual search**: client-side Cmd+K palette (JSON index) + SQLite FTS5 (for AI agents)
- **Inline category search**: listing pages can swap card grids for searchable result tables
- **Clickable method anchors**: method lists jump directly to highlighted declarations in code blocks
- **AI exports**: `llms.txt`, `llms-full.txt`, `graph.jsonld`, `sitemap.xml`, per-page `.json`
- **Dashboard**: stats overview, recent changes feed, category cards, most-connected pages
- **Incremental ingestion**: SHA-256 content hashing, only re-processes changed files
- **Clean & force workflow**: `llmwiki clean` resets state, `--force` re-ingests everything
- **Build history**: root + site `build-history.json` log each build summary
- **Cross-platform**: works on Windows, macOS, and Linux
- **Minimal dependencies**: just `markdown` + `pymupdf` (everything else is stdlib)
- **AI agent integration**: MCP server for IDE integration (VS Code, Cursor, JetBrains, Windsurf), CLI-first agent access (no MCP required), staleness warnings, honest token benchmarking, CLI extension generation for GitHub Copilot

---

## Configuration

LLMWiki stores its configuration in `llmwiki.json`, created by `llmwiki init`.

```json
{
  "project": { "name": "my-project", "description": "" },
  "sources": [
    { "path": "/path/to/source", "type": "auto", "exclude": ["node_modules", ".git"] }
  ],
  "pdf_sources": [],
  "build": { "out_dir": "site", "incremental": true, "theme": "emerald-dark" },
  "serve": { "port": 8765, "host": "127.0.0.1" },
  "cross_references": { "enabled": true, "importance_iterations": 20, "cluster_min_size": 3 },
  "exclude_global": ["node_modules", ".git", "build", "dist", "__pycache__"]
}
```

See [docs/configuration.md](docs/configuration.md) for the full reference.

---

## AI Agent Integration

Three access tiers, in order of universality. **The CLI is the primary interface** — many organizations cannot enable MCP servers, so everything works without one.

### 1. CLI (works everywhere an agent has a shell)

```bash
llmwiki search "<query>" --agent        # token-lean results: IDs + method signatures
llmwiki get "<page-id>"                 # full page, embedded source stripped
llmwiki search "method:<name>" --agent  # locate a function/method declaration
llmwiki status                          # is the index fresh vs the source tree?
llmwiki query "SELECT ..." --json       # read-only SQL over the FTS5 database
```

If `llmwiki` isn't on PATH (locked-down environments), every command also works as `python -m llmwiki ...`.

Add a compact (~15 line) instruction block to your agent files (CLAUDE.md, AGENTS.md, copilot-instructions.md) — **opt-in, never automatic**:

```bash
llmwiki setup-agent --cli
```

### 2. Static files (no tools at all)

`llms.txt` (index), `llms-full.txt`, `search-index.json`, per-page `.json`, `graph.jsonld` — any agent that can read files can use the wiki.

### 3. MCP server (bonus, where IDEs allow it)

```bash
llmwiki mcp                 # stdio JSON-RPC server backed by the same FTS5 database
llmwiki setup-agent --mcp   # generate configs for VS Code / Cursor / JetBrains / Windsurf
```

### Staleness protection

The wiki is a build artifact; code changes constantly during agent sessions. Every search/get/MCP response is preceded by a **STALE INDEX warning** when source files changed since the last ingest, telling the agent to prefer raw files or re-run `llmwiki all`. Check anytime with `llmwiki status`.

Measure your real token numbers (honest grep-and-read baseline, methodology printed):

```bash
llmwiki benchmark "authentication flow"
```

See [docs/ai-integration.md](docs/ai-integration.md) and [docs/token-efficiency.md](docs/token-efficiency.md) for details.

### Export Files

LLMWiki generates several files designed for consumption by LLMs and AI agents:

| File              | Format  | Purpose                                                      |
| ----------------- | ------- | ------------------------------------------------------------ |
| `llms.txt`      | Text    | Index of all pages per[llmstxt.org](https://llmstxt.org) spec |
| `llms-full.txt` | Text    | Flattened text dump of all page content (≤5 MB)             |
| `graph.jsonld`  | JSON-LD | Knowledge graph in Schema.org format                         |
| `sitemap.xml`   | XML     | Standard sitemap for crawlers                                |
| `llmwiki.db`    | SQLite  | FTS5-indexed database for structured queries                 |
| `*.json`        | JSON    | Per-page metadata alongside each HTML page                   |

See [docs/ai-integration.md](docs/ai-integration.md) for SQL query examples.

---

## Documentation

| Guide                                       | Description                                          |
| ------------------------------------------- | ---------------------------------------------------- |
| [Architecture](docs/architecture.md)         | Data model, pipeline flow, adapter system            |
| [Getting Started](docs/getting-started.md)   | Step-by-step tutorial                                |
| [Configuration](docs/configuration.md)       | Full`llmwiki.json` reference                       |
| [Adapters](docs/adapters.md)                 | Built-in adapters, language support, custom adapters |
| [AI Integration](docs/ai-integration.md)     | Agent files, SQL cookbook                            |
| [Cross-References](docs/cross-references.md) | Edge extraction, PageRank, clusters                  |
| [CLI Reference](docs/cli-reference.md)       | Every command with flags and examples                |
| [FAQ](docs/faq.md)                           | Common questions and answers                         |
| [Contributing](CONTRIBUTING.md)              | Development setup, PR guidelines                     |
| [Changelog](CHANGELOG.md)                    | Release history                                      |

---

## Requirements

- Python 3.9+
- 2 pip dependencies: `markdown`, `pymupdf>=1.24.0`
- No database server — SQLite is built into Python

---

## License

MIT — see [LICENSE](LICENSE).
