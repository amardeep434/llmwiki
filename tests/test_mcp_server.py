"""Tests for llmwiki MCP server."""

from __future__ import annotations

import json

import pytest

from llmwiki.mcp_server import get_tools_list, handle_request


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ENTRIES = [
    {
        "id": "com/example/Utility",
        "title": "Utility",
        "category": "core",
        "url": "/wiki/com/example/Utility.html",
        "importance": 8,
        "tags": ["method:doSomething", "method:parse"],
        "body": "Utility class providing helper methods for parsing and formatting.",
    },
    {
        "id": "com/example/Config",
        "title": "Config",
        "category": "core",
        "url": "/wiki/com/example/Config.html",
        "importance": 5,
        "tags": ["method:load"],
        "body": "Configuration loader that reads settings from disk.",
    },
    {
        "id": "com/example/Server",
        "title": "Server",
        "category": "network",
        "url": "/wiki/com/example/Server.html",
        "importance": 10,
        "tags": ["method:start", "method:stop"],
        "body": "HTTP server implementation with lifecycle management.",
    },
]

SAMPLE_XREF = {
    "edges": [
        {"from": "com/example/Server", "to": "com/example/Config"},
        {"from": "com/example/Server", "to": "com/example/Utility"},
        {"from": "com/example/Config", "to": "com/example/Utility"},
    ],
    "stats": {
        "total_pages": 3,
        "total_edges": 3,
        "total_clusters": 1,
    },
}


@pytest.fixture()
def wiki_dir(tmp_path):
    """Create a temporary wiki directory with sample data files."""
    idx = tmp_path / "search-index.json"
    idx.write_text(json.dumps({"entries": SAMPLE_ENTRIES}), encoding="utf-8")
    xref = tmp_path / "cross-references.json"
    xref.write_text(json.dumps(SAMPLE_XREF), encoding="utf-8")
    return str(tmp_path)


# ---------------------------------------------------------------------------
# get_tools_list
# ---------------------------------------------------------------------------

def test_get_tools_list_returns_six_tools():
    tools = get_tools_list()
    assert len(tools) == 6
    names = {t["name"] for t in tools}
    assert names == {
        "llmwiki_search",
        "llmwiki_get_page",
        "llmwiki_list_categories",
        "llmwiki_find_method",
        "llmwiki_get_connections",
        "llmwiki_stats",
    }


# ---------------------------------------------------------------------------
# initialize
# ---------------------------------------------------------------------------

def test_initialize(wiki_dir):
    req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    resp = handle_request(req, wiki_dir)
    assert resp["id"] == 1
    result = resp["result"]
    assert result["protocolVersion"] == "2024-11-05"
    assert result["capabilities"] == {"tools": {}}
    assert result["serverInfo"]["name"] == "llmwiki"


# ---------------------------------------------------------------------------
# notifications/initialized
# ---------------------------------------------------------------------------

def test_notifications_initialized_returns_none(wiki_dir):
    req = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    assert handle_request(req, wiki_dir) is None


# ---------------------------------------------------------------------------
# ping
# ---------------------------------------------------------------------------

def test_ping(wiki_dir):
    req = {"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}}
    resp = handle_request(req, wiki_dir)
    assert resp["result"] == {}


# ---------------------------------------------------------------------------
# tools/list
# ---------------------------------------------------------------------------

def test_tools_list(wiki_dir):
    req = {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}
    resp = handle_request(req, wiki_dir)
    tools = resp["result"]["tools"]
    assert len(tools) == 6
    assert all("inputSchema" in t for t in tools)


# ---------------------------------------------------------------------------
# unknown method
# ---------------------------------------------------------------------------

def test_unknown_method(wiki_dir):
    req = {"jsonrpc": "2.0", "id": 99, "method": "bogus/method", "params": {}}
    resp = handle_request(req, wiki_dir)
    assert "error" in resp
    assert resp["error"]["code"] == -32601


# ---------------------------------------------------------------------------
# tools/call — llmwiki_search
# ---------------------------------------------------------------------------

def test_search_finds_results(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 10, "method": "tools/call",
        "params": {"name": "llmwiki_search", "arguments": {"query": "utility"}},
    }
    resp = handle_request(req, wiki_dir)
    content = resp["result"]["content"]
    assert len(content) == 1
    results = json.loads(content[0]["text"])
    assert len(results) >= 1
    assert any(r["title"] == "Utility" for r in results)


def test_search_no_results(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 11, "method": "tools/call",
        "params": {"name": "llmwiki_search", "arguments": {"query": "nonexistent_xyz"}},
    }
    resp = handle_request(req, wiki_dir)
    text = resp["result"]["content"][0]["text"]
    assert "No results" in text


def test_search_respects_limit(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 12, "method": "tools/call",
        "params": {"name": "llmwiki_search", "arguments": {"query": "method", "limit": 1}},
    }
    resp = handle_request(req, wiki_dir)
    results = json.loads(resp["result"]["content"][0]["text"])
    assert len(results) <= 1


def test_search_missing_index(tmp_path):
    req = {
        "jsonrpc": "2.0", "id": 13, "method": "tools/call",
        "params": {"name": "llmwiki_search", "arguments": {"query": "test"}},
    }
    resp = handle_request(req, str(tmp_path))
    text = resp["result"]["content"][0]["text"]
    assert "No search index" in text


# ---------------------------------------------------------------------------
# tools/call — llmwiki_get_page
# ---------------------------------------------------------------------------

def test_get_page_by_id(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 20, "method": "tools/call",
        "params": {"name": "llmwiki_get_page", "arguments": {"id": "com/example/Utility"}},
    }
    resp = handle_request(req, wiki_dir)
    page = json.loads(resp["result"]["content"][0]["text"])
    assert page["title"] == "Utility"
    assert page["category"] == "core"


def test_get_page_by_title(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 21, "method": "tools/call",
        "params": {"name": "llmwiki_get_page", "arguments": {"title": "config"}},
    }
    resp = handle_request(req, wiki_dir)
    page = json.loads(resp["result"]["content"][0]["text"])
    assert page["id"] == "com/example/Config"


def test_get_page_not_found(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 22, "method": "tools/call",
        "params": {"name": "llmwiki_get_page", "arguments": {"id": "does/not/exist"}},
    }
    resp = handle_request(req, wiki_dir)
    text = resp["result"]["content"][0]["text"]
    assert "Page not found" in text


def test_get_page_no_args(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 23, "method": "tools/call",
        "params": {"name": "llmwiki_get_page", "arguments": {}},
    }
    resp = handle_request(req, wiki_dir)
    text = resp["result"]["content"][0]["text"]
    assert "required" in text.lower()


# ---------------------------------------------------------------------------
# tools/call — llmwiki_list_categories
# ---------------------------------------------------------------------------

def test_list_categories(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 30, "method": "tools/call",
        "params": {"name": "llmwiki_list_categories", "arguments": {}},
    }
    resp = handle_request(req, wiki_dir)
    cats = json.loads(resp["result"]["content"][0]["text"])
    cat_names = {c["category"] for c in cats}
    assert "core" in cat_names
    assert "network" in cat_names
    # core has 2 entries, network has 1
    core = next(c for c in cats if c["category"] == "core")
    assert core["count"] == 2


# ---------------------------------------------------------------------------
# tools/call — llmwiki_find_method
# ---------------------------------------------------------------------------

def test_find_method_found(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 40, "method": "tools/call",
        "params": {"name": "llmwiki_find_method", "arguments": {"name": "doSomething"}},
    }
    resp = handle_request(req, wiki_dir)
    results = json.loads(resp["result"]["content"][0]["text"])
    assert len(results) == 1
    assert results[0]["title"] == "Utility"


def test_find_method_not_found(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 41, "method": "tools/call",
        "params": {"name": "llmwiki_find_method", "arguments": {"name": "nonExistent"}},
    }
    resp = handle_request(req, wiki_dir)
    text = resp["result"]["content"][0]["text"]
    assert "No pages found" in text


# ---------------------------------------------------------------------------
# tools/call — llmwiki_get_connections
# ---------------------------------------------------------------------------

def test_get_connections(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 50, "method": "tools/call",
        "params": {"name": "llmwiki_get_connections", "arguments": {"id": "com/example/Server"}},
    }
    resp = handle_request(req, wiki_dir)
    conns = json.loads(resp["result"]["content"][0]["text"])
    assert conns["page"] == "com/example/Server"
    assert "com/example/Config" in conns["outbound"]
    assert "com/example/Utility" in conns["outbound"]
    assert conns["inbound"] == []


def test_get_connections_inbound(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 51, "method": "tools/call",
        "params": {"name": "llmwiki_get_connections", "arguments": {"id": "com/example/Utility"}},
    }
    resp = handle_request(req, wiki_dir)
    conns = json.loads(resp["result"]["content"][0]["text"])
    assert "com/example/Server" in conns["inbound"]
    assert "com/example/Config" in conns["inbound"]


# ---------------------------------------------------------------------------
# tools/call — llmwiki_stats
# ---------------------------------------------------------------------------

def test_stats(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 60, "method": "tools/call",
        "params": {"name": "llmwiki_stats", "arguments": {}},
    }
    resp = handle_request(req, wiki_dir)
    stats = json.loads(resp["result"]["content"][0]["text"])
    assert stats["total_pages"] == 3
    assert stats["total_edges"] == 3
    assert stats["total_clusters"] == 1
    assert "wiki_tokens" in stats


# ---------------------------------------------------------------------------
# tools/call — unknown tool
# ---------------------------------------------------------------------------

def test_unknown_tool(wiki_dir):
    req = {
        "jsonrpc": "2.0", "id": 70, "method": "tools/call",
        "params": {"name": "bogus_tool", "arguments": {}},
    }
    resp = handle_request(req, wiki_dir)
    assert "error" in resp
    assert resp["error"]["code"] == -32602
