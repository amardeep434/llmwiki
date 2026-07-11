# Cross-References

LLMWiki's cross-reference engine builds a directed knowledge graph from page content, computes importance scores via PageRank, and detects topic clusters. This document explains the internals.

---

## Overview

```
Page Bodies            Edge List           Importance      Clusters
┌──────────┐     ┌──────────────────┐   ┌────────────┐   ┌──────────┐
│ imports   │     │ A → B (ref)      │   │ A: 0.42    │   │ Cluster 1│
│ wikilinks ├────►│ A → C (ref)      ├──►│ B: 0.87    ├──►│ {A,B,C}  │
│ class refs│     │ D → B (ref)      │   │ C: 0.15    │   │ Cluster 2│
└──────────┘     └──────────────────┘   │ D: 0.31    │   │ {D,E,F}  │
                                        └────────────┘   └──────────┘
```

The process runs in three stages:
1. **Edge extraction** — parse references from page bodies and frontmatter
2. **Importance scoring** — compute PageRank over the directed graph
3. **Cluster detection** — find connected components in the undirected projection

---

## Edge Extraction

### Source 1: Frontmatter References

Each page's YAML frontmatter includes a `references` field populated by adapters during ingestion:

```yaml
references: [com.example.DatabaseUtil, com.example.BaseClass]
```

These are direct cross-references detected by the adapter (e.g., Java `import` statements).

### Source 2: Body Text Parsing

The `crossref.py` module scans page bodies with five regex patterns:

| Pattern | Regex | Example Match |
|---------|-------|---------------|
| Wiki links | `\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]` | `[[DatabaseUtil]]` or `[[DatabaseUtil\|DB Utils]]` |
| Java imports | `import\s+([\w.]+);` | `import com.example.Util;` |
| Class references | `(?:new\s+\|extends\s+\|implements\s+)([\w.]+)` | `extends BaseAdapter` |
| SailPoint API | `\b(sailpoint\.\w+\.\w+)\b` | `sailpoint.api.SailPointContext` |
| Connector names | `\b(Active Directory\|LDAP\|...\|SOAP)\b` | `Active Directory` |

**Filtering:** Java standard library references are automatically excluded:
- `java.*`
- `javax.*`
- `org.w3c.*`
- `org.xml.*`

### Source 3: Title-Mention Matching

The `graph.py` module performs a second pass over all pages, scanning each page body for substring mentions of other pages' titles. This produces `"mentions"` type edges.

**Algorithm:**
1. Build a `title → page_id` index (only titles ≥6 chars, excluding generic words like "source", "config", "method", etc.)
2. For each page, scan its body (lowercased) for all known titles
3. If a title appears as a substring, add a `(page_id, target_id, "mentions")` edge
4. Cap at 20 mention-edges per page to prevent hub explosion

**Impact:** Title-mention matching significantly increases graph connectivity. On a typical project, this adds thousands of edges beyond what pattern-based extraction finds alone.

### Edge List Construction

All references (frontmatter + body) are merged and deduplicated per page. The result is a list of directed edges:

```
(from_page_id, to_reference, "references")
```

---

## Reference Resolution

Raw references often don't match page IDs exactly. The resolution step maps fuzzy references to actual page IDs:

### Algorithm

1. **Build an index** of all page IDs:
   - Full ID (lowercase) → page ID
   - Last path segment (lowercase) → page ID

2. **For each edge**, try to resolve the target:
   - Look up `target.lower()` in the index
   - Fall back: look up the last `.`-separated segment (e.g., `com.example.Util` → `Util`)
   - Self-references are filtered out

### Example

```
Pages: {"utility/DatabaseUtil", "utility/AccountUtil", "task/CleanupTask"}

Reference: "com.vf.core.utility.DatabaseUtil"
  → lowercase: "com.vf.core.utility.databaseutil"
  → no exact match
  → last segment: "databaseutil"
  → matches: "utility/DatabaseUtil" ✓
```

---

## PageRank Importance Scoring

After resolving edges, LLMWiki computes importance scores using a simplified PageRank algorithm.

### Parameters

| Parameter | Value | Configurable |
|-----------|-------|-------------- |
| Iterations | 20 | No (currently hardcoded) |
| Damping factor | 0.85 | No (standard value) |
| Normalization | 0.0–1.0 | Automatic |

### Algorithm

```
Initialize: score[node] = 1/N for all nodes

For each iteration:
    For each node:
        rank_sum = Σ (score[source] / out_degree[source])
                   for each source linking to node
        score[node] = (1 - damping) / N + damping × rank_sum

Normalize: divide all scores by max(scores)
```

### Interpretation

| Score Range | Meaning |
|-------------|---------|
| 0.8 – 1.0 | Hub page — many pages depend on it |
| 0.4 – 0.8 | Important page — moderate connectivity |
| 0.1 – 0.4 | Regular page — some connections |
| 0.0 – 0.1 | Peripheral page — few or no connections |

### Example Output

```
utility/DatabaseUtil     → 1.0000  (most connected)
utility/AccountUtil      → 0.7823
utility/CommonOperations → 0.6541
task/CleanupTask         → 0.2103
docs/readme              → 0.0412  (orphan or leaf)
```

---

## Cluster Detection

Clusters group related pages based on connectivity, independent of explicit categories.

### Algorithm

1. **Project to undirected graph**: for every directed edge A→B, add undirected edges A↔B
2. **BFS connected components**: standard breadth-first search to find connected components
3. **Filter by size**: only components with ≥3 members become clusters (currently hardcoded)
4. **Label clusters**: the top 3 most common tags across cluster members form the label

### Output Format

```json
{
  "id": "cluster-1",
  "label": "java / utility / database",
  "members": ["utility/DatabaseUtil", "utility/AccountUtil", "utility/CommonOps"],
  "member_count": 3,
  "top_tags": ["java", "utility", "database"]
}
```

### How Clusters Differ from Categories

| Aspect | Categories | Clusters |
|--------|-----------|----------|
| Source | Adapter-assigned (package path, directory) | Computed from cross-references |
| Granularity | One per page | Pages can span categories |
| Purpose | File organization | Conceptual grouping |
| Stability | Stable (tied to file paths) | Changes as references evolve |

---

## Graph Data in the Site

### cross-references.json

The full graph is saved to `site/cross-references.json`:

```json
{
  "nodes": [
    {
      "id": "utility/DatabaseUtil",
      "title": "DatabaseUtil",
      "type": "utility",
      "tags": ["java", "method:getConnection"],
      "in_degree": 12,
      "out_degree": 5,
      "importance": 1.0,
      "cluster_id": "cluster-1"
    }
  ],
  "edges": [
    { "from": "task/CleanupTask", "to": "utility/DatabaseUtil", "type": "references" }
  ],
  "clusters": [...],
  "stats": {
    "total_pages": 127,
    "total_edges": 342,
    "total_clusters": 8,
    "orphans": 15
  }
}
```

### SQLite Tables

The SQLite schema includes `edges` and `clusters` tables, but the standard build currently writes graph data only to `site/cross-references.json`. See [AI Integration](ai-integration.md) for the SQL queries that match the populated database tables.

---

## Tuning

### More accurate importance scores

`cross_references.importance_iterations` is currently documented but not wired into the graph builder. PageRank runs for 20 iterations today.

If you change the implementation, this is the shape of the config you would eventually expose:

```json
{ "cross_references": { "importance_iterations": 50 } }
```

Scores typically converge within 20–30 iterations for graphs under 1,000 nodes, but the shipped build uses the hardcoded value above.

### Larger or smaller clusters

`cross_references.cluster_min_size` is also currently hardcoded to 3. If that setting is wired up later, the config would look like:

```json
{ "cross_references": { "cluster_min_size": 5 } }
```

A higher value would produce fewer, larger clusters. A value of `2` would capture even small pairwise connections.

### Disable cross-references

For documentation-only projects where cross-references aren't meaningful:

```json
{ "cross_references": { "enabled": false } }
```
