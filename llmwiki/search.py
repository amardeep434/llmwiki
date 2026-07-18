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
            SELECT p.id, p.title, p.category, p.importance_score, p.language,
                   p.body_plain,
                   snippet(pages_fts, 1, '>>>', '<<<', '...', 50) as snippet
            FROM pages_fts
            JOIN pages p ON pages_fts.rowid = p.rowid
            WHERE pages_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        results = []
        for row in c.fetchall():
            r = dict(row)
            body = r.pop("body_plain", "") or ""
            lang = r.get("language", "")
            # Extract method signatures for source code pages
            if lang:
                sigs = _extract_signatures(body, lang)
                if sigs:
                    r["methods"] = sigs
            results.append(r)
    except sqlite3.OperationalError:
        results = []

    conn.close()
    return results


def search_method(db_path: Path, method_name: str, limit: int = 20) -> list[dict]:
    """Search for a specific method/function by name across all pages.

    Returns pages that contain the method with the matching signature highlighted.
    """
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Search in tags (method:xyz) and body for the method name.
    # Prioritize pages that declare the method (in tags) over pages that just reference it.
    try:
        c.execute("""
            SELECT p.id, p.title, p.category, p.importance_score, p.language,
                   p.body_plain, p.tags
            FROM pages p
            WHERE p.language != ''
              AND (p.tags LIKE ? OR p.body_plain LIKE ?)
            ORDER BY (CASE WHEN p.tags LIKE ? THEN 0 ELSE 1 END)
            LIMIT ?
        """, (f'%"method:{method_name}"%', f'%{method_name}%',
              f'%"method:{method_name}"%', limit))

        results = []
        for row in c.fetchall():
            r = dict(row)
            body = r.pop("body_plain", "") or ""
            r.pop("tags", None)
            lang = r.get("language", "")
            # Extract all signatures, filter to matching method
            all_sigs = _extract_signatures(body, lang)
            matching = [s for s in all_sigs if method_name in s]
            if matching:
                r["methods"] = matching
                results.append(r)
    except sqlite3.OperationalError:
        results = []

    conn.close()
    return results


def format_results_json(results: list[dict]) -> str:
    """Format search results as JSON array."""
    return json.dumps(results, indent=2)


def format_results_agent(results: list[dict]) -> str:
    """Format optimized for AI agent consumption — minimal tokens, max signal.

    Includes: page ID (for llmwiki get), title, category, methods (if any).
    Omits: verbose snippets, importance scores, language field.
    """
    lines = [f"{len(results)} results\n"]
    for r in results:
        line = f"- [{r.get('category', '')}] {r['title']} (id: {r['id']})"
        lines.append(line)
        if r.get("methods"):
            for m in r["methods"]:
                lines.append(f"    {m}")
    lines.append("")
    lines.append("Use `llmwiki get \"<id>\"` for full page content.")
    return "\n".join(lines)


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


def get_page(db_path: Path, page_id: str) -> dict | None:
    """Retrieve a single page by ID with full content."""
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, title, category, source_path, body_plain, tags, "
        "importance_score, language, url FROM pages WHERE id = ?",
        (page_id,),
    ).fetchone()
    conn.close()

    if not row:
        return None
    return dict(row)


def format_page_for_agent(page: dict) -> str:
    """Format a page for direct LLM consumption — structured and concise."""
    body = page.get("body_plain", "")

    # Extract method signatures from body for source code pages
    signatures = _extract_signatures(body, page.get("language", ""))

    parts = [
        f"# {page['title']}",
        f"Category: {page.get('category', '')}",
        f"Language: {page.get('language', '')}",
        f"Source: {page.get('source_path', '')}",
    ]

    if signatures:
        parts.append("\n## Method Signatures\n")
        parts.extend(f"- `{sig}`" for sig in signatures)

    # Include body but strip the full source code block (too large)
    body_trimmed = _strip_source_block(body)
    if body_trimmed.strip():
        parts.append(f"\n## Content\n\n{body_trimmed}")

    return "\n".join(parts)


def _extract_signatures(body: str, language: str) -> list[str]:
    """Extract method/function signatures from the source code in body."""
    import re

    # Look for the source code inside <details> block
    details_match = re.search(r"<details>.*?```\w*\n(.*?)```", body, re.DOTALL)
    if not details_match:
        return []

    source = details_match.group(1)

    patterns = {
        "java": re.compile(
            r"^\s*(?:public|protected|private)\s+(?:static\s+)?(?:synchronized\s+)?"
            r"([\w<>\[\], ]+\s+\w+\s*\([^)]*\))",
            re.MULTILINE,
        ),
        "python": re.compile(r"^\s*def\s+(\w+\s*\([^)]*\))", re.MULTILINE),
        "javascript": re.compile(
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+\s*\([^)]*\))", re.MULTILINE
        ),
        "typescript": re.compile(
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+\s*\([^)]*\))", re.MULTILINE
        ),
    }

    pat = patterns.get(language)
    if not pat:
        return []

    matches = pat.findall(source)
    # Clean up whitespace
    return [" ".join(m.split()) for m in matches[:30]]


def _strip_source_block(body: str) -> str:
    """Remove the <details> full source block to save tokens."""
    import re
    return re.sub(r"<details>.*?</details>", "", body, flags=re.DOTALL).strip()
