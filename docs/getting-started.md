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
3. Create `raw/`, `wiki/`, `site/` directories
4. Generate `llmwiki.json` configuration

**Optional flags:**

| Flag | Description |
|------|-------------|
| `--name` | Project name (defaults to directory name) |
| `--output` | Where to create the project (defaults to `.`) |

**Example:**

```bash
llmwiki init --source ~/projects/my-app --name "My App" --output ~/wikis/my-app
```

---

## Step 3: Add PDF Documentation (Optional)

To include PDF files, edit `llmwiki.json` and add entries to `pdf_sources`:

```json
{
  "pdf_sources": [
    { "path": "/path/to/docs/architecture.pdf", "label": "architecture" },
    { "path": "/path/to/manuals/", "label": "manuals" }
  ]
}
```

- Point `path` at a single PDF file or a directory (all `.pdf` files will be found recursively)
- The `label` becomes the category for those pages

---

## Step 4: Ingest

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

**Tip:** To run only one adapter:

```bash
llmwiki ingest --adapter source-code
llmwiki ingest --adapter pdf
```

**Tip:** To force re-ingestion of all files (ignoring the state cache):

```bash
llmwiki ingest --force
```

---

## Step 4b: Clean (When Needed)

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

## Step 5: Build the Site

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

**Tip:** Force a full rebuild (ignore incremental state):

```bash
llmwiki build --full
```

**Tip:** Build with a specific theme:

```bash
llmwiki build --theme vodafone
```

Available built-in themes: `emerald-dark` (default), `vodafone`. Run `llmwiki themes` to see all options.

---

## Step 6: Serve and Browse

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

## Step 7: Search

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

## Step 8: Run Everything at Once

The `all` command runs the full pipeline in sequence:

```bash
llmwiki all
```

This executes: `ingest` → `build` (which includes graph, search index, and exports).

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
