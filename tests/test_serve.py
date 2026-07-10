"""Tests for local server."""

from llmwiki.serve import serve_site


class TestServe:
    def test_missing_directory(self, tmp_path):
        ret = serve_site(str(tmp_path / "nonexistent"))
        assert ret == 2
