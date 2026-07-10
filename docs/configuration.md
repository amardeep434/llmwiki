# Configuration Reference

LLMWiki is configured via `llmwiki.json`, created automatically by `llmwiki init`. This document covers every field.

---

## Full Default Configuration

```json
{
  "project": {
    "name": "my-project",
    "description": ""
  },
  "sources": [
    {
      "path": "/absolute/path/to/source",
      "type": "auto",
      "exclude": [
        "node_modules", ".git", "build", "dist", "__pycache__",
        "*.min.js", "*.min.css", "*.map", "*.lock", ".venv", "venv",
        "*.pyc", "*.class", "*.o", "*.so", "*.dll",
        "*.jpg", "*.png", "*.gif", "*.ico", "*.svg",
        "*.zip", "*.tar", "*.gz", "*.jar", "*.war",
        ".DS_Store", "Thumbs.db"
      ]
    }
  ],
  "pdf_sources": [],
  "build": {
    "out_dir": "site",
    "incremental": true,
    "search_mode": "auto"
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
    "node_modules", ".git", "build", "dist", "__pycache__"
  ]
}
```

---

## Field Reference

### `project`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | *(directory name)* | Project name displayed on the dashboard and in exports |
| `description` | string | `""` | Short project description for `llms.txt` header |

### `sources`

Array of source directories to ingest. Each entry:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | string | *(required)* | Absolute or relative path to the source directory |
| `type` | string | `"auto"` | Adapter selection: `"auto"` runs all matching adapters, or specify one (e.g., `"source-code"`, `"xml"`) |
| `exclude` | string[] | *(see defaults)* | Patterns to exclude from this source |

**Exclusion patterns** support two formats:
- **Glob patterns** (`*.min.js`, `*.pyc`): matched against filenames
- **Directory names** (`node_modules`, `.git`): matched against path components

### `pdf_sources`

Array of PDF files or directories to ingest:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | string | *(required)* | Path to a `.pdf` file or a directory containing PDFs |
| `label` | string | `"docs"` | Category name for the resulting wiki pages |

**Example:**

```json
{
  "pdf_sources": [
    { "path": "/home/user/manuals/admin-guide.pdf", "label": "admin" },
    { "path": "/home/user/specs/", "label": "specifications" }
  ]
}
```

### `build`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `out_dir` | string | `"site"` | Output directory name for the generated site |
| `incremental` | boolean | `true` | Enable incremental builds (skip unchanged files) |
| `search_mode` | string | `"auto"` | Search index mode: `"auto"`, `"fts5"`, or `"json"` |

### `serve`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `port` | integer | `8765` | HTTP server port |
| `host` | string | `"127.0.0.1"` | Bind address (`"0.0.0.0"` for network access) |

### `cross_references`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable cross-reference extraction and graph building |
| `importance_iterations` | integer | `20` | Number of PageRank iterations |
| `cluster_min_size` | integer | `3` | Minimum connected component size to form a cluster |

### `exclude_global`

| Type | Default |
|------|---------|
| string[] | `["node_modules", ".git", "build", "dist", "__pycache__"]` |

Global exclusion patterns applied to all sources in addition to per-source excludes.

---

## Example Configurations

### Java Project

```json
{
  "project": { "name": "my-java-app", "description": "Enterprise Java application" },
  "sources": [
    {
      "path": "./src",
      "type": "auto",
      "exclude": ["*.class", "*.jar", "build", "target"]
    }
  ],
  "pdf_sources": [
    { "path": "./docs/specs", "label": "specifications" }
  ],
  "build": { "out_dir": "site", "incremental": true }
}
```

### Python Monorepo

```json
{
  "project": { "name": "platform", "description": "Microservices platform" },
  "sources": [
    { "path": "./services/auth", "type": "auto", "exclude": [".venv", "__pycache__"] },
    { "path": "./services/api", "type": "auto", "exclude": [".venv", "__pycache__"] },
    { "path": "./libs/common", "type": "auto", "exclude": [".venv", "__pycache__"] }
  ],
  "cross_references": { "enabled": true, "importance_iterations": 30 }
}
```

### Documentation-Only (PDFs)

```json
{
  "project": { "name": "vendor-docs" },
  "sources": [],
  "pdf_sources": [
    { "path": "/path/to/vendor/manuals", "label": "manuals" },
    { "path": "/path/to/vendor/api-docs", "label": "api" }
  ]
}
```

---

## Build State

LLMWiki tracks build state in `.llmwiki-state.json` (auto-generated, do not edit):

```json
{
  "_meta": {
    "version": "1.0.0",
    "build_number": 3,
    "last_build": "2026-07-11T10:30:00+00:00"
  },
  "files": {
    "/path/to/File.java": {
      "content_hash": "a1b2c3d4e5f6g7h8",
      "raw_path": "raw/com/example/File.md",
      "status": "current"
    }
  }
}
```

This enables incremental ingestion: files are hashed with SHA-256, and only new or modified files are re-processed.

---

## Config File Location

By default, commands look for `llmwiki.json` in the current directory. Override with `--config`:

```bash
llmwiki ingest --config /path/to/llmwiki.json
llmwiki build --config /path/to/llmwiki.json
llmwiki all --config /path/to/llmwiki.json
```
