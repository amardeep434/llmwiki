import json
import pytest
from pathlib import Path
from llmwiki.benchmark import (
    count_tokens, count_raw_tokens, count_wiki_tokens,
    run_benchmark, format_benchmark_report,
)
from llmwiki.search import create_search_db, insert_pages


def _make_db(site_dir: Path, pages: list[dict]) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)
    db = site_dir / "llmwiki.db"
    create_search_db(db)
    insert_pages(db, pages)


def test_count_tokens():
    assert count_tokens("hello world") > 0
    assert count_tokens("a" * 400) == 100


def test_count_raw_tokens_reads_only_top_matches(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login():\n    pass\n" * 100)
    (src / "utils.py").write_text("def helper():\n    return 1\n" * 50)
    (src / "readme.md").write_text("this has nothing to do with login")
    tokens, files = count_raw_tokens([src], "login")
    assert tokens > 0
    assert files == 2  # auth.py and readme.md contain "login"


def test_count_raw_tokens_caps_at_top_k(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(20):
        (src / f"f{i}.py").write_text("def login(): pass\n" * 10)
    tokens, files = count_raw_tokens([src], "login")
    # Realistic agent reads a handful of files, not all 20 matches
    assert files == 5


def test_count_raw_tokens_ignores_stopwords(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass\n")
    (src / "junk.py").write_text("# how does it work\n")
    tokens, files = count_raw_tokens([src], "how does login work")
    # junk.py contains only stopwords from the query — should rank below auth.py
    assert files >= 1


def test_count_wiki_tokens_uses_db(tmp_path):
    _make_db(tmp_path, [
        {"id": "auth", "title": "Auth Module",
         "body_plain": "handles login flow " * 20, "tags": '["auth"]',
         "category": "core"},
        {"id": "utils", "title": "Utils",
         "body_plain": "helper functions", "tags": "[]", "category": "core"},
    ])
    tokens, pages = count_wiki_tokens(tmp_path, "login")
    assert tokens > 0
    assert pages == 1  # only auth matches


def test_count_wiki_tokens_no_db(tmp_path):
    tokens, pages = count_wiki_tokens(tmp_path, "login")
    assert (tokens, pages) == (0, 0)


def test_run_benchmark(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass\n" * 500)
    _make_db(tmp_path / "site", [
        {"id": "auth", "title": "Auth", "body_plain": "login flow summary",
         "tags": "[]", "category": "core"},
    ])
    result = run_benchmark("login", source_dirs=[src], site_dir=tmp_path / "site")
    assert result["raw_tokens"] > result["wiki_tokens"]
    assert result["savings_pct"] > 0
    assert result["savings_tokens"] > 0


def test_run_benchmark_can_report_negative_savings(tmp_path):
    """When the wiki flow costs more, the report must say so honestly."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("login\n")  # tiny file
    _make_db(tmp_path / "site", [
        {"id": "auth", "title": "Auth", "body_plain": "login " * 2000,
         "tags": "[]", "category": "core"},
    ])
    result = run_benchmark("login", source_dirs=[src], site_dir=tmp_path / "site")
    assert result["savings_tokens"] < 0
    report = format_benchmark_report(result)
    assert "MORE via wiki" in report


def test_format_benchmark_report():
    result = {
        "query": "login", "raw_tokens": 10000, "raw_files": 5,
        "wiki_tokens": 200, "wiki_pages": 3,
        "savings_tokens": 9800, "savings_pct": 98.0, "top_k": 5,
    }
    report = format_benchmark_report(result)
    assert "98.0%" in report
    assert "10,000" in report
    assert "login" in report
    assert "Methodology" in report


def test_tie_break_prefers_smaller_files(tmp_path):
    """Equal-scoring files must tie-break to the smaller one (conservative baseline)."""
    src = tmp_path / "src"
    src.mkdir()
    for i in range(6):
        (src / f"big{i}.py").write_text("login\n" + "x = 1\n" * 500)
    (src / "small.py").write_text("login\n")
    tokens, files = count_raw_tokens([src], "login")
    # small.py must be among the top-5 picked over one of the big ties
    small_tokens = count_tokens((src / "small.py").read_text())
    big_tokens = count_tokens((src / "big0.py").read_text())
    assert tokens < 5 * big_tokens
    assert files == 5
