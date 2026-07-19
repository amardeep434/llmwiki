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
    "theme": "emerald-dark"
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
  "agent_assist": false,
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

Array of source directories to ingest. `llmwiki init` creates one entry pointing at the `--source` path. You can add more to include additional codebases, documentation directories, or separate repos.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | string | *(required)* | Absolute or relative path to the source directory |
| `type` | string | `"auto"` | Documented adapter selector, but per-source type filtering is not currently implemented in the ingest pipeline |
| `exclude` | string[] | *(see defaults)* | Patterns to exclude from this source |

**Multi-source example:**

```json
{
  "sources": [
    {
      "path": "/home/user/projects/my-app/src",
      "type": "auto",
      "exclude": ["node_modules", ".git", "*.min.js"]
    },
    {
      "path": "/home/user/projects/my-app/docs",
      "type": "auto",
      "exclude": [".git"]
    },
    {
      "path": "/home/user/projects/shared-libs",
      "type": "auto",
      "exclude": ["node_modules", ".git", "test"]
    }
  ]
}
```

Each source directory is scanned by all adapters (source-code, XML, markdown, config). Pages from different sources are merged into the same wiki with cross-references between them.

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
| `incremental` | boolean | `true` | Controls incremental ingestion state; current `build` always regenerates `wiki/` and `site/` from `raw/` |
| `theme` | string | `"emerald-dark"` | UI theme name. Built-in: `emerald-dark`, `vodafone`. Run `llmwiki themes` to list all. |

**Theme override via CLI:**

```bash
llmwiki build --theme vodafone
```

The `--theme` flag overrides the config value for that build.

### `serve`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `port` | integer | `8765` | Documented default, but `llmwiki serve` currently reads this only from the CLI flag |
| `host` | string | `"127.0.0.1"` | Documented default, but `llmwiki serve` currently reads this only from the CLI flag (`"0.0.0.0"` for network access) |

### `cross_references`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable cross-reference extraction and graph building |
| `importance_iterations` | integer | `20` | Documented setting, but PageRank iterations are currently hardcoded to 20 |
| `cluster_min_size` | integer | `3` | Documented setting, but cluster detection currently uses a hardcoded minimum size of 3 |
| `custom_patterns` | string[] | `[]` | Extra regex patterns for domain-specific references (product APIs, connector names). First capture group (or whole match) becomes a reference. Built-in extraction is deliberately generic — put domain vocabulary here, e.g. `"\\b(sailpoint\\.\\w+\\.\\w+)\\b"` |

Per-source option: set `"extract_beanshell": true` on an XML source entry to extract inline BeanShell scripts into their own pages (SailPoint IIQ idiom; off by default so generic XML stays clean).

### `agent_assist`

| Type | Default | Description |
|------|---------|-------------|
| boolean | `false` | Enable wiki-first agent behavior for IDE integration |

When set to `true`, generated agent instructions ask agents to search the wiki before reading raw files. Enable with `llmwiki agent --enable`. Run `llmwiki benchmark` to measure actual savings.

### `exclude_global`

| Type | Default |
|------|---------|
| string[] | `["node_modules", ".git", "build", "dist", "__pycache__"]` |

Global exclusion patterns applied to all sources in addition to per-source excludes.

### `security`

Controls the two secret-protection layers. Both are on by default; you rarely
need to configure this block.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `allow_sensitive_files` | boolean | `false` | Opt out of the sensitive-file exclusion floor. When `false` (default), files that routinely hold secrets are refused at load time regardless of your `exclude` lists. |
| `redact` | boolean | `true` | Scrub high-confidence secrets (AWS/Google keys, private keys, JWTs, URL credentials, `password=`/`token=` assignments) from every page body at ingest, before anything is written to `raw/`, the DB, the search index, or exports. |
| `redact_patterns` | string[] | `[]` | Extra redaction regexes (redacted as kind `custom`). Invalid patterns are skipped with a logged warning. |

**Sensitive-file floor.** These patterns are always merged into every source's
`exclude` and into `exclude_global` at load time (so even frozen/legacy configs
are protected without migration), unless `allow_sensitive_files` is `true`:

```
.env, .env.*, *.pem, *.key, *.p12, *.pfx, *.jks, *.keystore,
id_rsa*, id_ed25519*, id_dsa*, .netrc, .npmrc, .pypirc,
*credentials*, *secret*, *.tfstate, .ssh, .aws, .gnupg
```

```json
{
  "security": {
    "allow_sensitive_files": false,
    "redact": true,
    "redact_patterns": ["INTERNAL-[A-Z0-9]{12}"]
  }
}
```

The `llmwiki lint` `secret-suspect` rule also flags any secret still present in
pages built before redaction existed, and `llms-full.txt` is re-scrubbed at
export time as a final safety net.

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
  "cross_references": { "enabled": true, "importance_iterations": 20, "cluster_min_size": 3 }
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
