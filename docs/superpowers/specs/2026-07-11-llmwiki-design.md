# LLMWiki — Generic Codebase + Documentation Knowledge Base Pipeline

**Date:** 2026-07-11
**Status:** Design
**Approach:** Clean-room build inspired by [Pratiyush/llm-wiki](https://github.com/Pratiyush/llm-wiki) architecture

---

## 1. Problem Statement

Codebases accumulate vast amounts of knowledge — business logic in workflows, utility patterns in Java classes, integration details in connector configs, operational knowledge in PDF documentation — but this knowledge is fragmented across hundreds of files in different formats. Developers and AI agents struggle to find, connect, and reason about this knowledge.

**LLMWiki** is a generic, reusable pipeline that transforms any codebase + its documentation into a searchable, interlinked, evolving knowledge base — browsable by humans as a static site and queryable by AI agents via structured exports.

## 2. Goals

1. **Generic and reusable** — works with any codebase in any language, not tied to any specific technology
2. **Zero-config start** — `llmwiki init --source /path/to/project && llmwiki all && llmwiki serve`
3. **Fully local** — no external services, no cloud dependencies, no API keys
4. **Minimal dependencies** — Python 3.9+ stdlib + `markdown` + `pymupdf4llm` (2 pip packages)
5. **Dual audience** — beautiful browsable HTML for humans + structured exports for AI agents
6. **Evolving knowledge graph** — cross-references auto-extracted, importance scored, clusters detected
7. **Incremental builds** — only reprocess changed files, track build history over time
8. **Enterprise-grade** — handles 1000+ files, 177+ PDFs, production-quality output

## 3. Non-Goals

- No LLM enrichment (no Ollama, no API calls) — pure static extraction
- No real-time server (static site served via stdlib `http.server`)
- No user authentication or access control
- No collaborative editing (wiki pages can be hand-edited but no merge/conflict resolution)
- No image extraction from PDFs (text-only for now)

## 4. Architecture

### 4.1 Three-Layer Data Model

Inspired by [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):

```
Layer 1: raw/     ← Immutable machine-extracted content (never hand-edited)
Layer 2: wiki/    ← Curated markdown with cross-links (can be hand-edited)
Layer 3: site/    ← Generated outputs (HTML, SQLite, exports — safe to delete & regenerate)
```

**Layer 1 — `raw/` (immutable source of truth)**

Machine-generated markdown extracted from source files and PDFs. Each file has standardized YAML frontmatter and markdown body. Files are keyed by content hash for incremental builds. This layer is append-only during ingestion — files are never modified after creation, only replaced if source content changes.

```
raw/
├── codebase/
│   ├── <category>/
│   │   └── <slug>.md           # One page per source file
│   └── beanshell/
│       └── <parent>__<block>.md # Extracted inline scripts
├── docs/
│   ├── <label>/
│   │   └── <slug>.md           # Converted PDF pages
│   └── <label>/
│       └── <slug>.md
└── .llmwiki-state.json         # mtime + hash tracking per source file
```

**Layer 2 — `wiki/` (curated, interlinked)**

Generated from raw/ during build, but can be hand-edited. Cross-references, backlinks, and category indexes are injected here. Hand-edits are preserved across rebuilds via a merge strategy: the build system tracks which sections are auto-generated (marked with `<!-- llmwiki:auto -->` HTML comments) and which are hand-written. During rebuild, only auto-generated sections are replaced; hand-written sections are preserved in place.

```
wiki/
├── index.md                    # Master catalog with stats
├── overview.md                 # Living synthesis
├── cross-references.md         # Auto-generated cross-reference map
├── changelog.md                # Build history (auto-appended)
├── categories/
│   └── <category>.md           # Category index pages (auto-generated)
├── pages/
│   ├── codebase/
│   │   └── <category>/
│   │       └── <slug>.md       # Per-file detail pages
│   └── docs/
│       └── <label>/
│           └── <slug>.md
├── entities/                   # Cross-cutting entities (auto-detected)
│   └── <EntityName>.md
└── concepts/                   # Patterns, frameworks (auto-detected)
    └── <ConceptName>.md
```

**Layer 3 — `site/` (generated output)**

```
site/
├── index.html                  # Dashboard home page
├── style.css                   # All CSS (embedded, no CDN)
├── script.js                   # All JS (embedded, no CDN except highlight.js)
├── categories/
│   └── <category>/
│       ├── index.html          # Category index page
│       └── <slug>.html         # Per-file detail page
├── docs/
│   └── <label>/
│       └── <slug>.html         # Per-PDF page
├── graph.html                  # Interactive knowledge graph explorer
├── changelog.html              # Build history page
├── search-index.json           # Client-side fuzzy search index
├── search-chunks/
│   └── <category>.json         # Per-category search entries (lazy-loaded)
├── llmwiki.db                  # SQLite FTS5 database (AI agent queries)
├── llms.txt                    # AI-consumable short index
├── llms-full.txt               # AI-consumable full text dump
├── graph.jsonld                # JSON-LD knowledge graph
├── sitemap.xml                 # Standard sitemap
├── cross-references.json       # Machine-readable cross-ref data
├── build-history.json          # Structured build changelog
└── <page>.json                 # Per-page JSON siblings (structured metadata + body)
```

### 4.2 Pipeline Flow

```
                    llmwiki init
                         │
                         ▼
              Scan source directories
              Auto-detect languages & docs
              Generate llmwiki.json config
                         │
                         ▼
                   llmwiki ingest
                         │
          ┌──────────────┼──────────────────┐
          ▼              ▼                  ▼
    Source Code       PDF Docs          Markdown
    Adapter(s)        Adapter           Adapter
          │              │                 │
          ▼              ▼                 ▼
     Normalizer (standardized frontmatter + body)
          │
          ▼
     raw/<source>/<category>/<slug>.md
     .llmwiki-state.json updated
                         │
                         ▼
                   llmwiki build
                         │
     ┌───────────────────┼────────────────────┐
     ▼                   ▼                    ▼
  Wiki Gen          Cross-Ref            Site Gen
  (raw→wiki)        Engine              (wiki→site)
     │                   │                    │
     ▼                   ▼                    ▼
  wiki/ pages      graph.json           site/ HTML
  + categories     + backlinks          + CSS/JS
  + entities       + clusters           + search index
  + concepts       + importance         + SQLite DB
                                        + AI exports
                                        + build changelog
```

### 4.3 Adapter System

#### Base Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class WikiPage:
    """Standardized page output from any adapter."""
    slug: str                        # URL-safe identifier
    title: str                       # Human-readable title
    category: str                    # Hierarchical grouping (e.g., "workflows", "java/utility")
    source_path: str                 # Original file path (for incremental tracking)
    body: str                        # Markdown content
    language: str = ""               # Source language (java, python, xml, etc.)
    tags: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)    # Cross-references to other pages
    metadata: dict = field(default_factory=dict)            # Adapter-specific metadata
    content_hash: str = ""           # SHA-256 for change detection

class BaseAdapter(ABC):
    """All adapters implement this interface."""
    name: str
    extensions: list[str]            # File extensions this adapter handles

    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Return True if this adapter can process the given file."""
        ...

    @abstractmethod
    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        """Extract one or more WikiPage objects from the given file.
        
        Returns a list because one file may produce multiple pages
        (e.g., XML with inline BeanShell → parent page + extracted blocks).
        """
        ...

    def discover(self, root: Path, config: dict) -> list[Path]:
        """Find all files this adapter should process under root.
        Default: walk root and match by extension.
        """
        ...
```

#### Built-in Adapters

| Adapter | `name` | Extensions | Extraction Logic |
|---------|--------|-----------|-----------------|
| **SourceCodeAdapter** | `source-code` | `.java`, `.py`, `.ts`, `.js`, `.go`, `.rs`, `.cs`, `.c`, `.cpp`, `.rb`, `.kt`, `.swift`, `.scala`, `.php`, `.sh`, `.sql` | Language-aware parsing: extracts class/function/method signatures, docstrings/javadoc/jsdoc comments, import statements, module structure. For unsupported languages, falls back to comment extraction + structure detection via indentation/braces. |
| **XMLAdapter** | `xml` | `.xml`, `.xsl`, `.xslt`, `.xsd`, `.wsdl` | Parses XML structure, extracts element hierarchy, attributes, text content. Detects inline scripts (`<Source>`, `<Script>`, `<Code>` elements) and optionally extracts them as separate BeanShell/script pages with backlinks to parent. |
| **PDFAdapter** | `pdf` | `.pdf` | Uses pymupdf4llm to convert PDF → markdown. Auto-splits on chapter headings if document > threshold (configurable, default 50 pages). Preserves tables, code blocks, and structural formatting. Strips headers/footers/page numbers. |
| **MarkdownAdapter** | `markdown` | `.md`, `.mdx`, `.rst` | Pass-through with frontmatter normalization. Extracts existing frontmatter, adds missing fields (title from first heading, category from directory). |
| **ConfigAdapter** | `config` | `.json`, `.yaml`, `.yml`, `.toml`, `.properties`, `.ini`, `.env`, `.cfg` | Groups key-value pairs, documents each section/group, links to files that reference these config keys. |
| **GenericAdapter** | `generic` | `*` (fallback) | Basic text → markdown. Detects likely language from shebang/content, wraps in fenced code block with syntax hint. |

#### Adapter Auto-Detection

During `llmwiki init --source <path>`:

1. Walk the source directory (respecting `.gitignore` and default excludes)
2. Group files by extension
3. Select the most specific adapter for each extension
4. Report: "Found 74 Java files, 705 XML files, 27 properties files, 3 markdown files"
5. If unknown extensions found, report them and suggest the generic adapter

#### Custom Adapter Registration

Users can add custom adapters by placing Python files in `~/.llmwiki/adapters/` or `<project>/.llmwiki/adapters/`:

```python
from llmwiki.adapters.base import BaseAdapter, WikiPage

class TerraformAdapter(BaseAdapter):
    name = "terraform"
    extensions = [".tf", ".tfvars"]
    
    def can_handle(self, path):
        return path.suffix in self.extensions
    
    def extract(self, path, config):
        # Custom extraction logic
        return [WikiPage(...)]
```

### 4.4 Cross-Reference Engine

The cross-reference engine runs after ingestion and builds a directed knowledge graph.

#### Reference Extraction (per-adapter)

Each adapter extracts references during `extract()`:

| Source Type | References Extracted |
|------------|---------------------|
| Java | `import` statements → other Java pages; class/interface references in method signatures |
| XML (SailPoint) | `<Reference class="...">` → rule/workflow pages; `<ReferencedRules>` → rule library pages; subprocess calls → workflow pages |
| BeanShell | Java class references (`import`, `new ClassName()`, `ClassName.method()`) → Java pages |
| PDF docs | SailPoint API class names mentioned in text → Java/XML pages (fuzzy matching) |
| Config | Token/key names → files that use those tokens |

#### Graph Construction

```python
@dataclass
class KnowledgeGraph:
    nodes: dict[str, GraphNode]     # page_id → node
    edges: list[GraphEdge]          # directed edges
    clusters: list[Cluster]         # auto-detected topic clusters
    
@dataclass
class GraphNode:
    id: str                         # page slug
    title: str
    type: str                       # "java", "workflow", "rule", "pdf", etc.
    in_degree: int                  # number of pages referencing this one
    out_degree: int                 # number of pages this one references
    importance: float               # PageRank-inspired score (0.0 - 1.0)
    cluster_id: str | None          # which topic cluster this belongs to
    
@dataclass
class GraphEdge:
    from_id: str
    to_id: str
    edge_type: str                  # "calls", "imports", "references", "documents", "configures"
    
@dataclass
class Cluster:
    id: str
    label: str                      # auto-generated from most-common tags/categories
    members: list[str]              # page IDs
```

#### Importance Scoring

A simplified PageRank-like algorithm:

1. Initialize all pages with score 1.0
2. For N iterations (default 20):
   - Each page distributes its score equally across outbound edges
   - Each page's new score = 0.15 + 0.85 × (sum of incoming score shares)
3. Normalize to 0.0–1.0 range
4. Store as `importance_score` in SQLite and frontmatter

Pages with high importance surface first in search results and appear in the dashboard's "Most Connected" section.

#### Cluster Detection

Simple connected-component analysis:

1. Build undirected version of the graph
2. Find connected components with > 3 members
3. Label each cluster by the most common category/tags of its members
4. Store cluster membership on each node

#### Backlink Injection

After graph construction, every page in `wiki/` gets a "Referenced By" section appended (or updated if it already exists) listing all pages that have edges pointing to it.

### 4.5 Incremental Build System

#### State Tracking (`.llmwiki-state.json`)

```json
{
  "_meta": {
    "version": "1.0.0",
    "last_build": "2026-07-11T02:45:00+05:30",
    "build_number": 47
  },
  "files": {
    "/home/user/project/src/Main.java": {
      "mtime": 1752190800.0,
      "content_hash": "a1b2c3d4...",
      "raw_path": "raw/codebase/java/Main.md",
      "status": "current"
    }
  }
}
```

#### Incremental Build Flow

1. Walk all source directories
2. For each file, compare mtime + content_hash against `.llmwiki-state.json`
3. Classify each file: `new`, `modified`, `unchanged`, `deleted`
4. Only process `new` and `modified` files through adapters
5. For `deleted` files, mark wiki pages as archived (not deleted)
6. Re-run cross-reference engine on the full graph (fast — it's just JSON)
7. Regenerate only affected HTML pages + search index
8. Append build diff to `build-history.json`

#### Build History (`site/build-history.json`)

```json
[
  {
    "build_number": 47,
    "timestamp": "2026-07-11T02:45:00+05:30",
    "type": "incremental",
    "duration_seconds": 3.2,
    "changes": {
      "added": [{"id": "workflow/ManageMailbox", "title": "ManageMailbox Provisioning"}],
      "updated": [{"id": "java/CommonOperations", "title": "CommonOperations.java"}],
      "archived": [{"id": "workflow/OldTestWorkflow", "title": "Old Test Workflow"}]
    },
    "graph_diff": {
      "edges_added": 12,
      "edges_removed": 2,
      "new_clusters": ["Mailbox Provisioning"]
    },
    "stats": {
      "total_pages": 892,
      "total_edges": 2341,
      "total_clusters": 12
    }
  }
]
```

### 4.6 Static Site Generator

#### Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Markdown → HTML | `markdown` library with `fenced_code`, `tables`, `toc`, `sane_lists` extensions | Only runtime dependency; same as llm-wiki |
| CSS | Embedded Python string constant (~30-40KB) | No build step, no bundler, no CDN |
| JS | Embedded Python string constant (~30-40KB) | Vanilla JS, no framework |
| Syntax highlighting | highlight.js via pinned jsDelivr CDN | Only CDN dependency; degrades gracefully without network |
| Fonts | System font stack (no CDN) | `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` |
| Knowledge graph viz | vis-network via pinned jsDelivr CDN | Interactive force-directed graph; degrades to static list without network |
| HTTP server | `http.server.SimpleHTTPRequestHandler` (stdlib) | No dependencies |

#### Page Types

| Page | URL | Content |
|------|-----|---------|
| **Dashboard** | `/index.html` | Stats strip, activity timeline (SVG), recent changes feed, knowledge graph overview, category cards, most-connected pages bar chart |
| **Category Index** | `/categories/<cat>/index.html` | List of all pages in category, filterable by tags, sortable by importance/name/date |
| **Page Detail** | `/categories/<cat>/<slug>.html` | Metadata card, content body, BeanShell blocks (collapsible), cross-references (outbound + inbound backlinks), source code (collapsible) |
| **Doc Page** | `/docs/<label>/<slug>.html` | Converted PDF content with table of contents |
| **Graph Explorer** | `/graph.html` | Interactive force-directed graph with type/cluster filters, click-to-navigate, hover-preview |
| **Build Changelog** | `/changelog.html` | Timeline of all builds with change diffs |
| **Search** | Client-side via Cmd+K | Fuzzy search over `search-index.json`, structured queries (`type:`, `category:`, `tag:`) |

#### Dashboard Home Page

The dashboard is the primary entry point and shows the pulse of the knowledge base:

- **Stats strip** — total pages, total cross-references, total clusters, last build time
- **Activity timeline** — SVG bar chart showing pages added/updated over the last 30 days
- **Recent changes feed** — last 10 additions/updates/removals with timestamps and colored indicators (🟢 added, 🟡 updated, 🔴 archived)
- **Knowledge graph overview** — miniaturized force-directed graph (click "Explore" to go to full `/graph.html`)
- **Category cards** — grid of category cards with page counts and freshness indicators
- **Most connected pages** — horizontal bar chart of the top 10 pages by importance score

#### Interactive Features (client-side JS)

1. **Cmd+K search palette** — fuzzy search with structured query support (`type:workflow tag:approval`)
2. **Knowledge graph explorer** — vis-network force-directed graph, filter by type/cluster, click to navigate, hover for preview
3. **Collapsible sections** — BeanShell blocks, source code, long cross-reference lists (auto-collapse > 20 items)
4. **Filter bars** — on category index pages, filter by tags, importance range, date range
5. **Dark/light theme** — system-aware + manual toggle, persisted in localStorage
6. **Keyboard shortcuts** — `/` search, `j/k` navigate rows, `g h` home, `g c` categories, `?` help
7. **Copy buttons** — copy code blocks, copy page as markdown
8. **Breadcrumbs** — full navigation path on every page
9. **Reading progress bar** — scroll-linked on long pages

### 4.7 Search System

#### Dual Search Architecture

**1. Client-side fuzzy search (for humans browsing the site)**

- `search-index.json` — meta-level index with category entries + chunk manifest
- `search-chunks/<category>.json` — per-category entries loaded lazily on demand
- Each entry: `{id, url, title, type, category, tags, body_snippet (first 1200 chars), importance}`
- Cmd+K command palette with fuzzy matching on title + body
- Structured queries: `type:workflow`, `category:java`, `tag:approval`, `sort:importance`

**2. SQLite FTS5 (for AI agents and CLI queries)**

```sql
CREATE TABLE pages (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT,
    source_path TEXT,
    body_md TEXT,                    -- full markdown source
    body_plain TEXT,                 -- stripped plain text
    content_hash TEXT,
    tags TEXT,                       -- JSON array
    references_out TEXT,             -- JSON array of outbound page IDs
    references_in TEXT,              -- JSON array of inbound page IDs (backlinks)
    importance_score REAL DEFAULT 0.0,
    cluster_id TEXT,
    language TEXT,
    metadata TEXT,                   -- JSON object (adapter-specific)
    created_at TEXT,
    updated_at TEXT
);

CREATE VIRTUAL TABLE pages_fts USING fts5(
    title, body_plain, tags, category,
    content='pages', content_rowid='rowid'
);

CREATE TABLE edges (
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    PRIMARY KEY (from_id, to_id, edge_type)
);

CREATE TABLE clusters (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    member_count INTEGER,
    top_tags TEXT                    -- JSON array
);

CREATE TABLE build_history (
    build_number INTEGER PRIMARY KEY,
    timestamp TEXT,
    type TEXT,                      -- "full" or "incremental"
    duration_seconds REAL,
    added_count INTEGER,
    updated_count INTEGER,
    archived_count INTEGER,
    changes TEXT                     -- JSON object with full diff
);
```

AI agents query directly:
```bash
# Full-text search
sqlite3 site/llmwiki.db "SELECT title, snippet(pages_fts, 1, '>>>', '<<<', '...', 50) FROM pages_fts WHERE pages_fts MATCH 'provisioning workflow' ORDER BY rank LIMIT 10"

# Find most important pages
sqlite3 site/llmwiki.db "SELECT title, importance_score FROM pages ORDER BY importance_score DESC LIMIT 20"

# Trace cross-references
sqlite3 site/llmwiki.db "SELECT p.title, e.edge_type FROM edges e JOIN pages p ON e.to_id = p.id WHERE e.from_id = 'workflow/ManageEntitlement'"

# Find cluster members
sqlite3 site/llmwiki.db "SELECT title FROM pages WHERE cluster_id = 'entitlement-management'"
```

### 4.8 AI-Consumable Exports

| Export | File | Format | Purpose |
|--------|------|--------|---------|
| **llms.txt** | `/llms.txt` | Per [llmstxt.org](https://llmstxt.org) spec | Short index of all categories + pages with URLs |
| **llms-full.txt** | `/llms-full.txt` | Plain text, 5MB cap | Flattened text dump of all page bodies (for pasting into LLM context) |
| **JSON-LD graph** | `/graph.jsonld` | Schema.org `@graph` | Full knowledge graph as linked data (`CreativeWork` nodes for pages, relationships as edges) |
| **Sitemap** | `/sitemap.xml` | Standard sitemap | All page URLs with `lastmod` timestamps |
| **Per-page JSON** | `/<page>.json` | Structured JSON | `{id, title, category, type, tags, body_text, references, importance, sha256}` |
| **SQLite DB** | `/llmwiki.db` | SQLite3 + FTS5 | Full queryable database (see Section 4.7) |
| **Cross-references** | `/cross-references.json` | JSON | Full graph as `{nodes: [...], edges: [...], clusters: [...]}` |

### 4.9 Configuration

#### Auto-Generated Config (`llmwiki.json`)

Created by `llmwiki init`. Designed to work with zero manual editing for basic use cases.

```json
{
  "project": {
    "name": "My Project",
    "description": "Auto-detected from README or package manifest"
  },
  "sources": [
    {
      "path": "/path/to/project",
      "type": "auto",
      "exclude": ["node_modules", ".git", "build", "dist", "__pycache__",
                   "*.min.js", "*.min.css", "*.map", "*.lock"]
    }
  ],
  "pdf_sources": [
    {
      "path": "/path/to/docs",
      "label": "Documentation",
      "type": "auto"
    }
  ],
  "build": {
    "out_dir": "site",
    "incremental": true,
    "search_mode": "auto",
    "highlight_cdn": "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0"
  },
  "serve": {
    "port": 8765,
    "host": "127.0.0.1"
  },
  "cross_references": {
    "enabled": true,
    "importance_iterations": 20,
    "cluster_min_size": 3
  },
  "exclude_global": [
    "*.pyc", "*.class", "*.o", "*.so", "*.dll",
    "*.jpg", "*.png", "*.gif", "*.ico", "*.svg",
    "*.zip", "*.tar", "*.gz", "*.jar", "*.war",
    ".DS_Store", "Thumbs.db"
  ]
}
```

#### Interactive Init Flow

```
$ llmwiki init --source /home/amardeep/RioIAM

🔍 Scanning /home/amardeep/RioIAM...

Found:
  74 Java files (src/, pluginsrc/)
  705 XML files (config/)
  36 Properties files
  3 Markdown files
  13 PDF files (doc/)

Project name [RioIAM]: █
Description [SailPoint IdentityIQ implementation]: █

Do you have additional documentation directories? (y/N): y
  Path: /home/amardeep/Downloads/8.5p1 Connector and Integration Guides/
  Label [Connector Guides]: █
  Add another? (y/N): y
  Path: /home/amardeep/Downloads/identityiq-8.5/doc/
  Label [IIQ 8.5 Documentation]: █
  Add another? (y/N): N

✅ Created llmwiki.json
✅ Created raw/, wiki/, site/ directories

Run `llmwiki ingest` to extract content, then `llmwiki build` to generate the site.
```

## 5. CLI Interface

### Commands

| Command | Description |
|---------|-------------|
| `llmwiki init --source <path>` | Interactive setup: scan directory, detect languages, create config |
| `llmwiki ingest` | Run all adapters, populate `raw/` from configured sources |
| `llmwiki ingest --adapter <name>` | Run only a specific adapter (e.g., `--adapter pdf`) |
| `llmwiki ingest --source <path>` | Ingest a specific source path only |
| `llmwiki build` | Build `wiki/` and `site/` from `raw/` (incremental by default) |
| `llmwiki build --full` | Force full rebuild (ignore state) |
| `llmwiki serve` | Serve `site/` locally at `http://127.0.0.1:8765` |
| `llmwiki serve --port <N>` | Serve on a custom port |
| `llmwiki search <query>` | CLI search against SQLite FTS5 database |
| `llmwiki graph` | Rebuild knowledge graph only |
| `llmwiki export` | Generate all AI-consumable exports |
| `llmwiki lint` | Check for broken cross-references, orphaned pages |
| `llmwiki stats` | Print inventory statistics |
| `llmwiki diff` | Show what changed since last build |
| `llmwiki all` | Full pipeline: ingest → build → graph → export → lint |

### Entry Point

```toml
[project.scripts]
llmwiki = "llmwiki.cli:main"
```

Also runnable as `python -m llmwiki`.

## 6. Project Structure

```
~/llmwiki/                          # Standalone git repo, pip-installable
├── pyproject.toml
├── README.md
├── LICENSE
├── llmwiki/
│   ├── __init__.py                 # Version, lazy imports
│   ├── __main__.py                 # python -m llmwiki entry
│   ├── cli.py                      # argparse CLI dispatcher
│   ├── config.py                   # Load/validate llmwiki.json
│   ├── state.py                    # .llmwiki-state.json management
│   ├── ingest.py                   # Adapter orchestration → raw/
│   ├── build.py                    # wiki/ + site/ generation
│   ├── graph.py                    # Knowledge graph construction
│   ├── crossref.py                 # Cross-reference extraction
│   ├── importance.py               # PageRank-style scoring
│   ├── clusters.py                 # Topic cluster detection
│   ├── search.py                   # SQLite FTS5 + client-side index
│   ├── serve.py                    # Local HTTP server (stdlib)
│   ├── exporters.py                # llms.txt, JSON-LD, sitemap
│   ├── lint.py                     # Broken links, orphans, consistency
│   ├── adapters/
│   │   ├── __init__.py             # Adapter registry + auto-detection
│   │   ├── base.py                 # BaseAdapter ABC + WikiPage dataclass
│   │   ├── source_code.py          # Language-aware source code extraction
│   │   ├── xml_adapter.py          # XML structure + inline script extraction
│   │   ├── pdf_adapter.py          # PDF → markdown via pymupdf4llm
│   │   ├── markdown_adapter.py     # Markdown pass-through
│   │   ├── config_adapter.py       # Config file documentation
│   │   └── generic_adapter.py      # Fallback text adapter
│   └── render/
│       ├── __init__.py
│       ├── css.py                  # All CSS as Python string constant
│       ├── js.py                   # All JS as Python string constant
│       └── html.py                 # HTML page generators (functions, not template files)
└── tests/
    ├── test_adapters.py
    ├── test_build.py
    ├── test_crossref.py
    ├── test_graph.py
    ├── test_search.py
    └── test_cli.py
```

## 7. Dependencies

### Runtime (pip install)

```toml
[project]
requires-python = ">=3.9"
dependencies = [
    "markdown>=3.9",
    "pymupdf4llm>=0.0.17",
]
```

### Stdlib (no install needed)

`sqlite3`, `http.server`, `json`, `re`, `pathlib`, `hashlib`, `argparse`, `webbrowser`, `dataclasses`, `abc`, `collections`, `typing`, `xml.etree.ElementTree`, `urllib.parse`, `datetime`, `shutil`, `textwrap`, `math`

### CDN (loaded at view-time in browser, not Python deps)

- highlight.js 11.9.0 — syntax highlighting (pinned jsDelivr, degrades gracefully)
- vis-network 9.1.9 — knowledge graph visualization (pinned jsDelivr, degrades to static list)

### No runtime dependency on

- Node.js, npm
- Any cloud API
- Docker
- Any database server (SQLite is stdlib)
- Any ML/AI models

## 8. Error Handling

- **Corrupt PDFs** — log warning, skip file, continue processing
- **Unparseable source files** — fall back to generic adapter (raw text)
- **Missing source directories** — error on `ingest`, clear message
- **Circular cross-references** — handled by graph algorithm (PageRank converges regardless)
- **Very large files** — configurable size limit (default 5MB), skip with warning
- **Encoding issues** — try UTF-8, fall back to latin-1, log warning
- **Broken cross-references** — reported by `llmwiki lint`, shown with broken-link badge in UI

## 9. Performance Targets

| Metric | Target |
|--------|--------|
| Full ingest (872 files + 177 PDFs) | < 120 seconds |
| Incremental ingest (10 changed files) | < 5 seconds |
| Full build (892 pages) | < 30 seconds |
| Incremental build (10 changed pages) | < 3 seconds |
| Search query (SQLite FTS5) | < 50ms |
| Client-side search (Cmd+K) | < 200ms |
| Site serve startup | < 1 second |
| Memory usage | < 512MB for 1000-page wiki |

## 10. Future Extensions (out of scope for v1)

- LLM enrichment via Ollama (auto-summaries, entity extraction)
- MCP server for AI agent integration
- Watch mode (auto-rebuild on file changes)
- Obsidian vault overlay
- Git integration (show file history, blame info)
- Multi-project support (multiple codebases in one wiki)
- PDF image extraction
- API documentation generation (from javadoc/jsdoc)
