"""Topic cluster detection via connected components."""

from __future__ import annotations

from collections import defaultdict, Counter


def detect_clusters(
    edges: list[tuple[str, str, str]],
    page_meta: dict[str, dict],
    min_size: int = 3,
) -> list[dict]:
    """Detect topic clusters as connected components.

    Args:
        edges: Directed edges (from, to, type).
        page_meta: {page_id: {"category": ..., "tags": [...]}}.
        min_size: Minimum component size to count as a cluster.

    Returns:
        List of cluster dicts with id, label, members, top_tags.
    """
    # Build undirected adjacency
    adj: dict[str, set[str]] = defaultdict(set)
    for from_id, to_id, _ in edges:
        adj[from_id].add(to_id)
        adj[to_id].add(from_id)

    # Find connected components via BFS
    visited: set[str] = set()
    components: list[set[str]] = []
    all_nodes = set(adj.keys()) | set(page_meta.keys())

    for node in all_nodes:
        if node in visited:
            continue
        component: set[str] = set()
        queue = [node]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            component.add(current)
            for neighbor in adj.get(current, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
        if len(component) >= min_size:
            components.append(component)

    # Label clusters
    clusters = []
    for i, members in enumerate(sorted(components, key=len, reverse=True)):
        tag_counts: Counter[str] = Counter()
        cat_counts: Counter[str] = Counter()
        for m in members:
            meta = page_meta.get(m, {})
            for t in meta.get("tags", []):
                tag_counts[t] += 1
            cat = meta.get("category", "")
            if cat:
                cat_counts[cat] += 1

        top_tags = [t for t, _ in tag_counts.most_common(3)]
        label = " / ".join(top_tags) if top_tags else f"Cluster {i + 1}"

        clusters.append({
            "id": f"cluster-{i + 1}",
            "label": label,
            "members": sorted(members),
            "member_count": len(members),
            "top_tags": top_tags,
        })

    return clusters
