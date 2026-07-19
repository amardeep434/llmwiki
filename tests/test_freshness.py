"""Tests for index freshness detection."""

import json
import time
from pathlib import Path

import pytest

from llmwiki.freshness import check_freshness, format_freshness_warning
from llmwiki.state import BuildState


@pytest.fixture
def project(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass\n")
    (src / "utils.py").write_text("def helper(): pass\n")
    config = {"sources": [{"path": str(src), "exclude": []}], "pdf_sources": []}
    state_path = tmp_path / ".llmwiki-state.json"
    return {"src": src, "config": config, "state_path": state_path}


def _ingest_state(project):
    """Record current files in state, like ingest does."""
    import hashlib
    state = BuildState(project["state_path"])
    for f in sorted(project["src"].iterdir()):
        h = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
        state.record_file(str(f), h, "raw/x.md")
    state.save()


def test_never_built(project):
    result = check_freshness(project["config"], project["state_path"])
    assert result["never_built"]
    assert "never been built" in format_freshness_warning(result)


def test_fresh_after_ingest(project):
    _ingest_state(project)
    result = check_freshness(project["config"], project["state_path"])
    assert not result["stale"]
    assert format_freshness_warning(result) == ""


def test_modified_file_detected(project):
    _ingest_state(project)
    # Ensure mtime tick + content change
    (project["src"] / "auth.py").write_text("def login(): return 42\n")
    result = check_freshness(project["config"], project["state_path"])
    assert result["stale"]
    assert result["modified"] == 1
    warning = format_freshness_warning(result)
    assert "STALE" in warning


def test_touched_but_unchanged_file_is_fresh(project):
    """mtime change with identical content must not report stale (hash confirms)."""
    _ingest_state(project)
    f = project["src"] / "auth.py"
    content = f.read_text(encoding="utf-8")
    future = time.time() + 100
    f.write_text(content)
    import os
    os.utime(f, (future, future))
    result = check_freshness(project["config"], project["state_path"])
    assert result["modified"] == 0


def test_new_file_detected(project):
    _ingest_state(project)
    (project["src"] / "new_module.py").write_text("def fresh(): pass\n")
    result = check_freshness(project["config"], project["state_path"])
    assert result["stale"]
    assert result["new"] == 1


def test_deleted_file_detected(project):
    _ingest_state(project)
    (project["src"] / "utils.py").unlink()
    result = check_freshness(project["config"], project["state_path"])
    assert result["stale"]
    assert result["deleted"] == 1


def test_state_records_mtime_and_size(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("x = 1\n")
    state = BuildState(tmp_path / "state.json")
    state.record_file(str(f), "abc", "raw/a.md")
    entry = state.files[str(f)]
    assert "mtime" in entry
    assert entry["size"] == f.stat().st_size


def test_same_second_same_size_change_detected(project):
    """A same-size edit must be caught even if mtime seconds are equal (hash confirms)."""
    _ingest_state(project)
    f = project["src"] / "auth.py"
    state_mtime = __import__("json").loads(
        project["state_path"].read_text(encoding="utf-8")
    )["files"][str(f)]["mtime"]
    # Same byte length, different content; force recorded whole-second mtime
    f.write_text("def login(): res2\n")
    import os
    os.utime(f, (int(state_mtime), int(state_mtime)))
    result = check_freshness(project["config"], project["state_path"])
    assert result["modified"] == 1
