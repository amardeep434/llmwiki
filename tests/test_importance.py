"""Tests for PageRank-style importance scoring."""

from llmwiki.importance import compute_importance


class TestImportance:
    def test_single_node(self):
        nodes = {"a"}
        edges = []
        scores = compute_importance(nodes, edges)
        assert "a" in scores
        assert 0.0 <= scores["a"] <= 1.0

    def test_hub_gets_high_score(self):
        nodes = {"hub", "a", "b", "c"}
        edges = [
            ("a", "hub", "references"),
            ("b", "hub", "references"),
            ("c", "hub", "references"),
        ]
        scores = compute_importance(nodes, edges)
        assert scores["hub"] > scores["a"]
        assert scores["hub"] > scores["b"]

    def test_isolated_nodes_equal(self):
        nodes = {"a", "b", "c"}
        edges = []
        scores = compute_importance(nodes, edges)
        assert abs(scores["a"] - scores["b"]) < 0.01

    def test_scores_normalized(self):
        nodes = {"a", "b", "c", "d"}
        edges = [("a", "b", "r"), ("b", "c", "r"), ("c", "d", "r"), ("d", "a", "r")]
        scores = compute_importance(nodes, edges)
        assert all(0.0 <= s <= 1.0 for s in scores.values())
