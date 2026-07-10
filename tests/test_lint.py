"""Tests for lint rules."""

from pathlib import Path
from llmwiki.lint import lint_wiki


class TestLint:
    def test_detect_orphans(self, tmp_path):
        graph = {"nodes": [
            {"id": "a", "title": "A", "in_degree": 0, "out_degree": 0},
            {"id": "b", "title": "B", "in_degree": 1, "out_degree": 1},
        ], "edges": []}
        issues = lint_wiki(tmp_path, graph)
        orphan_issues = [i for i in issues if i["rule"] == "orphan"]
        assert len(orphan_issues) == 1
        assert orphan_issues[0]["page"] == "a"
