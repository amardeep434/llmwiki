"""PageRank-style importance scoring for wiki pages."""

from __future__ import annotations

from collections import defaultdict


def compute_importance(
    nodes: set[str],
    edges: list[tuple[str, str, str]],
    iterations: int = 20,
    damping: float = 0.85,
) -> dict[str, float]:
    """Compute importance scores using simplified PageRank.

    Args:
        nodes: Set of page IDs.
        edges: List of (from_id, to_id, edge_type) tuples.
        iterations: Number of iterations.
        damping: Damping factor (0.85 is standard).

    Returns:
        {page_id: score} with scores normalized to 0.0-1.0.
    """
    if not nodes:
        return {}

    n = len(nodes)
    scores = {node: 1.0 / n for node in nodes}

    # Build adjacency
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for from_id, to_id, _ in edges:
        if from_id in nodes and to_id in nodes:
            outgoing[from_id].append(to_id)
            incoming[to_id].append(from_id)

    base = (1.0 - damping) / n

    for _ in range(iterations):
        new_scores = {}
        for node in nodes:
            rank_sum = 0.0
            for src in incoming.get(node, []):
                out_count = len(outgoing.get(src, []))
                if out_count > 0:
                    rank_sum += scores[src] / out_count
            new_scores[node] = base + damping * rank_sum
        scores = new_scores

    # Normalize to 0.0-1.0
    max_score = max(scores.values()) if scores else 1.0
    if max_score > 0:
        scores = {k: v / max_score for k, v in scores.items()}

    return scores
