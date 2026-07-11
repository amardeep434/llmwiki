"""Site CSS as a Python string constant — dark emerald three-panel design."""

CSS = """\
/* ===================================================================
   LLMWiki — Dark Emerald Theme (DESIGN.md compliant)
   Three-panel Obsidian-style layout with Linear precision
   =================================================================== */

/* ===== Custom Properties (Dark Default) ===== */
:root {
  /* Accent */
  --accent: #10b981;
  --accent-hover: #34d399;
  --accent-muted: #065f46;
  --accent-subtle: #022c22;

  /* Surfaces (dark default) */
  --canvas: #0a0a0f;
  --surface-0: #12121a;
  --surface-1: #1a1a25;
  --surface-2: #22222e;
  --surface-3: #2a2a38;

  /* Text */
  --ink: #e4e4e7;
  --ink-muted: #a1a1aa;
  --ink-subtle: #71717a;
  --ink-faint: #52525b;

  /* Borders */
  --hairline: #27272a;
  --hairline-strong: #3f3f46;

  /* Semantic */
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #6366f1;

  /* Graph node colors */
  --node-java: #f59e0b;
  --node-xml: #6366f1;
  --node-beanshell: #ec4899;
  --node-docs: #10b981;
  --node-config: #8b5cf6;
  --node-tokens: #f97316;

  /* Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --font-mono: 'SF Mono', 'Cascadia Code', 'JetBrains Mono', Consolas, 'Liberation Mono', monospace;

  /* Layout */
  --sidebar-width: 260px;
  --graph-panel-width: 280px;
  --topbar-height: 48px;

  /* Spacing */
  --sp-1: 4px;
  --sp-2: 8px;
  --sp-3: 12px;
  --sp-4: 16px;
  --sp-5: 20px;
  --sp-6: 24px;
  --sp-8: 32px;
  --sp-10: 40px;
  --sp-12: 48px;

  /* Radii */
  --radius: 8px;
  --radius-sm: 6px;
  --radius-xs: 4px;

  /* Transitions */
  --ease: 150ms ease-out;
}

/* ===== Light Theme Overrides ===== */
[data-theme="light"] {
  --canvas: #fafafa;
  --surface-0: #ffffff;
  --surface-1: #f4f4f5;
  --surface-2: #e4e4e7;
  --surface-3: #d4d4d8;
  --ink: #18181b;
  --ink-muted: #52525b;
  --ink-subtle: #71717a;
  --ink-faint: #a1a1aa;
  --hairline: #e4e4e7;
  --hairline-strong: #d4d4d8;
  --accent-subtle: #ecfdf5;
  --accent-muted: #a7f3d0;
}

/* ===== Reset & Base ===== */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 14px;
  scroll-behavior: smooth;
  -webkit-text-size-adjust: 100%;
}

body {
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink);
  background: var(--canvas);
  min-height: 100vh;
  overflow: hidden;
}

::selection {
  background: var(--accent);
  color: #fff;
}

:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

a {
  color: var(--accent);
  text-decoration: none;
  transition: color var(--ease);
}

a:hover {
  color: var(--accent-hover);
}

img { max-width: 100%; height: auto; }

/* ===== Scrollbar ===== */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--hairline-strong);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: var(--ink-subtle); }

/* Firefox */
* { scrollbar-width: thin; scrollbar-color: var(--hairline-strong) transparent; }

/* ===== Three-Panel Layout ===== */
.app-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr var(--graph-panel-width);
  grid-template-rows: var(--topbar-height) 1fr;
  height: 100vh;
  overflow: hidden;
}

.app-layout.sidebar-collapsed {
  grid-template-columns: 0px 1fr var(--graph-panel-width);
}

.app-layout.graph-collapsed {
  grid-template-columns: var(--sidebar-width) 1fr 0px;
}

.app-layout.sidebar-collapsed.graph-collapsed {
  grid-template-columns: 0px 1fr 0px;
}

/* ===== Top Bar ===== */
.topbar {
  grid-column: 1 / -1;
  grid-row: 1;
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: 0 var(--sp-4);
  height: var(--topbar-height);
  background: var(--surface-1);
  border-bottom: 1px solid var(--hairline);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  text-decoration: none;
  white-space: nowrap;
}

.topbar-brand:hover { color: var(--ink); }

.topbar-brand .brand-icon {
  color: var(--accent);
  font-size: 16px;
}

.topbar-nav {
  display: flex;
  gap: var(--sp-1);
  margin-left: var(--sp-4);
}

.topbar-nav a {
  padding: var(--sp-1) var(--sp-3);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-muted);
  transition: color var(--ease), background var(--ease);
}

.topbar-nav a:hover {
  color: var(--ink);
  background: var(--surface-2);
}

.topbar-nav a.active {
  color: var(--accent);
  background: var(--accent-subtle);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-left: auto;
}

.search-trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-1) var(--sp-3);
  background: var(--surface-2);
  border: 1px solid var(--hairline);
  border-radius: 999px;
  font-size: 12px;
  color: var(--ink-subtle);
  cursor: pointer;
  transition: border-color var(--ease), background var(--ease);
}

.search-trigger:hover {
  border-color: var(--hairline-strong);
  background: var(--surface-3);
}

.search-trigger kbd {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 1px 4px;
  background: var(--surface-1);
  border: 1px solid var(--hairline);
  border-radius: 3px;
}

.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--hairline);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--ink-muted);
  cursor: pointer;
  font-size: 14px;
  transition: color var(--ease), border-color var(--ease);
}

.theme-toggle:hover {
  color: var(--accent);
  border-color: var(--accent);
}

.sidebar-toggle,
.graph-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--hairline);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--ink-muted);
  cursor: pointer;
  font-size: 14px;
  transition: color var(--ease), border-color var(--ease);
}

.sidebar-toggle:hover,
.graph-toggle:hover {
  color: var(--accent);
  border-color: var(--accent);
}

/* ===== Left Sidebar ===== */
.sidebar {
  grid-column: 1;
  grid-row: 2;
  background: var(--surface-0);
  border-right: 1px solid var(--hairline);
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--sp-4) 0;
  transition: width var(--ease), opacity var(--ease);
}

.sidebar-collapsed .sidebar {
  width: 0;
  opacity: 0;
  overflow: hidden;
  padding: 0;
  border: none;
}

.sidebar-search {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin: 0 var(--sp-3) var(--sp-4);
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border: 1px solid var(--hairline);
  border-radius: var(--radius-sm);
  color: var(--ink-subtle);
  font-size: 12px;
  cursor: pointer;
  transition: border-color var(--ease);
}

.sidebar-search:hover {
  border-color: var(--hairline-strong);
}

.sidebar-section {
  margin-bottom: var(--sp-2);
}

.sidebar-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-1) var(--sp-4);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-subtle);
  cursor: pointer;
  user-select: none;
}

.sidebar-section-header:hover { color: var(--ink-muted); }

.sidebar-section-header .count {
  font-size: 10px;
  color: var(--ink-faint);
  font-weight: 400;
}

.sidebar-tree {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-tree-item {
  display: flex;
  align-items: center;
  padding: var(--sp-1) var(--sp-4);
  padding-left: var(--sp-6);
  font-size: 13px;
  color: var(--ink-muted);
  cursor: pointer;
  transition: background var(--ease), color var(--ease);
  border-radius: 0;
}

.sidebar-tree-item:hover {
  background: var(--surface-2);
  color: var(--ink);
}

.sidebar-tree-item.active {
  background: var(--accent-subtle);
  color: var(--accent);
}

.sidebar-tree-item .item-count {
  margin-left: auto;
  font-size: 11px;
  color: var(--ink-faint);
}

.sidebar-section.collapsed .sidebar-tree {
  display: none;
}

/* ===== Main Content ===== */
.main-content {
  grid-column: 2;
  grid-row: 2;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--sp-6);
  min-width: 0;
}

.content-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

/* ===== Right Graph Panel ===== */
.graph-panel {
  grid-column: 3;
  grid-row: 2;
  background: var(--surface-0);
  border-left: 1px solid var(--hairline);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: width var(--ease), opacity var(--ease);
}

.graph-collapsed .graph-panel {
  width: 0;
  opacity: 0;
  overflow: hidden;
  border: none;
}

.graph-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--hairline);
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.graph-panel-header a {
  font-size: 11px;
  font-weight: 500;
  text-transform: none;
  letter-spacing: 0;
}

.graph-panel-canvas {
  flex: 1;
  min-height: 200px;
}

/* ===== Breadcrumbs ===== */
.breadcrumbs {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: var(--sp-4);
  font-size: 13px;
  color: var(--ink-subtle);
}

.breadcrumbs a {
  color: var(--ink-muted);
}

.breadcrumbs a:hover { color: var(--accent); }

.breadcrumbs .sep { color: var(--ink-faint); }

.breadcrumbs .current {
  color: var(--ink);
  font-weight: 600;
}

/* ===== Stats Cards ===== */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-6);
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-4);
  background: var(--surface-0);
  border: 1px solid var(--hairline);
  border-radius: var(--radius);
}

.stat-card .stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
  line-height: 1.2;
}

.stat-card .stat-label {
  font-size: 12px;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 500;
}

/* ===== Section Headings ===== */
.section-heading {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: var(--sp-4);
  line-height: 1.4;
}

/* ===== Card Grid ===== */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-6);
}

.card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  padding: var(--sp-4);
  background: var(--surface-0);
  border: 1px solid var(--hairline);
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--ink);
  transition: border-color var(--ease), transform var(--ease);
}

.card:hover {
  border-color: var(--hairline-strong);
  transform: translateY(-1px);
  text-decoration: none;
  color: var(--ink);
}

.card h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  margin: 0;
}

.card .card-meta {
  font-size: 12px;
  color: var(--ink-muted);
}

/* ===== Recent Changes Feed ===== */
.changes-feed {
  list-style: none;
  padding: 0;
  margin-bottom: var(--sp-6);
}

.changes-feed li {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) 0;
  border-bottom: 1px solid var(--hairline);
  font-size: 13px;
}

.changes-feed li:last-child { border-bottom: none; }

.change-badge {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 3px;
  white-space: nowrap;
}

.change-badge.added { background: var(--accent-subtle); color: var(--accent); }
.change-badge.updated { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
.change-badge.archived { background: rgba(239, 68, 68, 0.1); color: var(--error); }

/* ===== Top Connected Pages ===== */
.connected-list {
  list-style: none;
  padding: 0;
  margin-bottom: var(--sp-6);
}

.connected-list li {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) 0;
  font-size: 13px;
}

.connected-list .rank {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-faint);
  width: 20px;
  text-align: right;
}

.connected-list .page-link { flex: 1; }

.connected-list .imp-bar-wrap {
  width: 80px;
  height: 3px;
  background: var(--hairline);
  border-radius: 2px;
  overflow: hidden;
}

.connected-list .imp-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-muted), var(--accent));
  border-radius: 2px;
}

.ref-count {
  font-size: 11px;
  color: var(--ink-subtle);
  font-weight: 500;
}

/* ===== Filter Bar ===== */
.filter-bar {
  margin-bottom: var(--sp-4);
}

.filter-input {
  width: 100%;
  max-width: 360px;
  padding: var(--sp-2) var(--sp-3);
  font-size: 13px;
  font-family: var(--font-sans);
  border: 1px solid var(--hairline);
  border-radius: var(--radius-xs);
  background: var(--surface-0);
  color: var(--ink);
  transition: border-color var(--ease);
}

.filter-input::placeholder { color: var(--ink-faint); }

.filter-input:focus {
  outline: none;
  border-color: var(--accent);
}

/* ===== Pages Table ===== */
.pages-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.pages-table thead th {
  text-align: left;
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--hairline);
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-muted);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  background: var(--surface-1);
}

.pages-table thead th:hover { color: var(--accent); }

.pages-table tbody tr {
  border-bottom: 1px solid var(--hairline);
  transition: background var(--ease);
}

.pages-table tbody tr:nth-child(even) { background: var(--surface-0); }
.pages-table tbody tr:nth-child(odd) { background: var(--canvas); }

.pages-table tbody tr:hover { background: var(--surface-2); }
.pages-table tbody tr.hidden { display: none; }

.pages-table tbody tr.row-focus {
  background: var(--surface-2);
  outline: 1px solid var(--accent);
  outline-offset: -1px;
}

.pages-table td {
  padding: var(--sp-2) var(--sp-3);
  vertical-align: middle;
}

.pages-table td a { font-weight: 500; }

.pages-table .sort-icon {
  font-size: 10px;
  margin-left: 4px;
  opacity: 0.5;
}

/* ===== Tags ===== */
.tag {
  display: inline-block;
  padding: 2px 8px;
  margin: 1px 2px;
  font-size: 11px;
  font-weight: 500;
  background: var(--surface-2);
  color: var(--ink-muted);
  border-radius: 999px;
  transition: color var(--ease);
}

.tag:hover { color: var(--accent); }

/* ===== Type Badge ===== */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  background: var(--accent-subtle);
  color: var(--accent);
  border-radius: var(--radius-xs);
}

/* ===== Importance Bar ===== */
.imp-bar {
  height: 3px;
  background: var(--hairline);
  border-radius: 2px;
  max-width: 100px;
  overflow: hidden;
}

.imp-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-muted), var(--accent));
  border-radius: 2px;
}

/* ===== Page Detail ===== */
.page-detail {
  max-width: 800px;
}

.meta-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  margin-bottom: var(--sp-6);
  background: var(--surface-0);
  border: 1px solid var(--hairline);
  border-radius: var(--radius);
  font-size: 12px;
  color: var(--ink-muted);
}

.meta-bar .meta-item {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
}

.meta-bar .meta-label {
  color: var(--ink-subtle);
  font-weight: 500;
}

/* ===== Article Body Typography ===== */
.page-body {
  line-height: 1.7;
}

.page-body h1 {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
  margin: var(--sp-8) 0 var(--sp-4);
  color: var(--ink);
}

.page-body h2 {
  font-size: 20px;
  font-weight: 600;
  line-height: 1.3;
  letter-spacing: -0.01em;
  margin: var(--sp-8) 0 var(--sp-3);
  padding-bottom: var(--sp-2);
  border-bottom: 1px solid var(--hairline);
}

.page-body h3 {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  margin: var(--sp-6) 0 var(--sp-2);
}

.page-body h4 {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  margin: var(--sp-5) 0 var(--sp-2);
}

.page-body p { margin-bottom: var(--sp-4); }

.page-body ul,
.page-body ol {
  margin-bottom: var(--sp-4);
  padding-left: var(--sp-6);
}

.page-body li { margin-bottom: var(--sp-1); }

.page-body blockquote {
  margin: var(--sp-4) 0;
  padding: var(--sp-3) var(--sp-4);
  border-left: 3px solid var(--accent);
  background: var(--surface-0);
  border-radius: 0 var(--radius-xs) var(--radius-xs) 0;
  color: var(--ink-muted);
}

.page-body table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: var(--sp-4);
  font-size: 13px;
}

.page-body table th,
.page-body table td {
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--hairline);
  text-align: left;
}

.page-body table th {
  background: var(--surface-1);
  font-weight: 600;
  color: var(--ink-muted);
}

/* ===== Code Blocks ===== */
code {
  font-family: var(--font-mono);
  font-size: 13px;
}

:not(pre) > code {
  padding: 2px 5px;
  background: var(--surface-0);
  border: 1px solid var(--hairline);
  border-radius: var(--radius-xs);
  font-size: 12px;
}

pre {
  position: relative;
  margin: var(--sp-4) 0;
  padding: var(--sp-4);
  background: var(--surface-0);
  border: 1px solid var(--hairline);
  border-radius: var(--radius);
  overflow-x: auto;
  line-height: 1.5;
  font-size: 13px;
}

pre code {
  padding: 0;
  background: none;
  border: none;
  font-size: inherit;
}

.copy-btn {
  position: absolute;
  top: var(--sp-2);
  right: var(--sp-2);
  padding: 3px 8px;
  font-size: 11px;
  font-family: var(--font-sans);
  background: var(--surface-1);
  color: var(--ink-subtle);
  border: 1px solid var(--hairline);
  border-radius: var(--radius-xs);
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--ease), color var(--ease);
}

pre:hover .copy-btn { opacity: 1; }

.copy-btn:hover {
  color: var(--accent);
  border-color: var(--accent);
}

.copy-btn.copied { color: var(--success); border-color: var(--success); }

/* ===== Cross-References & Backlinks ===== */
.cross-refs,
.backlinks {
  margin-top: var(--sp-8);
  padding-top: var(--sp-6);
  border-top: 1px solid var(--hairline);
}

.cross-refs h2,
.backlinks h2 {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: var(--sp-3);
  border-bottom: none;
  padding-bottom: 0;
}

.cross-refs ul,
.backlinks ul {
  list-style: none;
  padding: 0;
}

.cross-refs li,
.backlinks li {
  padding: var(--sp-1) 0;
  font-size: 13px;
  color: var(--ink-muted);
}

.cross-refs .ref-arrow,
.backlinks .ref-arrow {
  color: var(--ink-faint);
  margin-right: var(--sp-2);
}

/* ===== JSON Link ===== */
.json-link {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  margin-top: var(--sp-6);
  padding: var(--sp-2) var(--sp-3);
  font-size: 11px;
  color: var(--ink-subtle);
  background: var(--surface-0);
  border: 1px solid var(--hairline);
  border-radius: var(--radius-xs);
  transition: color var(--ease);
}

.json-link:hover { color: var(--accent); }

/* ===== Command Palette ===== */
.palette-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  background: rgba(10, 10, 15, 0.8);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.palette-overlay[hidden] { display: none; }

.palette-dialog {
  width: 560px;
  max-width: 90vw;
  background: var(--surface-0);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  overflow: hidden;
}

.palette-input {
  display: block;
  width: 100%;
  padding: var(--sp-4) var(--sp-5);
  font-size: 14px;
  font-family: var(--font-sans);
  border: none;
  border-bottom: 1px solid var(--hairline);
  background: var(--surface-0);
  color: var(--ink);
  outline: none;
}

.palette-input::placeholder { color: var(--ink-faint); }

.palette-results {
  max-height: 360px;
  overflow-y: auto;
}

.palette-result {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-5);
  cursor: pointer;
  transition: background var(--ease);
  font-size: 13px;
}

.palette-result:hover,
.palette-result.selected {
  background: var(--surface-2);
}

.palette-result .result-icon {
  font-size: 14px;
  width: 20px;
  text-align: center;
  color: var(--ink-subtle);
}

.palette-result .result-title {
  font-weight: 500;
  color: var(--ink);
}

.palette-result .result-category {
  font-size: 11px;
  padding: 1px 6px;
  background: var(--surface-2);
  border-radius: 3px;
  color: var(--ink-subtle);
  margin-left: auto;
}

.palette-result .result-type {
  font-size: 11px;
  color: var(--ink-faint);
  white-space: nowrap;
}

.palette-hints {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-4);
  padding: var(--sp-2) var(--sp-4);
  font-size: 11px;
  color: var(--ink-faint);
  border-top: 1px solid var(--hairline);
}

.palette-empty {
  padding: var(--sp-6);
  text-align: center;
  color: var(--ink-subtle);
  font-size: 13px;
}

/* ===== Keyboard Help Modal ===== */
.kbd-help-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 15, 0.8);
}

.kbd-help-overlay[hidden] { display: none; }

.kbd-help-dialog {
  background: var(--surface-0);
  border: 1px solid var(--hairline);
  border-radius: var(--radius);
  padding: var(--sp-6);
  max-width: 420px;
  width: 90%;
}

.kbd-help-dialog h2 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: var(--sp-4);
  padding-bottom: var(--sp-2);
  border-bottom: 1px solid var(--hairline);
}

.kbd-help-dialog dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--sp-2) var(--sp-4);
  font-size: 13px;
}

.kbd-help-dialog dt { text-align: right; }

kbd {
  display: inline-block;
  padding: 2px 5px;
  font-size: 11px;
  font-family: var(--font-mono);
  background: var(--surface-1);
  border: 1px solid var(--hairline);
  border-radius: 3px;
}

/* ===== Collapsible Details ===== */
details {
  margin: var(--sp-4) 0;
  border: 1px solid var(--hairline);
  border-radius: var(--radius);
  overflow: hidden;
}

details summary {
  padding: var(--sp-3) var(--sp-4);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  background: var(--surface-0);
  transition: background var(--ease);
  user-select: none;
  list-style: none;
}

details summary::-webkit-details-marker { display: none; }

details summary::before {
  content: "\\25B6";
  display: inline-block;
  margin-right: var(--sp-2);
  font-size: 10px;
  transition: transform var(--ease);
}

details[open] summary::before { transform: rotate(90deg); }

details summary:hover { background: var(--surface-2); }

details > :not(summary) { padding: 0 var(--sp-4); }
details[open] > :not(summary):first-of-type { padding-top: var(--sp-3); }
details[open] > :not(summary):last-child { padding-bottom: var(--sp-3); }

/* ===== View All Link ===== */
.view-all-link {
  text-align: center;
  margin-top: var(--sp-4);
  font-size: 13px;
  font-weight: 500;
}

/* ===== Page Title ===== */
.page-title {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
  margin-bottom: var(--sp-4);
  color: var(--ink);
}

/* ===== Category Page Count ===== */
.page-count {
  font-size: 13px;
  color: var(--ink-muted);
  margin-bottom: var(--sp-4);
}

/* ===== Mobile Bottom Tab Bar ===== */
.bottom-tabs {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--surface-1);
  border-top: 1px solid var(--hairline);
  padding: var(--sp-2) 0;
}

.bottom-tabs nav {
  display: flex;
  justify-content: space-around;
}

.bottom-tabs a {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 10px;
  color: var(--ink-subtle);
  padding: var(--sp-1);
  text-decoration: none;
}

.bottom-tabs a.active { color: var(--accent); }
.bottom-tabs a .tab-icon { font-size: 18px; }

/* ===== Print Styles ===== */
@media print {
  .topbar,
  .sidebar,
  .graph-panel,
  .palette-overlay,
  .kbd-help-overlay,
  .copy-btn,
  .bottom-tabs,
  .filter-bar,
  .sidebar-toggle,
  .graph-toggle {
    display: none !important;
  }

  body {
    color: #000;
    background: #fff;
    overflow: visible;
  }

  .app-layout {
    display: block;
    height: auto;
    overflow: visible;
  }

  .main-content {
    overflow: visible;
    padding: 0;
  }

  .page-detail { max-width: 100%; }

  a { color: #000; text-decoration: underline; }

  pre {
    border: 1px solid #ccc;
    page-break-inside: avoid;
  }
}

/* ===== Responsive: Tablet (1024–1279px) ===== */
@media (max-width: 1279px) {
  .app-layout {
    grid-template-columns: 0px 1fr 0px;
  }

  .sidebar {
    position: fixed;
    top: var(--topbar-height);
    left: 0;
    bottom: 0;
    width: var(--sidebar-width);
    z-index: 40;
    transform: translateX(-100%);
    transition: transform var(--ease);
  }

  .app-layout.sidebar-open .sidebar {
    transform: translateX(0);
    opacity: 1;
    width: var(--sidebar-width);
  }

  .graph-panel {
    position: fixed;
    top: var(--topbar-height);
    right: 0;
    bottom: 0;
    width: var(--graph-panel-width);
    z-index: 40;
    transform: translateX(100%);
    transition: transform var(--ease);
  }

  .app-layout.graph-open .graph-panel {
    transform: translateX(0);
    opacity: 1;
    width: var(--graph-panel-width);
  }

  .sidebar-toggle,
  .graph-toggle {
    display: inline-flex;
  }
}

/* ===== Responsive: Desktop (≥1280px) ===== */
@media (min-width: 1280px) {
  .sidebar-toggle,
  .graph-toggle {
    display: inline-flex;
  }
}

/* ===== Responsive: Mobile (<1024px) ===== */
@media (max-width: 1023px) {
  .app-layout {
    grid-template-columns: 1fr;
    grid-template-rows: var(--topbar-height) 1fr;
  }

  .topbar-nav { display: none; }

  .sidebar {
    position: fixed;
    top: var(--topbar-height);
    left: 0;
    bottom: 0;
    width: 80vw;
    max-width: 300px;
    z-index: 40;
    transform: translateX(-100%);
    transition: transform var(--ease);
  }

  .app-layout.sidebar-open .sidebar {
    transform: translateX(0);
    opacity: 1;
  }

  .graph-panel {
    position: fixed;
    top: var(--topbar-height);
    right: 0;
    bottom: 0;
    width: 80vw;
    max-width: 300px;
    z-index: 40;
    transform: translateX(100%);
    transition: transform var(--ease);
  }

  .app-layout.graph-open .graph-panel {
    transform: translateX(0);
    opacity: 1;
  }

  .main-content {
    padding: var(--sp-4);
    padding-bottom: 60px;
  }

  .bottom-tabs { display: block; }

  .card-grid {
    grid-template-columns: 1fr;
  }

  .palette-dialog {
    width: 100vw;
    max-width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .pages-table {
    display: block;
    overflow-x: auto;
  }
}

/* ===== Utilities ===== */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.text-muted { color: var(--ink-muted); }
.text-subtle { color: var(--ink-subtle); }
.mt-4 { margin-top: var(--sp-4); }
.mt-6 { margin-top: var(--sp-6); }
.mb-4 { margin-bottom: var(--sp-4); }
.mb-6 { margin-bottom: var(--sp-6); }
"""
