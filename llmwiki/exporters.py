"""AI-consumable export generators."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path


def export_llms_txt(
    pages: dict,
    output: Path,
    project_name: str,
    project_description: str = "",
) -> None:
    """Generate llms.txt per llmstxt.org spec."""
    description = project_description or f"Knowledge base with {len(pages)} pages."
    lines = [
        f"# {project_name}",
        "",
        f"> {description}",
        "",
        "## Key entry points",
        "",
        "- `search-index.json` — client-side index with title/category/tags/body",
        "- `llmwiki.db` — SQLite FTS5 search database",
        "- `cross-references.json` — knowledge graph export",
        "",
    ]
    categories: dict[str, list] = {}
    for pid, pdata in pages.items():
        cat = pdata.get("category", "misc") or "misc"
        categories.setdefault(cat, []).append((pid, pdata))

    for cat, cat_pages in sorted(categories.items()):
        lines.extend(["", f"## {cat.title()}", ""])
        for pid, pdata in sorted(
            cat_pages,
            key=lambda item: (-float(item[1].get("importance", 0)), item[1].get("title", item[0])),
        ):
            url = _page_url(pid, pdata)
            lines.append(f"- [{pdata.get('title', pid)}]({url}) — category: {cat}")

    lines.extend([
        "",
        "## Additional Resources",
        "",
        "- [Full Content](llms-full.txt)",
        "- [Knowledge Graph](graph.jsonld)",
        "- [Sitemap](sitemap.xml)",
    ])
    output.write_text("\n".join(lines), encoding="utf-8")


def export_llms_full_txt(
    pages: dict,
    output: Path,
    project_name: str = "",
    max_bytes: int = 5_000_000,
) -> None:
    """Generate llms-full.txt — flattened text dump."""
    body_limit = 2000
    name = project_name or "llmwiki"
    lines = [
        f"# {name} — Full Content Export",
        "",
        f"Total pages: {len(pages)}",
        f"Body truncated at: {body_limit} chars per page",
        f"File size limit: {max_bytes} bytes",
        "",
        "---",
        "",
    ]
    total = 0
    for pid, pdata in sorted(
        pages.items(),
        key=lambda item: (-float(item[1].get("importance", 0)), item[1].get("title", item[0])),
    ):
        title = pdata.get("title", pid)
        cat = pdata.get("category", "")
        importance = float(pdata.get("importance", 0))
        body = pdata.get("body", "")
        truncated = len(body) > body_limit
        clipped = body[:body_limit]
        if truncated:
            clipped += "\n[truncated]"
        entry = (
            f"## {title}\n"
            f"Category: {cat} | Importance: {importance:.4f}\n\n"
            f"{clipped}\n\n"
            "---\n"
        )
        total += len(entry.encode("utf-8"))
        if total > max_bytes:
            break
        lines.append(entry)
    output.write_text("\n".join(lines), encoding="utf-8")


def export_graph_jsonld(
    pages: dict,
    output: Path,
    project_name: str = "llmwiki",
    project_description: str = "",
    graph: dict | None = None,
) -> None:
    """Generate JSON-LD knowledge graph."""
    # Build edge lookup from graph data if available
    edge_map: dict[str, list[str]] = {}
    if graph:
        for edge in graph.get("edges", []):
            from_id = edge.get("from", "")
            to_id = edge.get("to", "")
            if from_id and to_id:
                edge_map.setdefault(from_id, []).append(to_id)

    json_graph = []
    for pid, pdata in pages.items():
        # Use graph edges when available, fall back to page references
        mention_ids = edge_map.get(pid, []) if edge_map else []
        if not mention_ids:
            mention_ids = pdata.get("references", [])
        mentions = [_reference_entry(ref, pages) for ref in mention_ids]

        json_graph.append({
            "@type": "CreativeWork",
            "@id": pid,
            "name": pdata.get("title", pid),
            "description": pdata.get("body", "")[:200],
            "keywords": pdata.get("tags", []),
            "url": _page_url(pid, pdata),
            "inLanguage": pdata.get("language", ""),
            "isPartOf": pdata.get("category", ""),
            "mentions": mentions,
            "relatedLink": [m["url"] for m in mentions if m.get("url")],
        })
    data = {
        "@context": "https://schema.org",
        "name": project_name,
        "description": project_description or f"Knowledge graph for {project_name}",
        "@graph": json_graph,
    }
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")


def export_jsonld(pages: dict, output: Path) -> None:
    """Backward-compatible alias for JSON-LD export."""
    export_graph_jsonld(pages, output)


def export_sitemap(pages: dict, output: Path, base_url: str) -> None:
    """Generate sitemap.xml."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base = base_url.rstrip("/")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for pid, pdata in pages.items():
        safe_loc = escape(base + _page_url(pid, pdata))
        lines.append(f"  <url><loc>{safe_loc}</loc><lastmod>{now}</lastmod></url>")
    lines.append("</urlset>")
    output.write_text("\n".join(lines), encoding="utf-8")


def export_all(
    pages: dict,
    site_dir: Path,
    project_name: str,
    base_url: str = "http://localhost:8765",
    project_description: str = "",
    graph: dict | None = None,
) -> None:
    """Generate all AI-consumable exports."""
    export_llms_txt(pages, site_dir / "llms.txt", project_name, project_description)
    export_llms_full_txt(pages, site_dir / "llms-full.txt", project_name)
    export_graph_jsonld(
        pages, site_dir / "graph.jsonld", project_name, project_description,
        graph=graph,
    )
    export_sitemap(pages, site_dir / "sitemap.xml", base_url)


def _page_url(page_id: str, pdata: dict) -> str:
    """Build the public URL for a page."""
    category = (pdata.get("category", "") or "uncategorized").lower()
    slug = page_id.split("/")[-1] if "/" in page_id else page_id
    return pdata.get("url") or f"/categories/{category}/{slug}.html"


def _reference_entry(reference_id: str, pages: dict) -> dict:
    """Build a JSON-LD relationship entry."""
    target = pages.get(reference_id, {})
    return {
        "@id": reference_id,
        "name": target.get("title", reference_id),
        "url": _page_url(reference_id, target),
    }
