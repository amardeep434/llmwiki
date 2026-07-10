"""Tests for WikiPage dataclass and BaseAdapter interface."""

from pathlib import Path
from llmwiki.adapters.base import WikiPage, BaseAdapter


class TestWikiPage:
    def test_create_minimal(self):
        page = WikiPage(slug="test", title="Test", category="cat",
                        source_path="/tmp/test.py", body="# Hello")
        assert page.slug == "test"
        assert page.title == "Test"
        assert page.tags == []
        assert page.references == []

    def test_compute_hash(self):
        page = WikiPage(slug="a", title="A", category="c",
                        source_path="/x", body="content")
        h = page.compute_hash()
        assert len(h) == 16
        assert h == page.content_hash

    def test_hash_changes_with_content(self):
        p1 = WikiPage(slug="a", title="A", category="c",
                      source_path="/x", body="content1")
        p2 = WikiPage(slug="a", title="A", category="c",
                      source_path="/x", body="content2")
        assert p1.compute_hash() != p2.compute_hash()

    def test_to_frontmatter(self):
        page = WikiPage(slug="my-page", title="My Page", category="java",
                        source_path="/src/Main.java", body="# Hello",
                        language="java", tags=["util", "core"])
        page.compute_hash()
        fm = page.to_frontmatter()
        assert "---" in fm
        assert 'title: "My Page"' in fm
        assert "slug: \"my-page\"" in fm
        assert "tags: [util, core]" in fm

    def test_to_frontmatter_escapes_quotes(self):
        page = WikiPage(slug="test", title='A "quoted" title', category="cat",
                        source_path='/path/with: colon', body="body")
        page.compute_hash()
        fm = page.to_frontmatter()
        assert '\\"' in fm  # quotes escaped
        assert "---" in fm  # still valid structure

    def test_to_markdown(self):
        page = WikiPage(slug="test", title="Test", category="cat",
                        source_path="/x", body="# Body\n\nContent here.")
        md = page.to_markdown()
        assert md.startswith("---\n")
        assert "# Body" in md
        assert "Content here." in md
        assert page.content_hash != ""


class TestBaseAdapter:
    def test_cannot_instantiate_directly(self):
        try:
            BaseAdapter()
            assert False, "Should raise TypeError"
        except TypeError:
            pass

    def test_subclass_must_implement(self):
        class BadAdapter(BaseAdapter):
            name = "bad"
            extensions = [".bad"]

        try:
            BadAdapter()
            assert False, "Should raise TypeError"
        except TypeError:
            pass

    def test_concrete_subclass(self):
        class GoodAdapter(BaseAdapter):
            name = "good"
            extensions = [".good"]

            def can_handle(self, path):
                return path.suffix == ".good"

            def extract(self, path, config):
                return [WikiPage(slug="x", title="X", category="c",
                                 source_path=str(path), body="body")]

        adapter = GoodAdapter()
        assert adapter.can_handle(Path("test.good"))
        assert not adapter.can_handle(Path("test.bad"))
        pages = adapter.extract(Path("test.good"), {})
        assert len(pages) == 1

    def test_discover(self, tmp_path):
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("world")
        (tmp_path / "c.py").write_text("pass")

        class TxtAdapter(BaseAdapter):
            name = "txt"
            extensions = [".txt"]
            def can_handle(self, path): return path.suffix == ".txt"
            def extract(self, path, config): return []

        adapter = TxtAdapter()
        found = adapter.discover(tmp_path)
        assert len(found) == 2
        assert all(f.suffix == ".txt" for f in found)
