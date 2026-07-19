"""Static site builder: raw/ → wiki/ → site/."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import time
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
from llmwiki.search import create_search_db, insert_pages, delete_pages_not_in


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
        graph = build_graph(raw_dir, config)
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

    # Build generic content type groups (Tier 1 + Tier 2 sub-categories)
    content_type_groups = _build_content_type_groups(pages, categories)

    # Token stats: count the summary layer only (embedded full-source
    # <details> blocks excluded), which is what agents actually consume.
    from llmwiki.search import _strip_source_block
    wiki_tokens = sum(
        len(_strip_source_block(pdata.get("body", ""))) for pdata in pages.values()
    ) // 4
    raw_source_tokens = 0
    for source in config.get("sources", []):
        src_path = Path(source["path"])
        if src_path.exists():
            for f in src_path.rglob("*"):
                if f.is_file() and f.suffix not in {".pyc", ".class", ".o", ".so", ".dll", ".jar", ".png", ".jpg", ".gif", ".ico", ".svg", ".zip", ".tar", ".gz"}:
                    try:
                        raw_source_tokens += len(f.read_bytes()) // 4
                    except OSError:
                        pass

    # Add last_build to stats for the 4th stats card
    dash_stats = dict(graph["stats"])
    dash_stats["last_build"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    dash_stats["wiki_tokens"] = wiki_tokens
    dash_stats["raw_source_tokens"] = raw_source_tokens

    # Compute recent changes by comparing page hashes to previous build
    recent_changes = _compute_recent_changes(root, pages)

    dashboard_html = render_dashboard(
        dash_stats, recent_changes, content_type_groups, top_pages,
        clusters=graph.get("clusters", []),
        content_type_groups=content_type_groups,
        all_categories=categories,
        **theme_kwargs,
    )
    (site_dir / "index.html").write_text(dashboard_html, encoding="utf-8")

    # 9-10. Render category indexes and page details
    cat_dir = site_dir / "categories"
    cat_dir.mkdir(exist_ok=True)

    # Render categories/index.html listing all categories
    all_cats_html = render_categories_index(categories,
                                            content_type_groups=content_type_groups,
                                            **theme_kwargs)
    (cat_dir / "index.html").write_text(all_cats_html, encoding="utf-8")

    for cat, cat_pages in categories.items():
        # Normalize directory name to lowercase for case-sensitive filesystems
        cat_lower = cat.lower()
        cat_path = cat_dir / cat_lower
        cat_path.mkdir(parents=True, exist_ok=True)

        # Category index page
        idx_html = render_category_index(cat, cat_pages,
                                         clusters=graph.get("clusters", []),
                                         total_pages=len(pages),
                                         content_type_groups=content_type_groups,
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
            body_text = pdata.get("body", "")
            truncated_body = body_text[:5000]
            page_json = {
                "id": pid,
                "title": pdata.get("title", ""),
                "category": pdata.get("category", ""),
                "tags": pdata.get("tags", []),
                "importance": pdata.get("importance", 0),
                "url": pdata.get("url", current_url),
                "source_path": pdata.get("source_path", ""),
                "language": pdata.get("language", ""),
                "cluster_id": pdata.get("cluster_id"),
                "in_degree": pdata.get("in_degree", 0),
                "backlinks": [
                    {
                        "title": bl.get("title", ""),
                        "url": bl.get("url", ""),
                        "category": bl.get("category", ""),
                    }
                    for bl in backlinks.get(pid, [])
                ],
                "methods": _extract_methods(pdata.get("tags", [])),
                "body_length": len(body_text),
                "is_truncated": len(body_text) > 5000,
                "body_text": truncated_body,
                "references": pdata.get("references", []),
            }
            (cat_path / f"{slug}.json").write_text(
                json.dumps(page_json, indent=2), encoding="utf-8"
            )

    # 10b. Generate index pages for subcategory parent directories
    # Sidebar links may point to parent prefixes (e.g. com/vf) that don't
    # have their own category entry. Collect all pages under each prefix
    # and generate an index.html so links don't show file-browser listings.
    _generate_subcategory_indexes(
        categories, cat_dir, content_type_groups, graph, theme_kwargs,
        total_pages=len(pages),
    )

    # 11. Build search index → search-index.json
    search_index = _build_search_index(pages, categories)
    (site_dir / "search-index.json").write_text(
        json.dumps(search_index, indent=2), encoding="utf-8"
    )

    # 12. Create and populate SQLite search database
    # NOTE: body_plain is raw markdown with embedded source code, which is noisy
    # for FTS. A future improvement would strip markdown/code fences and produce
    # cleaner plain text for higher-quality full-text search results.
    #
    # Build into a temp DB and atomically swap it into place: readers (agents
    # mid-query) never observe a half-populated or locked database, and a fresh
    # temp DB drops any ghost rows left by earlier builds. delete_pages_not_in
    # is belt-and-braces (heals a reused temp / the in-place fallback path).
    db_path = site_dir / "llmwiki.db"
    db_rows = [
        {
            "id": pid,
            "title": pdata.get("title", ""),
            "category": pdata.get("category", ""),
            "source_path": pdata.get("source_path", ""),
            "body_plain": pdata.get("body", ""),
            "tags": json.dumps(pdata.get("tags", [])),
            "importance_score": pdata.get("importance", 0),
            "cluster_id": pdata.get("cluster_id"),
            "language": pdata.get("language", ""),
            "in_degree": pdata.get("in_degree", 0),
            "url": pdata.get("url", ""),
        }
        for pid, pdata in pages.items()
    ]
    _build_search_db_atomic(db_path, db_rows, set(pages.keys()))

    # 13. Generate graph.html (interactive knowledge graph)
    graph_html = render_graph_page(graph,
                                   content_type_groups=content_type_groups,
                                   **theme_kwargs)
    (site_dir / "graph.html").write_text(graph_html, encoding="utf-8")

    # 14. Generate changelog.html and update build-history.json
    history_path = root / "build-history.json"
    history = _load_build_history(history_path)
    build_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "type": "full" if full else "incremental",
        "total_pages": len(pages),
        "total_categories": len(categories),
        "total_edges": graph["stats"]["total_edges"],
        "total_clusters": graph["stats"]["total_clusters"],
    }
    history.append(build_entry)
    history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    # Also copy to site/ so changelog is accessible via browser
    (site_dir / "build-history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8"
    )

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


def _build_search_db_atomic(db_path: Path, db_rows: list, ids: set) -> None:
    """Populate a temp DB and atomically replace the live one.

    ``os.replace`` is atomic on POSIX even while a reader holds the old file
    open — the reader keeps its (now-unlinked) inode and new readers see the
    fresh DB. On Windows a locked target raises PermissionError; retry a few
    times, then fall back to writing the live DB in place (the pre-existing
    behaviour) so a build never hard-fails on a transient lock.
    """
    tmp_path = db_path.with_name(db_path.name + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    try:
        create_search_db(tmp_path)
        insert_pages(tmp_path, db_rows)
        delete_pages_not_in(tmp_path, ids)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise

    for _ in range(3):
        try:
            os.replace(str(tmp_path), str(db_path))
            return
        except PermissionError:
            time.sleep(0.2)

    # Fallback: target stayed locked. Write in place (old behaviour) and clean
    # up the temp file so it never lingers as a stale artifact.
    print("llmwiki: warning — could not atomically swap search DB (target "
          "locked); writing in place.")
    create_search_db(db_path)
    insert_pages(db_path, db_rows)
    delete_pages_not_in(db_path, ids)
    try:
        tmp_path.unlink()
    except OSError:
        pass


def _compute_recent_changes(root: Path, pages: dict) -> list:
    """Compare current pages to previous build state to find changes.

    Maintains a ``.llmwiki-pages-state.json`` file at *root* that maps
    page IDs to content hashes.  On each call, diffs old vs new to
    produce a list of ``{title, url, action, type, time_ago}`` dicts.
    """
    state_path = root / ".llmwiki-pages-state.json"
    old_state: dict[str, str] = {}
    if state_path.exists():
        try:
            old_state = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            old_state = {}

    # Build current state: page_id → content hash
    new_state: dict[str, str] = {}
    for pid, pdata in pages.items():
        body = pdata.get("body", "")
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
        new_state[pid] = content_hash

    changes: list[dict] = []

    # Detect added and modified pages
    for pid, new_hash in new_state.items():
        pdata = pages[pid]
        title = pdata.get("title", pid)
        url = pdata.get("url", "#")
        cat = pdata.get("category", "")

        if pid not in old_state:
            changes.append({
                "title": title, "url": url, "action": "added",
                "type": cat, "time_ago": "this build",
            })
        elif old_state[pid] != new_hash:
            changes.append({
                "title": title, "url": url, "action": "modified",
                "type": cat, "time_ago": "this build",
            })

    # Detect removed pages
    for pid in old_state:
        if pid not in new_state:
            changes.append({
                "title": pid, "url": "#", "action": "removed",
                "type": "", "time_ago": "this build",
            })

    # Sort: added first, then modified, then removed — limit to 20
    action_order = {"added": 0, "modified": 1, "removed": 2}
    changes.sort(key=lambda c: action_order.get(c["action"], 9))
    changes = changes[:20]

    # Save new state
    state_path.write_text(json.dumps(new_state), encoding="utf-8")

    return changes


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


def _extract_methods(tags: list[str]) -> list[str]:
    """Extract method names from method:* tags."""
    methods = []
    for tag in tags or []:
        if isinstance(tag, str) and tag.startswith("method:"):
            methods.append(tag.split(":", 1)[1])
    return methods


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


def _generate_subcategory_indexes(
    categories: dict,
    cat_dir: Path,
    content_type_groups: dict,
    graph: dict,
    theme_kwargs: dict,
    total_pages: int = 0,
) -> None:
    """Generate index.html for subcategory parent paths that lack one.

    The sidebar links to truncated sub-category paths (e.g. ``com/vf``)
    which may not correspond to an actual category.  For every such
    prefix that has no ``index.html``, collect all pages whose category
    starts with that prefix and render a category index page so the
    browser shows a real page instead of a directory listing.
    """
    # Gather all subcategory prefixes from content type groups
    prefixes: set[str] = set()
    for ct_data in content_type_groups.values():
        for sc_name in ct_data.get("subcategories", {}):
            prefixes.add(sc_name.lower())

    existing_cats = {c.lower() for c in categories}

    for prefix in prefixes:
        if prefix in existing_cats:
            continue  # already has a proper index.html
        prefix_path = cat_dir / prefix
        if (prefix_path / "index.html").exists():
            continue  # already generated

        # Collect all pages whose category starts with this prefix
        merged_pages: list[dict] = []
        for cat, cat_pages in categories.items():
            if cat.lower().startswith(prefix + "/") or cat.lower() == prefix:
                merged_pages.extend(cat_pages)

        if not merged_pages:
            continue

        prefix_path.mkdir(parents=True, exist_ok=True)
        idx_html = render_category_index(
            prefix, merged_pages,
            clusters=graph.get("clusters", []),
            total_pages=total_pages,
            content_type_groups=content_type_groups,
            **theme_kwargs,
        )
        (prefix_path / "index.html").write_text(idx_html, encoding="utf-8")


# ---------------------------------------------------------------------------
# Content Type Detection (generic — works for any codebase)
# ---------------------------------------------------------------------------


def _detect_content_type(page_data: dict) -> str:
    """Detect content type from page data. Generic — works for any codebase."""
    lang = page_data.get("language", "")
    cat = page_data.get("category", "").lower()
    tags = page_data.get("tags", [])
    src = page_data.get("source_path", "")
    ext = Path(src).suffix.lower() if src else ""

    if cat.startswith("beanshell") or "beanshell" in tags:
        return "Inline Scripts"
    if cat == "tokens":
        return "Token Registry"
    if "pdf" in tags or ext == ".pdf":
        return "Documentation"
    if lang in ("java", "python", "javascript", "typescript", "go", "rust",
                "csharp", "ruby", "kotlin", "swift", "scala", "php", "c", "cpp"):
        return "Source Code"
    if lang == "xml" or ext in (".xml", ".xsl", ".xsd", ".wsdl"):
        return "XML / Markup"
    if ext in (".md", ".mdx", ".rst"):
        return "Documentation"
    if lang in ("properties", "json", "yaml", "toml", "ini", "cfg") or \
       ext in (".properties", ".json", ".yaml", ".yml", ".toml", ".ini", ".env", ".cfg"):
        return "Configuration"
    return "Other"


_CONTENT_TYPE_META = {
    "Source Code": {"icon": "\U0001f4c4", "color": "node-java", "desc": "Application source code files"},
    "XML / Markup": {"icon": "\U0001f4cb", "color": "node-xml", "desc": "XML configuration and markup files"},
    "Documentation": {"icon": "\U0001f4da", "color": "node-docs", "desc": "PDF guides, markdown documentation"},
    "Configuration": {"icon": "\u2699\ufe0f", "color": "node-config", "desc": "Properties, JSON, YAML config files"},
    "Inline Scripts": {"icon": "\U0001f4dc", "color": "node-beanshell", "desc": "Extracted inline scripts from XML"},
    "Token Registry": {"icon": "\U0001f3f7\ufe0f", "color": "node-tokens", "desc": "Environment token documentation"},
    "Other": {"icon": "\U0001f4e6", "color": "node-config", "desc": "Other project files"},
}


def _build_content_type_groups(pages: dict, categories: dict) -> dict:
    """Build Tier 1 content type groups with Tier 2 sub-categories.

    Returns: {
        "Source Code": {
            "count": 113,
            "icon": "📄",
            "color": "node-java",
            "desc": "...",
            "subcategories": {
                "com/vf/core/utility": {"count": 13, "url": "/categories/com/vf/core/utility/"},
                ...
            }
        },
        ...
    }
    """
    groups: dict[str, dict] = {}

    for pid, pdata in pages.items():
        ct = _detect_content_type(pdata)
        cat = pdata.get("category", "") or "uncategorized"

        if ct not in groups:
            meta = _CONTENT_TYPE_META.get(ct, _CONTENT_TYPE_META["Other"])
            groups[ct] = {
                "count": 0,
                "icon": meta["icon"],
                "color": meta["color"],
                "desc": meta["desc"],
                "subcategories": {},
            }

        groups[ct]["count"] += 1

        # Add to subcategory (use top 2 path segments for readability)
        parts = cat.split("/")
        subcat = "/".join(parts[:2]) if len(parts) > 1 else cat
        if subcat not in groups[ct]["subcategories"]:
            groups[ct]["subcategories"][subcat] = {
                "count": 0,
                "url": f"/categories/{subcat.lower()}/",
            }
        groups[ct]["subcategories"][subcat]["count"] += 1

    # Sort groups by count desc, subcategories by count desc
    sorted_groups = dict(sorted(groups.items(), key=lambda x: x[1]["count"], reverse=True))
    for g in sorted_groups.values():
        g["subcategories"] = dict(sorted(
            g["subcategories"].items(), key=lambda x: x[1]["count"], reverse=True
        ))
        # Generate dynamic description from top subcategories
        top_subs = list(g["subcategories"].keys())[:3]
        if top_subs:
            formatted = [s.replace("/", " › ").title() for s in top_subs]
            suffix = f" + {len(g['subcategories']) - 3} more" if len(g["subcategories"]) > 3 else ""
            g["desc"] = ", ".join(formatted) + suffix

    return sorted_groups
