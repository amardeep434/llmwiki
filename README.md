# LLMWiki

**Transform any codebase + PDF documentation into a searchable, interlinked knowledge base.**

LLMWiki is a zero-config pipeline that ingests source code (30+ languages), XML, PDFs, Markdown, and config files, then generates a static HTML site with full-text search, a knowledge graph with PageRank scoring, and AI-ready exports — all with just 2 pip dependencies.

---

## Quick Start

### macOS / Linux

```bash
pip install -e .
llmwiki init --source /path/to/your/project
llmwiki all
llmwiki serve
# Open http://127.0.0.1:8765
```

### Windows

```batch
python -m pip install -e .
llmwiki init --source C:\path\to\your\project
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
│              │    │  (immutable  │    │  (curated    │
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
| Wiki  | `wiki/` | Curated pages, editable by humans    | Yes      |
| Site  | `site/` | Generated HTML, search index, exports| No       |

---

## CLI Reference

| Command            | Description                                      |
|--------------------|--------------------------------------------------|
| `llmwiki init`     | Initialize project — scan source, create config  |
| `llmwiki ingest`   | Run adapters to populate `raw/`                  |
| `llmwiki build`    | Build `wiki/` and `site/` from `raw/`            |
| `llmwiki serve`    | Start local HTTP server (default port 8765)      |
| `llmwiki search`   | Full-text search via SQLite FTS5                 |
| `llmwiki graph`    | Rebuild the knowledge graph                      |
| `llmwiki export`   | Generate AI-consumable exports                   |
| `llmwiki lint`     | Check for broken links and orphaned pages        |
| `llmwiki stats`    | Print inventory statistics                       |
| `llmwiki diff`     | Show changes since last build                    |
| `llmwiki all`      | Full pipeline: ingest → build → graph → export   |

See [docs/cli-reference.md](docs/cli-reference.md) for flags and examples.

---

## Feature Highlights

- **6 built-in adapters**: source-code (30+ languages), XML, PDF, Markdown, config files, generic text
- **Knowledge graph**: PageRank importance scoring, cluster detection via connected components
- **Dual search**: client-side Cmd+K palette (JSON index) + SQLite FTS5 (for AI agents)
- **AI exports**: `llms.txt`, `llms-full.txt`, `graph.jsonld`, `sitemap.xml`, per-page `.json`
- **Dashboard**: stats overview, category cards, most-connected pages
- **Incremental builds**: SHA-256 content hashing, only re-processes changed files
- **Cross-platform**: works on Windows, macOS, and Linux
- **Minimal dependencies**: just `markdown` + `pymupdf4llm` (everything else is stdlib)

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
  "build": { "out_dir": "site", "incremental": true, "search_mode": "auto" },
  "serve": { "port": 8765, "host": "127.0.0.1" },
  "cross_references": { "enabled": true, "importance_iterations": 20, "cluster_min_size": 3 },
  "exclude_global": ["node_modules", ".git", "build", "dist", "__pycache__"]
}
```

See [docs/configuration.md](docs/configuration.md) for the full reference.

---

## AI Agent Integration

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
- 2 pip dependencies: `markdown`, `pymupdf4llm`
- No database server — SQLite is built into Python

---

## License

MIT — see [LICENSE](LICENSE).
