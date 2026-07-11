# AI Integration

LLMWiki generates several file formats specifically designed for consumption by LLMs, AI agents, and automated tools. This guide covers each export format and provides a SQL query cookbook for working with the SQLite database.

---

## Generated Files

| File | Format | Size | Purpose |
|------|--------|------|---------|
| `llms.txt` | Plain text | Small | Page index following the [llmstxt.org](https://llmstxt.org) specification |
| `llms-full.txt` | Plain text | ≤5 MB | Flattened text dump of all page content |
| `graph.jsonld` | JSON-LD | Medium | Knowledge graph in Schema.org format |
| `sitemap.xml` | XML | Small | Standard sitemap for web crawlers |
| `llmwiki.db` | SQLite | Variable | Full-text search database with FTS5 |
| `search-index.json` | JSON | Medium | Client-side search index |
| `cross-references.json` | JSON | Medium | Full knowledge graph (nodes, edges, clusters) |
| `build-history.json` | JSON | Small | Build log copied into `site/` for the changelog view |
| `*.json` | JSON | Small | Per-page metadata alongside each `.html` file |

---

## llms.txt

Follows the [llmstxt.org](https://llmstxt.org) specification — a simple text index that LLMs can read to understand what's in the knowledge base:

```
# My Project

> Knowledge base with 127 pages

## Config

- [db-config](/categories/config/db-config.html)
- [app-settings](/categories/config/app-settings.html)

## Java

- [DatabaseUtil](/categories/utility/DatabaseUtil.html)
- [AccountUtil](/categories/utility/AccountUtil.html)
```

**Use case:** Feed to an LLM as context when asking questions about your codebase.

---

## llms-full.txt

A flattened text dump of page content. Each page body is truncated to 2,000 characters, and the final file stops at 5 MB:

```
============================================================
DatabaseUtil
============================================================
## Overview

Manages database connections and query execution.

## Methods

- `getConnection()`
- `executeQuery()`
...
```

**Use case:** Load the entire knowledge base into an LLM's context window for comprehensive Q&A.

---

## graph.jsonld

Knowledge graph in JSON-LD (Schema.org) format:

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "CreativeWork",
      "@id": "utility/DatabaseUtil",
      "name": "DatabaseUtil",
      "description": "Manages database connections...",
      "keywords": ["java", "utility"],
      "isPartOf": "utility"
    }
  ]
}
```

**Use case:** Structured knowledge graph for RAG pipelines, semantic search, or graph databases.

---

## Per-Page JSON Files

Every HTML page has a `.json` sibling in the same directory:

```json
{
  "id": "utility/DatabaseUtil",
  "title": "DatabaseUtil",
  "category": "utility",
  "tags": ["java"],
  "importance": 0.8432,
  "body_text": "## Overview\n\nManages database connections...",
  "references": ["com.example.ConnectionPool", "com.example.QueryBuilder"]
}
```

**Use case:** API-like access to individual page metadata without parsing HTML.

---

## SQLite FTS5 Database

The `llmwiki.db` file is a SQLite database with full-text search capabilities. It's the most powerful integration point for AI agents.

### Schema

**`pages`** — core page metadata:

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | Page slug |
| `title` | TEXT | Page title |
| `category` | TEXT | Category name |
| `source_path` | TEXT | Original file path |
| `body_md` | TEXT | Markdown body |
| `body_plain` | TEXT | Plain text body (for FTS) |
| `content_hash` | TEXT | SHA-256 content hash |
| `tags` | TEXT | JSON array of tags |
| `references_out` | TEXT | JSON array of outbound refs |
| `references_in` | TEXT | JSON array of inbound refs |
| `importance_score` | REAL | PageRank score (0.0–1.0) |
| `cluster_id` | TEXT | Topic cluster identifier |
| `language` | TEXT | Programming language |
| `metadata` | TEXT | JSON metadata |

**`pages_fts`** — FTS5 virtual table (title, body_plain, tags, category)

In the standard build flow, the populated `pages` columns are `id`, `title`, `category`, `body_plain`, `tags`, and `importance_score`. The remaining columns are schema placeholders for future enrichments.

**`edges`** — cross-reference edges:

| Column | Type | Description |
|--------|------|-------------|
| `from_id` | TEXT | Source page ID |
| `to_id` | TEXT | Target page ID |
| `edge_type` | TEXT | Reference type (e.g., `"references"`) |

This table is created in the SQLite schema, but the standard build currently writes graph relationships to `site/cross-references.json` instead of populating `edges`.

**`clusters`** — detected topic clusters:

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | Cluster identifier |
| `label` | TEXT | Human-readable label |
| `member_count` | INTEGER | Number of pages |
| `top_tags` | TEXT | Most common tags |

This table is also created but not populated by the standard build; cluster data currently lives in `site/cross-references.json`.

**`build_history`** — build audit trail:

| Column | Type | Description |
|--------|------|-------------|
| `build_number` | INTEGER (PK) | Sequential build number |
| `timestamp` | TEXT | ISO 8601 timestamp |
| `type` | TEXT | Build type (incremental/full) |
| `duration_seconds` | REAL | Build duration |

The SQLite table exists, but the current build writes history to `build-history.json` rather than inserting rows here.

---

## SQL Query Cookbook

### 1. Full-text search

```sql
SELECT p.id, p.title, p.category,
       snippet(pages_fts, 1, '>>>', '<<<', '...', 50) AS snippet
FROM pages_fts
JOIN pages p ON pages_fts.rowid = p.rowid
WHERE pages_fts MATCH 'database connection'
ORDER BY rank
LIMIT 10;
```

### 2. Find the most important pages

```sql
SELECT id, title, category, importance_score
FROM pages
ORDER BY importance_score DESC
LIMIT 20;
```

### 3. Find pages by category

```sql
SELECT id, title, importance_score
FROM pages
WHERE category = 'utility'
ORDER BY importance_score DESC;
```

### 4. Find pages with extracted methods/functions

```sql
SELECT id, title, category, tags
FROM pages
WHERE tags LIKE '%method:%'
ORDER BY importance_score DESC
LIMIT 20;
```

### 5. Count pages per category

```sql
SELECT category, COUNT(*) AS page_count
FROM pages
GROUP BY category
ORDER BY page_count DESC;
```

### 6. Find pages by tag

```sql
SELECT id, title, category
FROM pages
WHERE tags LIKE '%"java"%'
ORDER BY importance_score DESC;
```

### 7. Search page bodies without FTS operators

```sql
SELECT id, title, category
FROM pages
WHERE lower(body_plain) LIKE '%authentication%'
ORDER BY importance_score DESC;
```

### 8. Find the longest extracted pages

```sql
SELECT id, title, category, length(body_plain) AS chars
FROM pages
ORDER BY chars DESC
LIMIT 20;
```

### 9. Top pages within a category

```sql
SELECT id, title, importance_score
FROM pages
WHERE category = 'utility'
ORDER BY importance_score DESC
LIMIT 10;
```

### 10. Search within a specific category

```sql
SELECT p.id, p.title,
       snippet(pages_fts, 1, '>>>', '<<<', '...', 50) AS snippet
FROM pages_fts
JOIN pages p ON pages_fts.rowid = p.rowid
WHERE pages_fts MATCH 'authentication'
  AND p.category = 'security'
ORDER BY rank
LIMIT 10;
```

### 11. Find pages missing extracted tags

```sql
SELECT id, title, category
FROM pages
WHERE tags IS NULL OR tags = '[]'
ORDER BY title;
```

### 12. Summary statistics

```sql
SELECT
    COUNT(*) AS total_pages,
    COUNT(DISTINCT category) AS total_categories,
    SUM(CASE WHEN tags LIKE '%method:%' THEN 1 ELSE 0 END) AS pages_with_method_tags,
    ROUND(AVG(importance_score), 4) AS avg_importance
FROM pages;
```

---

## Integration Patterns

### RAG Pipeline

1. Agent receives a user question
2. Query `pages_fts` with extracted keywords
3. Retrieve top-N page bodies from `pages.body_plain`
4. Feed as context to the LLM

### Code Navigation Agent

1. User asks "how does X work?"
2. Search `pages_fts` for X
3. Follow related entries in per-page `.json` files or `cross-references.json`
4. Use `importance_score` to prioritize which pages to include in context

### Documentation Audit

1. Query for pages with low `importance_score`
2. Find pages missing extracted tags or very short `body_plain` content
3. Cross-check with `cross-references.json` if you need graph-level orphan analysis
