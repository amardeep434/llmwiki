"""Index freshness checks — detect when the wiki lags the source tree.

A stale index silently feeding agents outdated answers is worse than no
index: the agent acts on wrong context and pays extra tokens recovering.
Every query surface (CLI search/get, MCP tools) calls check_freshness()
and prepends a warning when the source tree has drifted since the last
ingest. The check is stat-based (mtime + size) with a hash confirmation
only for files whose stat changed, so it stays cheap on large repos.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from llmwiki.state import BuildState

MAX_EXAMPLES = 5


def check_freshness(config: dict, state_path: Path) -> dict:
    """Compare recorded ingest state against the current source tree.

    Returns a dict:
        stale (bool), never_built (bool),
        modified / deleted / new (int counts),
        examples (list[str] of changed paths, capped).
    """
    if not state_path.exists():
        return _result(never_built=True)

    state = BuildState(state_path)
    if not state.files:
        return _result(never_built=True)

    current = _discover_current_files(config)
    recorded = set(state.files.keys())

    new_files = sorted(current - recorded)
    deleted = sorted(recorded - current)

    modified: list[str] = []
    for src in recorded & current:
        meta = state.files[src]
        p = Path(src)
        try:
            st = p.stat()
        except OSError:
            continue
        rec_mtime = meta.get("mtime")
        rec_size = meta.get("size")
        if rec_mtime is not None and rec_size is not None:
            if int(st.st_mtime) == int(rec_mtime) and st.st_size == rec_size:
                continue
        # stat changed (or old state without stat info) — confirm by hash
        try:
            content = p.read_bytes()
        except OSError:
            continue
        if hashlib.sha256(content).hexdigest()[:16] != meta.get("content_hash"):
            modified.append(src)

    examples = (modified + new_files + deleted)[:MAX_EXAMPLES]
    return _result(
        modified=len(modified),
        new=len(new_files),
        deleted=len(deleted),
        examples=examples,
    )


def format_freshness_warning(freshness: dict) -> str:
    """One-line warning for CLI/MCP output, or empty string when fresh."""
    if freshness.get("never_built"):
        return "⚠ llmwiki index has never been built — run `llmwiki all` first."
    if not freshness.get("stale"):
        return ""
    parts = []
    for key in ("modified", "new", "deleted"):
        if freshness.get(key):
            parts.append(f"{freshness[key]} {key}")
    detail = ", ".join(parts)
    return (
        f"⚠ llmwiki index is STALE ({detail} source files since last ingest) — "
        "results may not reflect current code. Run `llmwiki all` to refresh, "
        "or read the changed files directly."
    )


def _discover_current_files(config: dict) -> set[str]:
    """Discover the set of source files the adapters would ingest today."""
    from llmwiki.adapters import _ensure_all_loaded, _REGISTRY

    _ensure_all_loaded()
    found: set[str] = set()

    for source in config.get("sources", []):
        src_path = Path(source["path"])
        if not src_path.exists():
            continue
        exclude = source.get("exclude", [])
        for adapter_cls in _REGISTRY.values():
            adapter = adapter_cls()
            for f in adapter.discover(src_path, exclude=exclude):
                found.add(str(f))

    for pdf_source in config.get("pdf_sources", []):
        src_path = Path(pdf_source.get("path", ""))
        if src_path.is_file():
            found.add(str(src_path))
        elif src_path.is_dir():
            for f in src_path.rglob("*.pdf"):
                found.add(str(f))

    return found


def _result(modified: int = 0, new: int = 0, deleted: int = 0,
            never_built: bool = False, examples: list[str] | None = None) -> dict:
    return {
        "stale": bool(modified or new or deleted),
        "never_built": never_built,
        "modified": modified,
        "new": new,
        "deleted": deleted,
        "examples": examples or [],
    }
