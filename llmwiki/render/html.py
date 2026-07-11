"""HTML page generator functions.

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


def page_head(title: str, description: str = "") -> str:
    """Generate <!DOCTYPE> through opening <body>."""
    safe_title = escape(title)
    safe_desc = escape(description)
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{safe_title} — LLMWiki</title>\n'
        f'<meta name="description" content="{safe_desc}">\n'
        '<link rel="stylesheet" href="/style.css">\n'
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/'
        'cdn-release@11.9.0/build/styles/github.min.css" '
        'media="(prefers-color-scheme: light)" crossorigin="anonymous">\n'
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/'
        'cdn-release@11.9.0/build/styles/github-dark.min.css" '
        'media="(prefers-color-scheme: dark)" crossorigin="anonymous">\n'
        f'<script>{PRE_PAINT_SCRIPT}</script>\n'
        '</head>\n'
        '<body>\n'
    )


def nav_bar(active: str = "") -> str:
    """Generate sticky navigation bar."""
    links = [
        ("Home", "/", "home"),
        ("Categories", "/categories/", "categories"),
        ("Graph", "/graph.html", "graph"),
        ("Changelog", "/changelog.html", "changelog"),
    ]
    items = []
    for label, href, key in links:
        cls = ' class="active"' if key == active else ""
        items.append(f'<a href="{href}"{cls}>{escape(label)}</a>')

    return (
        '<nav class="nav-bar">\n'
        '<div class="nav-brand"><a href="/">\U0001F4DA LLMWiki</a></div>\n'
        f'<div class="nav-links">{"".join(items)}</div>\n'
        '<div class="nav-actions">\n'
        '<button class="nav-search" aria-label="Search (Cmd+K)">'
        '\U0001F50D</button>\n'
        '<button class="theme-toggle" aria-label="Toggle theme">'
        '\U0001F319</button>\n'
        '</div>\n'
        '</nav>\n'
    )


def breadcrumbs(crumbs: List[Tuple[str, str]]) -> str:
    """Generate breadcrumb navigation from list of (label, href) tuples."""
    if not crumbs:
        return ""
    parts = []
    for label, href in crumbs[:-1]:
        parts.append(f'<a href="{escape(href)}">{escape(label)}</a>')
    parts.append(f'<span>{escape(crumbs[-1][0])}</span>')
    return (
        '<nav class="breadcrumbs" aria-label="Breadcrumb">'
        f'{" \u203A ".join(parts)}'
        '</nav>\n'
    )


def page_foot() -> str:
    """Generate command palette HTML + scripts + closing tags."""
    return (
        '\n<div id="command-palette" class="palette-overlay" hidden>\n'
        '<div class="palette-dialog">\n'
        '<input type="text" class="palette-input" '
        'placeholder="Search pages... (type:, category:, tag:)">\n'
        '<div class="palette-results"></div>\n'
        '<div class="palette-hints">'
        '\u2191\u2193 navigate \u00B7 \u21B5 open \u00B7 esc close'
        '</div>\n'
        '</div>\n'
        '</div>\n'
        '<script src="https://cdn.jsdelivr.net/gh/highlightjs/'
        'cdn-release@11.9.0/build/highlight.min.js" defer '
        'crossorigin="anonymous"></script>\n'
        '<!-- To generate SRI hash: curl -s https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js | openssl dgst -sha384 -binary | openssl base64 -A -->\n'
        '<script src="/script.js" defer></script>\n'
        '</body>\n'
        '</html>\n'
    )


def md_to_html(body: str) -> str:
    """Convert markdown body to HTML."""
    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "toc", "sane_lists"]
    )
    return _sanitize_html(md.convert(body))


def _format_category_display(name: str) -> str:
    """Format a category name for display.

    Replaces '/' with ' › ', '-' with spaces, and title-cases.
    """
    return name.replace("-", " ").replace("/", " › ").title()


def render_dashboard(
    stats: dict,
    recent_changes: list,
    categories: dict,
    top_pages: list,
) -> str:
    """Render the dashboard home page.

    Args:
        stats: Graph stats dict with total_pages, total_edges, etc.
        recent_changes: List of change dicts with type, title, url.
        categories: {category_name: {"count": N}} dict.
        top_pages: List of page dicts with title, url, in_degree.
    """
    parts = [
        page_head("Home", "Knowledge base dashboard"),
        nav_bar("home"),
        '<main class="container">\n',
        '<section class="hero"><h1>\U0001F4DA Knowledge Base</h1></section>\n',
    ]

    # Stats strip
    total_pages = stats.get("total_pages", 0)
    total_edges = stats.get("total_edges", 0)
    total_clusters = stats.get("total_clusters", 0)
    parts.append('<div class="stats-strip">\n')
    for num, label in [
        (total_pages, "Pages"),
        (total_edges, "Cross-refs"),
        (total_clusters, "Topics"),
    ]:
        parts.append(
            f'<div class="stat-card">'
            f'<span class="stat-num">{num}</span>'
            f'<span class="stat-label">{label}</span>'
            f'</div>\n'
        )
    parts.append('</div>\n')

    # Recent changes
    if recent_changes:
        parts.append(
            '<section class="recent-changes"><h2>Recent Changes</h2><ul>\n'
        )
        icons = {"added": "\U0001F7E2", "updated": "\U0001F7E1", "archived": "\U0001F534"}
        for change in recent_changes[:10]:
            ctype = change.get("type", "")
            icon = icons.get(ctype, "\u26AA")
            title = escape(change.get("title", "Unknown"))
            url = escape(change.get("url", "#"))
            parts.append(
                f'<li>{icon} <strong>{escape(ctype.upper())}</strong> '
                f'<a href="{url}">{title}</a></li>\n'
            )
        parts.append('</ul></section>\n')

    # Category cards — limited to top 20 by page count
    if categories:
        total_cat_count = len(categories)
        sorted_cats = sorted(
            categories.items(),
            key=lambda item: item[1].get("count", 0),
            reverse=True,
        )
        display_limit = 20
        shown_cats = sorted_cats[:display_limit]

        parts.append(
            '<section class="categories"><h2>Categories</h2>'
            '<div class="card-grid">\n'
        )
        for cat_name, cat_data in shown_cats:
            count = cat_data.get("count", 0)
            display = escape(_format_category_display(cat_name))
            cat_url = escape(cat_name.lower())
            parts.append(
                f'<a href="/categories/{cat_url}/" '
                f'class="category-card">'
                f'<h3>{display}</h3>'
                f'<span class="card-count">{count} pages</span></a>\n'
            )
        parts.append('</div>\n')
        if total_cat_count > display_limit:
            parts.append(
                f'<p class="view-all-link">'
                f'<a href="/categories/">View all {total_cat_count} categories →</a>'
                f'</p>\n'
            )
        parts.append('</section>\n')

    # Most connected pages
    if top_pages:
        parts.append(
            '<section class="top-pages"><h2>Most Connected</h2><ol>\n'
        )
        for tp in top_pages[:10]:
            title = escape(tp.get("title", "?"))
            url = escape(tp.get("url", "#"))
            refs = tp.get("in_degree", 0)
            parts.append(
                f'<li><a href="{url}">{title}</a>'
                f' <span class="ref-count">{refs} refs</span></li>\n'
            )
        parts.append('</ol></section>\n')

    parts.append('</main>\n')
    parts.append(page_foot())
    return "".join(parts)


def render_category_index(category: str, pages: list) -> str:
    """Render a category index page with filter bar and sortable table.

    Args:
        category: Category slug.
        pages: List of page dicts with title, tags, importance, url.
    """
    display_name = escape(_format_category_display(category))
    cat_url = category.lower()
    parts = [
        page_head(display_name, f"All {display_name} pages"),
        nav_bar("categories"),
        breadcrumbs([
            ("Home", "/"),
            ("Categories", "/categories/"),
            (display_name, f"/categories/{escape(cat_url)}/"),
        ]),
        '<main class="container">\n',
        f'<h1>{display_name}</h1>\n',
        f'<p>{len(pages)} pages</p>\n',
        '<div class="filter-bar">'
        '<input type="text" placeholder="Filter pages..." '
        'class="filter-input">'
        '</div>\n',
        '<table class="pages-table">\n',
        '<thead><tr><th>Title</th><th>Tags</th><th>Importance</th>'
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
        data_tags = escape(" ".join(tags))
        parts.append(
            f'<tr data-tags="{data_tags}">'
            f'<td><a href="{url}">{title}</a></td>'
            f'<td>{tags_html}</td>'
            f'<td><div class="imp-bar" style="width:{imp_pct}%"></div></td>'
            f'</tr>\n'
        )

    parts.append('</tbody></table>\n')
    parts.append('</main>\n')
    parts.append(page_foot())
    return "".join(parts)


def render_page_detail(page: dict, backlinks: list) -> str:
    """Render a page detail view with metadata, body, refs, and backlinks.

    Args:
        page: Page dict with title, category, language, tags, importance,
              body, references.
        backlinks: List of dicts with title and url.
    """
    title = escape(page.get("title", "Untitled"))
    cat = page.get("category", "")
    cat_display = escape(_format_category_display(cat)) if cat else "Uncategorized"
    cat_url = cat.lower() if cat else "uncategorized"
    parts = [
        page_head(title, f"Detail page for {title}"),
        nav_bar(),
        breadcrumbs([
            ("Home", "/"),
            ("Categories", "/categories/"),
            (cat_display, f"/categories/{escape(cat_url)}/"),
            (title, "#"),
        ]),
        '<main class="container">\n',
        '<article class="page-detail">\n',
    ]

    # Metadata card
    parts.append('<div class="meta-card">\n')
    parts.append(
        f'<span><strong>Type:</strong> {escape(cat)}</span>\n'
    )
    lang = page.get("language", "")
    if lang:
        parts.append(
            f'<span><strong>Language:</strong> {escape(lang)}</span>\n'
        )
    tags = page.get("tags", [])
    if tags:
        tags_html = " ".join(
            f'<span class="tag">{escape(t)}</span>' for t in tags
        )
        parts.append(
            f'<span><strong>Tags:</strong> {tags_html}</span>\n'
        )
    imp = page.get("importance", 0)
    parts.append(
        f'<span><strong>Importance:</strong> {imp:.2f}</span>\n'
    )
    parts.append('</div>\n')

    # Body — markdown to HTML
    body = page.get("body", "")
    if body:
        parts.append(md_to_html(body))
        parts.append('\n')

    # Cross-references (outbound)
    refs = page.get("references", [])
    if refs:
        parts.append(
            '<section class="cross-refs"><h2>References</h2><ul>\n'
        )
        for r in refs:
            parts.append(f'<li>\u2192 {escape(str(r))}</li>\n')
        parts.append('</ul></section>\n')

    # Backlinks (inbound)
    if backlinks:
        parts.append(
            '<section class="backlinks"><h2>Referenced By</h2><ul>\n'
        )
        for bl in backlinks:
            bl_title = escape(bl.get("title", "?"))
            bl_url = escape(bl.get("url", "#"))
            parts.append(
                f'<li>\u2190 <a href="{bl_url}">{bl_title}</a></li>\n'
            )
        parts.append('</ul></section>\n')

    parts.append('</article>\n')
    parts.append('</main>\n')
    parts.append(page_foot())
    return "".join(parts)


def render_graph_page(graph: dict) -> str:
    """Render interactive knowledge graph page using vis-network CDN."""
    nodes_json = json.dumps(graph.get("nodes", []))
    edges_json = json.dumps(graph.get("edges", []))
    stats = graph.get("stats", {})

    parts = [
        page_head("Knowledge Graph", "Interactive knowledge graph visualization"),
        nav_bar("graph"),
        '<main class="container">\n',
        '<h1>Knowledge Graph</h1>\n',
        f'<p class="text-muted">'
        f'{stats.get("total_pages", 0)} nodes · '
        f'{stats.get("total_edges", 0)} edges · '
        f'{stats.get("total_clusters", 0)} clusters</p>\n',
        '<div id="graph-container" style="width:100%;height:70vh;'
        'border:1px solid var(--border);border-radius:var(--radius-lg);'
        'background:var(--card-bg);margin-top:1rem;"></div>\n',
        '<script src="https://cdn.jsdelivr.net/npm/vis-network@9/standalone/'
        'umd/vis-network.min.js" crossorigin="anonymous"></script>\n',
        '<script>\n',
        '(function(){\n',
        '"use strict";\n',
        'var rawNodes = ', nodes_json, ';\n',
        'var rawEdges = ', edges_json, ';\n',
        _GRAPH_SCRIPT,
        '})();\n',
        '</script>\n',
        '</main>\n',
        page_foot(),
    ]
    return "".join(parts)


_GRAPH_SCRIPT = """\
var CATEGORY_COLORS = {
  "rule": "#7C3AED", "workflow": "#2563EB", "application": "#059669",
  "task": "#D97706", "report": "#DC2626", "custom": "#6366F1",
  "emailtemplate": "#EC4899", "connector-guides": "#14B8A6",
  "iiq-docs": "#F59E0B", "quicklink": "#8B5CF6",
};

function catColor(cat) {
  if (!cat) return "#6B7280";
  var base = cat.split("/")[0].toLowerCase();
  return CATEGORY_COLORS[base] || "#6B7280";
}

var isDark = document.documentElement.getAttribute("data-theme") === "dark";
var fontColor = isDark ? "#e2e8f0" : "#1a1a2e";

var visNodes = rawNodes.map(function(n) {
  var imp = n.importance || 0;
  var size = 8 + imp * 40;
  return {
    id: n.id,
    label: n.title || n.id,
    size: size,
    color: { background: catColor(n.category), border: catColor(n.category) },
    font: { color: fontColor, size: Math.max(10, size * 0.6) },
    title: (n.title || n.id) + " (" + (n.category || "?") + ")\\nImportance: " + imp.toFixed(2) + "\\nRefs: " + (n.in_degree || 0),
    _url: "/categories/" + (n.category || n.id).toLowerCase() + "/" + n.id.split("/").pop() + ".html",
  };
});

var visEdges = rawEdges.map(function(e, i) {
  return { from: e.from, to: e.to, arrows: "to", color: { color: "#9ca3af", opacity: 0.4 } };
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


def render_changelog_page(history: list) -> str:
    """Render changelog page from build history entries."""
    parts = [
        page_head("Changelog", "Build history and changes"),
        nav_bar("changelog"),
        '<main class="container">\n',
        '<h1>Changelog</h1>\n',
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
            # Format timestamp for display
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

    parts.append('</main>\n')
    parts.append(page_foot())
    return "".join(parts)


def render_categories_index(categories: dict) -> str:
    """Render the /categories/ index page listing all categories.

    Args:
        categories: {category_name: [page_dicts]} mapping.
    """
    total = len(categories)
    parts = [
        page_head("All Categories", f"Browse all {total} categories"),
        nav_bar("categories"),
        breadcrumbs([("Home", "/"), ("Categories", "#")]),
        '<main class="container">\n',
        f'<h1>All Categories ({total})</h1>\n',
        '<div class="filter-bar">'
        '<input type="text" placeholder="Filter categories..." '
        'class="filter-input">'
        '</div>\n',
        '<div class="card-grid">\n',
    ]

    sorted_cats = sorted(
        categories.items(),
        key=lambda item: len(item[1]),
        reverse=True,
    )
    for cat_name, cat_pages in sorted_cats:
        count = len(cat_pages)
        display = escape(_format_category_display(cat_name))
        cat_url = escape(cat_name.lower())
        parts.append(
            f'<a href="/categories/{cat_url}/" '
            f'class="category-card" data-tags="{escape(cat_name.lower())}">'
            f'<h3>{display}</h3>'
            f'<span class="card-count">{count} pages</span></a>\n'
        )

    parts.append('</div>\n')
    parts.append('</main>\n')
    parts.append(page_foot())
    return "".join(parts)
