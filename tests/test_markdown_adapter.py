"""Tests for markdown pass-through adapter."""

from pathlib import Path
from llmwiki.adapters.markdown_adapter import MarkdownAdapter


class TestMarkdownAdapter:
    def setup_method(self):
        self.adapter = MarkdownAdapter()

    def test_can_handle(self, tmp_path):
        f = tmp_path / "README.md"
        f.write_text("# Hello")
        assert self.adapter.can_handle(f)

    def test_extract_with_frontmatter(self, tmp_path):
        f = tmp_path / "guide.md"
        f.write_text("---\ntitle: My Guide\ntags: [a, b]\n---\n\n# Guide\n\nContent.")
        pages = self.adapter.extract(f, {})
        assert len(pages) == 1
        assert pages[0].title == "My Guide"

    def test_extract_without_frontmatter(self, tmp_path):
        f = tmp_path / "notes.md"
        f.write_text("# My Notes\n\nSome notes here.")
        pages = self.adapter.extract(f, {})
        assert len(pages) == 1
        assert pages[0].title == "My Notes"

    def test_extract_title_from_filename(self, tmp_path):
        f = tmp_path / "api-reference.md"
        f.write_text("No heading here, just text.")
        pages = self.adapter.extract(f, {})
        assert pages[0].title == "api-reference"
