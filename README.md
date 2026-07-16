# LLMWiki

**Transform any codebase + PDF documentation into a searchable, interlinked knowledge base.**

LLMWiki is a zero-config pipeline that ingests source code (30+ languages), XML, PDFs, Markdown, and config files, then generates a static HTML site with full-text search, a knowledge graph with PageRank scoring, and AI-ready exports — all with just 2 pip dependencies.

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

| Layer | Path    | Purpose                              | Mutable? |
|-------|---------|--------------------------------------|----------|
| Raw   | `raw/`  | Adapter output, never hand-edited    | No       |
| Wiki  | `wiki/` | Generated intermediate markdown      | No       |
| Site  | `site/` | Generated HTML, search index, exports| No       |

---

## CLI Reference

| Command            | Description                                      |
|--------------------|--------------------------------------------------|
| `llmwiki init`     | Initialize project — scan source, create config  |
| `llmwiki ingest`   | Run adapters to populate `raw/`                  |
| `llmwiki ingest --force` | Force re-ingest all files (ignore state cache) |
| `llmwiki clean`    | Clean generated data and reset state             |
| `llmwiki build`    | Build `wiki/` and `site/` from `raw/`            |
| `llmwiki build --theme <name>` | Build with a specific UI theme        |
| `llmwiki serve`    | Start local HTTP server (default port 8765)      |
| `llmwiki search`   | Full-text search via SQLite FTS5                 |
| `llmwiki graph`    | Rebuild the knowledge graph                      |
| `llmwiki export`   | Generate AI-consumable exports                   |
| `llmwiki lint`     | Check for broken links and orphaned pages        |
| `llmwiki stats`    | Print inventory statistics                       |
| `llmwiki themes`   | List available UI themes                         |
| `llmwiki add-source <path>` | Add a source directory or PDF folder to config |
| `llmwiki all`      | Full pipeline: ingest → build → graph → export → lint |
| `llmwiki agent`    | Enable/disable wiki-first agent behavior        |
| `llmwiki search --context` | Search with full LLM-ready context output |
| `llmwiki benchmark` | Compare token usage: raw files vs wiki search  |
| `llmwiki mcp`      | Start MCP server for IDE integration             |
| `llmwiki setup-agent` | Generate MCP configs for VS Code, Cursor, etc. |

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
- **AI agent integration**: MCP server for IDE integration (VS Code, Cursor, JetBrains, Windsurf), wiki-first agent behavior with 90%+ token savings, CLI extension generation for GitHub Copilot

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

LLMWiki includes powerful AI agent integration features that enable your IDE's AI assistant to leverage the wiki instead of reading raw files, reducing token usage by 90%+.

### MCP Server for IDE Integration

Start the MCP server to connect your IDE (VS Code, Cursor, JetBrains, Windsurf) to the wiki:

```bash
llmwiki mcp
```

Generate IDE configuration files:

```bash
llmwiki setup-agent --all
```

Enable wiki-first agent behavior:

```bash
llmwiki agent --enable
```

Measure token savings:

```bash
llmwiki benchmark "authentication flow"
```

See [docs/ai-integration.md](docs/ai-integration.md) and [docs/token-efficiency.md](docs/token-efficiency.md) for details.

### Export Files

LLMWiki generates several files designed for consumption by LLMs and AI agents:

| File               | Format   | Purpose                                           |
|--------------------|----------|---------------------------------------------------|
| `llms.txt`         | Text     | Index of all pages per [llmstxt.org](https://llmstxt.org) spec |
| `llms-full.txt`    | Text     | Flattened text dump of all page content (≤5 MB)   |
| `graph.jsonld`     | JSON-LD  | Knowledge graph in Schema.org format              |
| `sitemap.xml`      | XML      | Standard sitemap for crawlers                     |
| `llmwiki.db`       | SQLite   | FTS5-indexed database for structured queries      |
| `*.json`           | JSON     | Per-page metadata alongside each HTML page        |

See [docs/ai-integration.md](docs/ai-integration.md) for SQL query examples.

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Architecture](docs/architecture.md) | Data model, pipeline flow, adapter system |
| [Getting Started](docs/getting-started.md) | Step-by-step tutorial |
| [Configuration](docs/configuration.md) | Full `llmwiki.json` reference |
| [Adapters](docs/adapters.md) | Built-in adapters, language support, custom adapters |
| [AI Integration](docs/ai-integration.md) | Agent files, SQL cookbook |
| [Cross-References](docs/cross-references.md) | Edge extraction, PageRank, clusters |
| [CLI Reference](docs/cli-reference.md) | Every command with flags and examples |
| [FAQ](docs/faq.md) | Common questions and answers |
| [Contributing](CONTRIBUTING.md) | Development setup, PR guidelines |
| [Changelog](CHANGELOG.md) | Release history |

---

## Requirements

- Python 3.9+
- 2 pip dependencies: `markdown`, `pymupdf>=1.24.0`
- No database server — SQLite is built into Python

---

## License

MIT — see [LICENSE](LICENSE).
