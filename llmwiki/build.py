"""Static site builder: raw/ → wiki/ → site/."""

from __future__ import annotations

import json
from pathlib import Path

from llmwiki.graph import build_graph, save_graph, _load_pages
from llmwiki.render.html import (
    render_dashboard,
    render_category_index,
    render_page_detail,
)
from llmwiki.render.css import CSS
from llmwiki.render.js import JS


def build_site(root: Path, config: dict, full: bool = False) -> dict:
    """Build the full static site.

    Args:
        root: Project root containing raw/, wiki/, site/.
        config: Loaded llmwiki.json config.
        full: Force full rebuild.

    Returns:
        Summary dict with stats.
    """
    raw_dir = root / "raw"
    wiki_dir = root / "wiki"
    out_name = config.get("build", {}).get("out_dir", "site")
    site_dir = root / out_name

    # Ensure directories exist
    wiki_dir.mkdir(exist_ok=True)
    site_dir.mkdir(exist_ok=True)

    # 1. Build knowledge graph from raw/
    graph = build_graph(raw_dir)

    # 2. Save cross-references.json
    save_graph(graph, site_dir / "cross-references.json")

    # 3. Load all pages
    pages = _load_pages(raw_dir)

    # 4. Build backlink index from graph edges
    backlinks: dict[str, list[dict]] = {}
    node_map = {n["id"]: n for n in graph.get("nodes", [])}
    for edge in graph.get("edges", []):
        to_id = edge["to"]
        from_id = edge["from"]
        from_node = node_map.get(from_id)
        if from_node:
            backlinks.setdefault(to_id, []).append({
                "title": from_node.get("title", from_id),
                "url": _page_url(from_id),
            })

    # 5. Enrich pages with importance scores and cluster IDs
    for pid, pdata in pages.items():
        node = node_map.get(pid, {})
        pdata["importance"] = node.get("importance", 0)
        pdata["cluster_id"] = node.get("cluster_id")
        pdata["in_degree"] = node.get("in_degree", 0)
        pdata["url"] = _page_url(pid)

    # 6. Group pages by category
    categories: dict[str, list[dict]] = {}
    for pid, pdata in pages.items():
        cat = pdata.get("category", "misc")
        categories.setdefault(cat, []).append({**pdata, "id": pid})

    # 7. Write style.css and script.js
    (site_dir / "style.css").write_text(CSS, encoding="utf-8")
    (site_dir / "script.js").write_text(JS, encoding="utf-8")

    # 8. Render dashboard → index.html
    top_pages = sorted(
        [
            {
                "title": n["title"],
                "url": _page_url(n["id"]),
                "in_degree": n["in_degree"],
            }
            for n in graph.get("nodes", [])
        ],
        key=lambda x: x["in_degree"],
        reverse=True,
    )
    cat_summary = {cat: {"count": len(pgs)} for cat, pgs in categories.items()}
    dashboard_html = render_dashboard(
        graph["stats"], [], cat_summary, top_pages
    )
    (site_dir / "index.html").write_text(dashboard_html, encoding="utf-8")

    # 9-10. Render category indexes and page details
    cat_dir = site_dir / "categories"
    cat_dir.mkdir(exist_ok=True)
    for cat, cat_pages in categories.items():
        cat_path = cat_dir / cat
        cat_path.mkdir(parents=True, exist_ok=True)

        # Category index page
        idx_html = render_category_index(cat, cat_pages)
        (cat_path / "index.html").write_text(idx_html, encoding="utf-8")

        # Individual page details + JSON siblings
        for pdata in cat_pages:
            pid = pdata["id"]
            slug = pid.split("/")[-1] if "/" in pid else pid

            # Page detail HTML
            page_html = render_page_detail(pdata, backlinks.get(pid, []))
            (cat_path / f"{slug}.html").write_text(
                page_html, encoding="utf-8"
            )

            # JSON sibling for AI agents
            page_json = {
                "id": pid,
                "title": pdata.get("title", ""),
                "category": pdata.get("category", ""),
                "tags": pdata.get("tags", []),
                "importance": pdata.get("importance", 0),
                "body_text": pdata.get("body", "")[:5000],
                "references": pdata.get("references", []),
            }
            (cat_path / f"{slug}.json").write_text(
                json.dumps(page_json, indent=2), encoding="utf-8"
            )

    # 11. Build search index → search-index.json
    search_index = _build_search_index(pages, categories)
    (site_dir / "search-index.json").write_text(
        json.dumps(search_index, indent=2), encoding="utf-8"
    )

    # 12. Return stats
    return {
        "total_pages": len(pages),
        "total_categories": len(categories),
        "total_edges": graph["stats"]["total_edges"],
        "total_clusters": graph["stats"]["total_clusters"],
    }


def _page_url(page_id: str) -> str:
    """Convert page ID (slug) to URL path."""
    parts = page_id.split("/")
    if len(parts) >= 2:
        cat = "/".join(parts[:-1])
        slug = parts[-1]
        return f"/categories/{cat}/{slug}.html"
    return f"/categories/{page_id}/{page_id}.html"


def _build_search_index(pages: dict, categories: dict) -> dict:
    """Build client-side search index for the command palette."""
    entries = []
    for pid, pdata in pages.items():
        entries.append({
            "id": pid,
            "title": pdata.get("title", ""),
            "url": pdata.get("url", ""),
            "type": pdata.get("category", ""),
            "category": pdata.get("category", ""),
            "tags": pdata.get("tags", []),
            "importance": pdata.get("importance", 0),
            "body": pdata.get("body", "")[:1200],
        })
    return {
        "entries": entries,
        "categories": sorted(categories.keys()),
        "_mode": "flat",
    }
