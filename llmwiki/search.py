"""Search system — SQLite FTS5 for AI agents, client-side index for humans."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def create_search_db(db_path: Path) -> None:
    """Create the SQLite FTS5 search database."""
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT,
            source_path TEXT,
            body_md TEXT,
            body_plain TEXT,
            content_hash TEXT,
            tags TEXT,
            references_out TEXT,
            references_in TEXT,
            importance_score REAL DEFAULT 0.0,
            cluster_id TEXT,
            language TEXT,
            in_degree INTEGER DEFAULT 0,
            url TEXT,
            metadata TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    _ensure_pages_columns(c)

    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
            title, body_plain, tags, category,
            content='pages', content_rowid='rowid'
        )
    """)

    # Triggers to keep FTS index in sync with pages table
    c.execute("""
        CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
            INSERT INTO pages_fts(rowid, title, body_plain, tags, category)
            VALUES (new.rowid, new.title, new.body_plain, new.tags, new.category);
        END
    """)
    c.execute("""
        CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
            INSERT INTO pages_fts(pages_fts, rowid, title, body_plain, tags, category)
            VALUES ('delete', old.rowid, old.title, old.body_plain, old.tags, old.category);
        END
    """)
    c.execute("""
        CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
            INSERT INTO pages_fts(pages_fts, rowid, title, body_plain, tags, category)
            VALUES ('delete', old.rowid, old.title, old.body_plain, old.tags, old.category);
            INSERT INTO pages_fts(rowid, title, body_plain, tags, category)
            VALUES (new.rowid, new.title, new.body_plain, new.tags, new.category);
        END
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            from_id TEXT NOT NULL,
            to_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            PRIMARY KEY (from_id, to_id, edge_type)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS clusters (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            member_count INTEGER,
            top_tags TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS build_history (
            build_number INTEGER PRIMARY KEY,
            timestamp TEXT,
            type TEXT,
            duration_seconds REAL,
            added_count INTEGER,
            updated_count INTEGER,
            archived_count INTEGER,
            changes TEXT
        )
    """)

    conn.commit()
    conn.close()


def _ensure_pages_columns(cursor: sqlite3.Cursor) -> None:
    """Backfill newer columns for existing databases."""
    existing = {
        row[1]: row[2]
        for row in cursor.execute("PRAGMA table_info(pages)").fetchall()
    }
    required = {
        "source_path": "TEXT",
        "language": "TEXT",
        "cluster_id": "TEXT",
        "in_degree": "INTEGER DEFAULT 0",
        "url": "TEXT",
    }
    for column, definition in required.items():
        if column not in existing:
            cursor.execute(f"ALTER TABLE pages ADD COLUMN {column} {definition}")


def insert_page(db_path: Path, page: dict) -> None:
    """Insert or replace a page in the search database.

    FTS index is kept in sync automatically via triggers created by create_search_db().
    """
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    # DELETE + INSERT instead of INSERT OR REPLACE so the delete trigger fires
    # for existing rows (REPLACE = DELETE + INSERT under the hood but doesn't
    # reliably fire the AFTER DELETE trigger on all SQLite builds).
    c.execute("DELETE FROM pages WHERE id = ?", (page["id"],))
    c.execute("""
        INSERT INTO pages (
            id, title, category, source_path, body_plain, tags,
            importance_score, cluster_id, language, in_degree, url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        page["id"], page["title"], page.get("category", ""),
        page.get("source_path", ""), page.get("body_plain", ""), page.get("tags", "[]"),
        page.get("importance_score", 0.0),
        page.get("cluster_id"), page.get("language", ""),
        page.get("in_degree", 0), page.get("url", ""),
    ))

    conn.commit()
    conn.close()


def search_pages(db_path: Path, query: str, limit: int = 20) -> list[dict]:
    """Full-text search against the FTS5 index."""
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute("""
            SELECT p.id, p.title, p.category, p.importance_score,
                   snippet(pages_fts, 1, '>>>', '<<<', '...', 50) as snippet
            FROM pages_fts
            JOIN pages p ON pages_fts.rowid = p.rowid
            WHERE pages_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        results = [dict(row) for row in c.fetchall()]
    except sqlite3.OperationalError:
        results = []

    conn.close()
    return results


def format_results_json(results: list[dict]) -> str:
    """Format search results as JSON array."""
    return json.dumps(results, indent=2)


def format_results_compact(results: list[dict]) -> str:
    """Format as minimal text: one line per result (lowest token usage)."""
    lines = []
    for r in results:
        lines.append(f"{r['title']} [{r.get('category', '')}] imp={r.get('importance_score', 0):.3f}")
    return "\n".join(lines)


def format_results_context(results: list[dict], db_path: Path) -> str:
    """Format with full page bodies for LLM context consumption."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    parts = []
    for r in results:
        row = conn.execute(
            "SELECT body_plain, tags, url FROM pages WHERE id = ?", (r["id"],)
        ).fetchone()
        if row:
            body = row["body_plain"] or ""
            tags = row["tags"] or "[]"
            url = row["url"] or ""
            parts.append(
                f"## {r['title']}\n"
                f"Category: {r.get('category', '')}\n"
                f"URL: {url}\n"
                f"Tags: {tags}\n\n"
                f"{body}\n"
            )
    conn.close()
    total_tokens = sum(len(p) for p in parts) // 4
    header = f"# Search Results ({len(results)} pages, ~{total_tokens:,} tokens)\n\n"
    return header + "\n---\n\n".join(parts)


def cli_search(query: str, db_path: str) -> int:
    """CLI search entry point."""
    results = search_pages(Path(db_path), query)
    if not results:
        print(f"No results for: {query}")
        return 0

    print(f"Found {len(results)} results for: {query}\n")
    for r in results:
        print(f"  [{r.get('category', '')}] {r['title']}")
        if r.get("snippet"):
            print(f"    {r['snippet']}")
        print()
    return 0
