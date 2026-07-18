"""MCP server for llmwiki — exposes search tools via JSON-RPC 2.0 over stdio."""

from __future__ import annotations

import json
import sys
from pathlib import Path


SERVER_NAME = "llmwiki"
SERVER_VERSION = "0.1.0"

TOOLS = [
    {
        "name": "llmwiki_search",
        "description": "Search the knowledge base for pages matching a query. Returns titles, categories, snippets, and importance scores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (keywords, method names, or concepts)"},
                "limit": {"type": "integer", "description": "Max results (default 10)", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "llmwiki_get_page",
        "description": "Get full content of a specific wiki page by ID or title. Returns body, tags, methods, references, and backlinks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Page ID (e.g. 'com/vf/core/Utility')"},
                "title": {"type": "string", "description": "Page title (alternative to ID)"},
            },
        },
    },
    {
        "name": "llmwiki_list_categories",
        "description": "List all categories in the knowledge base with page counts.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "llmwiki_find_method",
        "description": "Find pages containing a specific method or function declaration.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Method/function name to search for"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "llmwiki_get_connections",
        "description": "Get cross-reference connections (inbound and outbound links) for a page.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Page ID"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "llmwiki_stats",
        "description": "Get wiki statistics: page count, edge count, cluster count, token efficiency numbers.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def get_tools_list() -> list[dict]:
    """Return the list of available tools."""
    return TOOLS


def handle_request(request: dict, wiki_dir: str) -> dict | None:
    """Handle a single JSON-RPC request. Returns response dict or None for notifications."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return _response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if method == "notifications/initialized":
        return None  # Notification, no response

    if method == "tools/list":
        return _response(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        return _handle_tool_call(req_id, tool_name, arguments, wiki_dir)

    if method == "ping":
        return _response(req_id, {})

    # Unknown method
    return _error(req_id, -32601, f"Method not found: {method}")


def _handle_tool_call(req_id, tool_name: str, args: dict, wiki_dir: str) -> dict:
    """Dispatch a tool call to the appropriate handler."""
    wiki = Path(wiki_dir)
    handlers = {
        "llmwiki_search": lambda: _tool_search(wiki, args),
        "llmwiki_get_page": lambda: _tool_get_page(wiki, args),
        "llmwiki_list_categories": lambda: _tool_list_categories(wiki),
        "llmwiki_find_method": lambda: _tool_find_method(wiki, args),
        "llmwiki_get_connections": lambda: _tool_get_connections(wiki, args),
        "llmwiki_stats": lambda: _tool_stats(wiki),
    }
    handler = handlers.get(tool_name)
    if not handler:
        return _error(req_id, -32602, f"Unknown tool: {tool_name}")
    try:
        result_text = handler()
        return _response(req_id, {"content": [{"type": "text", "text": result_text}]})
    except Exception as e:
        return _response(req_id, {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True})


def _db_path(wiki: Path) -> Path:
    return wiki / "llmwiki.db"


def _freshness_prefix(wiki: Path) -> str:
    """Staleness warning line to prepend to tool output ('' when fresh)."""
    try:
        from llmwiki.config import load_config
        from llmwiki.freshness import check_freshness, format_freshness_warning

        cfg_path = wiki.parent / "llmwiki.json"
        state_path = wiki.parent / ".llmwiki-state.json"
        if not cfg_path.exists():
            return ""
        warning = format_freshness_warning(
            check_freshness(load_config(cfg_path), state_path)
        )
        return warning + "\n\n" if warning else ""
    except Exception:
        return ""


def _tool_search(wiki: Path, args: dict) -> str:
    """Search the knowledge base via FTS5, falling back to the JSON index."""
    query = args.get("query", "")
    limit = args.get("limit", 10)
    if not query:
        return "Error: query is required"

    db = _db_path(wiki)
    if db.exists():
        from llmwiki.search import search_pages

        results = search_pages(db, query, limit=limit)
        if not results:
            return f"No results for: {query}"
        payload = [
            {
                "id": r.get("id"),
                "title": r.get("title", ""),
                "category": r.get("category", ""),
                "snippet": r.get("snippet", ""),
                "methods": r.get("methods", []),
            }
            for r in results
        ]
        return _freshness_prefix(wiki) + json.dumps(payload, indent=2)

    return _index_search(wiki, query, limit)


def _index_search(wiki: Path, query: str, limit: int) -> str:
    """Fallback keyword search over search-index.json (no DB built)."""
    idx_path = wiki / "search-index.json"
    if not idx_path.exists():
        return "No search index found. Run `llmwiki all` to build the wiki."

    data = json.loads(idx_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    keywords = query.lower().split()

    results = []
    for entry in entries:
        text = f"{entry.get('title', '')} {entry.get('body', '')} {' '.join(entry.get('tags', []))}".lower()
        if any(kw in text for kw in keywords):
            results.append({
                "id": entry.get("id"),
                "title": entry.get("title", ""),
                "category": entry.get("category", ""),
                "url": entry.get("url", ""),
                "importance": entry.get("importance", 0),
                "snippet": entry.get("body", "")[:200],
            })
    results.sort(key=lambda x: x["importance"], reverse=True)
    results = results[:limit]

    if not results:
        return f"No results for: {query}"
    return json.dumps(results, indent=2)


def _tool_get_page(wiki: Path, args: dict) -> str:
    """Get full page content by ID or title (full body, source-stripped)."""
    page_id = args.get("id", "")
    title = args.get("title", "")
    if not page_id and not title:
        return "Error: either 'id' or 'title' is required"

    db = _db_path(wiki)
    if db.exists():
        from llmwiki.search import get_page, format_page_for_agent, search_pages

        page = get_page(db, page_id) if page_id else None
        if page is None and title:
            for candidate in search_pages(db, title, limit=5):
                if candidate.get("title", "").lower() == title.lower():
                    page = get_page(db, candidate["id"])
                    break
        if page is None:
            return f"Page not found: {page_id or title}"
        return _freshness_prefix(wiki) + format_page_for_agent(page)

    # Fallback: JSON index (bodies truncated at build time)
    idx_path = wiki / "search-index.json"
    if not idx_path.exists():
        return "No search index found."

    data = json.loads(idx_path.read_text(encoding="utf-8"))
    for entry in data.get("entries", []):
        if (page_id and entry.get("id") == page_id) or \
           (title and entry.get("title", "").lower() == title.lower()):
            return json.dumps({
                "id": entry.get("id"),
                "title": entry.get("title"),
                "category": entry.get("category"),
                "url": entry.get("url"),
                "tags": entry.get("tags", []),
                "importance": entry.get("importance", 0),
                "body": entry.get("body", ""),
                "note": "truncated index body — build llmwiki.db for full content",
            }, indent=2)

    return f"Page not found: {page_id or title}"


def _tool_list_categories(wiki: Path) -> str:
    """List all categories with counts."""
    idx_path = wiki / "search-index.json"
    if not idx_path.exists():
        return "No search index found."
    data = json.loads(idx_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    cats: dict[str, int] = {}
    for e in entries:
        cat = e.get("category", "uncategorized")
        cats[cat] = cats.get(cat, 0) + 1
    sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)
    return json.dumps([{"category": c, "count": n} for c, n in sorted_cats], indent=2)


def _tool_find_method(wiki: Path, args: dict) -> str:
    """Find pages with a specific method/function."""
    name = args.get("name", "")
    if not name:
        return "Error: method name is required"

    db = _db_path(wiki)
    if db.exists():
        from llmwiki.search import search_method

        results = search_method(db, name)
        if not results:
            return f"No pages found with method: {name}"
        payload = [
            {
                "id": r.get("id"),
                "title": r.get("title", ""),
                "category": r.get("category", ""),
                "methods": r.get("methods", []),
            }
            for r in results
        ]
        return _freshness_prefix(wiki) + json.dumps(payload, indent=2)

    idx_path = wiki / "search-index.json"
    if not idx_path.exists():
        return "No search index found."
    data = json.loads(idx_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    method_tag = f"method:{name}"
    results = []
    for e in entries:
        if method_tag in e.get("tags", []):
            results.append({
                "title": e.get("title", ""),
                "category": e.get("category", ""),
                "url": e.get("url", ""),
            })
    if not results:
        return f"No pages found with method: {name}"
    return json.dumps(results, indent=2)


def _tool_get_connections(wiki: Path, args: dict) -> str:
    """Get cross-references for a page."""
    page_id = args.get("id", "")
    if not page_id:
        return "Error: page id is required"
    xref_path = wiki / "cross-references.json"
    if not xref_path.exists():
        return "No cross-references found."
    graph = json.loads(xref_path.read_text(encoding="utf-8"))
    edges = graph.get("edges", [])
    outbound = [e["to"] for e in edges if e.get("from") == page_id]
    inbound = [e["from"] for e in edges if e.get("to") == page_id]
    return json.dumps({"page": page_id, "outbound": outbound, "inbound": inbound}, indent=2)


def _tool_stats(wiki: Path) -> str:
    """Get wiki statistics."""
    xref_path = wiki / "cross-references.json"
    idx_path = wiki / "search-index.json"
    stats = {}
    if xref_path.exists():
        graph = json.loads(xref_path.read_text(encoding="utf-8"))
        gs = graph.get("stats", {})
        stats["total_pages"] = gs.get("total_pages", 0)
        stats["total_edges"] = gs.get("total_edges", 0)
        stats["total_clusters"] = gs.get("total_clusters", 0)
    if idx_path.exists():
        data = json.loads(idx_path.read_text(encoding="utf-8"))
        entries = data.get("entries", [])
        wiki_tokens = sum(len(e.get("body", "")) for e in entries) // 4
        stats["wiki_tokens"] = wiki_tokens
    return json.dumps(stats, indent=2)


def _response(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def run_server(wiki_dir: str) -> None:
    """Run the MCP server on stdio."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle_request(request, wiki_dir)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
