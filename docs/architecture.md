# Architecture

LLMWiki transforms source code and documentation into a searchable knowledge base through a three-layer pipeline. This document covers the data model, processing pipeline, adapter system, cross-reference engine, and search architecture.

---

## 3-Layer Data Model

```
Sources                raw/                  wiki/                 site/
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│ .java    │     │ Immutable    │     │ Generated    │     │ index.html       │
│ .py      │────►│ markdown     │────►│ markdown     │────►│ categories/      │
│ .xml     │     │ with YAML    │     │ (intermediate) │     │ search-index.json│
│ .pdf     │     │ frontmatter  │     │              │     │ llmwiki.db       │
│ .md      │     │              │     │              │     │ llms.txt         │
│ .json    │     │              │     │              │     │ graph.jsonld     │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────────┘
                   (never edit)        (generated)           (regenerated)
```

### Layer Details

| Layer | Directory | Contents | Lifecycle |
|-------|-----------|----------|-----------|
| **Raw** | `raw/` | Adapter-generated markdown with YAML frontmatter. One `.md` file per source file. | Regenerated on every `ingest`. Never hand-edit. |
| **Wiki** | `wiki/` | Generated intermediate markdown enriched with importance, tags, and cluster data. | Regenerated on every `build`. Do not hand-edit. |
| **Site** | `site/` | Static HTML, CSS, JS, search indexes, graph data, and exported artifacts. | Rebuilt by `build`, then supplemented by `export`. |

### Page Format

Every page in `raw/` and `wiki/` follows this format:

```markdown
---
title: "MyClassName"
slug: "com-example/MyClassName"
category: "com/example"
source_path: "/abs/path/to/MyClassName.java"
language: "java"
content_hash: "a1b2c3d4e5f6g7h8"
tags: [java]
references: [com.example.OtherClass, com.example.BaseClass]
---

## Overview

Class documentation extracted from Javadoc.

## Methods

- `doSomething()`
- `processData()`

## Source Code

<details><summary>Full source (42 lines)</summary>
...
</details>
```

---

## Pipeline Flow

```
llmwiki init          llmwiki ingest         llmwiki build         llmwiki export
     │                     │                      │                      │
     ▼                     ▼                      ▼                      ▼
  Scan source         Run adapters           Load raw/ pages        Generate AI exports
  Detect adapters     Hash each file         Build knowledge graph    ├─ llms.txt
  Create dirs         Skip unchanged           ├─ Extract edges        ├─ llms-full.txt
  Write config        Extract WikiPages        ├─ Compute PageRank     ├─ graph.jsonld
                      Write raw/*.md           ├─ Detect clusters      └─ sitemap.xml
                      Update state file      Regenerate wiki/
                                             Render HTML
                                             Build search index
                                             Write CSS/JS
                                             Write build-history.json
```

### Step 1: Init (`llmwiki init --source PATH`)

1. Scans the source directory
2. Auto-detects which adapters are needed (by file extension)
3. Creates `raw/`, `wiki/`, `site/` directories
4. Writes `llmwiki.json` configuration

### Step 2: Ingest (`llmwiki ingest`)

1. Loads configuration from `llmwiki.json`
2. For each configured source, runs matching adapters
3. Each adapter produces `WikiPage` objects (slug, title, category, body, references)
4. Pages are written as markdown files to `raw/{category}/{slug}.md`
5. Content hashing (SHA-256) enables incremental ingestion — unchanged files are skipped
6. Build state is tracked in `.llmwiki-state.json`

### Step 3: Build (`llmwiki build`)

1. Loads all `raw/*.md` pages and parses frontmatter
2. Builds the knowledge graph:
   - Extracts cross-references from frontmatter and body text
   - Resolves fuzzy references (partial slug matching)
   - Computes PageRank importance scores (hardcoded to 20 iterations, 0.85 damping)
   - Detects topic clusters via connected components (BFS, hardcoded minimum size 3)
3. Regenerates `wiki/` as enriched intermediate markdown
4. Renders HTML:
   - Dashboard (`index.html`) with stats, categories, top pages, and recent changes
   - Category index pages (`categories/{cat}/index.html`)
   - Individual page detail pages with backlinks and mini graph panel
   - Per-page JSON files for AI agents
5. Generates search infrastructure:
   - `search-index.json` for client-side Cmd+K search
   - `llmwiki.db` SQLite FTS5 database
6. Writes `style.css` and `script.js` (theme system, search palette, mini graph)
7. Applies the configured theme (CSS custom properties via `build.theme` or `--theme` flag)
8. Writes `build-history.json` at the project root and copies it into `site/`

### Step 4: Export (`llmwiki export`)

1. Loads the current page set from `raw/`
2. Generates AI export artifacts:
   - `llms.txt`
   - `llms-full.txt`
   - `graph.jsonld`
   - `sitemap.xml`

### Step 5: Serve (`llmwiki serve`)

1. Serves the generated `site/` directory over HTTP
2. Uses CLI `--host` / `--port` values rather than `llmwiki.json`

---

## Adapter System

Adapters are the ingestion plugins that convert source files into `WikiPage` objects.

```
                    ┌──────────────┐
                    │ BaseAdapter  │  (abstract)
                    │  can_handle()│
                    │  extract()   │
                    │  discover()  │
                    └──────┬───────┘
           ┌───────┬───────┼───────┬──────────┬──────────┐
           ▼       ▼       ▼       ▼          ▼          ▼
       source   xml     pdf    markdown   config    generic
        code
```

### Registration

Adapters register via the `@register` decorator:

```python
from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage

@register
class MyAdapter(BaseAdapter):
    name = "my-adapter"
    extensions = [".xyz"]

    def can_handle(self, path: Path) -> bool:
        return path.suffix == ".xyz"

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        # Return one or more WikiPage objects
        ...
```

### Auto-Detection

`llmwiki init` calls `detect_adapters(root)`, which:
1. Imports all built-in adapter modules
2. For each registered adapter, calls `discover(root)` to find matching files
3. Returns a mapping of adapter name → list of matching paths

### Exclusion Rules

The `BaseAdapter._is_excluded()` method supports two patterns:
- **Glob patterns** (containing `*` or `?`): matched against the filename
- **Plain names**: matched against individual path components relative to root

---

## Cross-Reference Engine

The cross-reference system creates a directed graph of page relationships.

### Edge Extraction (`crossref.py`)

Five regex patterns extract references from page bodies:

| Pattern | Matches | Example |
|---------|---------|---------|
| `[[target]]` or `[[target\|label]]` | Wiki-style links | `[[MyClass]]` |
| `import pkg.Class;` | Java imports | `import com.example.Util;` |
| `new/extends/implements Class` | Java class references | `extends BaseAdapter` |
| `sailpoint.pkg.Class` | SailPoint API references | `sailpoint.api.SailPointContext` |
| Connector names | Application connectors | `Active Directory`, `LDAP`, `REST` |

Java stdlib packages (`java.*`, `javax.*`, `org.w3c.*`, `org.xml.*`) are automatically filtered out.

### Title-Based Cross-References (`graph.py`)

In addition to pattern-based extraction, the graph builder performs **title-mention matching**: each page's body is scanned for occurrences of other page titles (≥6 characters, case-insensitive substring match). This produces `"mentions"` edges and dramatically increases graph connectivity.

- Titles shorter than 6 characters are skipped to avoid false positives
- Common generic words (e.g., "source", "import", "config") are excluded
- Edges per page are capped at 20 to prevent hub explosion

### Reference Resolution (`graph.py`)

Fuzzy matching resolves references to actual page IDs:
1. Build an index: `last-segment → full-id` for all pages
2. For each edge, look up the target by lowercase match
3. Fall back to matching the last `.`-separated segment

### Importance Scoring (`importance.py`)

PageRank with simplified parameters:
- **Iterations**: 20 (currently hardcoded; `cross_references.importance_iterations` is not wired yet)
- **Damping factor**: 0.85 (standard)
- **Output**: scores normalized to 0.0–1.0

### Cluster Detection (`clusters.py`)

Connected component analysis via BFS:
1. Build undirected adjacency from directed edges
2. BFS to find connected components
3. Filter components below 3 members (currently hardcoded; `cluster_min_size` is not wired yet)
4. Label clusters by most common tags

---

## Search Architecture

LLMWiki provides two independent search systems:

### Client-Side Search (for humans)

- **Index**: `search-index.json` — flat array of page entries with title, URL, category, tags, and body excerpt (first 1200 chars)
- **UI**: Cmd+K / Ctrl+K command palette in the browser
- **Matching**: JavaScript fuzzy search over title, category, and body text
- **Zero server dependency**: works with any static file host

### SQLite FTS5 (for AI agents)

- **Database**: `llmwiki.db` in the site directory
- **Tables**: `pages` (populated metadata), `pages_fts` (FTS5 virtual table), plus schema placeholders for `edges`, `clusters`, and `build_history`
- **FTS5 columns**: title, body_plain, tags, category
- **Sync**: triggers keep FTS index in sync with the pages table automatically
- **Query**: standard FTS5 `MATCH` syntax with `snippet()` support

```sql
SELECT p.id, p.title, snippet(pages_fts, 1, '>>>', '<<<', '...', 50)
FROM pages_fts
JOIN pages p ON pages_fts.rowid = p.rowid
WHERE pages_fts MATCH 'authentication'
ORDER BY rank
LIMIT 10;
```

---

## Theme System

LLMWiki supports swappable UI themes via CSS custom properties. The layout, components, and JavaScript stay identical — only colors and typography change.

### Architecture

```
llmwiki/render/themes/
├── __init__.py         # Theme registry (get_theme, list_themes, register_theme)
├── emerald_dark.py     # Default theme
└── vodafone.py         # Vodafone brand theme
```

### How Themes Work

Each theme is a `Theme` dataclass that defines CSS custom properties:

- **Core colors**: accent, canvas, surface (4 levels), ink (4 levels), hairlines
- **Semantic colors**: success, warning, error, info
- **Graph node colors**: per-category (java, xml, beanshell, docs, config, tokens)
- **Light mode overrides**: automatically generated for `[data-theme="light"]`
- **Typography**: font-sans, font-mono

### Selecting a Theme

1. **Config file**: `{"build": {"theme": "vodafone"}}`
2. **CLI flag**: `llmwiki build --theme vodafone` (overrides config)
3. **Default**: `emerald-dark` if not specified

### Built-In Themes

| Name | Description |
|------|-------------|
| `emerald-dark` | Dark-first with emerald accent. Inspired by Supabase/VoltAgent. |
| `vodafone` | Bold Vodafone Red on dark surfaces. Monumental and confident. |

### Creating a Custom Theme

Create a `.py` file in `llmwiki/render/themes/`:

```python
from llmwiki.render.themes import Theme, register_theme

register_theme(Theme(
    name="my-theme",
    display_name="My Theme",
    description="Description here.",
    accent="#3b82f6",
    accent_hover="#60a5fa",
    accent_muted="#1e3a5f",
    accent_subtle="#0f172a",
    canvas="#0f0f14",
    surface_0="#16161d",
    surface_1="#1e1e28",
    surface_2="#262630",
    surface_3="#2e2e3a",
    ink="#e4e4e7",
    ink_muted="#a1a1aa",
    ink_subtle="#71717a",
    ink_faint="#52525b",
    hairline="#27272a",
    hairline_strong="#3f3f46",
))
```

Then import your module in `llmwiki/render/themes/__init__.py`'s `_ensure_loaded()` function.

---

## Mini Graph Panel

Every detail page includes a **mini graph panel** — a canvas-based force-directed visualization showing the page's local neighborhood (2-hop).

### How It Works

1. The page HTML includes a `<div id="mini-graph" data-page="...">` element in the third panel
2. On page load, JavaScript fetches `cross-references.json`
3. It extracts the 2-hop neighborhood (capped at 40 nodes)
4. A spring-based force simulation runs 30 iterations to compute layout
5. Nodes are rendered on an HTML5 `<canvas>` with color-coded categories
6. The current page is highlighted; clicking other nodes navigates to them

### Three-Panel UI Layout

The site uses a responsive three-panel layout:

```
┌─────────────┬──────────────────────────────────┬───────────────┐
│   Sidebar   │          Content Area            │  Graph Panel  │
│   (nav)     │     (page detail/dashboard)      │  (mini graph) │
│             │                                  │               │
└─────────────┴──────────────────────────────────┴───────────────┘
```

- **Sidebar**: category navigation, page list, search link
- **Content**: main page body with headings, code, backlinks
- **Graph panel**: canvas-rendered force-directed graph of cross-references

Panels are collapsible via toggle buttons and automatically collapse on narrow viewports (<1280px).

---

## File Structure

```
my-project/
├── llmwiki.json          # Project configuration
├── .llmwiki-state.json   # Build state (content hashes)
├── raw/                  # Adapter output (immutable)
│   ├── com/example/      # Categorized by package/path
│   │   ├── MyClass.md
│   │   └── Utils.md
│   └── docs/
│       └── readme.md
├── wiki/                 # Generated intermediate pages
│   └── ...
├── build-history.json    # Build log at project root
└── site/                 # Generated output
    ├── index.html        # Dashboard
    ├── style.css
    ├── script.js
    ├── search-index.json # Client-side search
    ├── cross-references.json
    ├── build-history.json
    ├── llmwiki.db        # SQLite FTS5
    ├── llms.txt          # AI: page index
    ├── llms-full.txt     # AI: full text dump
    ├── graph.jsonld      # AI: knowledge graph
    ├── sitemap.xml       # Standard sitemap
    └── categories/
        ├── java/
        │   ├── index.html
        │   ├── MyClass.html
        │   └── MyClass.json
        └── docs/
            └── index.html
```
