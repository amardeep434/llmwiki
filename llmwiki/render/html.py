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

    # Category cards
    if categories:
        parts.append(
            '<section class="categories"><h2>Categories</h2>'
            '<div class="card-grid">\n'
        )
        for cat_name in sorted(categories.keys()):
            cat_data = categories[cat_name]
            count = cat_data.get("count", 0)
            display = escape(cat_name.replace("-", " ").title())
            parts.append(
                f'<a href="/categories/{escape(cat_name)}/" '
                f'class="category-card">'
                f'<h3>{display}</h3>'
                f'<span class="card-count">{count} pages</span></a>\n'
            )
        parts.append('</div></section>\n')

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
    display_name = escape(
        category.replace("-", " ").replace("/", " \u203A ").title()
    )
    parts = [
        page_head(display_name, f"All {display_name} pages"),
        nav_bar("categories"),
        breadcrumbs([
            ("Home", "/"),
            ("Categories", "/categories/"),
            (display_name, "#"),
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
    parts = [
        page_head(title, f"Detail page for {title}"),
        nav_bar(),
        breadcrumbs([
            ("Home", "/"),
            ("Categories", "/categories/"),
            (escape(cat.title()), f"/categories/{escape(cat)}/"),
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
