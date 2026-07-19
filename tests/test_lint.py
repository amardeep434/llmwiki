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

    def test_secret_suspect_flags_jwt(self, tmp_path):
        """A raw page carrying a JWT yields a secret-suspect error.

        Guards wikis built before redaction existed — the page file itself
        still holds the secret and lint must surface it.
        """
        raw_dir = tmp_path / "raw" / "misc"
        raw_dir.mkdir(parents=True)
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w"
        (raw_dir / "leaky.md").write_text(f"# Leaky\n\nAuthorization: Bearer {jwt}\n")

        issues = lint_wiki(tmp_path / "raw", {"nodes": []})
        secret_issues = [i for i in issues if i["rule"] == "secret-suspect"]
        assert len(secret_issues) >= 1
        assert all(i["severity"] == "error" for i in secret_issues)
        assert any("jwt" in i["message"] for i in secret_issues)

    def test_no_secret_suspect_for_clean_pages(self, tmp_path):
        raw_dir = tmp_path / "raw" / "misc"
        raw_dir.mkdir(parents=True)
        (raw_dir / "clean.md").write_text("# Clean\n\nOrdinary documentation.\n")
        issues = lint_wiki(tmp_path / "raw", {"nodes": []})
        assert not [i for i in issues if i["rule"] == "secret-suspect"]
