"""Static site builder: raw/ → wiki/ → site/."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from llmwiki.graph import build_graph, save_graph, _load_pages
from llmwiki.render.html import (
    render_dashboard,
    render_category_index,
    render_page_detail,
    render_graph_page,
    render_changelog_page,
    render_categories_index,
)
from llmwiki.render.css import CSS
from llmwiki.render.js import JS
from llmwiki.render.themes import get_theme, get_all_js_themes, get_theme_labels, get_color_options
from llmwiki.search import create_search_db, insert_page


def build_site(root: Path, config: dict, full: bool = False) -> dict:
    """Build the full static site.

    Args:
        root: Project root containing raw/, wiki/, site/.
        config: Loaded llmwiki.json config.
        full: Force full rebuild. When False, the ``build.incremental``
              config key (default True) controls the behaviour.

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

    cross_refs_enabled = config.get("cross_references", {}).get("enabled", True)

    # 1. Optionally build knowledge graph from raw/
    if cross_refs_enabled:
        graph = build_graph(raw_dir)
        save_graph(graph, site_dir / "cross-references.json")
    else:
        graph = {"nodes": [], "edges": [], "clusters": [], "stats": {
            "total_pages": 0, "total_edges": 0, "total_clusters": 0, "orphans": 0,
        }}

    # 2. Load all pages
    pages = _load_pages(raw_dir)

    # Update stats with actual page count when graph is disabled
    if not cross_refs_enabled:
        graph["stats"]["total_pages"] = len(pages)

    # 3. Build page URL map (category-based, matches filesystem)
    page_urls: dict[str, str] = {}
    for pid, pdata in pages.items():
        cat = (pdata.get("category", "") or "uncategorized").lower()
        slug_file = pid.split("/")[-1] if "/" in pid else pid
        page_urls[pid] = f"/categories/{cat}/{slug_file}.html"

    # 4. Build backlink index from graph edges
    backlinks: dict[str, list[dict]] = {}
    node_map = {n["id"]: n for n in graph.get("nodes", [])}
    for edge in graph.get("edges", []):
        to_id = edge["to"]
        from_id = edge["from"]
        from_node = node_map.get(from_id)
        if from_node:
            from_cat = from_node.get("type", "")
            if not from_cat:
                from_page = pages.get(from_id, {})
                from_cat = from_page.get("category", "Other")
            backlinks.setdefault(to_id, []).append({
                "title": from_node.get("title", from_id),
                "url": page_urls.get(from_id, "#"),
                "category": from_cat or "Other",
            })

    # 5. Enrich pages with importance scores, cluster IDs, and URLs
    for pid, pdata in pages.items():
        node = node_map.get(pid, {})
        pdata["importance"] = node.get("importance", 0)
        pdata["cluster_id"] = node.get("cluster_id")
        pdata["in_degree"] = node.get("in_degree", 0)
        pdata["url"] = page_urls.get(pid, "#")

    # 5. Write enriched pages to wiki/ (intermediate layer)
    wiki_pages_dir = wiki_dir / "pages"
    wiki_pages_dir.mkdir(parents=True, exist_ok=True)
    wiki_categories: dict[str, list[str]] = {}
    for pid, pdata in pages.items():
        # Default empty categories to "uncategorized"
        cat = pdata.get("category", "") or "uncategorized"
        pdata["category"] = cat

        wiki_page_path = wiki_pages_dir / f"{pid.replace('/', '_')}.md"
        fm_lines = [
            "---",
            f'title: "{pdata.get("title", "")}"',
            f'category: {cat}',
            f'importance: {pdata.get("importance", 0)}',
            f'cluster_id: {pdata.get("cluster_id", "")}',
            f'tags: [{", ".join(pdata.get("tags", []))}]',
            "---",
        ]
        wiki_page_path.write_text(
            "\n".join(fm_lines) + "\n\n" + pdata.get("body", ""),
            encoding="utf-8",
        )
        wiki_categories.setdefault(cat, []).append(
            f"- [{pdata.get('title', pid)}](pages/{pid.replace('/', '_')}.md)"
        )

    # Write wiki/index.md catalog
    idx_lines = ["# Wiki Page Catalog\n"]
    for cat in sorted(wiki_categories):
        idx_lines.append(f"\n## {cat}\n")
        idx_lines.extend(wiki_categories[cat])
    (wiki_dir / "index.md").write_text("\n".join(idx_lines) + "\n", encoding="utf-8")

    # 6. Group pages by category
    categories: dict[str, list[dict]] = {}
    for pid, pdata in pages.items():
        cat = pdata.get("category", "") or "uncategorized"
        pdata["category"] = cat
        categories.setdefault(cat, []).append({**pdata, "id": pid})

    # 7. Write style.css (with theme) and script.js
    theme_name = config.get("build", {}).get("theme", "emerald-dark")
    theme = get_theme(theme_name)
    themed_css = theme.to_css() + "\n" + CSS
    (site_dir / "style.css").write_text(themed_css, encoding="utf-8")
    (site_dir / "script.js").write_text(JS, encoding="utf-8")

    # Build JS theme data for runtime color switching
    themes_json = json.dumps(get_all_js_themes())
    theme_labels_json = json.dumps(get_theme_labels())
    color_options = get_color_options()
    theme_kwargs = {
        "themes_json": themes_json,
        "theme_labels_json": theme_labels_json,
        "color_options": color_options,
    }

    # 8. Render dashboard → index.html
    top_pages = sorted(
        [
            {
                "title": pdata.get("title", pid),
                "url": pdata.get("url", "#"),
                "in_degree": pdata.get("in_degree", 0),
            }
            for pid, pdata in pages.items()
        ],
        key=lambda x: x["in_degree"],
        reverse=True,
    )

    # Group 250+ sub-categories into logical dashboard groups
    dashboard_groups = _group_categories_for_dashboard(categories)

    # Add last_build to stats for the 4th stats card
    dash_stats = dict(graph["stats"])
    dash_stats["last_build"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    dashboard_html = render_dashboard(
        dash_stats, [], dashboard_groups, top_pages,
        clusters=graph.get("clusters", []),
        **theme_kwargs,
    )
    (site_dir / "index.html").write_text(dashboard_html, encoding="utf-8")

    # 9-10. Render category indexes and page details
    cat_dir = site_dir / "categories"
    cat_dir.mkdir(exist_ok=True)

    # Render categories/index.html listing all categories
    all_cats_html = render_categories_index(categories, **theme_kwargs)
    (cat_dir / "index.html").write_text(all_cats_html, encoding="utf-8")

    for cat, cat_pages in categories.items():
        # Normalize directory name to lowercase for case-sensitive filesystems
        cat_lower = cat.lower()
        cat_path = cat_dir / cat_lower
        cat_path.mkdir(parents=True, exist_ok=True)

        # Category index page
        idx_html = render_category_index(cat, cat_pages,
                                         clusters=graph.get("clusters", []),
                                         **theme_kwargs)
        (cat_path / "index.html").write_text(idx_html, encoding="utf-8")

        # Individual page details + JSON siblings
        for pdata in cat_pages:
            pid = pdata["id"]
            slug = pid.split("/")[-1] if "/" in pid else pid
            current_url = f"/categories/{cat_lower}/{slug}.html"

            # Page detail HTML
            page_html = render_page_detail(pdata, backlinks.get(pid, []),
                                           current_url=current_url,
                                           clusters=graph.get("clusters", []),
                                           **theme_kwargs)
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

    # 12. Create and populate SQLite search database
    db_path = site_dir / "llmwiki.db"
    create_search_db(db_path)
    for pid, pdata in pages.items():
        insert_page(db_path, {
            "id": pid,
            "title": pdata.get("title", ""),
            "category": pdata.get("category", ""),
            "body_plain": pdata.get("body", ""),
            "tags": json.dumps(pdata.get("tags", [])),
            "importance_score": pdata.get("importance", 0),
        })

    # 13. Generate graph.html (interactive knowledge graph)
    graph_html = render_graph_page(graph, **theme_kwargs)
    (site_dir / "graph.html").write_text(graph_html, encoding="utf-8")

    # 14. Generate changelog.html and update build-history.json
    history_path = root / "build-history.json"
    history = _load_build_history(history_path)
    build_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_pages": len(pages),
        "total_categories": len(categories),
        "total_edges": graph["stats"]["total_edges"],
        "total_clusters": graph["stats"]["total_clusters"],
    }
    history.append(build_entry)
    history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    changelog_html = render_changelog_page(history, **theme_kwargs)
    (site_dir / "changelog.html").write_text(changelog_html, encoding="utf-8")

    # 15. Return stats
    result = {
        "total_pages": len(pages),
        "total_categories": len(categories),
        "total_edges": graph["stats"]["total_edges"],
        "total_clusters": graph["stats"]["total_clusters"],
        "last_build": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    return result


def _page_url(page_id: str) -> str:
    """Convert page ID (slug) to URL path.

    All paths are lowercased to match the lowercase directory structure
    written to site/ (required for case-sensitive filesystems).
    """
    parts = page_id.split("/")
    if len(parts) >= 2:
        cat = "/".join(parts[:-1]).lower()
        slug = parts[-1]
        return f"/categories/{cat}/{slug}.html"
    return f"/categories/{page_id.lower()}/{page_id}.html"


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


def _load_build_history(path: Path) -> list:
    """Load existing build history or return empty list."""
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return []


# Mapping of top-level category segments to logical dashboard groups
_DASHBOARD_GROUP_MAP = {
    "rule": ("Rules", "node-xml", "Business logic rules and rule libraries"),
    "workflow": ("Workflows", "node-xml", "Identity lifecycle and provisioning workflows"),
    "emailtemplate": ("Email Templates", "node-config", "Notification and alert email templates"),
    "taskdefinition": ("Task Definitions", "node-config", "Scheduled and on-demand task configurations"),
    "form": ("Forms", "node-config", "UI form definitions for identity management"),
    "application": ("Applications", "node-config", "Connector definitions for target systems"),
    "custom": ("Custom Objects", "node-config", "Global configuration and custom object definitions"),
    "certificationdefinition": ("Certifications", "node-config", "Access certification campaign definitions"),
    "correlationconfig": ("Correlation Config", "node-config", "Identity correlation and matching rules"),
    "dynamicscope": ("Dynamic Scopes", "node-config", "Dynamic population scoping definitions"),
    "identitytrigger": ("Identity Triggers", "node-config", "Event-driven identity lifecycle triggers"),
    "quicklink": ("Quick Links", "node-config", "Navigation quick link definitions"),
    "workgroup": ("Workgroups", "node-config", "Workgroup and team definitions"),
    "requestdefinition": ("Request Definitions", "node-config", "Access request type definitions"),
    "objectconfig": ("Object Config", "node-config", "Object type configuration metadata"),
    "configuration": ("Configuration", "node-config", "System-level configuration objects"),
    "ssf_features": ("SSF Features", "node-config", "SailPoint Services Standard features"),
    "ssf_frameworks": ("SSF Frameworks", "node-config", "SailPoint Services Standard frameworks"),
    "ssf_tools": ("SSF Tools", "node-config", "SailPoint Services Standard deployment tools"),
    "beanshell": ("BeanShell Scripts", "node-beanshell", "Extracted inline scripts from workflows and rules"),
    "com": ("Java Source", "node-java", "Core utility classes, tasks, reports, and integrations"),
    "sailpoint": ("SailPoint SDK", "node-java", "SailPoint API and SDK classes"),
    "bsh": ("BeanShell Engine", "node-java", "BeanShell scripting engine classes"),
    "connector-guides": ("Connector Guides", "node-docs", "SailPoint connector configuration and setup guides"),
    "iiq-docs": ("IIQ Documentation", "node-docs", "IdentityIQ 8.5 official documentation"),
    "docs": ("Project Docs", "node-docs", "Project-level documentation and guides"),
    "config": ("Config Files", "node-config", "General configuration file definitions"),
    "tokens": ("Token Registry", "node-tokens", "Environment token definitions and mappings"),
    "xml": ("XML Config", "node-xml", "XML-based configuration objects"),
}


def _group_categories_for_dashboard(
    categories: dict[str, list[dict]],
) -> dict[str, dict]:
    """Group 250+ sub-categories into ~15 logical dashboard groups.

    Returns {display_name: {"count": N, "color": css_var, "url": first_matching_category_url, "description": str}}
    """
    groups: dict[str, dict] = {}

    for cat, pages_list in categories.items():
        top = cat.split("/")[0].lower() if "/" in cat else cat.lower()
        entry = _DASHBOARD_GROUP_MAP.get(top, (top.replace("-", " ").title(), "node-config", ""))
        display = entry[0]
        color = entry[1]
        desc = entry[2] if len(entry) > 2 else ""

        if display not in groups:
            groups[display] = {"count": 0, "color": color, "url": f"/categories/{cat.lower()}/", "description": desc}
        groups[display]["count"] += len(pages_list)

    # Sort by count descending
    return dict(sorted(groups.items(), key=lambda x: x[1]["count"], reverse=True))
