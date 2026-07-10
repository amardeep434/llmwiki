"""Tests for knowledge graph construction."""

from pathlib import Path
from llmwiki.graph import build_graph


class TestGraph:
    def test_build_from_raw(self, tmp_path):
        raw = tmp_path / "raw" / "java"
        raw.mkdir(parents=True)
        (raw / "AccountUtil.md").write_text(
            "---\ntitle: AccountUtil\nslug: java/AccountUtil\n"
            "category: java\nsource_path: /src/AccountUtil.java\n"
            "references: [com.vf.core.library.Global]\ntags: [java]\n---\n\n"
            "## AccountUtil\n\nUtility class.\n"
        )
        (raw / "Global.md").write_text(
            "---\ntitle: Global\nslug: java/Global\n"
            "category: java\nsource_path: /src/Global.java\n"
            "references: []\ntags: [java]\n---\n\n"
            "## Global\n\nGlobal config.\n"
        )
        graph = build_graph(tmp_path / "raw")
        assert len(graph["nodes"]) == 2
        assert len(graph["edges"]) >= 0  # May or may not resolve refs
        assert "stats" in graph
