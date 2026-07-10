# CLI Reference

Complete reference for all LLMWiki commands, flags, and usage examples.

---

## Global Options

```bash
llmwiki --version    # Print version and exit
llmwiki --help       # Show help message
llmwiki -h           # Short help
```

---

## Commands

### `llmwiki init`

Initialize a new LLMWiki project by scanning a source directory.

```bash
llmwiki init --source PATH [--name NAME] [--output DIR]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--source` | Yes | — | Path to the source codebase to document |
| `--name` | No | *(directory name)* | Project name |
| `--output` | No | `.` | Where to create the project directories |

**Example:**

```bash
llmwiki init --source /home/user/my-app --name "My Application"
```

**Output:**

```
🔍 Scanning /home/user/my-app...
  Found 89 files for adapter 'source-code'
  Found 12 files for adapter 'xml'
  Found 5 files for adapter 'config'
  Found 3 files for adapter 'markdown'

✅ Created llmwiki.json
✅ Created raw/, wiki/, site/ directories

Run `llmwiki ingest` to extract content, then `llmwiki build` to generate the site.
```

**What it does:**
1. Scans the source directory for files matching registered adapters
2. Creates `raw/`, `wiki/`, `site/` directories
3. Writes a default `llmwiki.json` configuration file

---

### `llmwiki ingest`

Run adapters to extract content from source files into `raw/`.

```bash
llmwiki ingest [--adapter NAME] [--config PATH]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--adapter` | No | *(all adapters)* | Run only a specific adapter |
| `--config` | No | `llmwiki.json` | Path to the configuration file |

**Examples:**

```bash
# Run all adapters
llmwiki ingest

# Run only the source-code adapter
llmwiki ingest --adapter source-code

# Run only PDF ingestion
llmwiki ingest --adapter pdf

# Use a custom config location
llmwiki ingest --config /path/to/llmwiki.json
```

**Output:**

```
📥 Ingesting sources...
  Added: 42
  Modified: 3
  Unchanged: 82
```

**Incremental behavior:** Files are hashed with SHA-256. Only new or modified files are re-processed. The build state is stored in `.llmwiki-state.json`.

---

### `llmwiki build`

Generate the static site from `raw/` pages.

```bash
llmwiki build [--full] [--config PATH]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--full` | No | `false` | Force a full rebuild (ignore incremental state) |
| `--config` | No | `llmwiki.json` | Path to the configuration file |

**Examples:**

```bash
# Incremental build
llmwiki build

# Full rebuild
llmwiki build --full
```

**Output:**

```
🔨 Building site...
  Pages: 127
  Categories: 12
```

**What it generates:**
- `site/index.html` — dashboard
- `site/categories/` — HTML + JSON pages organized by category
- `site/search-index.json` — client-side search index
- `site/cross-references.json` — knowledge graph
- `site/style.css` and `site/script.js` — styling and interactive features

---

### `llmwiki serve`

Start a local HTTP server to browse the generated site.

```bash
llmwiki serve [--port PORT] [--host HOST]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--port` | No | `8765` | HTTP server port |
| `--host` | No | `127.0.0.1` | Bind address |

**Examples:**

```bash
# Default: http://127.0.0.1:8765
llmwiki serve

# Custom port
llmwiki serve --port 3000

# Allow network access
llmwiki serve --host 0.0.0.0 --port 8080
```

**Output:**

```
🌐 Serving at http://127.0.0.1:8765/
   Press Ctrl+C to stop.
```

Press **Ctrl+C** to stop the server.

---

### `llmwiki search`

Full-text search against the SQLite FTS5 index.

```bash
llmwiki search QUERY
```

| Argument | Required | Description |
|----------|----------|-------------|
| `QUERY` | Yes | Search query (FTS5 syntax supported) |

**Examples:**

```bash
llmwiki search "database connection"
llmwiki search "authentication OR authorization"
llmwiki search "config*"
```

**Output:**

```
Found 3 results for: database connection

  [utility] DatabaseUtil
    ...manages >>>database connection<<< pooling...

  [config] db-config
    ...>>>database<<< >>>connection<<< string setup...

  [docs] deployment-guide
    ...>>>database<<< >>>connection<<< requirements...
```

**FTS5 query syntax:**
- `word1 word2` — match both words (implicit AND)
- `word1 OR word2` — match either word
- `"exact phrase"` — match exact phrase
- `word*` — prefix matching
- `NEAR(word1 word2, 5)` — words within 5 tokens of each other

---

### `llmwiki graph`

Rebuild the knowledge graph from `raw/` pages.

```bash
llmwiki graph
```

No flags. Regenerates `site/cross-references.json` with updated nodes, edges, clusters, and importance scores.

---

### `llmwiki export`

Generate AI-consumable export files.

```bash
llmwiki export
```

No flags. Generates:
- `site/llms.txt` — page index
- `site/llms-full.txt` — full text dump (≤5 MB)
- `site/graph.jsonld` — JSON-LD knowledge graph
- `site/sitemap.xml` — standard sitemap

---

### `llmwiki lint`

Check for quality issues in the knowledge base.

```bash
llmwiki lint
```

No flags. Checks for:
- **Orphaned pages** (no inbound or outbound cross-references)
- **Broken wiki links** (`[[target]]` where target doesn't match any page ID)
- **Missing titles** (page title equals the slug/ID)

**Output format:**

```
[warning] orphan: Page 'misc/readme' has no cross-references
[error]   broken_link: Page 'utils' has broken wikilink: [[NonExistent]]
[info]    missing_title: Page 'config/db' has no distinct title
```

---

### `llmwiki stats`

Print inventory statistics for raw, wiki, and site directories.

```bash
llmwiki stats
```

**Output:**

```
📊 LLMWiki Statistics
  Raw: 127 files
  Wiki: 0 files
  Site: 342 files
```

---

### `llmwiki diff`

Show changes since the last build.

```bash
llmwiki diff
```

Reports files that have been added, modified, or deleted since the last ingestion.

---

### `llmwiki all`

Run the full pipeline in sequence.

```bash
llmwiki all [--config PATH] [--full]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--config` | No | `llmwiki.json` | Path to the configuration file |
| `--full` | No | `false` | Force full rebuild |

**Equivalent to running:**

```bash
llmwiki ingest && llmwiki build
```

**Example:**

```bash
llmwiki all --full
```

**Output:**

```
==================================================
  INGEST
==================================================
📥 Ingesting sources...
  Added: 127
  Modified: 0
  Unchanged: 0

==================================================
  BUILD
==================================================
🔨 Building site...
  Pages: 127
  Categories: 12
```
