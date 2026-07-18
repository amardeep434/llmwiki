"""Tests for SQLite FTS5 search."""

import json
from pathlib import Path
from llmwiki.search import (
    create_search_db, insert_page, search_pages, cli_search,
    format_results_json, format_results_compact, format_results_context
)


class TestSearch:
    def test_create_db(self, tmp_path):
        db_path = tmp_path / "test.db"
        create_search_db(db_path)
        assert db_path.exists()

    def test_insert_and_search(self, tmp_path):
        db_path = tmp_path / "test.db"
        create_search_db(db_path)
        insert_page(db_path, {
            "id": "java/main",
            "title": "Main",
            "category": "java",
            "body_plain": "Main entry point for the application",
            "tags": '["java"]',
            "importance_score": 0.5,
        })
        results = search_pages(db_path, "entry point")
        assert len(results) >= 1
        assert results[0]["title"] == "Main"

    def test_search_no_results(self, tmp_path):
        db_path = tmp_path / "test.db"
        create_search_db(db_path)
        results = search_pages(db_path, "nonexistent query")
        assert len(results) == 0

    def test_bulk_insert(self, tmp_path):
        db_path = tmp_path / "test.db"
        create_search_db(db_path)
        pages = [
            {"id": f"page{i}", "title": f"Page {i}", "category": "test",
             "body_plain": f"Content for page {i}", "tags": "[]", "importance_score": 0.1 * i}
            for i in range(20)
        ]
        for p in pages:
            insert_page(db_path, p)
        results = search_pages(db_path, "Content")
        assert len(results) >= 10

    def test_format_results_json(self):
        results = [{"id": "test", "title": "Test", "category": "core", "importance_score": 0.5, "snippet": "hello"}]
        output = format_results_json(results)
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert parsed[0]["title"] == "Test"

    def test_format_results_compact(self):
        results = [{"id": "test", "title": "Test Page", "category": "core", "importance_score": 0.5}]
        output = format_results_compact(results)
        assert "Test Page" in output
        assert "[core]" in output
        assert len(output.split("\n")) == 1

    def test_format_results_context(self, tmp_path):
        db = tmp_path / "test.db"
        create_search_db(db)
        insert_page(db, {
            "id": "auth", "title": "Auth Module", "category": "core",
            "body_plain": "handles login and auth flows", "tags": '["auth"]',
            "importance_score": 0.8, "url": "/categories/core/auth.html"
        })
        results = [{"id": "auth", "title": "Auth Module", "category": "core", "importance_score": 0.8}]
        output = format_results_context(results, db)
        assert "Auth Module" in output
        assert "handles login" in output
        assert "tokens" in output


class TestQuerySanitization:
    """Natural-language and method: queries must not error or silently miss."""

    def _db(self, tmp_path):
        db = tmp_path / "test.db"
        create_search_db(db)
        insert_page(db, {
            "id": "auth", "title": "Auth Module", "category": "core",
            "body_plain": "handles the authentication flow and login",
            "tags": '["auth", "method:refreshToken"]',
            "importance_score": 0.8, "language": "python",
        })
        return db

    def test_sanitize_strips_fts_syntax(self):
        from llmwiki.search import sanitize_fts_query
        expr = sanitize_fts_query('how does auth-flow work?')
        assert ":" not in expr
        assert "-" not in expr
        assert '"how"' in expr

    def test_sanitize_empty_query(self):
        from llmwiki.search import sanitize_fts_query
        assert sanitize_fts_query("???") == ""

    def test_natural_language_query_with_punctuation(self, tmp_path):
        db = self._db(tmp_path)
        results = search_pages(db, "how does the authentication flow work?")
        assert len(results) == 1
        assert results[0]["id"] == "auth"

    def test_hyphenated_query_does_not_error(self, tmp_path):
        db = self._db(tmp_path)
        results = search_pages(db, "auth-flow login")
        assert len(results) == 1

    def test_method_prefix_routes_to_method_search(self, tmp_path):
        db = self._db(tmp_path)
        # Previously "method:x" hit FTS5 column syntax -> OperationalError -> []
        results = search_pages(db, "method:refreshToken")
        assert isinstance(results, list)  # no exception, routed to search_method

    def test_context_output_strips_source_block(self, tmp_path):
        db = tmp_path / "test.db"
        create_search_db(db)
        insert_page(db, {
            "id": "big", "title": "Big File", "category": "core",
            "body_plain": "## Overview\n\nsummary here\n\n<details>\n"
                          "<summary>Full source</summary>\n\nSECRET_SOURCE\n</details>",
            "tags": "[]", "importance_score": 0.5,
        })
        from llmwiki.search import format_results_context
        out = format_results_context(
            [{"id": "big", "title": "Big File", "category": "core"}], db)
        assert "summary here" in out
        assert "SECRET_SOURCE" not in out
