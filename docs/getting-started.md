# Getting Started

This guide walks you through installing LLMWiki, ingesting a codebase, building the site, and searching it — in under 5 minutes.

---

## Prerequisites

- **Python 3.9 or later** (check with `python --version` or `python3 --version`)
- A codebase or set of PDFs you want to document

---

## Step 1: Install

### macOS / Linux

```bash
git clone https://github.com/your-org/llmwiki.git
cd llmwiki
pip install -e .
```

### Windows

```batch
git clone https://github.com/your-org/llmwiki.git
cd llmwiki
setup.bat
```

Or manually:

```batch
python -m pip install -e .
```

### Verify Installation

```bash
llmwiki --version
# llmwiki 0.1.0
```

---

## Step 2: Initialize a Project

Point LLMWiki at any source directory:

```bash
llmwiki init --source /path/to/your/codebase
```

This will:
1. Scan the source directory for supported file types
2. Report which adapters detected files (e.g., "Found 42 files for adapter 'source-code'")
3. Create `.llmwiki/raw/`, `.llmwiki/wiki/`, `.llmwiki/site/` inside your project
4. Generate `.llmwiki/llmwiki.json` configuration

**Default directory structure created:**

```
~/projects/my-app/              ← your source code
├── .llmwiki/                   ← wiki lives here (add to .gitignore)
│   ├── llmwiki.json            ← configuration
│   ├── raw/                    ← extracted markdown pages
│   ├── wiki/                   ← generated intermediate layer
│   └── site/                   ← generated static HTML site
├── src/                        ← your existing code
└── ...
```

**Optional flags:**

| Flag | Description |
|------|-------------|
| `--name` | Project name (defaults to directory name) |
| `--output` | Where to create the wiki (defaults to `<source>/.llmwiki/`) |

**Example:**

```bash
llmwiki init --source ~/projects/my-app --name "My App" --output ~/wikis/my-app
```

---

## Step 3: Configure Sources (Optional)

After init, edit `.llmwiki/llmwiki.json` to add additional source directories or documentation:

```json
{
  "sources": [
    { "path": "/home/user/projects/my-app", "type": "auto", "exclude": ["node_modules", ".git"] },
    { "path": "/home/user/projects/my-app/docs", "type": "auto", "exclude": [".git"] }
  ]
}
```

- **`sources[].path`** — absolute path to a codebase or docs directory. Each is scanned by all adapters (source-code, XML, markdown, config).
- Add as many entries as you need — pages from all sources are merged into one wiki with cross-references between them.

---

## Step 4: Add PDF Documentation (Optional)

Use the `add-source` CLI command to add PDF files or folders:

```bash
# Add a single PDF file
llmwiki add-source /path/to/admin-guide.pdf --type pdf --label admin

# Add an entire folder of PDFs (scanned recursively)
llmwiki add-source /path/to/manuals/ --type pdf --label manuals

# Add another documentation folder with a different label
llmwiki add-source /path/to/specs/ --type pdf --label specifications
```

Or edit `llmwiki.json` directly:

```json
{
  "pdf_sources": [
    { "path": "/path/to/admin-guide.pdf", "label": "admin" },
    { "path": "/path/to/manuals/", "label": "manuals" },
    { "path": "/path/to/specs/", "label": "specifications" }
  ]
}
```

- **`path`** — a single PDF file or a directory (all `.pdf` files found recursively)
- **`label`** — the category name for resulting wiki pages (each folder can have its own label)
- You can add as many entries as you need — each gets its own category in the wiki

**Adding code sources after init** also works:

```bash
# Add another codebase directory
llmwiki add-source /path/to/shared-libs

# Add a docs directory
llmwiki add-source /path/to/project/docs
```

---

## Step 5: Ingest

Extract content from all configured sources:

```bash
llmwiki ingest
```

Output:

```
📥 Ingesting sources...
  Added: 127
  Modified: 0
  Unchanged: 0
```

This runs each adapter over the source files and writes markdown pages to `raw/`. Files are hashed — running `ingest` again will skip unchanged files.

**Tip:** To force re-ingestion of all files (ignoring the state cache):

```bash
llmwiki ingest --force
```

---

## Step 5b: Clean (When Needed)

If you need to start fresh or clear out stale data:

```bash
# Clean site/ (default) — forces a rebuild
llmwiki clean

# Clean raw/ — forces full re-ingest
llmwiki clean --raw

# Clean everything (raw + wiki + site + state)
llmwiki clean --all
```

---

## Step 6: Build the Site

Generate the static HTML site, knowledge graph, and search index:

```bash
llmwiki build
```

Output:

```
🔨 Building site...
  Pages: 127
  Categories: 12
```

This creates:
- `site/index.html` — dashboard with stats and category overview
- `site/categories/` — HTML pages organized by category
- `site/search-index.json` — client-side search index
- `site/cross-references.json` — knowledge graph data

**Tip:** `--full` is accepted for compatibility, but current builds already regenerate `wiki/` and `site/` from `raw/`:

```bash
llmwiki build --full
```

**Tip:** Build with a specific theme:

```bash
llmwiki build --theme vodafone
```

Available built-in themes: `emerald-dark` (default), `vodafone`. Run `llmwiki themes` to see all options.

---

## Step 6.5: Enable AI Agent Integration (Optional)

Set up your IDE to use the wiki for intelligent code assistance:

```bash
# Generate MCP configs for your IDE
llmwiki setup-agent --all

# Enable wiki-first mode
llmwiki agent --enable

# Rebuild to update agent instructions
llmwiki build
```

Your IDE's AI assistant (Copilot, Cursor, Claude) will now query the wiki before reading raw files. Run `llmwiki benchmark "<query>"` to measure the actual savings on your repo.

See [Token Efficiency](token-efficiency.md) for measuring the savings.

---

## Step 7: Serve and Browse

Start the local development server:

```bash
llmwiki serve
```

```
🌐 Serving at http://127.0.0.1:8765/
   Press Ctrl+C to stop.
```

Open http://127.0.0.1:8765 in your browser. You'll see:

- **Dashboard** with page count, edge count, cluster count
- **Category cards** linking to each code/doc category
- **Most-connected pages** ranked by inbound links
- **Three-panel layout**: sidebar + content + graph panel
- **Dark/light theme toggle**

**Custom port or host:**

```bash
llmwiki serve --port 3000 --host 0.0.0.0
```

---

## Step 8: Search

### In the Browser

Press **Cmd+K** (macOS) or **Ctrl+K** (Windows/Linux) to open the search palette. Type to filter pages by title, category, or content.

### From the CLI

```bash
llmwiki search "database connection"
```

```
Found 3 results for: database connection

  [utility] DatabaseUtil
    ...manages >>>database connection<<< pooling...

  [config] db-config
    ...>>>database<<< >>>connection<<< string setup...

  [docs] deployment-guide
    ...>>>database<<< >>>connection<<< requirements...
```

---

## Step 9: Run Everything at Once

The `all` command runs the full pipeline in sequence:

```bash
llmwiki all
```

This executes: `ingest` → `build` → `graph` → `export` → `lint`.

---

## What's Next?

| Task | Guide |
|------|-------|
| Customize exclusions, build output, search mode | [Configuration](configuration.md) |
| Understand which adapters handle which files | [Adapters](adapters.md) |
| Use the knowledge base with AI agents | [AI Integration](ai-integration.md) |
| Check for broken links or orphaned pages | Run `llmwiki lint` |
| See change statistics | Run `llmwiki stats` |

---

## Platform Notes

### macOS

No special requirements. Works with the system Python (if 3.9+) or Homebrew Python.

### Linux

Most distributions include Python 3.9+. Ensure `pip` is installed:

```bash
# Debian/Ubuntu
sudo apt install python3-pip

# Fedora
sudo dnf install python3-pip
```

### Windows

- Use Python from [python.org](https://www.python.org/downloads/) or the Microsoft Store
- The `setup.bat` script handles `pip install -e .` automatically
- All paths in `llmwiki.json` can use forward slashes (`/`) or backslashes (`\`)
- The local server works on `127.0.0.1` by default — use `--host 0.0.0.0` for network access

### Virtual Environments (Recommended)

```bash
python -m venv .venv
source .venv/bin/activate    # macOS/Linux
.venv\Scripts\activate       # Windows
pip install -e .
```
