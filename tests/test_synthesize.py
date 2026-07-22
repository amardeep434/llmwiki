"""Tests for the Phase S synthesis layer (curated pages + work orders)."""

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from llmwiki.config import create_default_config, save_config
from llmwiki.ingest import ingest_all
from llmwiki.build import build_site
from llmwiki.graph import _load_curated_pages, build_graph
from llmwiki.lint import lint_wiki
from llmwiki.search import get_page, format_results_agent, search_pages
from llmwiki.synthesize import (
    SCHEMA_MD, compute_work_list, is_curated_stale, build_source_mtime_map,
    TODO_FILENAME,
)
from llmwiki.freshness import check_freshness


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_curated(curated_dir: Path, rel: str, *, title="T", type_="concept",
                   sources=None, synthesized_at="2026-07-20T10:00:00Z",
                   tags=None, body="Body.\n"):
    path = curated_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = ["---", f'title: "{title}"']
    if type_ is not None:
        fm.append(f"type: {type_}")
    if sources is not None:
        fm.append(f"sources: [{', '.join(sources)}]")
    if synthesized_at is not None:
        fm.append(f"synthesized_at: {synthesized_at}")
    if tags is not None:
        fm.append(f"tags: [{', '.join(tags)}]")
    fm.append("---")
    path.write_text("\n".join(fm) + "\n\n" + body, encoding="utf-8")
    return path


def _mini_project(tmp_path):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "auth.py").write_text(
        '"""Auth module."""\n\n\ndef login(user):\n    return user\n'
    )
    (project / "src" / "billing.py").write_text(
        '"""Billing module."""\n\n\ndef charge(amount):\n    return amount\n'
    )
    (project / "README.md").write_text("# Mini Project\n\nDocs.\n")
    return project


def _work(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    for d in ("raw", "wiki", "site", "curated"):
        (work / d).mkdir()
    return work


# ---------------------------------------------------------------------------
# Curated loading
# ---------------------------------------------------------------------------


class TestCuratedLoading:
    def test_slug_category_flag_and_sources_list(self, tmp_path):
        cur = tmp_path / "curated"
        _write_curated(cur, "notes/flow.md", type_="concept",
                       sources=["rule/core/x", "application/core/y"])
        pages = _load_curated_pages(cur)
        assert "curated/notes/flow" in pages
        p = pages["curated/notes/flow"]
        assert p["category"] == "curated/concept"
        assert p["curated"] is True
        assert p["sources"] == ["rule/core/x", "application/core/y"]

    def test_sources_string_form(self, tmp_path):
        cur = tmp_path / "curated"
        # String "[a, b]" form (as _parse_frontmatter yields for inline lists).
        path = cur / "notes" / "s.md"
        path.parent.mkdir(parents=True)
        path.write_text(
            '---\ntitle: "S"\ntype: note\nsources: [a/b, c/d]\n---\n\nBody\n',
            encoding="utf-8")
        pages = _load_curated_pages(cur)
        assert pages["curated/notes/s"]["sources"] == ["a/b", "c/d"]

    def test_type_defaults_to_note(self, tmp_path):
        cur = tmp_path / "curated"
        _write_curated(cur, "x.md", type_=None)
        _write_curated(cur, "y.md", type_="bogus")
        pages = _load_curated_pages(cur)
        assert pages["curated/x"]["category"] == "curated/note"
        assert pages["curated/y"]["category"] == "curated/note"
        # Raw type preserved for lint.
        assert pages["curated/x"]["type"] == ""
        assert pages["curated/y"]["type"] == "bogus"


# ---------------------------------------------------------------------------
# Build integration
# ---------------------------------------------------------------------------


class TestBuildIntegration:
    def _build_with_curated(self, tmp_path):
        project = _mini_project(tmp_path)
        work = _work(tmp_path)
        config = create_default_config("Mini", str(project))
        save_config(config, work / "llmwiki.json")
        state_path = work / ".llmwiki-state.json"
        ingest_all(config, work / "raw", state_path)
        build_site(work, config, full=True)

        # Pick a real extracted page id to cite.
        from llmwiki.graph import _load_pages
        pages = _load_pages(work / "raw")
        auth_id = next(pid for pid in pages if pid.endswith("auth"))

        _write_curated(work / "curated", "notes/authflow.md", title="Auth Flow",
                       type_="concept", sources=[auth_id])
        build_site(work, config, full=True)
        return work, auth_id

    def test_curated_page_in_db_with_importance_floor(self, tmp_path):
        work, _ = self._build_with_curated(tmp_path)
        db_path = work / "site" / "llmwiki.db"
        page = get_page(db_path, "curated/notes/authflow")
        assert page is not None
        assert page["importance_score"] >= 0.5
        assert page["category"] == "curated/concept"

    def test_cites_edge_in_crossrefs(self, tmp_path):
        work, auth_id = self._build_with_curated(tmp_path)
        xref = json.loads((work / "site" / "cross-references.json").read_text())
        cites = [e for e in xref["edges"]
                 if e["from"] == "curated/notes/authflow" and e["type"] == "cites"]
        assert cites, xref["edges"]
        assert any(e["to"] == auth_id for e in cites)

    def test_curated_marker_in_agent_output(self, tmp_path):
        results = [{"id": "curated/notes/x", "title": "X",
                    "category": "curated/concept"}]
        out = format_results_agent(results)
        assert "[curated]" in out

    def test_survives_delete_pages_not_in(self, tmp_path):
        work, _ = self._build_with_curated(tmp_path)
        db_path = work / "site" / "llmwiki.db"
        # A second rebuild runs delete_pages_not_in; curated id must persist.
        config = create_default_config("Mini", str(_mini_project(tmp_path / "again")))
        # Rebuild with same work dir/config already saved.
        from llmwiki.config import load_config
        cfg = load_config(work / "llmwiki.json")
        build_site(work, cfg, full=True)
        assert get_page(db_path, "curated/notes/authflow") is not None


# ---------------------------------------------------------------------------
# Freshness ignores curated
# ---------------------------------------------------------------------------


def test_freshness_ignores_curated(tmp_path):
    project = _mini_project(tmp_path)
    work = _work(tmp_path)
    config = create_default_config("Mini", str(project))
    save_config(config, work / "llmwiki.json")
    state_path = work / ".llmwiki-state.json"
    ingest_all(config, work / "raw", state_path)

    # Fresh right after ingest.
    assert not check_freshness(config, state_path)["stale"]

    # Adding a curated page under the wiki root must not make the index stale:
    # curated/ is not a configured source.
    _write_curated(work / "curated", "notes/n.md", sources=["x/y"])
    result = check_freshness(config, state_path)
    assert not result["stale"]


# ---------------------------------------------------------------------------
# SCHEMA.md init behaviour
# ---------------------------------------------------------------------------


class TestSchemaInit:
    def test_init_writes_schema(self, tmp_path):
        source = tmp_path / "src"
        source.mkdir()
        (source / "a.py").write_text("x = 1\n")
        out = tmp_path / "out"
        result = subprocess.run(
            [sys.executable, "-m", "llmwiki", "init",
             "--source", str(source), "--output", str(out), "--yes"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        assert result.returncode == 0, result.stderr
        schema = out / "SCHEMA.md"
        assert schema.exists()
        assert "Curated Knowledge Conventions" in schema.read_text()
        assert (out / "curated").is_dir()

    def test_second_init_preserves_edited_schema(self, tmp_path):
        source = tmp_path / "src"
        source.mkdir()
        (source / "a.py").write_text("x = 1\n")
        out = tmp_path / "out"
        base = [sys.executable, "-m", "llmwiki", "init",
                "--source", str(source), "--output", str(out), "--yes"]
        subprocess.run(base, capture_output=True, text=True)
        edited = "# My edits\n"
        (out / "SCHEMA.md").write_text(edited, encoding="utf-8")
        subprocess.run(base, capture_output=True, text=True)
        assert (out / "SCHEMA.md").read_text(encoding="utf-8") == edited

    def test_schema_md_constant_has_key_conventions(self):
        assert "type:" in SCHEMA_MD
        assert "sources:" in SCHEMA_MD
        assert "150" in SCHEMA_MD
        assert "[[page-id]]" in SCHEMA_MD
        assert "CONTRADICTION:" in SCHEMA_MD


# ---------------------------------------------------------------------------
# compute_work_list
# ---------------------------------------------------------------------------


class TestWorkList:
    def _built(self, tmp_path):
        project = _mini_project(tmp_path)
        work = _work(tmp_path)
        config = create_default_config("Mini", str(project))
        save_config(config, work / "llmwiki.json")
        ingest_all(config, work / "raw", work / ".llmwiki-state.json")
        build_site(work, config, full=True)
        return work, config

    def test_uncovered_page_yields_create_item(self, tmp_path):
        work, config = self._built(tmp_path)
        items = compute_work_list(work, config)
        assert items
        assert all(i["kind"] == "create" for i in items)
        assert all(i["target"].startswith("curated/") for i in items)

    def test_covered_fresh_page_absent(self, tmp_path):
        work, config = self._built(tmp_path)
        from llmwiki.graph import _load_pages
        auth_id = next(pid for pid in _load_pages(work / "raw") if pid.endswith("auth"))
        # Cover it with a fresh curated page (future timestamp).
        _write_curated(work / "curated", "notes/a.md", sources=[auth_id],
                       synthesized_at="2099-01-01T00:00:00Z")
        build_site(work, config, full=True)
        items = compute_work_list(work, config)
        # auth_id must not appear as a create target anymore.
        assert not any(auth_id in i["sources"] for i in items if i["kind"] == "create")

    def test_stale_source_yields_refresh_first(self, tmp_path):
        work, config = self._built(tmp_path)
        from llmwiki.graph import _load_pages
        auth_id = next(pid for pid in _load_pages(work / "raw") if pid.endswith("auth"))
        # Curated page synthesized in the past.
        _write_curated(work / "curated", "notes/a.md", sources=[auth_id],
                       synthesized_at="2000-01-01T00:00:00Z")
        build_site(work, config, full=True)
        # Touch the cited raw file forward so it is newer than synthesis.
        raw_file = next(p for p in (work / "raw").rglob("*.md")
                        if p.stem.endswith("auth"))
        future = raw_file.stat().st_mtime + 10_000
        os.utime(raw_file, (future, future))

        items = compute_work_list(work, config)
        assert items[0]["kind"] == "refresh"
        assert items[0]["target"] == "curated/notes/a.md"

    def test_budget_respected(self, tmp_path):
        work, config = self._built(tmp_path)
        items = compute_work_list(work, config, budget=1)
        assert len(items) <= 1

    def test_negative_budget_yields_empty(self, tmp_path):
        # Copilot PR#4 review: [:budget] with a negative value dropped items
        # from the end instead of capping. --budget -1 must mean "none".
        work, config = self._built(tmp_path)
        assert compute_work_list(work, config, budget=-1) == []

    def test_staleness_is_case_insensitive(self, tmp_path):
        # Copilot PR#5 review: coverage was case-insensitive but the staleness
        # helpers were not — a citation with different casing would never
        # produce a refresh item even when the cited source changed.
        work, config = self._built(tmp_path)
        from llmwiki.graph import _load_pages
        auth_id = next(pid for pid in _load_pages(work / "raw") if pid.endswith("auth"))
        _write_curated(work / "curated", "notes/a.md", sources=[auth_id.upper()],
                       synthesized_at="2000-01-01T00:00:00Z")
        build_site(work, config, full=True)
        raw_file = next(p for p in (work / "raw").rglob("*.md")
                        if p.stem.endswith("auth"))
        future = raw_file.stat().st_mtime + 10_000
        os.utime(raw_file, (future, future))
        items = compute_work_list(work, config)
        assert items and items[0]["kind"] == "refresh"
        assert items[0]["target"] == "curated/notes/a.md"

    def test_coverage_is_case_insensitive(self, tmp_path):
        # Copilot PR#4 review: a citation with different casing must still
        # count as coverage (ids are case-insensitive elsewhere).
        work, config = self._built(tmp_path)
        from llmwiki.graph import _load_pages
        auth_id = next(pid for pid in _load_pages(work / "raw") if pid.endswith("auth"))
        _write_curated(work / "curated", "notes/a.md", sources=[auth_id.upper()],
                       synthesized_at="2099-01-01T00:00:00Z")
        build_site(work, config, full=True)
        items = compute_work_list(work, config)
        assert not any(auth_id.lower() in [s.lower() for s in i["sources"]]
                       for i in items if i["kind"] == "create")

    def test_json_shape(self, tmp_path):
        work, config = self._built(tmp_path)
        items = compute_work_list(work, config)
        for it in items:
            assert set(it.keys()) == {"kind", "target", "sources", "reason"}
            assert isinstance(it["sources"], list)

    def test_empty_case_removes_stale_todo(self, tmp_path):
        # No sources, no cross-references → empty list; CLI must remove todo.
        source = tmp_path / "src"
        source.mkdir()
        (source / "a.py").write_text("x = 1\n")
        out = tmp_path / "out"
        subprocess.run(
            [sys.executable, "-m", "llmwiki", "init", "--source", str(source),
             "--output", str(out), "--yes"], capture_output=True, text=True)
        # Cover everything so nothing is left to synthesize: easiest is to leave
        # site unbuilt (no cross-references.json) and no curated pages → empty.
        todo = out / TODO_FILENAME
        todo.write_text("stale", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "llmwiki", "synthesize",
             "--config", str(out / "llmwiki.json")],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert "nothing needs synthesis" in result.stdout
        assert not todo.exists()


# ---------------------------------------------------------------------------
# Lint rules
# ---------------------------------------------------------------------------


class TestCuratedLint:
    def _graph(self, work, config):
        return build_graph(work / "raw", config, curated_dir=work / "curated")

    def test_uncited(self, tmp_path):
        work = _work(tmp_path)
        config = create_default_config("Mini", str(_mini_project(tmp_path)))
        _write_curated(work / "curated", "notes/u.md", sources=None)
        graph = self._graph(work, config)
        issues = lint_wiki(work / "raw", graph, curated_dir=work / "curated")
        assert any(i["rule"] == "uncited" for i in issues)

    def test_bad_source(self, tmp_path):
        work = _work(tmp_path)
        config = create_default_config("Mini", str(_mini_project(tmp_path)))
        _write_curated(work / "curated", "notes/b.md",
                       sources=["does/not/exist"])
        graph = self._graph(work, config)
        issues = lint_wiki(work / "raw", graph, curated_dir=work / "curated")
        bad = [i for i in issues if i["rule"] == "bad-source"]
        assert bad and bad[0]["severity"] == "error"

    def test_missing_type(self, tmp_path):
        work = _work(tmp_path)
        config = create_default_config("Mini", str(_mini_project(tmp_path)))
        _write_curated(work / "curated", "notes/m.md", type_="bogus",
                       sources=["x/y"])
        graph = self._graph(work, config)
        issues = lint_wiki(work / "raw", graph, curated_dir=work / "curated")
        assert any(i["rule"] == "missing-type" for i in issues)

    def test_stale_claim(self, tmp_path):
        project = _mini_project(tmp_path)
        work = _work(tmp_path)
        config = create_default_config("Mini", str(project))
        save_config(config, work / "llmwiki.json")
        ingest_all(config, work / "raw", work / ".llmwiki-state.json")
        from llmwiki.graph import _load_pages
        auth_id = next(pid for pid in _load_pages(work / "raw") if pid.endswith("auth"))
        _write_curated(work / "curated", "notes/s.md", sources=[auth_id],
                       synthesized_at="2000-01-01T00:00:00Z")
        raw_file = next(p for p in (work / "raw").rglob("*.md")
                        if p.stem.endswith("auth"))
        future = raw_file.stat().st_mtime + 10_000
        os.utime(raw_file, (future, future))
        graph = self._graph(work, config)
        issues = lint_wiki(work / "raw", graph, curated_dir=work / "curated")
        stale = [i for i in issues if i["rule"] == "stale-claim"]
        assert stale and stale[0]["severity"] == "error"


# ---------------------------------------------------------------------------
# End-to-end
# ---------------------------------------------------------------------------


def test_e2e_synthesis_loop(tmp_path):
    """init → ingest → build → write curated → build → [curated] in search →
    touch source → synthesize lists refresh AND lint flags stale-claim."""
    project = _mini_project(tmp_path)
    work = _work(tmp_path)
    config = create_default_config("Mini", str(project))
    save_config(config, work / "llmwiki.json")
    state_path = work / ".llmwiki-state.json"
    ingest_all(config, work / "raw", state_path)
    build_site(work, config, full=True)

    from llmwiki.graph import _load_pages
    auth_id = next(pid for pid in _load_pages(work / "raw") if pid.endswith("auth"))

    _write_curated(work / "curated", "notes/authflow.md", title="Auth Flow",
                   type_="concept", sources=[auth_id], tags=["auth"],
                   synthesized_at="2000-01-01T00:00:00Z",
                   body="How auth flows. See [[%s]].\n" % auth_id)
    build_site(work, config, full=True)

    # Agent search surfaces the [curated] marker.
    db_path = work / "site" / "llmwiki.db"
    results = search_pages(db_path, "auth flow")
    assert any(r["id"] == "curated/notes/authflow" for r in results)
    marked = format_results_agent(results)
    assert "[curated]" in marked

    # Touch the cited source's raw file mtime forward.
    raw_file = next(p for p in (work / "raw").rglob("*.md")
                    if p.stem.endswith("auth"))
    future = raw_file.stat().st_mtime + 10_000
    os.utime(raw_file, (future, future))

    # synthesize lists a refresh item for the curated page.
    items = compute_work_list(work, config)
    refresh = [i for i in items if i["kind"] == "refresh"]
    assert refresh and refresh[0]["target"] == "curated/notes/authflow.md"

    # lint flags stale-claim.
    graph = build_graph(work / "raw", config, curated_dir=work / "curated")
    issues = lint_wiki(work / "raw", graph, curated_dir=work / "curated")
    assert any(i["rule"] == "stale-claim" for i in issues)
