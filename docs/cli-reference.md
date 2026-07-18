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
✅ Created .llmwiki/raw/, .llmwiki/wiki/, .llmwiki/site/ directories

Run `llmwiki ingest` to extract content, then `llmwiki build` to generate the site.
```

**What it does:**
1. Scans the source directory for files matching registered adapters
2. Creates `.llmwiki/raw/`, `.llmwiki/wiki/`, `.llmwiki/site/` inside the source project (or at `--output` path)
3. Writes a default `llmwiki.json` configuration file

---

### `llmwiki ingest`

Run adapters to extract content from source files into `raw/`.

```bash
llmwiki ingest [--adapter NAME] [--force] [--config PATH]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--adapter` | No | *(all adapters)* | Accepted by the parser, but adapter-scoped ingestion is not currently wired up |
| `--force` | No | `false` | Force re-ingest all files (ignore state cache) |
| `--config` | No | `llmwiki.json` | Path to the configuration file |

**Examples:**

```bash
# Run all adapters
llmwiki ingest

# Force re-ingest everything (ignores cached hashes)
llmwiki ingest --force

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

**Incremental behavior:** Files are hashed with SHA-256. Only new or modified files are re-processed. The build state is stored in `.llmwiki-state.json`. Use `--force` to clear the state cache and re-process all files.

---

### `llmwiki clean`

Clean generated data and reset state.

```bash
llmwiki clean [--raw] [--site] [--all] [--config PATH]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--raw` | No | `false` | Clean `raw/` only (forces full re-ingest) |
| `--site` | No | `false` | Clean `site/` only (forces rebuild) |
| `--all` | No | `false` | Clean everything (raw + wiki + site + state) |
| `--config` | No | `llmwiki.json` | Path to the configuration file |

If no specific flag is given, defaults to cleaning `site/`.

**Examples:**

```bash
# Clean site (default)
llmwiki clean

# Clean raw (forces re-ingest of all files)
llmwiki clean --raw

# Clean everything and start fresh
llmwiki clean --all
```

**Output:**

```
🧹 Cleaned: raw/, .llmwiki-state.json
   Run `llmwiki ingest` to re-process all sources.
```

---

### `llmwiki build`

Generate the static site from `raw/` pages.

```bash
llmwiki build [--full] [--theme THEME] [--config PATH]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--full` | No | `false` | Accepted for compatibility; `build` already regenerates `wiki/` and `site/` from `raw/` |
| `--theme` | No | *(from config)* | Theme name (e.g., `emerald-dark`, `vodafone`) |
| `--config` | No | `llmwiki.json` | Path to the configuration file |

**Examples:**

```bash
# Rebuild wiki/ and site/
llmwiki build

# Accepted compatibility flag
llmwiki build --full

# Build with a specific theme
llmwiki build --theme vodafone
```

**Output:**

```
🔨 Building site...
  Pages: 127
  Categories: 12
```

**What it generates:**
- Regenerated `wiki/` intermediate pages
- `site/index.html` — dashboard
- `site/categories/` — HTML + JSON pages organized by category
- `site/search-index.json` — client-side search index
- `site/cross-references.json` — knowledge graph
- `build-history.json` at the project root and in `site/`
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
llmwiki search QUERY [--json|--compact|--context] [--config PATH]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `QUERY` | Yes | Search query (FTS5 syntax supported) |

| Flag | Default | Description |
|------|---------|-------------|
| `--json` | No | Output results as JSON array (for AI consumption) |
| `--compact` | No | Compact text format (title + snippet per line) |
| `--context` | No | Full LLM-ready context with page bodies |
| `--config` | No | Path to the configuration file |

**Examples:**

```bash
# Default human-readable output
llmwiki search "database connection"

# JSON output for AI agents
llmwiki search "authentication" --json

# Compact format (single line per result)
llmwiki search "config*" --compact

# Full context with page bodies (LLM-ready)
llmwiki search "user model" --context
```

**Default output:**

```
Found 3 results for: database connection

  [utility] DatabaseUtil
    ...manages >>>database connection<<< pooling...

  [config] db-config
    ...>>>database<<< >>>connection<<< string setup...

  [docs] deployment-guide
    ...>>>database<<< >>>connection<<< requirements...
```

**JSON output (`--json`):**

```json
[
  {
    "id": "utility/DatabaseUtil",
    "title": "DatabaseUtil",
    "category": "utility",
    "snippet": "...manages >>>database connection<<< pooling...",
    "url": "/categories/utility/DatabaseUtil.html"
  }
]
```

**Compact output (`--compact`):**

```
utility/DatabaseUtil | DatabaseUtil | ...manages >>>database connection<<< pooling...
config/db-config | db-config | ...>>>database<<< >>>connection<<< string setup...
```

**Context output (`--context`):**

```
=== Search Results: database connection ===

## [1] DatabaseUtil (utility)
Snippet: ...manages >>>database connection<<< pooling...

Full content:
# DatabaseUtil

Manages database connections and query execution.
...
[full page body]

---

## [2] db-config (config)
Snippet: ...>>>database<<< >>>connection<<< string setup...

Full content:
...
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
llmwiki graph [--config PATH]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--config` | No | `llmwiki.json` | Path to the configuration file |

Regenerates `site/cross-references.json` with updated nodes, edges, clusters, and importance scores.

---

### `llmwiki export`

Generate AI-consumable export files.

```bash
llmwiki export [--config PATH]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--config` | No | `llmwiki.json` | Path to the configuration file |

Generates:
- `site/llms.txt` — page index
- `site/llms-full.txt` — full text dump (≤5 MB)
- `site/graph.jsonld` — JSON-LD knowledge graph
- `site/sitemap.xml` — standard sitemap

---

### `llmwiki lint`

Check for quality issues in the knowledge base.

```bash
llmwiki lint [--config PATH]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--config` | No | `llmwiki.json` | Path to the configuration file |

Checks for:
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

### `llmwiki status`

Check whether the index is fresh versus the current source tree. Exits
non-zero when stale or never built, so it can gate hooks/CI.

```bash
llmwiki status [--config PATH] [--json]
```

Reports counts of modified/new/deleted source files since the last
ingest, with example paths. The same warning is automatically prepended
to `search`/`get`/MCP output when the index is stale.

---

### `llmwiki stats`

Print inventory statistics for raw, wiki, and site directories.

```bash
llmwiki stats [--config PATH]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--config` | No | `llmwiki.json` | Path to the configuration file |

**Output:**

```
📊 LLMWiki Statistics
  Raw: 127 files
  Wiki: 0 files
  Site: 342 files
```

---

### `llmwiki themes`

List available UI themes.

```bash
llmwiki themes
```

No flags. Lists all registered themes with their descriptions.

**Output:**

```
🎨 Available themes:

  emerald-dark         — Dark-first with emerald accent. Inspired by Supabase/VoltAgent.
  vodafone             — Bold Vodafone Red on dark surfaces. Monumental and confident.

Usage: llmwiki build --theme <name>
   Or: set "theme" in llmwiki.json under "build"
```

---

### `llmwiki add-source`

Add a source directory or PDF folder to the project configuration.

```bash
llmwiki add-source <path> [--type code|pdf] [--label NAME] [--config PATH]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `path` | Yes | — | Path to source directory, PDF file, or PDF folder |
| `--type` | No | `code` | Source type: `code` (codebase) or `pdf` (documentation) |
| `--label` | No | `docs` | Category label for PDF sources |
| `--config` | No | `llmwiki.json` | Path to the configuration file |

**Examples:**

```bash
# Add a code directory
llmwiki add-source ~/projects/shared-libs

# Add a PDF documentation folder
llmwiki add-source ~/manuals/ --type pdf --label admin-guides

# Add a single PDF file
llmwiki add-source ~/specs/architecture.pdf --type pdf --label architecture
```

Detects duplicates automatically. Run `llmwiki ingest` after adding sources.

---

### `llmwiki all`

Run the full pipeline in sequence.

```bash
llmwiki all [--config PATH] [--full]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--config` | No | `llmwiki.json` | Path to the configuration file |
| `--full` | No | `false` | Accepted for compatibility; the current build step already regenerates output |

**Equivalent to running:**

```bash
llmwiki ingest && llmwiki build && llmwiki graph && llmwiki export && llmwiki lint
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

==================================================
  GRAPH
==================================================
📊 Building knowledge graph...
  Nodes: 127
  Edges: 342
  Clusters: 8

==================================================
  EXPORT
==================================================
📤 Exporting AI-consumable formats...
  Generated: llms.txt, llms-full.txt, graph.jsonld, sitemap.xml

==================================================
  LINT
==================================================
🔍 Linting wiki...
  ✅ No issues found.
```

---

### `llmwiki agent`

Enable or disable wiki-first agent behavior.

```bash
llmwiki agent [--enable|--disable|--status] [--config PATH]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--enable` | No | Enable wiki-first agent behavior |
| `--disable` | No | Disable wiki-first agent behavior |
| `--status` | No | Show current agent mode status |
| `--config` | No | Path to the configuration file |

**Examples:**

```bash
# Enable wiki-first mode
llmwiki agent --enable

# Disable wiki-first mode
llmwiki agent --disable

# Check current status
llmwiki agent --status
```

**Output:**

```
✅ Agent mode enabled
   IDEs will query the wiki before reading raw files.
   Run `llmwiki build` to update agent instructions.
```

When enabled, generated agent instructions ask agents to search the wiki before reading raw files. Savings depend on the query type — run `llmwiki benchmark` for honest numbers.

---

### `llmwiki benchmark`

Compare token usage between raw file access and wiki search for a given query.

```bash
llmwiki benchmark QUERY [--config PATH]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `QUERY` | Yes | Search query to benchmark |

| Flag | Default | Description |
|------|---------|-------------|
| `--config` | No | Path to the configuration file |

**Example:**

```bash
llmwiki benchmark "authentication flow"
```

**Output:**

```
📊 Token Efficiency Benchmark

Query: "authentication flow"

Raw file approach:
  Files: 12
  Total tokens: 45,320
  Context size: 181,280 chars

Wiki search approach:
  Results: 3
  Total tokens: 2,840
  Context size: 11,360 chars

Efficiency:
  Token reduction: 93.7%
  Files saved: 9
  Tokens saved: 42,480
```

See [docs/token-efficiency.md](../token-efficiency.md) for methodology.

---

### `llmwiki mcp`

Start the MCP (Model Context Protocol) server for IDE integration.

```bash
llmwiki mcp [--config PATH]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--config` | No | Path to the configuration file |

**Example:**

```bash
llmwiki mcp
```

**Output:**

```
🚀 MCP server started (stdio mode)
   Listening for JSON-RPC messages on stdin/stdout
   Available tools: wiki_search, wiki_get_page, wiki_list_categories
   Press Ctrl+C to stop
```

The MCP server runs in stdio mode and communicates via JSON-RPC. IDEs connect to it using the configuration files generated by `llmwiki setup-agent`.

**Available MCP tools:**
- `wiki_search` — Full-text search with snippet results
- `wiki_get_page` — Retrieve full page content by ID
- `wiki_list_categories` — List all categories and page counts

---

### `llmwiki setup-agent`

Generate MCP configuration files for IDE integration.

```bash
llmwiki setup-agent [--mcp] [--vscode] [--cursor] [--jetbrains] [--windsurf] [--extension] [--cli] [--all] [--config PATH]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--mcp` | No | Generate generic MCP server config |
| `--vscode` | No | Generate VS Code settings.json snippet |
| `--cursor` | No | Generate Cursor IDE config |
| `--jetbrains` | No | Generate JetBrains IDE config |
| `--windsurf` | No | Generate Windsurf IDE config |
| `--extension` | No | Generate GitHub Copilot CLI extension |
| `--cli` | No | Generate Copilot CLI workspace config |
| `--all` | No | Generate all configuration files |
| `--config` | No | Path to the configuration file |

**Examples:**

```bash
# Generate all configs
llmwiki setup-agent --all

# Generate VS Code config only
llmwiki setup-agent --vscode

# Generate Cursor + JetBrains configs
llmwiki setup-agent --cursor --jetbrains

# Generate GitHub Copilot CLI extension
llmwiki setup-agent --extension
```

**Output:**

```
✅ Generated MCP configs:
   ~/.config/llmwiki/mcp-config.json
   ~/.vscode/settings.json (snippet)
   ~/.cursor/mcp.json
   ~/.config/JetBrains/mcp-servers.json
   ~/.windsurf/mcp-config.json
   .github/extensions/llmwiki-search/extension.mjs (Copilot CLI extension)
   .github/copilot-workspace.yml (Copilot CLI workspace config)

Next steps:
  1. Restart your IDE to load the MCP server
  2. Run `llmwiki mcp` to start the server (if not auto-started)
  3. Run `llmwiki agent --enable` to enable wiki-first mode
  4. Run `llmwiki build` to update agent instructions
```

The generated configs tell your IDE how to connect to the LLMWiki MCP server. Each IDE has a different config format; use the appropriate flag for your environment.
