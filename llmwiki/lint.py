"""Lint rules for wiki quality checks."""

from __future__ import annotations

import re
from pathlib import Path

from llmwiki.redact import detect_secrets


def lint_wiki(raw_dir: Path, graph: dict) -> list[dict]:
    """Run lint checks and return list of issues."""
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

    return issues
