"""HTML page generator functions — dark emerald three-panel design.

All HTML is generated programmatically — no template files.
Each function returns an HTML string for a specific page type.
"""

from __future__ import annotations

import json
import re
from html import escape
from typing import List, Tuple

import markdown

from llmwiki.render.js import PRE_PAINT_SCRIPT

# --- HTML sanitization for markdown output ---
_DANGEROUS_TAGS = re.compile(
    r'<\s*/?\s*(script|iframe|object|embed|form|input|button|textarea|select|style|link|meta|base)\b[^>]*>',
    re.IGNORECASE,
)
_EVENT_HANDLERS = re.compile(r'\s+on\w+\s*=', re.IGNORECASE)


def _sanitize_html(html_str: str) -> str:
    """Remove dangerous HTML tags and event handlers."""
    html_str = _DANGEROUS_TAGS.sub('', html_str)
    html_str = _EVENT_HANDLERS.sub(' data-removed=', html_str)
    return html_str


def _format_category_display(name: str) -> str:
    """Format a category name for display."""
    return name.replace("-", " ").replace("/", " \u203a ").title()


# ===========================================================================
# HEAD / FOOT
# ===========================================================================


def page_head(title: str, description: str = "") -> str:
    """Generate <!DOCTYPE> through opening <body> with three-panel layout start."""
    safe_title = escape(title)
    safe_desc = escape(description)
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{safe_title} \u2014 LLMWiki</title>\n'
        f'<meta name="description" content="{safe_desc}">\n'
        '<meta name="color-scheme" content="dark light">\n'
        '<link rel="icon" href="data:image/svg+xml,'
        '<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22>'
        '<text y=%22.9em%22 font-size=%2290%22>\U0001F48E</text></svg>">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/'
        'cdn-release@11.9.0/build/styles/github-dark.min.css" '
        'crossorigin="anonymous">\n'
        f'<script>{PRE_PAINT_SCRIPT}</script>\n'
        '</head>\n'
        '<body>\n'
    )


def page_foot() -> str:
    """Generate command palette + scripts + closing tags."""
    return (
        '\n<!-- Command Palette -->\n'
        '<div id="command-palette" class="palette-overlay" hidden>\n'
        '<div class="palette-dialog">\n'
        '<input type="text" class="palette-input" '
        'placeholder="Search pages\u2026 (type:, category:, tag:)" autocomplete="off">\n'
        '<div class="palette-results"></div>\n'
        '<div class="palette-hints">'
        '<span>\u2191\u2193 navigate</span>'
        '<span>\u21b5 open</span>'
        '<span>esc close</span>'
        '<span>\u2318K search</span>'
        '</div>\n'
        '</div>\n'
        '</div>\n'
        '<!-- Bottom Tab Bar (mobile) -->\n'
        '<div class="bottom-tabs">\n'
        '<nav>\n'
        '<a href="/" class="active"><span class="tab-icon">\U0001F3E0</span>Home</a>\n'
        '<a href="#" data-action="search"><span class="tab-icon">\U0001F50D</span>Search</a>\n'
        '<a href="/graph.html" data-action="graph"><span class="tab-icon">\U0001F578\uFE0F</span>Graph</a>\n'
        '<a href="#" data-action="sidebar"><span class="tab-icon">\u2630</span>Menu</a>\n'
        '</nav>\n'
        '</div>\n'
        '<script src="https://cdn.jsdelivr.net/gh/highlightjs/'
        'cdn-release@11.9.0/build/highlight.min.js" defer '
        'crossorigin="anonymous"></script>\n'
        '<script src="/script.js" defer></script>\n'
        '</body>\n'
        '</html>\n'
    )


# ===========================================================================
# TOPBAR
# ===========================================================================


def _topbar(active: str = "") -> str:
    """Generate the 48px sticky top bar."""
    links = [
        ("Home", "/", "home"),
        ("Categories", "/categories/", "categories"),
        ("Graph", "/graph.html", "graph"),
        ("Changelog", "/changelog.html", "changelog"),
    ]
    nav_items = []
    for label, href, key in links:
        cls = ' class="active"' if key == active else ""
        nav_items.append(f'<a href="{href}"{cls}>{escape(label)}</a>')

    return (
        '<header class="topbar">\n'
        '<button class="sidebar-toggle" aria-label="Toggle sidebar">\u2630</button>\n'
        '<a href="/" class="topbar-brand">'
        '<span class="brand-icon">\u25C6</span> LLMWiki</a>\n'
        f'<nav class="topbar-nav">{"".join(nav_items)}</nav>\n'
        '<div class="topbar-actions">\n'
        '<button class="search-trigger" aria-label="Search">'
        '\U0001F50D Search\u2026 <kbd>\u2318K</kbd></button>\n'
        '<button class="graph-toggle" aria-label="Toggle graph panel">\U0001F578\uFE0F</button>\n'
        '<button class="theme-toggle" aria-label="Toggle theme">\U0001F319</button>\n'
        '</div>\n'
        '</header>\n'
    )


# Keep backward-compatible name
def nav_bar(active: str = "") -> str:
    """Generate navigation bar (alias for _topbar)."""
    return _topbar(active)


# ===========================================================================
# SIDEBAR
# ===========================================================================


def render_sidebar(categories: dict, current_category: str = "") -> str:
    """Generate left sidebar with collapsible category tree."""
    parts = [
        '<aside class="sidebar">\n',
        '<div class="sidebar-search">\U0001F50D Search pages\u2026</div>\n',
    ]

    sorted_cats = sorted(categories.items(), key=lambda x: x[0].lower())
    for cat_name, cat_pages in sorted_cats:
        count = len(cat_pages) if isinstance(cat_pages, list) else cat_pages.get("count", 0)
        display = escape(_format_category_display(cat_name))
        cat_url = cat_name.lower()
        is_active = cat_name.lower() == current_category.lower() if current_category else False
        collapsed_cls = "" if is_active else " collapsed"

        parts.append(f'<div class="sidebar-section{collapsed_cls}">\n')
        parts.append(
            f'<div class="sidebar-section-header">'
            f'<span>{display}</span>'
            f'<span class="count">{count}</span>'
            f'</div>\n'
        )
        parts.append('<ul class="sidebar-tree">\n')

        # Show individual pages if available
        page_list = cat_pages if isinstance(cat_pages, list) else []
        for p in page_list[:15]:
            p_title = escape(p.get("title", "?")[:30])
            p_url = escape(p.get("url", f"/categories/{cat_url}/"))
            parts.append(
                f'<li><a class="sidebar-tree-item" href="{p_url}" '
                f'data-href="{p_url}">{p_title}</a></li>\n'
            )
        if len(page_list) > 15:
            parts.append(
                f'<li><a class="sidebar-tree-item" '
                f'href="/categories/{escape(cat_url)}/">'
                f'\u2026 {len(page_list) - 15} more</a></li>\n'
            )
        if not page_list:
            parts.append(
                f'<li><a class="sidebar-tree-item" '
                f'href="/categories/{escape(cat_url)}/">'
                f'View all ({count})</a></li>\n'
            )
        parts.append('</ul>\n</div>\n')

    parts.append('</aside>\n')
    return "".join(parts)


# ===========================================================================
# GRAPH PANEL
# ===========================================================================


def render_graph_panel(page_id: str = "") -> str:
    """Generate right mini-graph panel placeholder."""
    return (
        '<aside class="graph-panel">\n'
        '<div class="graph-panel-header">'
        '<span>Local Graph</span>'
        '<a href="/graph.html">Open full \u2192</a>'
        '</div>\n'
        f'<div class="graph-panel-canvas" id="mini-graph" data-page="{escape(page_id)}"></div>\n'
        '</aside>\n'
    )


# ===========================================================================
# BREADCRUMBS
# ===========================================================================


def breadcrumbs(crumbs: List[Tuple[str, str]]) -> str:
    """Generate breadcrumb navigation from list of (label, href) tuples."""
    if not crumbs:
        return ""
    parts = []
    for label, href in crumbs[:-1]:
        parts.append(f'<a href="{escape(href)}">{escape(label)}</a>')
        parts.append('<span class="sep">\u203a</span>')
    parts.append(f'<span class="current">{escape(crumbs[-1][0])}</span>')
    return (
        f'<nav class="breadcrumbs" aria-label="Breadcrumb">'
        f'{"".join(parts)}'
        f'</nav>\n'
    )


# ===========================================================================
# MARKDOWN
# ===========================================================================


def md_to_html(body: str) -> str:
    """Convert markdown body to HTML."""
    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "toc", "sane_lists"]
    )
    return _sanitize_html(md.convert(body))


# ===========================================================================
# DASHBOARD
# ===========================================================================


def render_dashboard(
    stats: dict,
    recent_changes: list,
    categories: dict,
    top_pages: list,
) -> str:
    """Render the dashboard home page with three-panel layout."""
    parts = [
        page_head("Home", "Knowledge base dashboard"),
        '<div class="app-layout">\n',
        _topbar("home"),
        render_sidebar(categories),
    ]

    # Main content
    parts.append('<main class="main-content">\n<div class="content-wrapper">\n')

    # Stats row
    total_pages = stats.get("total_pages", 0)
    total_edges = stats.get("total_edges", 0)
    total_clusters = stats.get("total_clusters", 0)
    parts.append('<div class="stats-row">\n')
    for value, label in [
        (total_pages, "Pages"),
        (total_edges, "Cross-refs"),
        (total_clusters, "Clusters"),
    ]:
        parts.append(
            f'<div class="stat-card">'
            f'<span class="stat-value">{value:,}</span>'
            f'<span class="stat-label">{label}</span>'
            f'</div>\n'
        )
    parts.append('</div>\n')

    # Recent changes
    if recent_changes:
        parts.append('<h2 class="section-heading">Recent Changes</h2>\n')
        parts.append('<ul class="changes-feed">\n')
        for change in recent_changes[:10]:
            ctype = change.get("type", "")
            title = escape(change.get("title", "Unknown"))
            url = escape(change.get("url", "#"))
            parts.append(
                f'<li><span class="change-badge {escape(ctype)}">{escape(ctype)}</span> '
                f'<a href="{url}">{title}</a></li>\n'
            )
        parts.append('</ul>\n')

    # Category cards (top 20)
    if categories:
        total_cat_count = len(categories)
        sorted_cats = sorted(
            categories.items(),
            key=lambda item: (
                len(item[1]) if isinstance(item[1], list)
                else item[1].get("count", 0)
            ),
            reverse=True,
        )
        display_limit = 20
        shown_cats = sorted_cats[:display_limit]

        parts.append('<h2 class="section-heading">Categories</h2>\n')
        parts.append('<div class="card-grid">\n')
        for cat_name, cat_data in shown_cats:
            count = len(cat_data) if isinstance(cat_data, list) else cat_data.get("count", 0)
            display = escape(_format_category_display(cat_name))
            cat_url = escape(cat_name.lower())
            parts.append(
                f'<a href="/categories/{cat_url}/" class="card">'
                f'<h3>{display}</h3>'
                f'<span class="card-meta">{count} pages</span></a>\n'
            )
        parts.append('</div>\n')
        if total_cat_count > display_limit:
            parts.append(
                f'<p class="view-all-link">'
                f'<a href="/categories/">View all {total_cat_count} categories \u2192</a>'
                f'</p>\n'
            )

    # Most connected pages (top 10) with importance bars
    if top_pages:
        parts.append('<h2 class="section-heading">Most Connected</h2>\n')
        parts.append('<ul class="connected-list">\n')
        for idx, tp in enumerate(top_pages[:10], 1):
            title = escape(tp.get("title", "?"))
            url = escape(tp.get("url", "#"))
            refs = tp.get("in_degree", 0)
            # Importance bar width relative to max
            max_refs = top_pages[0].get("in_degree", 1) if top_pages else 1
            pct = int((refs / max(max_refs, 1)) * 100)
            parts.append(
                f'<li>'
                f'<span class="rank">{idx}</span>'
                f'<a class="page-link" href="{url}">{title}</a>'
                f'<span class="imp-bar-wrap"><span class="imp-bar-fill" style="width:{pct}%"></span></span>'
                f'<span class="ref-count">{refs}</span>'
                f'</li>\n'
            )
        parts.append('</ul>\n')

    parts.append('</div>\n</main>\n')
    parts.append(render_graph_panel())
    parts.append('</div>\n')  # close .app-layout
    parts.append(page_foot())
    return "".join(parts)


# ===========================================================================
# CATEGORY INDEX
# ===========================================================================


def render_category_index(category: str, pages: list) -> str:
    """Render a category index page with filter bar and sortable table."""
    display_name = escape(_format_category_display(category))
    cat_url = category.lower()
    cat_summary = {}
    # Build minimal sidebar data
    cat_summary[category] = pages

    parts = [
        page_head(display_name, f"All {display_name} pages"),
        '<div class="app-layout">\n',
        _topbar("categories"),
        render_sidebar(cat_summary, category),
        '<main class="main-content">\n<div class="content-wrapper">\n',
        breadcrumbs([
            ("Home", "/"),
            ("Categories", "/categories/"),
            (display_name, f"/categories/{escape(cat_url)}/"),
        ]),
        f'<h1 class="page-title">{display_name}</h1>\n',
        f'<p class="page-count">{len(pages)} pages</p>\n',
        '<div class="filter-bar">'
        '<input type="text" placeholder="Filter pages\u2026" '
        'class="filter-input" autocomplete="off">'
        '</div>\n',
        '<table class="pages-table">\n',
        '<thead><tr>'
        '<th>Title</th>'
        '<th>Tags</th>'
        '<th>Importance</th>'
        '<th>Type</th>'
        '</tr></thead>\n',
        '<tbody>\n',
    ]

    sorted_pages = sorted(
        pages, key=lambda x: x.get("importance", 0), reverse=True
    )
    for p in sorted_pages:
        tags = p.get("tags", [])
        tags_html = " ".join(
            f'<span class="tag">{escape(t)}</span>' for t in tags
        )
        imp = p.get("importance", 0)
        imp_pct = int(imp * 100)
        title = escape(p.get("title", "?"))
        url = escape(p.get("url", "#"))
        ptype = escape(p.get("category", "")[:20])
        data_tags = escape(" ".join(tags))
        parts.append(
            f'<tr data-tags="{data_tags}">'
            f'<td><a href="{url}">{title}</a></td>'
            f'<td>{tags_html}</td>'
            f'<td><div class="imp-bar"><div class="imp-bar-fill" style="width:{imp_pct}%"></div></div></td>'
            f'<td><span class="type-badge">{ptype}</span></td>'
            f'</tr>\n'
        )

    parts.append('</tbody></table>\n')
    parts.append('</div>\n</main>\n')
    parts.append(render_graph_panel())
    parts.append('</div>\n')  # close .app-layout
    parts.append(page_foot())
    return "".join(parts)


# ===========================================================================
# PAGE DETAIL
# ===========================================================================


def render_page_detail(page: dict, backlinks: list) -> str:
    """Render a page detail view with metadata, body, refs, and backlinks."""
    title = escape(page.get("title", "Untitled"))
    cat = page.get("category", "")
    cat_display = escape(_format_category_display(cat)) if cat else "Uncategorized"
    cat_url = cat.lower() if cat else "uncategorized"
    page_id = page.get("id", "")
    slug = page_id.split("/")[-1] if "/" in page_id else page_id

    parts = [
        page_head(title, f"Detail page for {title}"),
        '<div class="app-layout">\n',
        _topbar(),
        # Minimal sidebar for detail pages
        '<aside class="sidebar">\n'
        '<div class="sidebar-search">\U0001F50D Search pages\u2026</div>\n'
        f'<div class="sidebar-section">\n'
        f'<div class="sidebar-section-header"><span>{cat_display}</span></div>\n'
        f'<ul class="sidebar-tree">\n'
        f'<li><a class="sidebar-tree-item active" href="#">{title[:30]}</a></li>\n'
        f'</ul>\n</div>\n'
        '</aside>\n',
        '<main class="main-content">\n<div class="content-wrapper">\n',
        breadcrumbs([
            ("Home", "/"),
            ("Categories", "/categories/"),
            (cat_display, f"/categories/{escape(cat_url)}/"),
            (title, "#"),
        ]),
        '<article class="page-detail">\n',
    ]

    # Metadata bar
    parts.append('<div class="meta-bar">\n')
    parts.append(
        f'<span class="meta-item">'
        f'<span class="meta-label">Type</span>'
        f'<span class="type-badge">{escape(cat)}</span></span>\n'
    )
    lang = page.get("language", "")
    if lang:
        parts.append(
            f'<span class="meta-item">'
            f'<span class="meta-label">Language</span> {escape(lang)}</span>\n'
        )
    tags = page.get("tags", [])
    if tags:
        tags_html = " ".join(
            f'<span class="tag">{escape(t)}</span>' for t in tags
        )
        parts.append(
            f'<span class="meta-item">'
            f'<span class="meta-label">Tags</span> {tags_html}</span>\n'
        )
    imp = page.get("importance", 0)
    parts.append(
        f'<span class="meta-item">'
        f'<span class="meta-label">Importance</span> {imp:.2f}</span>\n'
    )
    source = page.get("source_path", "")
    if source:
        parts.append(
            f'<span class="meta-item">'
            f'<span class="meta-label">Source</span> '
            f'<code>{escape(source)}</code></span>\n'
        )
    parts.append('</div>\n')

    # Body — markdown to HTML
    body = page.get("body", "")
    if body:
        parts.append(f'<div class="page-body">{md_to_html(body)}</div>\n')

    # Cross-references (outbound)
    refs = page.get("references", [])
    if refs:
        parts.append('<section class="cross-refs">\n<h2>References \u2192</h2>\n<ul>\n')
        for r in refs:
            ref_str = str(r)
            parts.append(
                f'<li><span class="ref-arrow">\u2192</span> {escape(ref_str)}</li>\n'
            )
        parts.append('</ul>\n</section>\n')

    # Backlinks (inbound)
    if backlinks:
        parts.append('<section class="backlinks">\n<h2>Referenced By \u2190</h2>\n<ul>\n')
        for bl in backlinks:
            bl_title = escape(bl.get("title", "?"))
            bl_url = escape(bl.get("url", "#"))
            parts.append(
                f'<li><span class="ref-arrow">\u2190</span> '
                f'<a href="{bl_url}">{bl_title}</a></li>\n'
            )
        parts.append('</ul>\n</section>\n')

    # JSON sibling link
    if slug:
        parts.append(
            f'<a class="json-link" href="{escape(slug)}.json">'
            f'\U0001F4CB JSON (for AI agents)</a>\n'
        )

    parts.append('</article>\n')
    parts.append('</div>\n</main>\n')
    parts.append(render_graph_panel(page_id))
    parts.append('</div>\n')  # close .app-layout
    parts.append(page_foot())
    return "".join(parts)


# ===========================================================================
# GRAPH PAGE (full)
# ===========================================================================


def render_graph_page(graph: dict) -> str:
    """Render interactive knowledge graph page using vis-network CDN."""
    nodes_json = json.dumps(graph.get("nodes", []))
    edges_json = json.dumps(graph.get("edges", []))
    stats = graph.get("stats", {})

    parts = [
        page_head("Knowledge Graph", "Interactive knowledge graph visualization"),
        '<div class="app-layout">\n',
        _topbar("graph"),
        '<aside class="sidebar">\n'
        '<div class="sidebar-search">\U0001F50D Search pages\u2026</div>\n'
        '</aside>\n',
        '<main class="main-content" style="padding:0;">\n',
        '<div style="padding:var(--sp-4);display:flex;align-items:center;gap:var(--sp-4);">'
        '<h1 style="font-size:20px;font-weight:600;margin:0;">Knowledge Graph</h1>'
        f'<span class="text-muted" style="font-size:12px;">'
        f'{stats.get("total_pages", 0)} nodes \u00b7 '
        f'{stats.get("total_edges", 0)} edges \u00b7 '
        f'{stats.get("total_clusters", 0)} clusters</span>'
        '</div>\n',
        '<div id="graph-container" style="width:100%;height:calc(100vh - '
        'var(--topbar-height) - 60px);background:var(--canvas);"></div>\n',
        '<script src="https://cdn.jsdelivr.net/npm/vis-network@9/standalone/'
        'umd/vis-network.min.js" crossorigin="anonymous"></script>\n',
        '<script>\n(function(){\n"use strict";\n',
        'var rawNodes = ', nodes_json, ';\n',
        'var rawEdges = ', edges_json, ';\n',
        _GRAPH_SCRIPT,
        '})();\n</script>\n',
        '</main>\n',
        '</div>\n',  # close .app-layout
        page_foot(),
    ]
    return "".join(parts)


_GRAPH_SCRIPT = """\
var TYPE_COLORS = {
  "rule": "#f59e0b", "workflow": "#6366f1", "application": "#10b981",
  "task": "#f97316", "report": "#ef4444", "custom": "#8b5cf6",
  "emailtemplate": "#ec4899", "connector-guides": "#14b8a6",
  "iiq-docs": "#f59e0b", "quicklink": "#8b5cf6",
  "beanshell": "#ec4899", "config": "#8b5cf6", "docs": "#10b981",
};

function typeColor(cat) {
  if (!cat) return "#71717a";
  var base = cat.split("/")[0].toLowerCase();
  return TYPE_COLORS[base] || "#71717a";
}

var fontColor = "#e4e4e7";

var visNodes = rawNodes.map(function(n) {
  var imp = n.importance || 0;
  var size = 6 + imp * 35;
  return {
    id: n.id,
    label: n.title || n.id,
    size: size,
    color: { background: typeColor(n.category), border: typeColor(n.category),
             highlight: { background: "#10b981", border: "#34d399" } },
    font: { color: fontColor, size: Math.max(9, size * 0.55) },
    title: (n.title || n.id) + " (" + (n.category || "?") + ")\\nImportance: " + imp.toFixed(2),
    _url: "/categories/" + (n.category || "uncategorized").toLowerCase() + "/" + n.id.split("/").pop() + ".html",
  };
});

var visEdges = rawEdges.map(function(e) {
  return { from: e.from, to: e.to, arrows: "to",
           color: { color: "#3f3f46", opacity: 0.5, highlight: "#10b981" } };
});

var container = document.getElementById("graph-container");
if (container && typeof vis !== "undefined") {
  var network = new vis.Network(container, {
    nodes: new vis.DataSet(visNodes),
    edges: new vis.DataSet(visEdges),
  }, {
    physics: {
      solver: "forceAtlas2Based",
      forceAtlas2Based: { gravitationalConstant: -30, centralGravity: 0.005, springLength: 100 },
      stabilization: { iterations: 150 },
    },
    interaction: { hover: true, tooltipDelay: 100 },
    nodes: { shape: "dot", borderWidth: 2 },
    edges: { smooth: { type: "continuous" } },
  });

  network.on("click", function(params) {
    if (params.nodes.length > 0) {
      var nodeId = params.nodes[0];
      var node = visNodes.find(function(n) { return n.id === nodeId; });
      if (node && node._url) window.location.href = node._url;
    }
  });
}
"""


# ===========================================================================
# CHANGELOG
# ===========================================================================


def render_changelog_page(history: list) -> str:
    """Render changelog page from build history entries."""
    parts = [
        page_head("Changelog", "Build history and changes"),
        '<div class="app-layout">\n',
        _topbar("changelog"),
        '<aside class="sidebar">\n'
        '<div class="sidebar-search">\U0001F50D Search pages\u2026</div>\n'
        '</aside>\n',
        '<main class="main-content">\n<div class="content-wrapper">\n',
        '<h1 class="page-title">Changelog</h1>\n',
    ]

    if not history:
        parts.append(
            '<p class="text-muted">No build history yet. '
            'Run <code>llmwiki all</code> to generate the first build.</p>\n'
        )
    else:
        parts.append('<table class="pages-table">\n')
        parts.append(
            '<thead><tr><th>Build Date</th><th>Pages</th>'
            '<th>Categories</th><th>Cross-refs</th><th>Clusters</th>'
            '</tr></thead>\n'
        )
        parts.append('<tbody>\n')
        for entry in reversed(history):
            ts = escape(entry.get("timestamp", "?"))
            try:
                from datetime import datetime as _dt
                dt = _dt.fromisoformat(ts)
                display_ts = dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                display_ts = ts
            parts.append(
                f'<tr>'
                f'<td>{escape(display_ts)}</td>'
                f'<td>{entry.get("total_pages", 0)}</td>'
                f'<td>{entry.get("total_categories", 0)}</td>'
                f'<td>{entry.get("total_edges", 0)}</td>'
                f'<td>{entry.get("total_clusters", 0)}</td>'
                f'</tr>\n'
            )
        parts.append('</tbody></table>\n')

    parts.append('</div>\n</main>\n')
    parts.append(render_graph_panel())
    parts.append('</div>\n')  # close .app-layout
    parts.append(page_foot())
    return "".join(parts)


# ===========================================================================
# CATEGORIES INDEX
# ===========================================================================


def render_categories_index(categories: dict) -> str:
    """Render the /categories/ index page listing all categories."""
    total = len(categories)
    parts = [
        page_head("All Categories", f"Browse all {total} categories"),
        '<div class="app-layout">\n',
        _topbar("categories"),
        render_sidebar(categories),
        '<main class="main-content">\n<div class="content-wrapper">\n',
        breadcrumbs([("Home", "/"), ("Categories", "#")]),
        f'<h1 class="page-title">All Categories ({total})</h1>\n',
        '<div class="filter-bar">'
        '<input type="text" placeholder="Filter categories\u2026" '
        'class="filter-input" autocomplete="off">'
        '</div>\n',
        '<div class="card-grid">\n',
    ]

    sorted_cats = sorted(
        categories.items(),
        key=lambda item: len(item[1]) if isinstance(item[1], list) else 0,
        reverse=True,
    )
    for cat_name, cat_pages in sorted_cats:
        count = len(cat_pages) if isinstance(cat_pages, list) else 0
        display = escape(_format_category_display(cat_name))
        cat_url = escape(cat_name.lower())
        parts.append(
            f'<a href="/categories/{cat_url}/" '
            f'class="card" data-tags="{escape(cat_name.lower())}">'
            f'<h3>{display}</h3>'
            f'<span class="card-meta">{count} pages</span></a>\n'
        )

    parts.append('</div>\n')
    parts.append('</div>\n</main>\n')
    parts.append(render_graph_panel())
    parts.append('</div>\n')  # close .app-layout
    parts.append(page_foot())
    return "".join(parts)
