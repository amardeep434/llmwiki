"""Tests for SQLite FTS5 search."""

from pathlib import Path
from llmwiki.search import create_search_db, insert_page, search_pages, cli_search


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
