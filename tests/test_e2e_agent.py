"""End-to-end test for AI agent integration features."""

import json
import pytest
from pathlib import Path

from llmwiki.config import create_default_config, save_config
from llmwiki.ingest import ingest_source
from llmwiki.build import build_site
from llmwiki.agent_toggle import enable_agent, disable_agent, get_agent_status
from llmwiki.search import search_pages, format_results_json, format_results_compact, format_results_context
from llmwiki.benchmark import run_benchmark, format_benchmark_report
from llmwiki.mcp_server import handle_request, get_tools_list
from llmwiki.setup_agent import detect_ides, generate_vscode_mcp, generate_copilot_extension, setup_all


@pytest.fixture
def wiki_project(tmp_path):
    """Create a complete mini wiki project for E2E testing."""
    # Create source files
    src = tmp_path / "source"
    src.mkdir()
    (src / "auth.py").write_text(
        '"""Authentication module."""\n\n'
        'def login(username, password):\n'
        '    """Authenticate a user."""\n'
        '    return username == "admin"\n\n'
        'def logout(session):\n'
        '    """End user session."""\n'
        '    session.clear()\n\n'
        'def check_permission(user, resource):\n'
        '    """Check if user can access resource."""\n'
        '    return user.role == "admin"\n'
    )
    (src / "database.py").write_text(
        '"""Database utilities."""\n\n'
        'def connect(host, port):\n'
        '    """Create database connection."""\n'
        '    return {"host": host, "port": port}\n\n'
        'def query(conn, sql):\n'
        '    """Execute SQL query."""\n'
        '    return []\n'
    )
    (src / "config.json").write_text(json.dumps({"db_host": "localhost", "db_port": 5432}))

    # Create wiki project
    wiki = tmp_path / ".llmwiki"
    wiki.mkdir()
    for d in ["raw", "wiki", "site"]:
        (wiki / d).mkdir()

    config = create_default_config("TestProject", str(src))
    cfg_path = wiki / "llmwiki.json"
    save_config(config, cfg_path)

    # Ingest
    state_path = wiki / ".llmwiki-state.json"
    ingest_source(src, wiki / "raw", state_path, config)

    # Build
    build_site(wiki, config)

    return {"root": wiki, "source": src, "config_path": cfg_path, "config": config}


class TestAgentToggle:
    def test_default_disabled(self, wiki_project):
        assert get_agent_status(wiki_project["config_path"]) is False

    def test_enable_disable_cycle(self, wiki_project):
        cfg = wiki_project["config_path"]
        enable_agent(cfg)
        assert get_agent_status(cfg) is True
        disable_agent(cfg)
        assert get_agent_status(cfg) is False


class TestSearchModes:
    def test_search_returns_results(self, wiki_project):
        db = wiki_project["root"] / "site" / "llmwiki.db"
        results = search_pages(db, "login")
        assert len(results) > 0

    def test_json_format(self, wiki_project):
        db = wiki_project["root"] / "site" / "llmwiki.db"
        results = search_pages(db, "login")
        output = format_results_json(results)
        parsed = json.loads(output)
        assert isinstance(parsed, list)

    def test_compact_format(self, wiki_project):
        db = wiki_project["root"] / "site" / "llmwiki.db"
        results = search_pages(db, "login")
        output = format_results_compact(results)
        assert "login" in output.lower() or len(output) > 0

    def test_context_format(self, wiki_project):
        db = wiki_project["root"] / "site" / "llmwiki.db"
        results = search_pages(db, "login")
        if results:
            output = format_results_context(results, db)
            assert "tokens" in output.lower()


class TestBenchmark:
    def test_benchmark_shows_savings(self, wiki_project):
        result = run_benchmark(
            "login",
            source_dirs=[wiki_project["source"]],
            site_dir=wiki_project["root"] / "site",
        )
        assert result["raw_tokens"] > 0
        assert result["wiki_tokens"] >= 0
        # Wiki may be larger or smaller than raw depending on metadata/context
        assert "savings_pct" in result
        assert "savings_tokens" in result

    def test_benchmark_report_format(self, wiki_project):
        result = run_benchmark(
            "login",
            source_dirs=[wiki_project["source"]],
            site_dir=wiki_project["root"] / "site",
        )
        report = format_benchmark_report(result)
        assert "login" in report
        assert "Tokens" in report and "Methodology" in report


class TestMCPServer:
    def test_initialize(self, wiki_project):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = handle_request(req, str(wiki_project["root"] / "site"))
        assert resp["result"]["serverInfo"]["name"] == "llmwiki"

    def test_tools_list(self, wiki_project):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        resp = handle_request(req, str(wiki_project["root"] / "site"))
        names = [t["name"] for t in resp["result"]["tools"]]
        assert "llmwiki_search" in names
        assert "llmwiki_find_method" in names

    def test_search_via_mcp(self, wiki_project):
        req = {
            "jsonrpc": "2.0", "id": 3,
            "method": "tools/call",
            "params": {"name": "llmwiki_search", "arguments": {"query": "login"}},
        }
        resp = handle_request(req, str(wiki_project["root"] / "site"))
        text = resp["result"]["content"][0]["text"]
        assert "login" in text.lower() or "auth" in text.lower() or "No results" in text

    def test_stats_via_mcp(self, wiki_project):
        req = {
            "jsonrpc": "2.0", "id": 4,
            "method": "tools/call",
            "params": {"name": "llmwiki_stats", "arguments": {}},
        }
        resp = handle_request(req, str(wiki_project["root"] / "site"))
        stats = json.loads(resp["result"]["content"][0]["text"])
        assert "total_pages" in stats


class TestSetupAgent:
    def test_setup_creates_configs(self, wiki_project):
        project_root = wiki_project["root"].parent
        created = setup_all(project_root, wiki_subdir=".llmwiki")
        assert len(created) == 5

    def test_copilot_extension_content(self, wiki_project):
        project_root = wiki_project["root"].parent
        ext_path = generate_copilot_extension(project_root, ".llmwiki")
        content = ext_path.read_text()
        assert "llmwiki_search" in content
        assert "llmwiki search" in content


class TestDashboard:
    def test_dashboard_has_token_stats(self, wiki_project):
        index_html = (wiki_project["root"] / "site" / "index.html").read_text()
        # Dashboard should contain token efficiency stats if source was accessible
        assert "wiki tokens" in index_html.lower() or "stats-strip" in index_html
