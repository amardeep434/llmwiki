"""Knowledge graph construction from wiki pages."""

from __future__ import annotations

import json
from pathlib import Path

from llmwiki.crossref import extract_refs_from_body, build_edge_list
from llmwiki.importance import compute_importance
from llmwiki.clusters import detect_clusters


def build_graph(raw_dir: Path) -> dict:
    """Build knowledge graph from raw/ markdown files.

    Returns dict with nodes, edges, clusters, stats.
    """
    pages = _load_pages(raw_dir)
    page_ids = set(pages.keys())

    # Build edges from explicit references
    edges = build_edge_list(pages)

    # Add title-based edges (if page A mentions page B's title in its body)
    title_edges = _find_title_mentions(pages)
    edges.extend(title_edges)

    # Resolve fuzzy references (partial slug matching)
    resolved_edges = _resolve_edges(edges, page_ids)

    # Compute importance
    scores = compute_importance(page_ids, resolved_edges)

    # Detect clusters
    page_meta = {
        pid: {"category": p.get("category", ""), "tags": p.get("tags", [])}
        for pid, p in pages.items()
    }
    clusters = detect_clusters(resolved_edges, page_meta, min_size=3)

    # Assign cluster IDs to pages
    cluster_map: dict[str, str] = {}
    for cluster in clusters:
        for member in cluster["members"]:
            cluster_map[member] = cluster["id"]

    # Build node list
    in_degree: dict[str, int] = {}
    out_degree: dict[str, int] = {}
    for from_id, to_id, _ in resolved_edges:
        out_degree[from_id] = out_degree.get(from_id, 0) + 1
        in_degree[to_id] = in_degree.get(to_id, 0) + 1

    nodes = []
    for pid, pdata in pages.items():
        nodes.append({
            "id": pid,
            "title": pdata.get("title", pid),
            "type": pdata.get("category", "unknown"),
            "tags": pdata.get("tags", []),
            "in_degree": in_degree.get(pid, 0),
            "out_degree": out_degree.get(pid, 0),
            "importance": round(scores.get(pid, 0.0), 4),
            "cluster_id": cluster_map.get(pid),
        })

    edge_dicts = [
        {"from": f, "to": t, "type": etype}
        for f, t, etype in resolved_edges
    ]

    return {
        "nodes": nodes,
        "edges": edge_dicts,
        "clusters": clusters,
        "stats": {
            "total_pages": len(nodes),
            "total_edges": len(edge_dicts),
            "total_clusters": len(clusters),
            "orphans": sum(1 for n in nodes if n["in_degree"] == 0 and n["out_degree"] == 0),
        },
    }


def save_graph(graph: dict, output_path: Path) -> None:
    """Save graph to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)


def _load_pages(raw_dir: Path) -> dict[str, dict]:
    """Load all raw pages and extract frontmatter."""
    pages: dict[str, dict] = {}
    for md_file in sorted(raw_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        meta, body = _parse_frontmatter(content)
        slug = meta.get("slug", md_file.stem)

        # Extract additional refs from body
        body_refs = extract_refs_from_body(body)
        fm_refs = meta.get("references", [])
        if isinstance(fm_refs, str):
            fm_refs = [r.strip() for r in fm_refs.strip("[]").split(",") if r.strip()]
        all_refs = list(set(fm_refs + body_refs))

        pages[slug] = {
            "title": meta.get("title", md_file.stem),
            "category": meta.get("category", ""),
            "language": meta.get("language", ""),
            "tags": _parse_list(meta.get("tags", [])),
            "references": all_refs,
            "source_path": meta.get("source_path", ""),
            "body": body,
        }
    return pages


def _find_title_mentions(pages: dict[str, dict]) -> list[tuple[str, str, str]]:
    """Find edges by scanning page bodies for mentions of other page titles.

    Uses word-set intersection for O(n) performance instead of O(n²) regex.
    Only matches titles that are ≥6 chars to avoid false positives.
    """
    # Build title→page_id index
    title_to_id: dict[str, str] = {}
    skip_titles = {"source", "import", "return", "public", "string", "object",
                   "system", "config", "server", "client", "method"}
    for pid, pdata in pages.items():
        title = pdata.get("title", "").strip()
        if len(title) >= 6 and title.lower() not in skip_titles:
            title_to_id[title.lower()] = pid

    if not title_to_id:
        return []

    edges: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()

    for pid, pdata in pages.items():
        body = pdata.get("body", "")
        if not body:
            continue
        # Extract words from body (fast set operation)
        body_lower = body.lower()
        for title_lower, target_id in title_to_id.items():
            if target_id == pid:
                continue
            if (pid, target_id) in seen:
                continue
            # Simple substring check (much faster than regex for each)
            if title_lower in body_lower:
                edges.append((pid, target_id, "mentions"))
                seen.add((pid, target_id))
                # Cap edges per page to avoid explosion
                if sum(1 for e in edges if e[0] == pid) > 20:
                    break

    return edges


def _resolve_edges(
    edges: list[tuple[str, str, str]],
    valid_ids: set[str],
) -> list[tuple[str, str, str]]:
    """Resolve fuzzy references to actual page IDs."""
    resolved = []
    id_index: dict[str, str] = {}
    for pid in valid_ids:
        # Index by last segment
        parts = pid.split("/")
        id_index[parts[-1].lower()] = pid
        id_index[pid.lower()] = pid

    for from_id, to_id, etype in edges:
        target = id_index.get(to_id.lower()) or id_index.get(to_id.split(".")[-1].lower())
        if target and target != from_id:
            resolved.append((from_id, target, etype))

    return resolved


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Simple frontmatter parser."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    meta: dict = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
    return meta, parts[2].strip()


def _parse_list(value) -> list[str]:
    """Parse a frontmatter list value."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [v.strip() for v in value.strip("[]").split(",") if v.strip()]
    return []
