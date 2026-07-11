"""Site CSS as a Python string constant."""

CSS = """\
/* ===== Custom Properties ===== */
:root {
  --bg: #ffffff;
  --fg: #1a1a2e;
  --fg-muted: #6b7280;
  --accent: #7C3AED;
  --accent-hover: #6D28D9;
  --accent-light: rgba(124, 58, 237, 0.08);
  --card-bg: #f8f9fa;
  --border: #e5e7eb;
  --code-bg: #f5f5f5;
  --nav-bg: rgba(255, 255, 255, 0.92);
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
  --radius: 8px;
  --radius-lg: 12px;
  --transition: 0.2s ease;
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji",
    "Segoe UI Emoji";
  --font-mono: "JetBrains Mono", "Fira Code", "Cascadia Code", Consolas,
    "Liberation Mono", "Courier New", monospace;
  --container: 1200px;
}

[data-theme="dark"] {
  --bg: #0c0a1d;
  --fg: #e2e8f0;
  --fg-muted: #94a3b8;
  --accent: #a78bfa;
  --accent-hover: #c4b5fd;
  --accent-light: rgba(167, 139, 250, 0.1);
  --card-bg: #1a1a2e;
  --border: #2d2d44;
  --code-bg: #1e1e2e;
  --nav-bg: rgba(12, 10, 29, 0.92);
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
}

/* ===== Reset & Base ===== */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  scroll-behavior: smooth;
  -webkit-text-size-adjust: 100%;
}

body {
  font-family: var(--font-sans);
  color: var(--fg);
  background: var(--bg);
  line-height: 1.7;
  min-height: 100vh;
  transition: background var(--transition), color var(--transition);
}

a {
  color: var(--accent);
  text-decoration: none;
  transition: color var(--transition);
}

a:hover {
  color: var(--accent-hover);
  text-decoration: underline;
}

img {
  max-width: 100%;
  height: auto;
}

/* ===== Container ===== */
.container {
  max-width: var(--container);
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

/* ===== Navigation Bar ===== */
.nav-bar {
  position: sticky;
  top: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0 1.5rem;
  height: 56px;
  background: var(--nav-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.nav-brand a {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--fg);
  text-decoration: none;
  white-space: nowrap;
}

.nav-brand a:hover {
  color: var(--accent);
}

.nav-links {
  display: flex;
  gap: 0.25rem;
  margin-left: 1rem;
}

.nav-links a {
  padding: 0.4rem 0.75rem;
  border-radius: var(--radius);
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--fg-muted);
  transition: background var(--transition), color var(--transition);
}

.nav-links a:hover,
.nav-links a.active {
  color: var(--accent);
  background: var(--accent-light);
  text-decoration: none;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

.nav-search,
.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card-bg);
  color: var(--fg-muted);
  font-size: 1rem;
  cursor: pointer;
  transition: border-color var(--transition), background var(--transition);
}

.nav-search:hover,
.theme-toggle:hover {
  border-color: var(--accent);
  background: var(--accent-light);
  color: var(--accent);
}

.hamburger {
  display: none;
  flex-direction: column;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.4rem;
}

.hamburger span {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--fg);
  border-radius: 2px;
  transition: transform var(--transition);
}

/* ===== Hero Section ===== */
.hero {
  text-align: center;
  padding: 2.5rem 0 1.5rem;
}

.hero h1 {
  font-size: 2.25rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, var(--accent), var(--accent-hover));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero p {
  margin-top: 0.5rem;
  color: var(--fg-muted);
  font-size: 1.1rem;
}

/* ===== Stats Strip ===== */
.stats-strip {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 2.5rem;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 1.25rem 2rem;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  min-width: 140px;
  transition: transform var(--transition), box-shadow var(--transition);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.stat-num {
  font-size: 2rem;
  font-weight: 800;
  color: var(--accent);
  line-height: 1;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--fg-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

/* ===== Card Grid ===== */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.category-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.25rem 1.5rem;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: var(--fg);
  transition: transform var(--transition), box-shadow var(--transition),
    border-color var(--transition);
}

.category-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
  border-color: var(--accent);
  text-decoration: none;
}

.category-card h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--fg);
  margin: 0;
}

.card-count {
  font-size: 0.85rem;
  color: var(--fg-muted);
  font-weight: 500;
}

/* ===== Sections ===== */
section {
  margin-bottom: 2.5rem;
}

section h2 {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--border);
}

/* ===== Recent Changes ===== */
.recent-changes ul {
  list-style: none;
  padding: 0;
}

.recent-changes li {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.95rem;
}

.recent-changes li:last-child {
  border-bottom: none;
}

/* ===== Top Pages ===== */
.top-pages ol {
  padding-left: 1.25rem;
}

.top-pages li {
  padding: 0.4rem 0;
}

.ref-count {
  font-size: 0.8rem;
  color: var(--fg-muted);
  background: var(--accent-light);
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-weight: 600;
  margin-left: 0.5rem;
}

/* ===== Filter Bar ===== */
.filter-bar {
  margin-bottom: 1rem;
}

.filter-input {
  width: 100%;
  max-width: 400px;
  padding: 0.6rem 1rem;
  font-size: 0.95rem;
  font-family: var(--font-sans);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card-bg);
  color: var(--fg);
  transition: border-color var(--transition), box-shadow var(--transition);
}

.filter-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-light);
}

/* ===== Pages Table ===== */
.pages-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.pages-table thead th {
  text-align: left;
  padding: 0.75rem 1rem;
  border-bottom: 2px solid var(--border);
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--fg-muted);
  cursor: pointer;
  user-select: none;
}

.pages-table thead th:hover {
  color: var(--accent);
}

.pages-table tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background var(--transition);
}

.pages-table tbody tr:hover {
  background: var(--accent-light);
}

.pages-table tbody tr.hidden {
  display: none;
}

.pages-table td {
  padding: 0.6rem 1rem;
  vertical-align: middle;
}

.pages-table td a {
  font-weight: 500;
}

/* ===== Tags / Badges ===== */
.tag {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  margin: 0.1rem;
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--accent-light);
  color: var(--accent);
  border-radius: 999px;
  border: 1px solid transparent;
  transition: border-color var(--transition);
}

.tag:hover {
  border-color: var(--accent);
}

/* ===== Importance Bar ===== */
.imp-bar {
  height: 6px;
  background: linear-gradient(90deg, var(--accent), var(--accent-hover));
  border-radius: 3px;
  min-width: 4px;
  max-width: 120px;
  transition: width var(--transition);
}

/* ===== Breadcrumbs ===== */
.breadcrumbs {
  padding: 0.75rem 1.5rem;
  font-size: 0.85rem;
  color: var(--fg-muted);
  max-width: var(--container);
  margin: 0 auto;
}

.breadcrumbs a {
  color: var(--fg-muted);
  text-decoration: none;
}

.breadcrumbs a:hover {
  color: var(--accent);
  text-decoration: underline;
}

.breadcrumbs span {
  color: var(--fg);
  font-weight: 600;
}

/* ===== Page Detail ===== */
.page-detail {
  max-width: 860px;
}

.meta-card {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem 2rem;
  padding: 1rem 1.25rem;
  margin-bottom: 2rem;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  font-size: 0.9rem;
}

.meta-card strong {
  color: var(--fg-muted);
  font-weight: 600;
}

/* ===== Article Body Typography ===== */
.page-detail h1 {
  font-size: 2rem;
  font-weight: 800;
  margin: 1.5rem 0 1rem;
  letter-spacing: -0.01em;
}

.page-detail h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 2rem 0 0.75rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--border);
}

.page-detail h3 {
  font-size: 1.2rem;
  font-weight: 700;
  margin: 1.5rem 0 0.5rem;
}

.page-detail p {
  margin-bottom: 1rem;
}

.page-detail ul,
.page-detail ol {
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}

.page-detail li {
  margin-bottom: 0.3rem;
}

.page-detail blockquote {
  margin: 1rem 0;
  padding: 0.75rem 1.25rem;
  border-left: 4px solid var(--accent);
  background: var(--accent-light);
  border-radius: 0 var(--radius) var(--radius) 0;
  color: var(--fg-muted);
}

.page-detail table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.page-detail table th,
.page-detail table td {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  text-align: left;
}

.page-detail table th {
  background: var(--card-bg);
  font-weight: 700;
}

/* ===== Code Blocks ===== */
code {
  font-family: var(--font-mono);
  font-size: 0.88em;
}

:not(pre) > code {
  padding: 0.15rem 0.4rem;
  background: var(--code-bg);
  border-radius: 4px;
  border: 1px solid var(--border);
  font-size: 0.85em;
}

pre {
  position: relative;
  margin: 1rem 0;
  padding: 1rem 1.25rem;
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow-x: auto;
  line-height: 1.5;
  font-size: 0.88rem;
}

pre code {
  padding: 0;
  background: none;
  border: none;
  font-size: inherit;
}

.copy-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  padding: 0.3rem 0.6rem;
  font-size: 0.75rem;
  font-family: var(--font-sans);
  background: var(--card-bg);
  color: var(--fg-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--transition), background var(--transition);
}

pre:hover .copy-btn {
  opacity: 1;
}

.copy-btn:hover {
  background: var(--accent-light);
  color: var(--accent);
  border-color: var(--accent);
}

.copy-btn.copied {
  color: #10b981;
  border-color: #10b981;
}

/* ===== Cross-References & Backlinks ===== */
.cross-refs,
.backlinks {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}

.cross-refs h2,
.backlinks h2 {
  font-size: 1.15rem;
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
  padding: 0.35rem 0;
  font-size: 0.9rem;
}

/* ===== Collapsible Details ===== */
details {
  margin: 1rem 0;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

details summary {
  padding: 0.75rem 1rem;
  font-weight: 600;
  cursor: pointer;
  background: var(--card-bg);
  transition: background var(--transition);
  user-select: none;
  list-style: none;
}

details summary::-webkit-details-marker {
  display: none;
}

details summary::before {
  content: "\\25B6";
  display: inline-block;
  margin-right: 0.5rem;
  font-size: 0.75rem;
  transition: transform var(--transition);
}

details[open] summary::before {
  transform: rotate(90deg);
}

details summary:hover {
  background: var(--accent-light);
}

details > :not(summary) {
  padding: 0 1rem;
}

details[open] > :not(summary):first-of-type {
  padding-top: 0.75rem;
}

details[open] > :not(summary):last-child {
  padding-bottom: 0.75rem;
}

/* ===== Command Palette ===== */
.palette-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.palette-overlay[hidden] {
  display: none;
}

.palette-dialog {
  width: 90%;
  max-width: 600px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.palette-input {
  display: block;
  width: 100%;
  padding: 1rem 1.25rem;
  font-size: 1.05rem;
  font-family: var(--font-sans);
  border: none;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  color: var(--fg);
  outline: none;
}

.palette-results {
  max-height: 360px;
  overflow-y: auto;
}

.palette-result {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1.25rem;
  cursor: pointer;
  transition: background var(--transition);
  font-size: 0.95rem;
}

.palette-result:hover,
.palette-result.selected {
  background: var(--accent-light);
}

.palette-result .result-title {
  font-weight: 600;
}

.palette-result .result-type {
  font-size: 0.8rem;
  color: var(--fg-muted);
  margin-left: auto;
  white-space: nowrap;
}

.palette-hints {
  padding: 0.5rem 1.25rem;
  font-size: 0.8rem;
  color: var(--fg-muted);
  border-top: 1px solid var(--border);
  text-align: center;
}

/* ===== Reading Progress Bar ===== */
.progress-bar {
  position: fixed;
  top: 56px;
  left: 0;
  height: 3px;
  background: var(--accent);
  z-index: 999;
  transition: width 0.1s linear;
}

/* ===== Keyboard Help Modal ===== */
.kbd-help-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
}

.kbd-help-overlay[hidden] {
  display: none;
}

.kbd-help-dialog {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: 1.5rem 2rem;
  max-width: 460px;
  width: 90%;
}

.kbd-help-dialog h2 {
  font-size: 1.15rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.5rem;
}

.kbd-help-dialog dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.4rem 1rem;
  font-size: 0.9rem;
}

.kbd-help-dialog dt {
  text-align: right;
}

kbd {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  font-size: 0.8rem;
  font-family: var(--font-mono);
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  box-shadow: 0 1px 0 var(--border);
}

/* ===== Print Styles ===== */
@media print {
  .nav-bar,
  .nav-actions,
  .hamburger,
  .filter-bar,
  .palette-overlay,
  .kbd-help-overlay,
  .copy-btn,
  .progress-bar {
    display: none !important;
  }

  body {
    color: #000;
    background: #fff;
  }

  .container {
    max-width: 100%;
    padding: 0;
  }

  .page-detail {
    max-width: 100%;
  }

  a {
    color: #000;
    text-decoration: underline;
  }

  pre {
    border: 1px solid #ccc;
    page-break-inside: avoid;
  }
}

/* ===== Mobile Responsive ===== */
@media (max-width: 768px) {
  .hamburger {
    display: flex;
  }

  .nav-links {
    display: none;
    position: absolute;
    top: 56px;
    left: 0;
    right: 0;
    flex-direction: column;
    background: var(--nav-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 0.5rem;
    box-shadow: var(--shadow);
  }

  .nav-links.open {
    display: flex;
  }

  .nav-links a {
    padding: 0.6rem 1rem;
  }

  .hero h1 {
    font-size: 1.6rem;
  }

  .stats-strip {
    gap: 0.5rem;
  }

  .stat-card {
    padding: 0.75rem 1rem;
    min-width: 100px;
  }

  .stat-num {
    font-size: 1.4rem;
  }

  .card-grid {
    grid-template-columns: 1fr;
  }

  .container {
    padding: 1rem;
  }

  .breadcrumbs {
    padding: 0.5rem 1rem;
  }

  .meta-card {
    flex-direction: column;
    gap: 0.5rem;
  }

  .pages-table {
    font-size: 0.85rem;
  }

  .pages-table td,
  .pages-table th {
    padding: 0.4rem 0.5rem;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .card-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1025px) and (max-width: 1440px) {
  .card-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1441px) {
  .card-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* ===== Scrollbar Styling ===== */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--fg-muted);
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

.text-muted {
  color: var(--fg-muted);
}

.view-all-link {
  text-align: center;
  margin-top: 1rem;
  font-size: 1rem;
  font-weight: 600;
}

.view-all-link a {
  color: var(--accent);
}

.mt-2 {
  margin-top: 2rem;
}

.mb-1 {
  margin-bottom: 1rem;
}
"""
