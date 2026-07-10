"""Tests for topic cluster detection."""

from llmwiki.clusters import detect_clusters


class TestClusters:
    def test_single_cluster(self):
        edges = [("a", "b", "r"), ("b", "c", "r"), ("c", "a", "r")]
        page_meta = {
            "a": {"category": "workflow", "tags": ["approval"]},
            "b": {"category": "workflow", "tags": ["approval"]},
            "c": {"category": "rule", "tags": ["approval"]},
        }
        clusters = detect_clusters(edges, page_meta, min_size=2)
        assert len(clusters) >= 1
        assert len(clusters[0]["members"]) == 3

    def test_no_clusters_when_disconnected(self):
        edges = []
        page_meta = {"a": {}, "b": {}, "c": {}}
        clusters = detect_clusters(edges, page_meta, min_size=3)
        assert len(clusters) == 0

    def test_two_clusters(self):
        edges = [
            ("a", "b", "r"), ("b", "a", "r"),
            ("c", "d", "r"), ("d", "c", "r"),
        ]
        page_meta = {
            "a": {"tags": ["x"]}, "b": {"tags": ["x"]},
            "c": {"tags": ["y"]}, "d": {"tags": ["y"]},
        }
        clusters = detect_clusters(edges, page_meta, min_size=2)
        assert len(clusters) == 2
