"""Tests for AI-consumable exports."""

import json
from pathlib import Path
from llmwiki.exporters import export_llms_txt, export_jsonld, export_sitemap, export_all


class TestExporters:
    def _make_pages(self):
        return {
            "java/main": {"title": "Main", "category": "java", "url": "/categories/java/main.html",
                          "body": "Main class.", "tags": ["java"]},
            "docs/guide": {"title": "Guide", "category": "docs", "url": "/categories/docs/guide.html",
                           "body": "A guide.", "tags": ["docs"]},
        }

    def test_llms_txt(self, tmp_path):
        pages = self._make_pages()
        output = tmp_path / "llms.txt"
        export_llms_txt(pages, output, "Test Project")
        content = output.read_text(encoding="utf-8")
        assert "Test Project" in content
        assert "Main" in content

    def test_jsonld(self, tmp_path):
        pages = self._make_pages()
        output = tmp_path / "graph.jsonld"
        export_jsonld(pages, output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert "@context" in data
        assert "@graph" in data

    def test_sitemap(self, tmp_path):
        pages = self._make_pages()
        output = tmp_path / "sitemap.xml"
        export_sitemap(pages, output, "http://localhost:8765")
        content = output.read_text(encoding="utf-8")
        assert "<urlset" in content

    def test_export_all(self, tmp_path):
        pages = self._make_pages()
        export_all(pages, tmp_path, "Test", "http://localhost:8765")
        assert (tmp_path / "llms.txt").exists()
        assert (tmp_path / "llms-full.txt").exists()
        assert (tmp_path / "graph.jsonld").exists()
        assert (tmp_path / "sitemap.xml").exists()
