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

The `crossref.py` module scans page bodies with three regex patterns:

| Pattern | Regex | Example Match |
|---------|-------|---------------|
| Wiki links | `\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]` | `[[DatabaseUtil]]` or `[[DatabaseUtil\|DB Utils]]` |
| Java imports | `^import\s+([\w.]+);` | `import com.example.Util;` |
| Class references | `(?:new\s+\|extends\s+\|implements\s+)([\w.]+)` | `extends BaseAdapter` |

**Filtering:** Java standard library references are automatically excluded:
- `java.*`
- `javax.*`
- `org.w3c.*`
- `org.xml.*`

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
| Iterations | 20 | Yes (`cross_references.importance_iterations`) |
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
3. **Filter by size**: only components with ≥ `cluster_min_size` (default: 3) members become clusters
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

The `edges` and `clusters` tables in `llmwiki.db` mirror this data for SQL queries. See [AI Integration](ai-integration.md) for query examples.

---

## Tuning

### More accurate importance scores

Increase the iteration count for large graphs:

```json
{ "cross_references": { "importance_iterations": 50 } }
```

Scores typically converge within 20–30 iterations for graphs under 1,000 nodes.

### Larger or smaller clusters

Adjust the minimum cluster size:

```json
{ "cross_references": { "cluster_min_size": 5 } }
```

A higher value produces fewer, larger clusters. A value of `2` captures even small pairwise connections.

### Disable cross-references

For documentation-only projects where cross-references aren't meaningful:

```json
{ "cross_references": { "enabled": false } }
```
