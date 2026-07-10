"""Tests for cross-reference extraction."""

from llmwiki.crossref import extract_refs_from_body, build_edge_list


class TestCrossRef:
    def test_extract_wikilinks(self):
        body = "This references [[CommonOperations]] and [[Global]]."
        refs = extract_refs_from_body(body)
        assert "CommonOperations" in refs
        assert "Global" in refs

    def test_extract_java_imports(self):
        body = "```java\nimport com.vf.core.utility.AccountUtil;\n```"
        refs = extract_refs_from_body(body)
        assert "com.vf.core.utility.AccountUtil" in refs

    def test_extract_no_refs(self):
        body = "Just plain text with no references."
        refs = extract_refs_from_body(body)
        assert refs == []

    def test_build_edge_list(self):
        pages = {
            "a": {"references": ["b", "c"]},
            "b": {"references": ["c"]},
            "c": {"references": []},
        }
        edges = build_edge_list(pages)
        assert ("a", "b", "references") in edges
        assert ("a", "c", "references") in edges
        assert ("b", "c", "references") in edges
        assert len(edges) == 3
