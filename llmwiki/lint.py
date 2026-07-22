"""Lint rules for wiki quality checks."""

from __future__ import annotations

import re
from pathlib import Path

from llmwiki.redact import detect_secrets


def lint_wiki(raw_dir: Path, graph: dict, curated_dir: Path | None = None) -> list[dict]:
    """Run lint checks and return list of issues.

    When ``curated_dir`` is given, Phase S rules also validate the curated
    synthesis layer (stale claims, missing citations, bad source ids, missing
    type).
    """
    issues = []

    # Check for orphaned pages (no inbound or outbound links)
    for node in graph.get("nodes", []):
        if node["in_degree"] == 0 and node["out_degree"] == 0:
            issues.append({
                "rule": "orphan",
                "severity": "warning",
                "page": node["id"],
                "message": f"Orphaned page: {node['title']} has no cross-references",
            })

    # Check for broken references
    valid_ids = {n["id"].lower() for n in graph.get("nodes", [])}
    valid_titles = {n.get("title", "").lower() for n in graph.get("nodes", [])}
    valid_targets = valid_ids | valid_titles
    if raw_dir.exists():
        for md_file in raw_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="replace")
            # Require a word char in the target — PDFs carry literal [[()]]
            # bracket runs that are not links (Phase V finding).
            wikilinks = re.findall(r"\[\[([^\]|]*\w[^\]|]*)", content)
            for link in wikilinks:
                if link.lower() not in valid_targets:
                    issues.append({
                        "rule": "broken_link",
                        "severity": "error",
                        "page": md_file.stem,
                        "message": f"Broken wikilink: [[{link}]]",
                    })

    # Check for suspected secrets in raw page bodies. Redaction scrubs new
    # ingests, but this catches wikis built before redaction existed — the
    # page files themselves may still carry a secret.
    if raw_dir.exists():
        for md_file in raw_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="replace")
            for finding in detect_secrets(content):
                issues.append({
                    "rule": "secret-suspect",
                    "severity": "error",
                    "page": md_file.stem,
                    "message": (
                        f"Suspected secret ({finding['kind']}): "
                        f"{finding['count']} occurrence(s) — rebuild to redact"
                    ),
                })

    # Check for missing titles
    for node in graph.get("nodes", []):
        if not node.get("title") or node["title"] == node["id"]:
            issues.append({
                "rule": "missing_title",
                "severity": "info",
                "page": node["id"],
                "message": "Page has no distinct title",
            })

    # Phase S: validate the curated synthesis layer.
    if curated_dir is not None:
        issues.extend(_lint_curated(raw_dir, curated_dir, graph))

    return issues


def _lint_curated(raw_dir: Path, curated_dir: Path, graph: dict) -> list[dict]:
    """Lint rules specific to curated/ pages."""
    from llmwiki.graph import _load_curated_pages, CURATED_TYPES
    from llmwiki.synthesize import build_source_mtime_map, is_curated_stale, changed_sources

    issues: list[dict] = []
    curated = _load_curated_pages(curated_dir)
    if not curated:
        return issues

    mtime_map = build_source_mtime_map(raw_dir)
    valid_ids = {n["id"] for n in graph.get("nodes", [])}
    valid_ids_lower = {i.lower() for i in valid_ids}

    for pid, page in curated.items():
        sources = page.get("sources", [])
        synthesized_at = page.get("synthesized_at", "")

        # uncited — no citations to trace claims to.
        if not sources:
            issues.append({
                "rule": "uncited",
                "severity": "warning",
                "page": pid,
                "message": "Curated page has no sources: — claims cannot be traced",
            })

        # bad-source — a cited id matches no existing page.
        for src in sources:
            if src not in valid_ids and src.lower() not in valid_ids_lower:
                issues.append({
                    "rule": "bad-source",
                    "severity": "error",
                    "page": pid,
                    "message": f"Unknown source id in sources: {src}",
                })

        # missing-type — type absent or not one of the allowed values.
        if page.get("type", "") not in CURATED_TYPES:
            issues.append({
                "rule": "missing-type",
                "severity": "warning",
                "page": pid,
                "message": (
                    "type missing or invalid — expected one of "
                    f"{', '.join(CURATED_TYPES)}"
                ),
            })

        # stale-claim — page older than a source it cites.
        if sources and is_curated_stale(synthesized_at, sources, mtime_map):
            stale_srcs = changed_sources(synthesized_at, sources, mtime_map)
            detail = (", ".join(stale_srcs)
                      if stale_srcs else "missing/unparseable synthesized_at")
            issues.append({
                "rule": "stale-claim",
                "severity": "error",
                "page": pid,
                "message": f"Curated page is stale — sources changed: {detail}",
            })

    return issues
