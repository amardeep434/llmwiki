"""Tests for the static site builder."""

from pathlib import Path
from llmwiki.build import build_site


class TestBuild:
    def _setup_raw(self, tmp_path):
        """Create minimal raw/ with two pages."""
        raw = tmp_path / "raw" / "java"
        raw.mkdir(parents=True)
        (raw / "Main.md").write_text(
            "---\ntitle: Main\nslug: java/main\ncategory: java\n"
            "source_path: /src/Main.java\nlanguage: java\n"
            "content_hash: abc123\ntags: [java]\nreferences: []\n---\n\n"
            "## Main\n\nMain entry point.\n"
        )
        (raw / "Utils.md").write_text(
            "---\ntitle: Utils\nslug: java/utils\ncategory: java\n"
            "source_path: /src/Utils.java\nlanguage: java\n"
            "content_hash: def456\ntags: [java, util]\nreferences: [java/main]\n---\n\n"
            "## Utils\n\nUtility class.\n"
        )
        return tmp_path

    def test_build_creates_site(self, tmp_path):
        root = self._setup_raw(tmp_path)
        (root / "wiki").mkdir()
        (root / "site").mkdir()
        config = {"build": {"out_dir": "site"}, "cross_references": {"enabled": True}}
        result = build_site(root, config, full=True)
        assert result["total_pages"] >= 2
        assert (root / "site" / "index.html").exists()
        assert (root / "site" / "style.css").exists()

    def test_build_creates_search_index(self, tmp_path):
        root = self._setup_raw(tmp_path)
        (root / "wiki").mkdir()
        (root / "site").mkdir()
        config = {"build": {"out_dir": "site"}, "cross_references": {"enabled": True}}
        build_site(root, config, full=True)
        assert (root / "site" / "search-index.json").exists()

    def test_build_creates_category_pages(self, tmp_path):
        root = self._setup_raw(tmp_path)
        (root / "wiki").mkdir()
        (root / "site").mkdir()
        config = {"build": {"out_dir": "site"}, "cross_references": {"enabled": True}}
        build_site(root, config, full=True)
        cat_files = list((root / "site").rglob("*.html"))
        assert len(cat_files) >= 2
