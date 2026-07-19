"""Phase 2 data-correctness tests: pruning, slug collisions, atomic DB swap."""

import sqlite3
from pathlib import Path

from llmwiki.config import create_default_config, save_config
from llmwiki.ingest import ingest_all, ingest_source
from llmwiki.build import build_site
from llmwiki.graph import _load_pages
from llmwiki.adapters.base import make_slug, _sanitize_slug_segment
from llmwiki.search import create_search_db, insert_page, delete_pages_not_in, get_page


def _sanitize_category(category: str) -> str:
    return "/".join(_sanitize_slug_segment(s) for s in category.split("/") if s)


def _mini_project(tmp_path):
    """A small nested project: two source files plus a doc."""
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
    for d in ("raw", "wiki", "site"):
        (work / d).mkdir()
    return work


class TestPruneDeleted:
    def test_deleted_source_pruned_end_to_end(self, tmp_path):
        project = _mini_project(tmp_path)
        work = _work(tmp_path)
        config = create_default_config("Mini", str(project))
        cfg_path = work / "llmwiki.json"
        save_config(config, cfg_path)
        state_path = work / ".llmwiki-state.json"

        ingest_all(config, work / "raw", state_path)
        build_site(work, config, full=True)

        # Locate the billing page id + raw file before deletion.
        pages = _load_pages(work / "raw")
        billing_ids = [pid for pid in pages if pid.endswith("billing")]
        assert billing_ids, f"billing page missing: {list(pages)}"
        billing_id = billing_ids[0]

        db_path = work / "site" / "llmwiki.db"
        assert get_page(db_path, billing_id) is not None
        idx_before = (work / "site" / "search-index.json").read_text(encoding="utf-8")
        assert "billing" in idx_before
        billing_raw = [p for p in (work / "raw").rglob("*.md")
                       if "billing" in p.stem]
        assert billing_raw

        # Delete the source, re-ingest + rebuild.
        (project / "src" / "billing.py").unlink()
        result = ingest_all(config, work / "raw", state_path)
        assert result["total_removed"] == 1, result
        build_site(work, config, full=True)

        # Gone from raw/, DB, and search index.
        assert not any("billing" in p.stem
                       for p in (work / "raw").rglob("*.md"))
        assert get_page(db_path, billing_id) is None
        idx_after = (work / "site" / "search-index.json").read_text(encoding="utf-8")
        assert billing_id not in idx_after

    def test_renamed_source_swaps_id(self, tmp_path):
        project = _mini_project(tmp_path)
        work = _work(tmp_path)
        config = create_default_config("Mini", str(project))
        state_path = work / ".llmwiki-state.json"

        ingest_all(config, work / "raw", state_path)
        build_site(work, config, full=True)
        db_path = work / "site" / "llmwiki.db"

        pages = _load_pages(work / "raw")
        old_id = next(pid for pid in pages if pid.endswith("auth"))
        assert get_page(db_path, old_id) is not None

        # Rename auth.py → identity.py
        (project / "src" / "auth.py").rename(project / "src" / "identity.py")
        result = ingest_all(config, work / "raw", state_path)
        assert result["total_removed"] == 1, result
        build_site(work, config, full=True)

        pages = _load_pages(work / "raw")
        new_id = next(pid for pid in pages if pid.endswith("identity"))
        assert get_page(db_path, new_id) is not None
        assert get_page(db_path, old_id) is None

    def test_adapter_filtered_run_does_not_prune(self, tmp_path):
        """A --adapter-filtered ingest_source run must never prune: it only
        sees a subset of files, so absent recorded files are not deletions."""
        project = _mini_project(tmp_path)
        work = _work(tmp_path)
        config = create_default_config("Mini", str(project))
        state_path = work / ".llmwiki-state.json"

        ingest_all(config, work / "raw", state_path)
        before = len(list((work / "raw").rglob("*.md")))

        # Delete a source, then run only the markdown adapter over the source.
        (project / "src" / "billing.py").unlink()
        ingest_source(project, work / "raw", state_path, dict(config["sources"][0]),
                      adapter_name="markdown")

        # billing raw page must still be present (no pruning on filtered run).
        assert any("billing" in p.stem for p in (work / "raw").rglob("*.md"))
        assert len(list((work / "raw").rglob("*.md"))) == before

    def test_legacy_db_ghost_row_healed(self, tmp_path):
        project = _mini_project(tmp_path)
        work = _work(tmp_path)
        config = create_default_config("Mini", str(project))
        state_path = work / ".llmwiki-state.json"

        ingest_all(config, work / "raw", state_path)
        build_site(work, config, full=True)
        db_path = work / "site" / "llmwiki.db"

        # Inject a bogus row directly (simulating a legacy/pre-existing ghost).
        insert_page(db_path, {
            "id": "ghost/orphan", "title": "Ghost",
            "body_plain": "stale", "tags": "[]",
        })
        assert get_page(db_path, "ghost/orphan") is not None

        build_site(work, config, full=True)
        assert get_page(db_path, "ghost/orphan") is None


class TestSlugCollision:
    def test_same_stem_same_category_both_preserved(self, tmp_path):
        """Two Utils.java files sharing a Java package (identical category) and
        stem → both pages exist, distinct ids, both raw files + contents
        preserved. Previously one silently overwrote the other."""
        project = tmp_path / "project"
        (project / "a").mkdir(parents=True)
        (project / "b").mkdir(parents=True)
        (project / "a" / "Utils.java").write_text(
            "package com.foo;\n\n/** A. */\npublic class Utils { int AAA = 1; }\n"
        )
        (project / "b" / "Utils.java").write_text(
            "package com.foo;\n\n/** B. */\npublic class Utils { int BBB = 2; }\n"
        )

        work = _work(tmp_path)
        config = create_default_config("Coll", str(project))
        state_path = work / ".llmwiki-state.json"
        ingest_all(config, work / "raw", state_path)

        pages = _load_pages(work / "raw")
        utils_ids = [pid for pid in pages if pid.endswith("utils")]
        # Same category com/foo, distinct path-aware ids.
        assert len(utils_ids) == 2, f"expected 2 distinct ids, got {utils_ids}"
        assert len(set(utils_ids)) == 2
        assert all(pages[pid]["category"] == "com/foo" for pid in utils_ids)

        # Both raw files exist (second was disambiguated to avoid overwrite).
        raw_utils = list((work / "raw" / "com" / "foo").glob("utils*.md"))
        assert len(raw_utils) == 2, [p.name for p in raw_utils]

        # Both contents survived (no silent overwrite).
        bodies = "\n".join(pages[pid]["body"] for pid in utils_ids)
        assert "AAA" in bodies
        assert "BBB" in bodies

    def test_flat_project_keeps_stem_only_slug(self, tmp_path):
        """A file directly at the source root keeps its historical stem-only
        slug (relative portion == stem, no directory context)."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "auth.py").write_text('"""Auth."""\n\n\ndef go():\n    return 1\n')

        work = _work(tmp_path)
        config = create_default_config("Flat", str(project))
        state_path = work / ".llmwiki-state.json"
        ingest_all(config, work / "raw", state_path)

        pages = _load_pages(work / "raw")
        src_pages = [pid for pid in pages if pages[pid]["language"] == "python"]
        assert len(src_pages) == 1, src_pages
        pid = src_pages[0]
        # Exact id: <sanitized category>/auth — stem-only relative segment,
        # identical to pre-change behaviour for root-level files.
        expected = f"{_sanitize_category(pages[pid]['category'])}/auth"
        assert pid == expected, f"expected {expected!r}, got {pid!r}"


class TestMakeSlug:
    """Direct, exact assertions for the shared slug helper."""

    def test_root_file_is_stem_only(self):
        root = Path("/proj")
        assert make_slug(root / "auth.py", root, "python") == "python/auth"

    def test_nested_files_gain_path_context(self):
        root = Path("/proj")
        assert make_slug(root / "a" / "utils.py", root, "python") == "python/a/utils"
        assert make_slug(root / "b" / "utils.py", root, "python") == "python/b/utils"
        assert (make_slug(root / "src" / "billing" / "utils.py", root, "svc")
                == "svc/src/billing/utils")

    def test_no_source_root_falls_back_to_stem(self):
        # Historical behaviour when adapters are called via direct extract().
        assert make_slug(Path("/proj/a/auth.py"), None, "python") == "python/auth"

    def test_root_file_matches_fallback(self):
        # Stability guarantee: a root-level file with a source root produces
        # exactly what the historical stem-only path produced.
        root = Path("/proj")
        assert (make_slug(root / "auth.py", root, "python")
                == make_slug(root / "auth.py", None, "python"))


class TestAtomicSwap:
    def test_swap_while_reader_holds_old_db(self, tmp_path):
        """Build succeeds while another connection holds the old DB open, and
        no llmwiki.db.tmp is left behind (POSIX)."""
        project = _mini_project(tmp_path)
        work = _work(tmp_path)
        config = create_default_config("Mini", str(project))
        state_path = work / ".llmwiki-state.json"
        ingest_all(config, work / "raw", state_path)
        build_site(work, config, full=True)

        db_path = work / "site" / "llmwiki.db"
        tmp_path_db = db_path.with_name(db_path.name + ".tmp")

        # Hold the old DB open across the rebuild.
        reader = sqlite3.connect(str(db_path))
        reader.execute("SELECT count(*) FROM pages").fetchone()
        try:
            build_site(work, config, full=True)
        finally:
            reader.close()

        assert db_path.exists()
        assert not tmp_path_db.exists(), "temp DB should be gone after swap"
        # Fresh DB is queryable.
        conn = sqlite3.connect(str(db_path))
        assert conn.execute("SELECT count(*) FROM pages").fetchone()[0] > 0
        conn.close()


class TestDeletePagesNotIn:
    def test_chunked_delete_removes_only_stale(self, tmp_path):
        db_path = tmp_path / "t.db"
        create_search_db(db_path)
        for i in range(1200):
            insert_page(db_path, {
                "id": f"p/{i}", "title": f"P{i}",
                "body_plain": "x", "tags": "[]",
            })
        keep = {f"p/{i}" for i in range(600)}
        removed = delete_pages_not_in(db_path, keep)
        assert removed == 600
        conn = sqlite3.connect(str(db_path))
        remaining = conn.execute("SELECT count(*) FROM pages").fetchone()[0]
        conn.close()
        assert remaining == 600
