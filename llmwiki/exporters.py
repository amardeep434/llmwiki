"""AI-consumable export generators."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def export_llms_txt(pages: dict, output: Path, project_name: str) -> None:
    """Generate llms.txt per llmstxt.org spec."""
    lines = [f"# {project_name}\n", f"> Knowledge base with {len(pages)} pages\n"]
    categories: dict[str, list] = {}
    for pid, pdata in pages.items():
        cat = pdata.get("category", "misc")
        categories.setdefault(cat, []).append((pid, pdata))

    for cat, cat_pages in sorted(categories.items()):
        lines.append(f"\n## {cat.title()}\n")
        for pid, pdata in cat_pages:
            lines.append(f"- [{pdata.get('title', pid)}]({pdata.get('url', '#')})")

    output.write_text("\n".join(lines), encoding="utf-8")


def export_llms_full_txt(pages: dict, output: Path, max_bytes: int = 5_000_000) -> None:
    """Generate llms-full.txt — flattened text dump."""
    lines = []
    total = 0
    for pid, pdata in sorted(pages.items()):
        title = pdata.get("title", pid)
        body = pdata.get("body", "")[:2000]
        entry = f"\n{'='*60}\n{title}\n{'='*60}\n{body}\n"
        total += len(entry.encode("utf-8"))
        if total > max_bytes:
            break
        lines.append(entry)
    output.write_text("".join(lines), encoding="utf-8")


def export_jsonld(pages: dict, output: Path) -> None:
    """Generate JSON-LD knowledge graph."""
    graph = []
    for pid, pdata in pages.items():
        graph.append({
            "@type": "CreativeWork",
            "@id": pid,
            "name": pdata.get("title", pid),
            "description": pdata.get("body", "")[:200],
            "keywords": pdata.get("tags", []),
            "isPartOf": pdata.get("category", ""),
        })
    data = {
        "@context": "https://schema.org",
        "@graph": graph,
    }
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")


def export_sitemap(pages: dict, output: Path, base_url: str) -> None:
    """Generate sitemap.xml."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for pid, pdata in pages.items():
        url = pdata.get("url", f"/{pid}.html")
        lines.append(f"  <url><loc>{base_url}{url}</loc><lastmod>{now}</lastmod></url>")
    lines.append("</urlset>")
    output.write_text("\n".join(lines), encoding="utf-8")


def export_all(pages: dict, site_dir: Path, project_name: str, base_url: str = "http://localhost:8765") -> None:
    """Generate all AI-consumable exports."""
    export_llms_txt(pages, site_dir / "llms.txt", project_name)
    export_llms_full_txt(pages, site_dir / "llms-full.txt")
    export_jsonld(pages, site_dir / "graph.jsonld")
    export_sitemap(pages, site_dir / "sitemap.xml", base_url)
