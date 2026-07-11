"""HTML page generator functions — dark emerald three-panel design.

All HTML is generated programmatically — no template files.
Each function returns an HTML string for a specific page type.
Ported from approved preview — pixel-accurate match.
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


# --- Badge helpers ---

_TYPE_BADGE_MAP = {
    "rule": "beanshell", "beanshell": "beanshell",
    "workflow": "xml", "application": "config",
    "task": "java", "report": "java", "custom": "config",
    "connector-guides": "docs", "iiq-docs": "docs", "docs": "docs",
    "config": "config", "java": "java", "xml": "xml", "tokens": "tokens",
}

_BADGE_LABELS = {
    "java": "Java", "xml": "XML", "beanshell": "BSH",
    "config": "Config", "docs": "Docs", "tokens": "Token",
}


def _type_badge(category: str) -> str:
    """Return a type badge HTML span."""
    base = category.split("/")[0].lower() if category else "config"
    badge_type = _TYPE_BADGE_MAP.get(base, "config")
    label = _BADGE_LABELS.get(badge_type, badge_type.upper())
    return f'<span class="badge badge--{badge_type}">{escape(label)}</span>'


# FIX 8: Improved type badge detection using language + category
def _detect_type_badge(page_data: dict) -> str:
    """Detect the correct type badge from page data (language + category + source_path)."""
    lang = page_data.get("language", "")
    cat = page_data.get("category", "").lower()
    src = page_data.get("source_path", "").lower()
    # Detect from language field
    if lang == "java":
        return "java"
    if lang == "xml":
        return "xml"
    if lang == "python":
        return "java"  # reuse java badge for source code
    # Detect from source path extension
    if src.endswith(".java"):
        return "java"
    if src.endswith(".xml"):
        return "xml"
    # Detect from category
    if "beanshell" in cat:
        return "beanshell"
    if "connector" in cat or "iiq-docs" in cat or "docs" in cat:
        return "docs"
    if any(x in cat for x in ["rule", "workflow", "form", "task", "emailtemplate"]):
        return "xml"
    if "token" in cat:
        return "tokens"
    return "config"


def _detect_type_badge_html(page_data: dict) -> str:
    """Return a type badge HTML span using improved detection."""
    badge_type = _detect_type_badge(page_data)
    label = _BADGE_LABELS.get(badge_type, badge_type.upper())
    return f'<span class="badge badge--{badge_type}">{escape(label)}</span>'


# FIX 9: Extract clean metadata from source path
def _clean_source_display(source_path: str, language: str = "") -> dict:
    """Extract clean display info from absolute source path."""
    result = {}
    if not source_path:
        return result
    # Extract package name for Java files
    if language == "java" or source_path.endswith(".java"):
        # e.g. /home/.../src/com/vf/core/utility/AccountUtil.java -> com.vf.core.utility
        parts = source_path.replace("\\", "/").split("/")
        # Find 'com' or 'src' boundary
        for i, p in enumerate(parts):
            if p in ("com", "org", "net", "bsh", "sailpoint"):
                pkg_parts = parts[i:-1]  # exclude filename
                result["package"] = ".".join(pkg_parts)
                break
        result["filename"] = parts[-1] if parts else source_path
    elif language == "xml" or source_path.endswith(".xml"):
        parts = source_path.replace("\\", "/").split("/")
        # Find 'config' boundary
        for i, p in enumerate(parts):
            if p == "config":
                result["config_path"] = "/".join(parts[i:])
                break
        if "config_path" not in result:
            result["filename"] = parts[-1] if parts else source_path
    else:
        parts = source_path.replace("\\", "/").split("/")
        result["filename"] = parts[-1] if parts else source_path
    return result


# FIX 14: Strip raw javadoc tags from descriptions
def _clean_javadoc(body: str) -> str:
    """Strip raw @param, @throws, @return tags from body text for cleaner display."""
    # Remove @param lines
    body = re.sub(r'^\s*@param\s+\S+\s*.*$', '', body, flags=re.MULTILINE)
    # Remove @throws / @exception lines
    body = re.sub(r'^\s*@(?:throws|exception)\s+\S+\s*.*$', '', body, flags=re.MULTILINE)
    # Remove @return lines
    body = re.sub(r'^\s*@return\s*.*$', '', body, flags=re.MULTILINE)
    # Remove @see lines
    body = re.sub(r'^\s*@see\s*.*$', '', body, flags=re.MULTILINE)
    # Remove @since, @version, @author, @deprecated
    body = re.sub(r'^\s*@(?:since|version|author|deprecated)\s*.*$', '', body, flags=re.MULTILINE)
    # Collapse multiple blank lines
    body = re.sub(r'\n{3,}', '\n\n', body)
    return body.strip()


# FIX 13: Render code blocks with header + copy button
def _render_code_blocks(html_body: str) -> str:
    """Replace <pre><code> blocks with styled code-block structure."""
    def _replace_code_block(match):
        attrs = match.group(1) or ""
        code_content = match.group(2)
        # Extract language from class attribute
        lang_match = re.search(r'class="[^"]*language-(\w+)', attrs)
        lang = lang_match.group(1) if lang_match else "text"
        lang_display = lang.upper() if len(lang) <= 4 else lang.title()
        return (
            f'<div class="code-block">'
            f'<div class="code-block__header">'
            f'<span class="code-block__lang">{escape(lang_display)}</span>'
            f'<button class="code-block__copy" onclick="'
            f"navigator.clipboard.writeText(this.closest('.code-block')"
            f".querySelector('code').textContent)"
            f'">Copy</button>'
            f'</div>'
            f'<pre><code{attrs}>{code_content}</code></pre>'
            f'</div>'
        )
    return re.sub(
        r'<pre><code([^>]*)>(.*?)</code></pre>',
        _replace_code_block,
        html_body,
        flags=re.DOTALL,
    )


# ===========================================================================
# HEAD / FOOT
# ===========================================================================


def page_head(title: str, description: str = "",
              themes_json: str = "", theme_labels_json: str = "",
              color_options: list = None) -> str:
    """Generate <!DOCTYPE> through opening <body> with shell layout start."""
    safe_title = escape(title)
    safe_desc = escape(description)
    theme_script = ""
    if themes_json:
        theme_script = (
            f'<script>window.LLMWIKI_THEMES={themes_json};'
            f'window.LLMWIKI_THEME_LABELS={theme_labels_json};</script>\n'
        )
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en" data-theme="dark">\n'
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
        f'{theme_script}'
        '</head>\n'
        '<body>\n'
    )


def page_foot() -> str:
    """Generate command palette + scripts + closing tags."""
    return (
        '\n<!-- Command Palette -->\n'
        '<div id="command-palette" class="palette-overlay" hidden>\n'
        '<div class="palette">\n'
        '<div class="palette__input-wrap">\n'
        '<span class="palette__icon">\u2315</span>\n'
        '<input type="text" class="palette__input" '
        'placeholder="Search pages\u2026 (type:, category:, tag:)" autocomplete="off">\n'
        '</div>\n'
        '<div class="palette__results" style="max-height:320px;overflow-y:auto;"></div>\n'
        '<div class="palette__footer">'
        '<kbd>\u2191\u2193</kbd> navigate '
        '<kbd>\u21b5</kbd> open '
        '<kbd>esc</kbd> close '
        '<kbd>\u2318K</kbd> search'
        '</div>\n'
        '</div>\n'
        '</div>\n'
        '<!-- Bottom Tab Bar (mobile) -->\n'
        '<div class="bottom-tabs" style="display:none;position:fixed;bottom:0;left:0;right:0;'
        'background:var(--surface-1);border-top:1px solid var(--hairline);z-index:50;">\n'
        '<nav style="display:flex;justify-content:space-around;padding:6px 0;">\n'
        '<a href="/" style="font-size:11px;text-align:center;color:var(--ink-muted);text-decoration:none;">'
        '<span style="display:block;font-size:16px;">\U0001F3E0</span>Home</a>\n'
        '<a href="#" data-action="search" style="font-size:11px;text-align:center;color:var(--ink-muted);text-decoration:none;">'
        '<span style="display:block;font-size:16px;">\U0001F50D</span>Search</a>\n'
        '<a href="/graph.html" style="font-size:11px;text-align:center;color:var(--ink-muted);text-decoration:none;">'
        '<span style="display:block;font-size:16px;">\U0001F578\uFE0F</span>Graph</a>\n'
        '<a href="#" data-action="sidebar" style="font-size:11px;text-align:center;color:var(--ink-muted);text-decoration:none;">'
        '<span style="display:block;font-size:16px;">\u2630</span>Menu</a>\n'
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


def _topbar(active: str = "", color_options: list = None) -> str:
    """Generate the 48px sticky top bar matching preview."""
    links = [
        ("Home", "/", "home"),
        ("Categories", "/categories/", "categories"),
        ("Graph", "/graph.html", "graph"),
        ("Changelog", "/changelog.html", "changelog"),
    ]
    nav_items = []
    for label, href, key in links:
        cls = " topbar__link--active" if key == active else ""
        nav_items.append(
            f'<a href="{href}" class="topbar__link{cls}">{escape(label)}</a>'
        )

    # Theme color selector
    options_html = ""
    if color_options:
        for val, display in color_options:
            sym = "\u25C6" if val != "vodafone" else "\u25CF"
            options_html += f'<option value="{escape(val)}">{sym} {escape(display)}</option>\n'
    else:
        options_html = (
            '<option value="emerald-dark">\u25C6 Emerald</option>\n'
            '<option value="vodafone">\u25CF Vodafone</option>\n'
        )

    return (
        '<header class="topbar">\n'
        '<div class="topbar__brand">\n'
        '<span class="topbar__brand-icon">\u25C6</span>\n'
        '<span>LLMWiki</span>\n'
        '</div>\n'
        f'<nav class="topbar__nav">{"".join(nav_items)}</nav>\n'
        '<div class="topbar__spacer"></div>\n'
        '<div class="topbar__search">\n'
        '<kbd>\u2318K</kbd>\n'
        '<span>Search\u2026</span>\n'
        '</div>\n'
        f'<select class="theme-select" id="theme-select">\n{options_html}</select>\n'
        '<button class="topbar__btn graph-toggle" title="Graph toggle">\u2B21</button>\n'
        '<button class="topbar__btn" id="theme-toggle" title="Toggle dark/light mode">\u25D0</button>\n'
        '</header>\n'
    )


# Keep backward-compatible name
def nav_bar(active: str = "", color_options: list = None) -> str:
    """Generate navigation bar (alias for _topbar)."""
    return _topbar(active, color_options)


# ===========================================================================
# SIDEBAR
# ===========================================================================


def render_sidebar(categories: dict, current_category: str = "",
                   current_url: str = "", clusters: list = None,
                   total_pages: int = 0) -> str:
    """Generate left sidebar with collapsible category tree."""
    # Calculate total pages if not provided
    if not total_pages:
        for cat_pages in categories.values():
            if isinstance(cat_pages, list):
                total_pages += len(cat_pages)
            elif isinstance(cat_pages, dict):
                total_pages += cat_pages.get("count", 0)

    parts = [
        '<aside class="sidebar">\n',
        '<div class="sidebar__section">\n',
        '<div class="sidebar__heading">Navigation</div>\n',
    ]

    # Dashboard link — FIX 12: active state
    dash_active = " sidebar__item--active" if current_url == "/" else ""
    parts.append(
        f'<a href="/" class="sidebar__item{dash_active}"><span class="sidebar__item-icon">\u25C6</span>'
        f'<span>Dashboard</span></a>\n'
    )

    # FIX 5: All Pages link
    all_pages_active = " sidebar__item--active" if current_url == "/categories/" else ""
    parts.append(
        f'<a href="/categories/" class="sidebar__item{all_pages_active}">'
        f'<span class="sidebar__item-icon">\u25A3</span>'
        f'<span>All Pages ({total_pages})</span></a>\n'
    )

    # Graph link
    graph_active = " sidebar__item--active" if current_url == "/graph.html" else ""
    parts.append(
        f'<a href="/graph.html" class="sidebar__item{graph_active}"><span class="sidebar__item-icon">\u25C8</span>'
        f'<span>Full Graph</span></a>\n'
    )
    parts.append('</div>\n')

    # FIX 4: Clusters section
    if clusters:
        parts.append('<div class="sidebar__section">\n')
        parts.append('<div class="sidebar__heading">Clusters</div>\n')
        for cluster in clusters[:15]:
            cl_label = escape(cluster.get("label", f"Cluster {cluster.get('id', '?')}"))
            cl_count = cluster.get("member_count", len(cluster.get("members", [])))
            parts.append(
                f'<div class="sidebar__item">'
                f'<span class="sidebar__item-icon">\u25CB</span>'
                f'<span>{cl_label}</span>'
                f'<span class="sidebar__item-count">{cl_count}</span></div>\n'
            )
        parts.append('</div>\n')

    # Categories section
    parts.append(
        '<div class="sidebar__section">\n'
        '<div class="sidebar__heading">Categories</div>\n'
    )

    sorted_cats = sorted(categories.items(), key=lambda x: x[0].lower())
    for cat_name, cat_pages in sorted_cats:
        count = len(cat_pages) if isinstance(cat_pages, list) else (
            cat_pages.get("count", 0) if isinstance(cat_pages, dict) else 0
        )
        display = escape(_format_category_display(cat_name))
        cat_url = cat_name.lower()
        is_active = cat_name.lower() == current_category.lower() if current_category else False
        active_cls = " sidebar__item--active" if is_active else ""

        parts.append(
            f'<a href="/categories/{escape(cat_url)}/" class="sidebar__item{active_cls}" '
            f'data-href="/categories/{escape(cat_url)}/">'
            f'<span class="sidebar__item-icon">\u25B8</span>'
            f'<span>{display}</span>'
            f'<span class="sidebar__item-count">{count}</span></a>\n'
        )

        # FIX 11: Show nested tree items for categories (top 5 pages)
        if isinstance(cat_pages, list) and (is_active or count <= 5):
            show_pages = cat_pages[:5]
            if show_pages:
                parts.append('<div class="sidebar__nested-section">\n<ul class="sidebar__tree sidebar__tree--nested">\n')
                for p in show_pages:
                    p_title = escape(p.get("title", "?")[:30])
                    p_url = p.get("url", "#")
                    # FIX 12: active state for nested items
                    nested_active = " sidebar__item--active" if current_url and current_url == p_url else ""
                    parts.append(
                        f'<li><a class="sidebar__item{nested_active}" href="{escape(p_url)}" data-href="{escape(p_url)}">'
                        f'<span class="sidebar__item-icon">\u00B7</span>'
                        f'<span>{p_title}</span></a></li>\n'
                    )
                if count > 5:
                    parts.append(
                        f'<li><a class="sidebar__item" href="/categories/{escape(cat_url)}/">'
                        f'<span class="sidebar__item-icon">\u2026</span>'
                        f'<span>{count - 5} more</span></a></li>\n'
                    )
                parts.append('</ul>\n</div>\n')

    parts.append('</div>\n</aside>\n')
    return "".join(parts)


# ===========================================================================
# GRAPH PANEL
# ===========================================================================


def render_graph_panel(page_id: str = "") -> str:
    """Generate right mini-graph panel matching preview."""
    return (
        '<div class="graph-panel">\n'
        '<div class="graph-panel__header">\n'
        '<span class="graph-panel__title">Local Graph</span>\n'
        '<a href="/graph.html" class="graph-panel__expand">Expand \u2192</a>\n'
        '</div>\n'
        '<div class="graph-panel__canvas">\n'
        '<div class="graph-panel__fade-top"></div>\n'
        '<div class="graph-panel__fade-bottom"></div>\n'
        f'<div id="mini-graph" data-page="{escape(page_id)}"></div>\n'
        '</div>\n'
        '<div class="graph-panel__legend">\n'
        '<div class="graph-panel__legend-item"><span class="graph-panel__legend-dot" '
        'style="background:var(--node-java)"></span><span>Java</span></div>\n'
        '<div class="graph-panel__legend-item"><span class="graph-panel__legend-dot" '
        'style="background:var(--node-xml)"></span><span>XML</span></div>\n'
        '<div class="graph-panel__legend-item"><span class="graph-panel__legend-dot" '
        'style="background:var(--node-beanshell)"></span><span>BSH</span></div>\n'
        '<div class="graph-panel__legend-item"><span class="graph-panel__legend-dot" '
        'style="background:var(--node-config)"></span><span>Config</span></div>\n'
        '<div class="graph-panel__legend-item"><span class="graph-panel__legend-dot" '
        'style="background:var(--node-tokens)"></span><span>Token</span></div>\n'
        '</div>\n'
        '</div>\n'
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
        parts.append('<span class="breadcrumbs__sep">\u203a</span>')
    parts.append(f'<span>{escape(crumbs[-1][0])}</span>')
    return f'<div class="breadcrumbs">{"".join(parts)}</div>\n'


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
    *,
    clusters: list = None,
    themes_json: str = "",
    theme_labels_json: str = "",
    color_options: list = None,
) -> str:
    """Render the dashboard home page with three-panel shell layout."""
    parts = [
        page_head("Home", "Knowledge base dashboard",
                  themes_json=themes_json, theme_labels_json=theme_labels_json,
                  color_options=color_options),
        '<div class="shell">\n',
        _topbar("home", color_options),
        render_sidebar(categories, clusters=clusters or [],
                       total_pages=stats.get("total_pages", 0)),
        '<main class="main">\n',
    ]

    # Stats strip — FIX 2: 4th card (Last Build)
    total_pages = stats.get("total_pages", 0)
    total_edges = stats.get("total_edges", 0)
    total_clusters = stats.get("total_clusters", 0)
    parts.append('<div class="stats-strip">\n')
    items = [
        (total_pages, "pages", True),
        (total_edges, "cross-refs", False),
        (total_clusters, "clusters", False),
    ]
    for i, (value, label, accent) in enumerate(items):
        if i > 0:
            parts.append('<div class="stats-strip__sep"></div>\n')
        val_cls = " stats-strip__value--accent" if accent else ""
        parts.append(
            f'<div class="stats-strip__item">'
            f'<span class="stats-strip__value{val_cls}">{value:,}</span>'
            f'<span class="stats-strip__label">{label}</span>'
            f'</div>\n'
        )
    # 4th stats card: Last Build
    parts.append('<div class="stats-strip__sep"></div>\n')
    parts.append(
        '<div class="stats-strip__item">'
        '<span class="stats-strip__value">Just now</span>'
        '<span class="stats-strip__label">Last build</span>'
        '</div>\n'
    )
    parts.append('</div>\n')

    # FIX 1: Recent changes feed (always render section)
    if recent_changes:
        parts.append('<div class="section">\n')
        parts.append(
            '<div class="section__header">'
            '<h2 class="section__title">Recent Changes</h2>'
            f'<span class="section__count">{len(recent_changes)} entries</span>'
            '</div>\n'
        )
        parts.append('<div class="feed">\n')
        for change in recent_changes[:10]:
            c_title = escape(change.get("title", "Unknown"))
            c_url = escape(change.get("url", "#"))
            c_type = change.get("type", "config")
            badge_cls = _TYPE_BADGE_MAP.get(c_type.split("/")[0].lower(), "config") if c_type else "config"
            badge_label = _BADGE_LABELS.get(badge_cls, badge_cls.upper())
            action = change.get("action", "updated")
            if action == "added":
                dot_cls = "feed__badge--new"
            elif action == "removed":
                dot_cls = "feed__badge--removed"
            else:
                dot_cls = "feed__badge--updated"
            c_time = escape(change.get("time_ago", ""))
            parts.append(
                f'<a href="{c_url}" class="feed__item">'
                f'<span class="feed__badge {dot_cls}"></span>'
                f'<span class="feed__type feed__type--{badge_cls}">{badge_label}</span>'
                f'<span class="feed__title">{c_title}</span>'
                f'<span class="feed__meta">{c_time}</span>'
                f'</a>\n'
            )
        parts.append('</div>\n</div>\n')
    else:
        # Empty state for recent changes
        parts.append('<div class="section">\n')
        parts.append(
            '<div class="section__header">'
            '<h2 class="section__title">Recent Changes</h2>'
            '</div>\n'
        )
        parts.append(
            '<div class="feed feed--empty">'
            '<span class="feed__empty-msg">'
            'No recent changes \u2014 run <code>llmwiki ingest</code> to track changes.'
            '</span></div>\n'
        )
        parts.append('</div>\n')

    # Category cards grid
    if categories:
        total_cat_count = len(categories)
        sorted_cats = sorted(
            categories.items(),
            key=lambda item: (
                len(item[1]) if isinstance(item[1], list)
                else (item[1].get("count", 0) if isinstance(item[1], dict) else 0)
            ),
            reverse=True,
        )

        parts.append('<div class="section">\n')
        parts.append(
            '<div class="section__header">'
            '<h2 class="section__title">Categories</h2>'
            f'<span class="section__count">{total_cat_count} active</span>'
            '</div>\n'
        )
        parts.append('<div class="cards-grid">\n')
        for cat_name, cat_data in sorted_cats[:20]:
            count = len(cat_data) if isinstance(cat_data, list) else (
                cat_data.get("count", 0) if isinstance(cat_data, dict) else 0
            )
            display = escape(cat_name)
            # Use grouped URL if available, otherwise construct from name
            cat_url = escape(cat_data.get("url", f"/categories/{cat_name.lower()}/")) if isinstance(cat_data, dict) else f"/categories/{cat_name.lower()}/"
            # Use grouped color if available
            color_var = cat_data.get("color", "node-config") if isinstance(cat_data, dict) else "node-config"
            icon_color = f"var(--{color_var})" if not color_var.startswith("var(") else color_var
            # FIX 3: card description
            desc = ""
            if isinstance(cat_data, dict):
                desc = cat_data.get("description", "")
            desc_html = f'<div class="card__desc">{escape(desc)}</div>' if desc else ""
            parts.append(
                f'<a href="{cat_url}" class="card">'
                f'<div class="card__header">'
                f'<span class="card__icon" style="background:{icon_color}"></span>'
                f'<span class="card__title">{display}</span>'
                f'<span class="card__count">{count}</span>'
                f'</div>{desc_html}</a>\n'
            )
        parts.append('</div>\n</div>\n')

    # Most connected pages
    if top_pages:
        parts.append('<div class="section">\n')
        parts.append(
            '<div class="section__header">'
            '<h2 class="section__title">Top Connected Pages</h2>'
            '<span class="section__count">by cross-ref density</span>'
            '</div>\n'
        )
        parts.append('<div class="connected-list">\n')
        max_refs = top_pages[0].get("in_degree", 1) if top_pages else 1
        for idx, tp in enumerate(top_pages[:10], 1):
            title = escape(tp.get("title", "?"))
            url = escape(tp.get("url", "#"))
            refs = tp.get("in_degree", 0)
            pct = int((refs / max(max_refs, 1)) * 100)
            parts.append(
                f'<a href="{url}" class="connected__item">'
                f'<span class="connected__rank">{idx}</span>'
                f'<div class="connected__info">'
                f'<div class="connected__name">{title}</div>'
                f'<div class="connected__refs">Referenced by {refs} pages</div>'
                f'</div>'
                f'<div class="connected__bar"><div class="connected__bar-fill" style="width:{pct}%"></div></div>'
                f'</a>\n'
            )
        parts.append('</div>\n</div>\n')

    parts.append('</main>\n')
    parts.append(render_graph_panel())
    parts.append('</div>\n')  # close .shell
    parts.append(page_foot())
    return "".join(parts)


# ===========================================================================
# CATEGORY INDEX
# ===========================================================================


def render_category_index(
    category: str, pages: list,
    *,
    clusters: list = None,
    themes_json: str = "",
    theme_labels_json: str = "",
    color_options: list = None,
) -> str:
    """Render a category index page with filter bar and sortable table."""
    display_name = escape(_format_category_display(category))
    cat_url = category.lower()
    cat_summary = {category: pages}

    parts = [
        page_head(display_name, f"All {display_name} pages",
                  themes_json=themes_json, theme_labels_json=theme_labels_json,
                  color_options=color_options),
        '<div class="shell">\n',
        _topbar("categories", color_options),
        render_sidebar(cat_summary, category, clusters=clusters or []),
        '<main class="main">\n',
        breadcrumbs([
            ("Home", "/"),
            ("Categories", "/categories/"),
            (display_name, f"/categories/{escape(cat_url)}/"),
        ]),
        f'<div class="filter-bar">\n'
        f'<span class="filter-bar__icon">\u2315</span>\n'
        f'<input class="filter-bar__input" type="text" '
        f'placeholder="Filter {display_name.lower()} by name, tag, or description...">\n'
        f'<span class="filter-bar__count">{len(pages)} items</span>\n'
        f'</div>\n',
        '<div class="table-wrap">\n<table>\n',
        '<thead><tr>'
        '<th>Name <span class="sort-icon">\u25BE</span></th>'
        '<th>Type</th>'
        '<th>Tags</th>'
        '<th>Refs <span class="sort-icon">\u25BE</span></th>'
        '<th>Importance</th>'
        '<th>Modified</th>'
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
        ptype = p.get("category", "")
        badge_html = _type_badge(ptype)
        refs = p.get("in_degree", 0)
        data_tags = escape(" ".join(tags))
        parts.append(
            f'<tr data-tags="{data_tags}">'
            f'<td class="td-accent"><a href="{url}">{title}</a></td>'
            f'<td>{badge_html}</td>'
            f'<td>{tags_html}</td>'
            f'<td class="td-mono">{refs}</td>'
            f'<td><div class="connected__bar" style="width:60px">'
            f'<div class="connected__bar-fill" style="width:{imp_pct}%"></div></div></td>'
            f'<td class="td-muted"></td>'
            f'</tr>\n'
        )

    parts.append('</tbody></table>\n</div>\n')
    parts.append('</main>\n')
    parts.append(render_graph_panel())
    parts.append('</div>\n')  # close .shell
    parts.append(page_foot())
    return "".join(parts)


# ===========================================================================
# PAGE DETAIL
# ===========================================================================


def render_page_detail(
    page: dict, backlinks: list,
    *,
    current_url: str = "",
    clusters: list = None,
    themes_json: str = "",
    theme_labels_json: str = "",
    color_options: list = None,
) -> str:
    """Render a page detail view with metadata, body, collapsible refs & backlinks."""
    title = escape(page.get("title", "Untitled"))
    cat = page.get("category", "")
    cat_display = escape(_format_category_display(cat)) if cat else "Uncategorized"
    cat_url = cat.lower() if cat else "uncategorized"
    page_id = page.get("id", "")
    slug = page_id.split("/")[-1] if "/" in page_id else page_id

    parts = [
        page_head(title, f"Detail page for {title}",
                  themes_json=themes_json, theme_labels_json=theme_labels_json,
                  color_options=color_options),
        '<div class="shell">\n',
        _topbar("", color_options),
        '<aside class="sidebar">\n'
        '<div class="sidebar__section">\n'
        '<div class="sidebar__heading">Navigation</div>\n'
        f'<a href="/" class="sidebar__item"><span class="sidebar__item-icon">\u25C6</span>'
        f'<span>Dashboard</span></a>\n'
        f'<a href="/categories/" class="sidebar__item">'
        f'<span class="sidebar__item-icon">\u25A3</span>'
        f'<span>All Pages</span></a>\n'
        f'<a href="/categories/{escape(cat_url)}/" class="sidebar__item">'
        f'<span class="sidebar__item-icon">\u25B8</span>'
        f'<span>{cat_display}</span></a>\n'
        f'<div class="sidebar__nested-section">\n<ul class="sidebar__tree sidebar__tree--nested">\n'
        f'<li class="sidebar__item sidebar__item--active">'
        f'<span class="sidebar__item-icon">\u00B7</span>'
        f'<span>{title[:30]}</span></li>\n'
        f'</ul>\n</div>\n'
        '</div>\n',
    ]

    # FIX 4: Clusters in detail sidebar
    if clusters:
        parts.append('<div class="sidebar__section">\n')
        parts.append('<div class="sidebar__heading">Clusters</div>\n')
        for cluster in clusters[:10]:
            cl_label = escape(cluster.get("label", f"Cluster {cluster.get('id', '?')}"))
            cl_count = cluster.get("member_count", len(cluster.get("members", [])))
            parts.append(
                f'<div class="sidebar__item">'
                f'<span class="sidebar__item-icon">\u25CB</span>'
                f'<span>{cl_label}</span>'
                f'<span class="sidebar__item-count">{cl_count}</span></div>\n'
            )
        parts.append('</div>\n')

    parts.append('</aside>\n')

    parts.extend([
        '<main class="main">\n',
        breadcrumbs([
            ("Home", "/"),
            ("Categories", "/categories/"),
            (cat_display, f"/categories/{escape(cat_url)}/"),
            (title, "#"),
        ]),
        '<div class="page-detail">\n',
    ])

    # FIX 8: Use improved type badge detection
    parts.append('<div class="page-meta">\n')
    badge_html = _detect_type_badge_html(page)
    parts.append(badge_html)
    parts.append('<span class="page-meta__sep"></span>\n')

    lang = page.get("language", "")
    if lang:
        parts.append(
            f'<span class="page-meta__item"><strong>Language:</strong> {escape(lang)}</span>\n'
            '<span class="page-meta__sep"></span>\n'
        )

    imp = page.get("importance", 0)
    parts.append(
        f'<span class="page-meta__item"><strong>Importance:</strong> {imp:.2f}</span>\n'
    )

    # FIX 9: Clean metadata — no raw filesystem paths
    source = page.get("source_path", "")
    if source:
        clean_info = _clean_source_display(source, lang)
        if clean_info.get("package"):
            parts.append(
                f'<span class="page-meta__sep"></span>\n'
                f'<span class="page-meta__item"><strong>Package:</strong> '
                f'<code>{escape(clean_info["package"])}</code></span>\n'
            )
        elif clean_info.get("config_path"):
            parts.append(
                f'<span class="page-meta__sep"></span>\n'
                f'<span class="page-meta__item"><strong>Path:</strong> '
                f'<code>{escape(clean_info["config_path"])}</code></span>\n'
            )
        elif clean_info.get("filename"):
            parts.append(
                f'<span class="page-meta__sep"></span>\n'
                f'<span class="page-meta__item"><strong>File:</strong> '
                f'<code>{escape(clean_info["filename"])}</code></span>\n'
            )

    # Line count from body
    body = page.get("body", "")
    if body:
        line_count = body.count('\n') + 1
        parts.append(
            f'<span class="page-meta__sep"></span>\n'
            f'<span class="page-meta__item"><strong>Lines:</strong> {line_count}</span>\n'
        )

    tags = page.get("tags", [])
    if tags:
        parts.append('<span class="page-meta__sep"></span>\n')
        for t in tags:
            parts.append(f'<span class="tag">{escape(t)}</span>\n')

    parts.append('</div>\n')

    # Body — markdown to HTML with FIX 13 (code blocks) and FIX 14 (clean javadoc)
    if body:
        cleaned_body = _clean_javadoc(body)
        rendered_body = md_to_html(cleaned_body)
        rendered_body = _render_code_blocks(rendered_body)
        parts.append(f'<div class="page-body">{rendered_body}</div>\n')

    # Cross-references (outbound) — collapsible, grouped by type
    refs = page.get("references", [])
    if refs or backlinks:
        ref_count = len(refs)
        bl_count = len(backlinks)
        parts.append(
            f'<div class="ref-summary" style="margin-top:var(--sp-6);padding-top:var(--sp-5);'
            f'border-top:1px solid var(--hairline);">\n'
            f'<span class="ref-summary__stat">{ref_count}</span> outbound\n'
            f'<span class="ref-summary__sep">\u00B7</span>\n'
            f'<span class="ref-summary__stat">{bl_count}</span> inbound\n'
            f'</div>\n'
        )

    # FIX 10: auto-open cross-refs when ≤5 items
    if refs:
        open_attr = " open" if len(refs) <= 5 else ""
        parts.append(
            f'<details class="ref-section"{open_attr}>\n'
            f'<summary>Cross References '
            f'<span style="margin-left:auto;font-size:11px;font-family:var(--font-mono);'
            f'color:var(--accent);">\u2192 {len(refs)} outgoing</span></summary>\n'
            f'<div class="ref-section__body">\n'
        )
        # FIX 6: Group refs by type
        if refs and isinstance(refs[0], dict):
            ref_groups: dict[str, list] = {}
            for r in refs:
                rtype = r.get("type", "other")
                ref_groups.setdefault(rtype, []).append(r)
            for rtype, ritems in ref_groups.items():
                badge = _type_badge(rtype)
                group_open = " open" if len(ritems) <= 5 else ""
                parts.append(
                    f'<details class="ref-group"{group_open}>\n'
                    f'<summary>{badge} {escape(_format_category_display(rtype))} '
                    f'<span class="ref-group__count">{len(ritems)}</span></summary>\n'
                    f'<div class="ref-group__body">\n'
                )
                for ri in ritems:
                    ri_name = escape(ri.get("title", ri.get("id", str(ri))))
                    ri_url = escape(ri.get("url", "#"))
                    parts.append(
                        f'<a href="{ri_url}" class="ref-link">'
                        f'<span class="ref-link__arrow">\u2192</span>'
                        f'<span class="ref-link__name">{ri_name}</span></a>\n'
                    )
                parts.append('</div>\n</details>\n')
        else:
            # Flat list (refs are strings) — group by detecting type from ID
            ref_type_groups: dict[str, list[str]] = {}
            for r in refs:
                ref_str = str(r)
                # Detect type from reference ID
                ref_lower = ref_str.lower()
                if ref_lower.startswith("com/") or ref_lower.startswith("com.") or ".java" in ref_lower:
                    rtype = "java"
                elif "beanshell" in ref_lower or "bsh" in ref_lower:
                    rtype = "beanshell"
                elif ref_lower.startswith("rule/") or ref_lower.startswith("workflow/"):
                    rtype = ref_lower.split("/")[0]
                else:
                    rtype = "other"
                ref_type_groups.setdefault(rtype, []).append(ref_str)

            if len(ref_type_groups) > 1:
                for rtype, ritems in ref_type_groups.items():
                    badge = _type_badge(rtype)
                    group_open = " open" if len(ritems) <= 5 else ""
                    parts.append(
                        f'<details class="ref-group"{group_open}>\n'
                        f'<summary>{badge} {escape(_format_category_display(rtype))} '
                        f'<span class="ref-group__count">{len(ritems)}</span></summary>\n'
                        f'<div class="ref-group__body">\n'
                    )
                    for ref_str in ritems:
                        parts.append(
                            f'<div class="ref-link">'
                            f'<span class="ref-link__arrow">\u2192</span>'
                            f'<span class="ref-link__name">{escape(ref_str)}</span></div>\n'
                        )
                    parts.append('</div>\n</details>\n')
            else:
                parts.append('<div class="ref-group__body">\n')
                for r in refs:
                    ref_str = escape(str(r))
                    parts.append(
                        f'<div class="ref-link">'
                        f'<span class="ref-link__arrow">\u2192</span>'
                        f'<span class="ref-link__name">{ref_str}</span></div>\n'
                    )
                parts.append('</div>\n')

        parts.append('</div>\n</details>\n')

    # FIX 7: Backlinks (inbound) — grouped by category
    if backlinks:
        open_attr = " open" if len(backlinks) <= 5 else ""
        parts.append(
            f'<details class="ref-section" style="margin-top:0;border-top:none;'
            f'padding:var(--sp-5);background:var(--surface-1);'
            f'border:1px solid var(--hairline);border-radius:var(--radius);"{open_attr}>\n'
            f'<summary><span style="color:var(--accent)">\u2190</span> Backlinks '
            f'<span style="margin-left:auto;font-size:11px;font-family:var(--font-mono);'
            f'color:var(--accent);">\u2190 {len(backlinks)} inbound</span></summary>\n'
            f'<div class="ref-section__body">\n'
        )

        # Group backlinks by their category
        bl_groups: dict[str, list] = {}
        for bl in backlinks:
            bl_cat = bl.get("category", "Other")
            if not bl_cat:
                bl_cat = "Other"
            # Use first path segment as group key
            bl_group_key = bl_cat.split("/")[0] if "/" in bl_cat else bl_cat
            bl_groups.setdefault(bl_group_key, []).append(bl)

        for bl_cat, bl_items in sorted(bl_groups.items()):
            badge = _type_badge(bl_cat)
            cat_display_bl = escape(_format_category_display(bl_cat))
            group_open = " open" if len(bl_items) <= 5 else ""
            parts.append(
                f'<details class="backlinks__group ref-group"{group_open}>\n'
                f'<summary>\u2190 {badge} {cat_display_bl} '
                f'<span class="ref-group__count">{len(bl_items)}</span></summary>\n'
                f'<div class="ref-group__body">\n'
            )
            for bli in bl_items:
                bl_title = escape(bli.get("title", "?"))
                bl_url = escape(bli.get("url", "#"))
                parts.append(
                    f'<a href="{bl_url}" class="ref-link">'
                    f'<span class="ref-link__arrow">\u2190</span>'
                    f'<span class="ref-link__name">{bl_title}</span></a>\n'
                )
            parts.append('</div>\n</details>\n')

        parts.append('</div>\n</details>\n')

    # JSON sibling link
    if slug:
        parts.append(
            f'<div class="json-link">'
            f'Structured data: <a href="{escape(slug)}.json">{escape(slug)}.json</a>'
            f'</div>\n'
        )

    parts.append('</div>\n')  # close .page-detail
    parts.append('</main>\n')
    parts.append(render_graph_panel(page_id))
    parts.append('</div>\n')  # close .shell
    parts.append(page_foot())
    return "".join(parts)


# ===========================================================================
# GRAPH PAGE (full)
# ===========================================================================


_GRAPH_INIT_SCRIPT = """\
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
  var cat = n.type || "uncategorized";
  return {
    id: n.id,
    label: n.title || n.id,
    size: size,
    color: { background: typeColor(cat), border: typeColor(cat),
             highlight: { background: "#10b981", border: "#34d399" } },
    font: { color: fontColor, size: Math.max(9, size * 0.55) },
    title: (n.title || n.id) + " (" + cat + ")\\nImportance: " + imp.toFixed(2),
    _url: "/categories/" + cat.toLowerCase() + "/" + n.id.split("/").pop() + ".html",
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


def render_graph_page(
    graph: dict,
    *,
    themes_json: str = "",
    theme_labels_json: str = "",
    color_options: list = None,
) -> str:
    """Render interactive knowledge graph page with force/neural toggle."""
    nodes_json = json.dumps(graph.get("nodes", []))
    edges_json = json.dumps(graph.get("edges", []))
    stats = graph.get("stats", {})

    n_nodes = stats.get("total_pages", 0)
    n_edges = stats.get("total_edges", 0)
    n_clusters = stats.get("total_clusters", 0)

    # Legend items
    legend_types = [
        ("Java", "var(--node-java)"),
        ("XML/Workflow", "var(--node-xml)"),
        ("BeanShell", "var(--node-beanshell)"),
        ("Config", "var(--node-config)"),
        ("Token", "var(--node-tokens)"),
        ("Docs", "var(--node-docs)"),
    ]
    legend_html = ""
    for lbl, color in legend_types:
        legend_html += (
            f'<div class="graph-full__legend-item">'
            f'<span class="graph-full__legend-dot" style="background:{color}"></span>'
            f'<span>{lbl}</span></div>\n'
        )

    parts = [
        page_head("Knowledge Graph", "Interactive knowledge graph visualization",
                  themes_json=themes_json, theme_labels_json=theme_labels_json,
                  color_options=color_options),
        '<div class="shell">\n',
        _topbar("graph", color_options),
        '<aside class="sidebar">\n'
        '<div class="sidebar__section">\n'
        '<div class="sidebar__heading">Navigation</div>\n'
        '<a href="/" class="sidebar__item"><span class="sidebar__item-icon">\u25C6</span>'
        '<span>Dashboard</span></a>\n'
        '<a href="/graph.html" class="sidebar__item sidebar__item--active">'
        '<span class="sidebar__item-icon">\u25C8</span>'
        '<span>Full Graph</span></a>\n'
        '</div>\n'
        '</aside>\n',
        '<main class="main">\n',
        '<div class="section">\n'
        '<div class="section__header">'
        '<h2 class="section__title">Knowledge Graph</h2>'
        '<span class="section__count">full topology</span>'
        '</div>\n'
        '</div>\n',
        # Graph view toggle
        '<div class="graph-view-toggle">\n'
        '<button class="active" data-gview="force">Force-Directed</button>\n'
        '<button data-gview="neural">Neural Network</button>\n'
        '</div>\n',
        # Force-directed graph container
        '<div id="graph-force" class="graph-full">\n'
        '<div class="graph-full__header">\n'
        '<div class="graph-full__stats">\n'
        f'<span><span class="graph-full__stat-val">{n_nodes:,}</span> nodes</span>\n'
        f'<span><span class="graph-full__stat-val">{n_edges:,}</span> edges</span>\n'
        f'<span><span class="graph-full__stat-val">{n_clusters}</span> clusters</span>\n'
        '</div>\n'
        '</div>\n'
        '<div class="graph-full__canvas">\n'
        '<div id="graph-container" style="width:100%;height:calc(100vh - var(--topbar-height, 48px) - 60px);"></div>\n'
        '</div>\n'
        f'<div class="graph-full__legend">\n{legend_html}</div>\n'
        '</div>\n',
        # Neural graph container (hidden initially)
        '<div id="graph-neural" class="neural-graph" style="display:none;height:calc(100vh - var(--topbar-height, 48px) - 60px);"></div>\n',
        # vis-network CDN
        '<script src="https://cdn.jsdelivr.net/npm/vis-network@9/standalone/'
        'umd/vis-network.min.js" crossorigin="anonymous"></script>\n',
        # Graph init script
        '<script>\n(function(){\n"use strict";\n',
        'var rawNodes = ', nodes_json, ';\n',
        'var rawEdges = ', edges_json, ';\n',
        _GRAPH_INIT_SCRIPT,
        '})();\n</script>\n',
        '</main>\n',
        '</div>\n',  # close .shell
        page_foot(),
    ]
    return "".join(parts)


# ===========================================================================
# CHANGELOG
# ===========================================================================


def render_changelog_page(
    history: list,
    *,
    themes_json: str = "",
    theme_labels_json: str = "",
    color_options: list = None,
) -> str:
    """Render changelog page from build history entries."""
    parts = [
        page_head("Changelog", "Build history and changes",
                  themes_json=themes_json, theme_labels_json=theme_labels_json,
                  color_options=color_options),
        '<div class="shell">\n',
        _topbar("changelog", color_options),
        '<aside class="sidebar">\n'
        '<div class="sidebar__section">\n'
        '<div class="sidebar__heading">Navigation</div>\n'
        '<a href="/" class="sidebar__item"><span class="sidebar__item-icon">\u25C6</span>'
        '<span>Dashboard</span></a>\n'
        '</div>\n'
        '</aside>\n',
        '<main class="main">\n',
        '<div class="section">\n'
        '<div class="section__header"><h2 class="section__title">Changelog</h2></div>\n'
        '</div>\n',
    ]

    if not history:
        parts.append(
            '<p style="color:var(--ink-subtle);font-size:13px;">No build history yet. '
            'Run <code>llmwiki all</code> to generate the first build.</p>\n'
        )
    else:
        parts.append('<div class="table-wrap">\n<table>\n')
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
                f'<td class="td-mono">{entry.get("total_pages", 0)}</td>'
                f'<td class="td-mono">{entry.get("total_categories", 0)}</td>'
                f'<td class="td-mono">{entry.get("total_edges", 0)}</td>'
                f'<td class="td-mono">{entry.get("total_clusters", 0)}</td>'
                f'</tr>\n'
            )
        parts.append('</tbody></table>\n</div>\n')

    parts.append('</main>\n')
    parts.append(render_graph_panel())
    parts.append('</div>\n')  # close .shell
    parts.append(page_foot())
    return "".join(parts)


# ===========================================================================
# CATEGORIES INDEX
# ===========================================================================


def render_categories_index(
    categories: dict,
    *,
    themes_json: str = "",
    theme_labels_json: str = "",
    color_options: list = None,
) -> str:
    """Render the /categories/ index page listing all categories."""
    total = len(categories)
    parts = [
        page_head("All Categories", f"Browse all {total} categories",
                  themes_json=themes_json, theme_labels_json=theme_labels_json,
                  color_options=color_options),
        '<div class="shell">\n',
        _topbar("categories", color_options),
        render_sidebar(categories),
        '<main class="main">\n',
        breadcrumbs([("Home", "/"), ("Categories", "#")]),
        f'<div class="section">\n'
        f'<div class="section__header"><h2 class="section__title">All Categories ({total})</h2></div>\n'
        f'</div>\n',
        '<div class="filter-bar">\n'
        '<span class="filter-bar__icon">\u2315</span>\n'
        '<input class="filter-bar__input" type="text" placeholder="Filter categories\u2026">\n'
        f'<span class="filter-bar__count">{total} items</span>\n'
        '</div>\n',
        '<div class="cards-grid">\n',
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
        base = cat_name.split("/")[0].lower()
        badge_type = _TYPE_BADGE_MAP.get(base, "config")
        color_map = {
            "java": "var(--node-java)", "xml": "var(--node-xml)",
            "beanshell": "var(--node-beanshell)", "config": "var(--node-config)",
            "docs": "var(--node-docs)", "tokens": "var(--node-tokens)",
        }
        icon_color = color_map.get(badge_type, "var(--accent)")
        parts.append(
            f'<a href="/categories/{cat_url}/" '
            f'class="card" data-tags="{escape(cat_name.lower())}">'
            f'<div class="card__header">'
            f'<span class="card__icon" style="background:{icon_color}"></span>'
            f'<span class="card__title">{display}</span>'
            f'<span class="card__count">{count}</span>'
            f'</div></a>\n'
        )

    parts.append('</div>\n')
    parts.append('</main>\n')
    parts.append(render_graph_panel())
    parts.append('</div>\n')  # close .shell
    parts.append(page_foot())
    return "".join(parts)
