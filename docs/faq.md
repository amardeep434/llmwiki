# FAQ

Frequently asked questions about LLMWiki.

---

## General

### What is LLMWiki?

LLMWiki is a pipeline that transforms any codebase and PDF documentation into a searchable, interlinked knowledge base. It generates a static HTML site with full-text search, a knowledge graph with PageRank importance scoring, and AI-ready exports — all with just 2 pip dependencies.

### What languages does it support?

The source-code adapter handles 30+ languages including Java, Python, JavaScript, TypeScript, Go, Rust, C#, C/C++, Ruby, Kotlin, Swift, Scala, PHP, Shell, SQL, and more. See [Adapters](adapters.md) for the full list.

### What are the system requirements?

- Python 3.9 or later
- 2 pip dependencies: `markdown` and `pymupdf4llm`
- No database server (SQLite is built into Python)
- Works on Windows, macOS, and Linux

---

## Scale and Performance

### How big can a project get?

LLMWiki has been tested with codebases of several thousand source files. The main constraints are:

- **Ingestion**: proportional to the number of source files × average file size
- **Graph building**: proportional to the number of pages × number of edges
- **Site output**: one HTML + one JSON file per page, plus shared assets
- **SQLite FTS5**: handles millions of rows efficiently
- **llms-full.txt**: capped at 5 MB to stay within LLM context limits

For very large projects (10,000+ files), incremental builds ensure that only changed files are re-processed.

### Is ingestion incremental?

Yes. LLMWiki computes a SHA-256 hash of each source file. On subsequent runs of `llmwiki ingest`, only new or modified files are processed. The build state is tracked in `.llmwiki-state.json`.

### How fast are builds?

For a typical project (100–500 source files), the full pipeline (`llmwiki all`) completes in a few seconds. Incremental builds after minor changes take less than a second.

---

## File Management

### How do I exclude files or directories?

Three levels of exclusion:

**1. Per-source exclusions** in `llmwiki.json`:

```json
{
  "sources": [{
    "path": "/path/to/source",
    "exclude": ["node_modules", ".git", "build", "*.min.js"]
  }]
}
```

**2. Global exclusions** applied to all sources:

```json
{
  "exclude_global": ["node_modules", ".git", "__pycache__", "*.pyc"]
}
```

**3. Exclusion pattern types:**
- **Glob patterns** (`*.min.js`, `*.class`): matched against filenames
- **Directory names** (`node_modules`, `.git`): matched against path components

### How do I reset the project?

Delete the generated directories and state file:

```bash
rm -rf raw/ wiki/ site/ .llmwiki-state.json
```

Then re-run `llmwiki ingest && llmwiki build`.

### Can I edit pages in wiki/?

Yes. The `wiki/` layer is designed for human curation. You can edit titles, add notes, reorganize, or merge pages. The `wiki/` directory is not overwritten by `llmwiki ingest` (which only writes to `raw/`).

### What happens to deleted source files?

Currently, LLMWiki does not automatically remove pages from `raw/` when source files are deleted. To clean up:

1. Delete the `raw/` directory
2. Re-run `llmwiki ingest`
3. Re-run `llmwiki build`

---

## PDFs

### How good is PDF conversion?

LLMWiki uses `pymupdf4llm` for PDF-to-markdown conversion, which provides high-quality output including:

- Headings and hierarchy
- Lists (ordered and unordered)
- Tables
- Bold, italic, and code formatting
- Page boundaries

Complex layouts (multi-column, heavy diagrams, scanned documents) may produce less accurate results. For best results, use text-based PDFs rather than scanned images.

### Can I add PDFs from multiple directories?

Yes. Add multiple entries to `pdf_sources`:

```json
{
  "pdf_sources": [
    { "path": "/path/to/admin-docs", "label": "admin" },
    { "path": "/path/to/api-specs", "label": "api" },
    { "path": "/path/to/single-doc.pdf", "label": "architecture" }
  ]
}
```

Each `label` becomes a separate category in the knowledge base.

### What if pymupdf4llm is not installed?

The PDF adapter degrades gracefully — it produces a placeholder page with the filename and a message to install the dependency. All other adapters continue to work normally.

---

## Search

### What's the difference between client-side and SQLite search?

| Feature | Client-Side (Cmd+K) | SQLite FTS5 |
|---------|---------------------|-------------|
| Target | Humans (browser) | AI agents (programmatic) |
| Index | `search-index.json` | `llmwiki.db` |
| Matching | Fuzzy JS matching | FTS5 `MATCH` syntax |
| Ranking | Title/category priority | BM25 relevance |
| Context | First 1200 chars per page | Full page body |
| Server required | No (static files) | No (SQLite file) |

### How do I search from the command line?

```bash
llmwiki search "my query"
```

This uses the SQLite FTS5 database (`site/llmwiki.db`).

### Does search support boolean operators?

Yes, via FTS5 syntax:

```bash
llmwiki search "auth* AND NOT session"
llmwiki search "database OR connection"
llmwiki search "NEAR(config file, 3)"
```

---

## Cross-References and Graph

### Why are some pages orphaned?

Orphaned pages have no cross-references to or from other pages. Common causes:

- Standalone configuration files
- Top-level README or docs with no code references
- Files in languages without structured import parsing

Orphans are reported by `llmwiki lint`.

### How is importance calculated?

PageRank with a 0.85 damping factor over 20 iterations. Pages that are referenced by many other pages score higher. Scores are normalized to 0.0–1.0. See [Cross-References](cross-references.md) for details.

### What are clusters?

Clusters are groups of pages connected by cross-references, detected via BFS connected components. A cluster represents a topic area (e.g., "all database-related utilities"). Minimum cluster size is configurable (default: 3).

---

## Deployment

### Can I host the site on a CDN or static host?

Yes. The `site/` directory is a self-contained static site. Deploy it to any static hosting:

```bash
# GitHub Pages
cp -r site/ docs/

# Netlify / Vercel
# Point build output to the site/ directory

# S3
aws s3 sync site/ s3://my-bucket/
```

### Does it work without JavaScript?

The core pages (dashboard, category indexes, page details) render as plain HTML. Search and theme toggling require JavaScript.

### Can I use a custom domain?

The generated site uses relative URLs, so it works at any path or domain without configuration changes.

---

## Troubleshooting

### "Config file not found: llmwiki.json"

You're not in the project directory. Either `cd` to the directory containing `llmwiki.json` or use `--config`:

```bash
llmwiki build --config /path/to/llmwiki.json
```

### "Error: source path does not exist"

The `--source` path passed to `llmwiki init` doesn't exist. Verify the path:

```bash
ls /path/to/your/source
```

### Build produces 0 pages

Check that:
1. `llmwiki ingest` was run first (files must exist in `raw/`)
2. The source path in `llmwiki.json` is correct
3. Files aren't all excluded by the exclusion patterns

### Search returns no results

The SQLite database may not exist yet. Run `llmwiki build` to generate `site/llmwiki.db`.
