"""Lint rules for wiki quality checks."""

from __future__ import annotations

import re
from pathlib import Path


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
    valid_ids = {n["id"] for n in graph.get("nodes", [])}
    if raw_dir.exists():
        for md_file in raw_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="replace")
            wikilinks = re.findall(r"\[\[([^\]|]+)", content)
            for link in wikilinks:
                if link.lower() not in {v.lower() for v in valid_ids}:
                    issues.append({
                        "rule": "broken_link",
                        "severity": "error",
                        "page": md_file.stem,
                        "message": f"Broken wikilink: [[{link}]]",
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
