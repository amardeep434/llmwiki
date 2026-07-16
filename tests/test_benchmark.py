import json
import pytest
from pathlib import Path
from llmwiki.benchmark import count_tokens, count_raw_tokens, count_wiki_tokens, run_benchmark, format_benchmark_report


def test_count_tokens():
    assert count_tokens("hello world") > 0
    assert count_tokens("a" * 400) == 100


def test_count_raw_tokens(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login():\n    pass\n" * 100)
    (src / "utils.py").write_text("def helper():\n    return 1\n" * 50)
    (src / "readme.md").write_text("this has nothing to do with login")
    tokens, files = count_raw_tokens([src], "login")
    assert tokens > 0
    assert files == 2  # auth.py and readme.md match "login"


def test_count_wiki_tokens(tmp_path):
    idx = {"entries": [
        {"id": "auth", "title": "Auth Module", "body": "handles login flow " * 20, "tags": ["auth"], "category": "core"},
        {"id": "utils", "title": "Utils", "body": "helper functions", "tags": [], "category": "core"},
    ]}
    (tmp_path / "search-index.json").write_text(json.dumps(idx))
    tokens, pages = count_wiki_tokens(tmp_path, "login")
    assert tokens > 0
    assert pages == 1  # only auth matches


def test_run_benchmark(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass\n" * 500)
    idx = {"entries": [{"id": "auth", "title": "Auth", "body": "login flow summary", "tags": [], "category": "core"}]}
    (tmp_path / "search-index.json").write_text(json.dumps(idx))
    result = run_benchmark("login", source_dirs=[src], wiki_dir=tmp_path)
    assert result["raw_tokens"] > result["wiki_tokens"]
    assert result["savings_pct"] > 0
    assert result["savings_tokens"] > 0


def test_format_benchmark_report():
    result = {
        "query": "login", "raw_tokens": 10000, "raw_files": 5,
        "wiki_tokens": 200, "wiki_pages": 3,
        "savings_tokens": 9800, "savings_pct": 98.0, "cost_saved_per_query": 0.049,
    }
    report = format_benchmark_report(result)
    assert "98.0%" in report
    assert "10,000" in report
    assert "login" in report
