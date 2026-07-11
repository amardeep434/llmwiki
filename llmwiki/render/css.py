"""Site CSS as a Python string constant — dark emerald three-panel design."""

CSS = """\
/* ═══════════════════════════════════════════════════════════
   LLMWiki Design System — Dark-First Knowledge Graph UI
   Ported from approved preview — pixel-accurate match
   ═══════════════════════════════════════════════════════════ */

/* Layout & spacing custom properties (colors come from themes) */
:root {
  --sp-1: 4px; --sp-2: 8px; --sp-3: 12px; --sp-4: 16px; --sp-5: 20px;
  --sp-6: 24px; --sp-8: 32px; --sp-10: 40px; --sp-12: 48px;
  --sidebar-w: 260px; --graph-w: 280px; --topbar-h: 48px;
  --radius: 8px; --radius-sm: 6px; --radius-xs: 4px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 14px; line-height: 1.6; -webkit-font-smoothing: antialiased; }
body { font-family: var(--font-sans); background: var(--canvas); color: var(--ink); overflow: hidden; height: 100vh; }
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); }

/* ─── Typography ─── */
.h1 { font-size: 24px; font-weight: 600; line-height: 1.3; letter-spacing: -0.01em; }
.h2 { font-size: 20px; font-weight: 600; line-height: 1.3; letter-spacing: -0.01em; }
.h3 { font-size: 16px; font-weight: 600; line-height: 1.4; }
.h4 { font-size: 14px; font-weight: 600; line-height: 1.4; }
.body-sm { font-size: 13px; line-height: 1.5; }
.caption { font-size: 12px; line-height: 1.4; letter-spacing: 0.01em; }
.mono { font-family: var(--font-mono); font-size: 13px; line-height: 1.5; }

/* ─── Shell ─── */
.shell {
  display: grid;
  grid-template-rows: var(--topbar-h) 1fr;
  grid-template-columns: var(--sidebar-w) 1fr var(--graph-w);
  height: 100vh; width: 100vw;
}
.shell.graph-collapsed { grid-template-columns: var(--sidebar-w) 1fr 0px; }
.shell.graph-collapsed .graph-panel { display: none; }
.shell.graph-open .graph-panel { display: flex; }

/* ─── Top Bar ─── */
.topbar {
  grid-column: 1 / -1;
  display: flex; align-items: center; gap: var(--sp-2);
  padding: 0 var(--sp-4);
  background: var(--surface-1); border-bottom: 1px solid var(--hairline);
  position: sticky; top: 0; z-index: 50; backdrop-filter: blur(12px);
  height: var(--topbar-h);
}
.topbar__brand { display: flex; align-items: center; gap: var(--sp-2); font-size: 14px; font-weight: 600; color: var(--ink); margin-right: var(--sp-6); }
.topbar__brand-icon { color: var(--accent); font-size: 16px; }
.topbar__nav { display: flex; align-items: center; height: 100%; }
.topbar__link {
  display: flex; align-items: center; height: 100%; padding: 0 var(--sp-3);
  font-size: 13px; color: var(--ink-muted); border-bottom: 2px solid transparent;
  transition: color 150ms, border-color 150ms; cursor: pointer;
}
.topbar__link:hover { color: var(--ink); }
.topbar__link--active { color: var(--accent); border-bottom-color: var(--accent); }
.topbar__spacer { flex: 1; }
.topbar__search {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: 6px 12px; background: var(--surface-2); border: 1px solid var(--hairline);
  border-radius: 20px; font-size: 13px; color: var(--ink-subtle); cursor: pointer;
  transition: border-color 150ms;
}
.topbar__search:hover { border-color: var(--hairline-strong); }
.topbar__search kbd { font-family: var(--font-mono); font-size: 11px; padding: 2px 5px; background: var(--surface-3); border-radius: 3px; color: var(--ink-faint); }
.topbar__btn {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: var(--radius-sm);
  border: 1px solid var(--hairline); background: transparent;
  color: var(--ink-muted); font-size: 14px; cursor: pointer;
  transition: background 150ms, color 150ms, border-color 150ms;
}
.topbar__btn:hover { background: var(--surface-2); color: var(--ink); border-color: var(--hairline-strong); }
.topbar__btn:active { transform: scale(0.97); }

.theme-select {
  appearance: none; -webkit-appearance: none;
  background: var(--surface-2); border: 1px solid var(--hairline);
  border-radius: 14px; padding: 4px 22px 4px 10px;
  font-size: 12px; font-family: var(--font-sans); color: var(--ink-muted);
  cursor: pointer; outline: none; transition: border-color 150ms, color 150ms;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='5'%3E%3Cpath d='M0 0l4 5 4-5z' fill='%2371717a'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 8px center;
}
.theme-select:hover { border-color: var(--hairline-strong); color: var(--ink); }
.theme-select:focus { border-color: var(--accent); }

/* ─── Left Sidebar ─── */
.sidebar { background: var(--surface-0); border-right: 1px solid var(--hairline); overflow-y: auto; padding: var(--sp-4) 0; }
.sidebar::-webkit-scrollbar { width: 4px; }
.sidebar::-webkit-scrollbar-thumb { background: var(--hairline-strong); border-radius: 2px; }
.sidebar__section { margin-bottom: var(--sp-5); }
.sidebar__heading { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-subtle); padding: var(--sp-1) var(--sp-4); margin-bottom: var(--sp-1); }
.sidebar__tree { list-style: none; }
.sidebar__tree--nested { margin-left: var(--sp-4); padding-left: var(--sp-3); border-left: 1px solid var(--hairline); }
.sidebar__item {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: 6px 12px 6px 16px; font-size: 13px; line-height: 1.4;
  color: var(--ink-muted); cursor: pointer; border-radius: var(--radius-xs);
  margin: 1px var(--sp-2); transition: background 150ms, color 150ms;
}
.sidebar__item:hover { background: var(--surface-2); color: var(--ink); }
.sidebar__item--active { background: var(--accent-subtle); color: var(--accent); }
.sidebar__item-icon { font-size: 11px; color: var(--ink-faint); width: 12px; text-align: center; flex-shrink: 0; }
.sidebar__item--active .sidebar__item-icon { color: var(--accent); }
.sidebar__item-count { margin-left: auto; font-size: 12px; color: var(--ink-faint); opacity: 0.7; font-family: var(--font-sans); unicode-bidi: isolate; direction: ltr; }
.sidebar__item--active .sidebar__item-count { color: var(--accent); }
.sidebar__nested-section { background: color-mix(in srgb, var(--surface-0) 50%, var(--canvas) 50%); border-radius: var(--radius-xs); margin: var(--sp-2); padding: var(--sp-2) 0; }

/* ─── Sidebar Content Types ─── */
.sidebar__ct-group { margin: 0; }
.sidebar__ct-group > summary { list-style: none; cursor: pointer; user-select: none; }
.sidebar__ct-group > summary::-webkit-details-marker { display: none; }
.sidebar__ct-group > summary::marker { display: none; content: ""; }
.sidebar__ct-tier1 { font-weight: 500; position: relative; }
.sidebar__ct-tier1 .sidebar__item-icon { font-size: 15px; width: 20px; text-align: center; }
.sidebar__ct-group > summary.sidebar__ct-tier1::after {
  content: "\25B8"; font-size: 10px; color: var(--ink-faint);
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  transition: transform 200ms ease;
}
.sidebar__ct-group[open] > .sidebar__ct-tier1::after { transform: translateY(-50%) rotate(90deg); }
.sidebar__ct-group > .sidebar__ct-tier2,
.sidebar__ct-group > .sidebar__ct-more { overflow: hidden; }
.sidebar__ct-tier2 { padding-left: 30px; font-size: 12px; }
.sidebar__ct-tier2 .sidebar__item-icon { font-size: 9px; }
.sidebar__ct-subdetail { margin: 0; }
.sidebar__ct-subdetail > summary { list-style: none; cursor: pointer; user-select: none; }
.sidebar__ct-subdetail > summary::-webkit-details-marker { display: none; }
.sidebar__ct-subdetail > summary::marker { display: none; content: ""; }
.sidebar__ct-subdetail > summary .sidebar__item-icon { font-size: 8px; transition: transform 200ms ease; }
.sidebar__ct-subdetail[open] > summary .sidebar__item-icon { transform: rotate(90deg); }
.sidebar__ct-tier3 { padding-left: 44px; font-size: 11px; color: var(--ink-faint); }
.sidebar__ct-tier3:hover { color: var(--ink-muted); }
.sidebar__ct-tier3 .sidebar__item-icon { font-size: 7px; }
.sidebar__ct-more { margin: 0; }
.sidebar__ct-more > summary { list-style: none; cursor: pointer; user-select: none; }
.sidebar__ct-more > summary::-webkit-details-marker { display: none; }
.sidebar__ct-more > summary::marker { display: none; content: ""; }

/* ─── Main Content ─── */
.main { overflow-y: auto; padding: var(--sp-6); background: var(--canvas); }
.main::-webkit-scrollbar { width: 6px; }
.main::-webkit-scrollbar-thumb { background: var(--hairline-strong); border-radius: 3px; }

/* ─── Page Nav (View Switcher) ─── */
.page-nav { display: flex; gap: var(--sp-1); margin-bottom: var(--sp-5); padding: 3px; background: var(--surface-0); border: 1px solid var(--hairline); border-radius: var(--radius); width: fit-content; }
.page-nav-btn {
  padding: 6px 14px; font-size: 12px; font-weight: 500; font-family: var(--font-sans);
  border: none; border-radius: var(--radius-sm); background: transparent;
  color: var(--ink-muted); cursor: pointer; transition: background 150ms, color 150ms;
}
.page-nav-btn:hover { background: var(--surface-2); color: var(--ink); }
.page-nav-btn.active { background: var(--accent); color: #fff; }
.page-nav-btn:active { transform: scale(0.97); }

/* ─── Theme Indicator ─── */
.theme-indicator { display: inline-flex; align-items: center; gap: var(--sp-2); font-size: 11px; color: var(--ink-subtle); padding: 4px 10px; background: var(--surface-0); border: 1px solid var(--hairline); border-radius: 12px; margin-bottom: var(--sp-5); }
.theme-indicator__dot { width: 7px; height: 7px; border-radius: 50%; background: var(--accent); }
.theme-indicator__name { font-weight: 500; color: var(--ink-muted); }

/* ─── View sections ─── */
.view { display: none; }
.view.active { display: block; }

/* ─── Stats Strip ─── */
.stats-strip { display: flex; gap: var(--sp-6); padding: var(--sp-4) var(--sp-5); background: var(--surface-0); border: 1px solid var(--hairline); border-radius: var(--radius); margin-bottom: var(--sp-8); }
.stats-strip__item { display: flex; align-items: baseline; gap: var(--sp-2); }
.stats-strip__value { font-size: 18px; font-weight: 600; color: var(--ink); letter-spacing: -0.01em; }
.stats-strip__value--accent { color: var(--accent); }
.stats-strip__label { font-size: 12px; color: var(--ink-subtle); }
.stats-strip__sep { width: 1px; background: var(--hairline); align-self: stretch; }

/* ─── Section ─── */
.section { margin-bottom: var(--sp-12); }
.section__header { display: flex; align-items: baseline; gap: var(--sp-3); margin-bottom: var(--sp-5); }
.section__title { font-size: 16px; font-weight: 600; color: var(--ink); letter-spacing: -0.01em; }
.section__count { font-size: 12px; color: var(--ink-subtle); font-family: var(--font-mono); }

/* ─── Feed ─── */
.feed { display: flex; flex-direction: column; gap: 1px; }
.feed__item { display: flex; align-items: center; gap: var(--sp-3); padding: var(--sp-3) var(--sp-4); background: var(--surface-0); border: 1px solid var(--hairline); border-radius: var(--radius-xs); margin-bottom: var(--sp-1); transition: border-color 150ms, transform 150ms; }
.feed__item:hover { border-color: var(--hairline-strong); transform: translateY(-1px); }
.feed__badge { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.feed__badge--new { background: var(--success); }
.feed__badge--updated { background: var(--warning); }
.feed__title { font-size: 13px; font-weight: 500; color: var(--ink); flex: 1; }
.feed__meta { font-size: 12px; color: var(--ink-subtle); font-family: var(--font-mono); }
.feed__type { font-size: 11px; padding: 2px 6px; border-radius: 3px; font-weight: 500; }
.feed__type--java { background: color-mix(in srgb, var(--node-java) 15%, transparent); color: var(--node-java); }
.feed__type--xml { background: color-mix(in srgb, var(--node-xml) 15%, transparent); color: var(--node-xml); }
.feed__type--beanshell { background: color-mix(in srgb, var(--node-beanshell) 15%, transparent); color: var(--node-beanshell); }
.feed__type--config { background: color-mix(in srgb, var(--node-config) 15%, transparent); color: var(--node-config); }
.feed__type--docs { background: color-mix(in srgb, var(--node-docs) 15%, transparent); color: var(--node-docs); }
.feed__type--tokens { background: color-mix(in srgb, var(--node-tokens) 15%, transparent); color: var(--node-tokens); }
.feed__badge--removed { background: var(--danger, #ef4444); }
.feed--empty { padding: var(--sp-6); text-align: center; background: var(--surface-0); border: 1px dashed var(--hairline-strong); border-radius: var(--radius-xs); }
.feed__empty-msg { font-size: 13px; color: var(--ink-subtle); }
.feed__empty-msg code { font-family: var(--font-mono); font-size: 12px; padding: 1px 4px; background: var(--surface-2); border-radius: 3px; color: var(--accent-hover); }

/* ─── Cards Grid ─── */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: var(--sp-4); }
.card { background: var(--surface-0); border: 1px solid var(--hairline); border-radius: var(--radius); padding: var(--sp-5); transition: border-color 150ms, transform 150ms; cursor: pointer; }
.card:hover { border-color: var(--hairline-strong); transform: translateY(-2px); }
.card__header { display: flex; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-2); }
.card__icon { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }
.card__title { font-size: 14px; font-weight: 600; color: var(--ink); }
.card__count { margin-left: auto; font-size: 12px; color: var(--accent); font-family: var(--font-mono); font-weight: 600; }
.card__desc { font-size: 12px; color: var(--ink-subtle); line-height: 1.4; margin-top: var(--sp-2); }
.card__icon-emoji { font-size: 18px; flex-shrink: 0; line-height: 1; }
.card__subs { font-size: 11px; color: var(--ink-faint); line-height: 1.4; margin-top: var(--sp-1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ─── Connected List ─── */
.connected-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.connected__item { display: flex; align-items: center; gap: var(--sp-3); padding: var(--sp-3) var(--sp-4); background: var(--surface-0); border: 1px solid var(--hairline); border-radius: var(--radius-xs); }
.connected__rank { font-size: 11px; font-family: var(--font-mono); color: var(--ink-faint); width: 20px; text-align: center; }
.connected__info { flex: 1; }
.connected__name { font-size: 13px; font-weight: 500; color: var(--ink); }
.connected__refs { font-size: 11px; color: var(--ink-subtle); margin-top: 2px; }
.connected__bar { width: 80px; height: 3px; background: var(--hairline); border-radius: 2px; overflow: hidden; }
.connected__bar-fill { height: 100%; border-radius: 2px; background: linear-gradient(90deg, var(--accent-muted), var(--accent)); }

/* ─── Table ─── */
.table-wrap { overflow-x: auto; border: 1px solid var(--hairline); border-radius: var(--radius); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead th { background: var(--surface-1); font-size: 12px; font-weight: 600; color: var(--ink-muted); text-align: left; padding: var(--sp-2) var(--sp-3); border-bottom: 1px solid var(--hairline); white-space: nowrap; cursor: pointer; user-select: none; }
thead th:hover { color: var(--ink); }
thead th .sort-icon { font-size: 10px; margin-left: 4px; color: var(--ink-faint); }
tbody tr { border-bottom: 1px solid var(--hairline); }
tbody tr:nth-child(even) { background: var(--surface-0); }
tbody tr:hover { background: var(--surface-2); }
tbody td { padding: var(--sp-2) var(--sp-3); color: var(--ink); }
tbody td.td-muted { color: var(--ink-muted); }
tbody td.td-mono { font-family: var(--font-mono); font-size: 12px; }
tbody td.td-accent { color: var(--accent); font-weight: 500; }

/* ─── Breadcrumbs ─── */
.breadcrumbs { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--ink-subtle); margin-bottom: var(--sp-4); }
.breadcrumbs a { color: var(--ink-muted); }
.breadcrumbs a:hover { color: var(--accent); }
.breadcrumbs__sep { color: var(--ink-faint); }

/* ─── Filter Bar ─── */
.filter-bar { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-4); padding: var(--sp-3) var(--sp-4); background: var(--surface-0); border: 1px solid var(--hairline); border-radius: var(--radius); }
.filter-bar__input { flex: 1; background: transparent; border: none; outline: none; font-size: 13px; color: var(--ink); font-family: var(--font-sans); }
.filter-bar__input::placeholder { color: var(--ink-faint); }
.filter-bar__icon { color: var(--ink-subtle); font-size: 13px; }
.filter-bar__count { font-size: 11px; color: var(--ink-subtle); font-family: var(--font-mono); }

/* ─── Page Detail ─── */
.page-detail { background: var(--surface-0); border: 1px solid var(--hairline); border-radius: var(--radius); padding: var(--sp-6); max-width: 800px; }
.page-meta { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); padding-bottom: var(--sp-4); border-bottom: 1px solid var(--hairline); margin-bottom: var(--sp-5); }
.page-meta__sep { width: 1px; height: 16px; background: var(--hairline); }
.page-meta__item { font-size: 12px; color: var(--ink-subtle); }
.page-meta__item strong { color: var(--ink-muted); font-weight: 500; }
.tag { display: inline-flex; align-items: center; padding: 2px 8px; font-size: 11px; border-radius: 10px; background: var(--surface-2); color: var(--ink-muted); transition: opacity 150ms; cursor: pointer; }
.tag:hover { opacity: 0.8; }
.page-body { font-size: 14px; line-height: 1.7; color: var(--ink); }
.page-body p { margin-bottom: var(--sp-4); }
.page-body h2 { font-size: 18px; font-weight: 600; letter-spacing: -0.01em; margin-top: var(--sp-6); margin-bottom: var(--sp-3); }
.page-body h3 { font-size: 15px; font-weight: 600; margin-top: var(--sp-5); margin-bottom: var(--sp-2); }
.page-body ul { margin: var(--sp-2) 0 var(--sp-4) var(--sp-5); }
.page-body li { margin-bottom: var(--sp-1); color: var(--ink-muted); font-size: 13px; }
.page-body li code { font-family: var(--font-mono); font-size: 12px; padding: 1px 4px; background: var(--surface-2); border-radius: 3px; color: var(--accent-hover); }
.page-body code { font-family: var(--font-mono); font-size: 12px; padding: 2px 5px; background: var(--surface-2); border-radius: 3px; color: var(--accent-hover); }

/* ─── Cross References ─── */
.xrefs { margin-top: var(--sp-6); padding-top: var(--sp-5); border-top: 1px solid var(--hairline); }
.xrefs__title { font-size: 13px; font-weight: 600; color: var(--ink-muted); margin-bottom: var(--sp-3); display: flex; align-items: center; gap: var(--sp-2); }
.xrefs__count { font-size: 11px; font-family: var(--font-mono); color: var(--accent); }
.xrefs__list { display: flex; flex-direction: column; gap: var(--sp-1); }
.xref { display: flex; align-items: center; gap: var(--sp-2); padding: var(--sp-2) var(--sp-3); border-radius: var(--radius-xs); font-size: 13px; color: var(--ink-muted); transition: background 150ms; }
.xref:hover { background: var(--surface-2); }
.xref__arrow { color: var(--ink-faint); font-size: 11px; width: 16px; text-align: center; }
.xref__name { color: var(--accent); }
.xref__type { margin-left: auto; }

/* ─── Backlinks ─── */
.backlinks { margin-top: var(--sp-6); padding: var(--sp-5); background: var(--surface-1); border: 1px solid var(--hairline); border-radius: var(--radius); }
.backlinks__title { font-size: 13px; font-weight: 600; color: var(--ink); margin-bottom: var(--sp-3); display: flex; align-items: center; gap: var(--sp-2); }
.backlinks__title-icon { color: var(--accent); }
.backlinks__group { margin-bottom: var(--sp-3); }
.backlinks__group-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ink-subtle); margin-bottom: var(--sp-1); padding-left: var(--sp-2); }
.backlinks__list { display: flex; flex-direction: column; gap: 2px; }
.backlink { display: flex; align-items: center; gap: var(--sp-2); padding: var(--sp-2) var(--sp-3); font-size: 13px; color: var(--ink-muted); border-radius: var(--radius-xs); transition: background 150ms; cursor: pointer; }
.backlink:hover { background: var(--surface-2); color: var(--ink); }
.backlink__arrow { color: var(--ink-faint); font-size: 10px; }
.backlink__name { color: var(--accent); }

/* ─── Code Block ─── */
.code-block { position: relative; background: var(--surface-0); border: 1px solid var(--hairline); border-radius: var(--radius); overflow: hidden; margin: var(--sp-4) 0; }
.code-block__header { display: flex; align-items: center; justify-content: space-between; padding: var(--sp-2) var(--sp-3); background: var(--surface-1); border-bottom: 1px solid var(--hairline); }
.code-block__lang { font-size: 11px; font-family: var(--font-mono); color: var(--ink-subtle); }
.code-block__copy { font-size: 11px; padding: 3px 8px; border-radius: var(--radius-xs); border: 1px solid var(--hairline); background: transparent; color: var(--ink-muted); cursor: pointer; transition: background 150ms, color 150ms; }
.code-block__copy:hover { background: var(--surface-2); color: var(--ink); }
.code-block__copy:active { transform: scale(0.97); }
.code-block pre { padding: var(--sp-4); overflow-x: auto; font-family: var(--font-mono); font-size: 13px; line-height: 1.5; color: var(--ink-muted); }
.code-block pre .kw { color: var(--node-beanshell); }
.code-block pre .str { color: var(--accent); }
.code-block pre .cmt { color: var(--ink-faint); font-style: italic; }
.code-block pre .fn { color: var(--node-java); }
.code-block pre .num { color: var(--node-tokens); }

/* ─── Badges ─── */
.badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 7px; font-size: 11px; font-weight: 500; border-radius: 3px; }
.badge--java { background: color-mix(in srgb, var(--node-java) 15%, transparent); color: var(--node-java); }
.badge--xml { background: color-mix(in srgb, var(--node-xml) 15%, transparent); color: var(--node-xml); }
.badge--beanshell { background: color-mix(in srgb, var(--node-beanshell) 15%, transparent); color: var(--node-beanshell); }
.badge--config { background: color-mix(in srgb, var(--node-config) 15%, transparent); color: var(--node-config); }
.badge--docs { background: color-mix(in srgb, var(--node-docs) 15%, transparent); color: var(--node-docs); }
.badge--tokens { background: color-mix(in srgb, var(--node-tokens) 15%, transparent); color: var(--node-tokens); }

/* ─── Command Palette ─── */
.palette-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: flex-start; justify-content: center; padding-top: 20vh; }
.palette-overlay[hidden] { display: none !important; }
.palette { background: var(--surface-0); border: 1px solid var(--hairline); border-radius: 12px; width: 560px; max-width: 100%; overflow: hidden; box-shadow: 0 0 0 1px var(--hairline-strong); }
.palette__input-wrap { display: flex; align-items: center; gap: var(--sp-3); padding: var(--sp-4) var(--sp-5); border-bottom: 1px solid var(--hairline); }
.palette__icon { color: var(--ink-subtle); font-size: 14px; }
.palette__input { flex: 1; background: transparent; border: none; outline: none; font-size: 14px; color: var(--ink); font-family: var(--font-sans); }
.palette__input::placeholder { color: var(--ink-faint); }
.palette__results { padding: var(--sp-2) 0; }
.palette__result { display: flex; align-items: center; gap: var(--sp-3); padding: var(--sp-2) var(--sp-5); cursor: pointer; transition: background 100ms; }
.palette__result:hover, .palette__result--active { background: var(--surface-2); }
.palette__result-icon { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-xs); background: var(--surface-1); border: 1px solid var(--hairline); font-size: 12px; color: var(--ink-muted); }
.palette__result-info { flex: 1; }
.palette__result-title { font-size: 13px; font-weight: 500; color: var(--ink); }
.palette__result-path { font-size: 11px; color: var(--ink-subtle); font-family: var(--font-mono); }
.palette__result-badge { margin-left: auto; }
.palette__footer { display: flex; align-items: center; gap: var(--sp-4); padding: var(--sp-2) var(--sp-5); border-top: 1px solid var(--hairline); font-size: 11px; color: var(--ink-faint); }
.palette__footer kbd { font-family: var(--font-mono); font-size: 10px; padding: 1px 4px; background: var(--surface-2); border-radius: 3px; border: 1px solid var(--hairline); }

/* ─── Graph Panel ─── */
.graph-panel { background: var(--surface-0); border-left: 1px solid var(--hairline); display: flex; flex-direction: column; overflow: hidden; position: relative; }
.graph-panel__header { display: flex; align-items: center; justify-content: space-between; padding: var(--sp-3) var(--sp-4); border-bottom: 1px solid var(--hairline); }
.graph-panel__title { font-size: 12px; font-weight: 600; color: var(--ink-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.graph-panel__expand { font-size: 11px; color: var(--accent); cursor: pointer; }
.graph-panel__canvas { flex: 1; position: relative; overflow: hidden; }
.graph-panel__canvas svg { width: 100%; height: 100%; }
.graph-panel__fade-top, .graph-panel__fade-bottom { position: absolute; left: 0; right: 0; height: 40px; pointer-events: none; z-index: 2; }
.graph-panel__fade-top { top: 0; background: linear-gradient(to bottom, var(--surface-0), transparent); }
.graph-panel__fade-bottom { bottom: 0; background: linear-gradient(to top, var(--surface-0), transparent); }
.graph-panel__legend { padding: var(--sp-3) var(--sp-4); border-top: 1px solid var(--hairline); display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.graph-panel__legend-item { display: flex; align-items: center; gap: 4px; font-size: 10px; color: var(--ink-subtle); }
.graph-panel__legend-dot { width: 6px; height: 6px; border-radius: 50%; }

/* ─── Full Graph View ─── */
.graph-full { background: var(--surface-0); border: 1px solid var(--hairline); border-radius: var(--radius); overflow: hidden; }
.graph-full__header { display: flex; align-items: center; justify-content: space-between; padding: var(--sp-4) var(--sp-5); border-bottom: 1px solid var(--hairline); }
.graph-full__stats { display: flex; gap: var(--sp-4); font-size: 12px; color: var(--ink-subtle); }
.graph-full__stat-val { font-weight: 600; color: var(--ink); margin-right: 4px; }
.graph-full__canvas { position: relative; }
.graph-full__canvas svg { width: 100%; height: 500px; display: block; }
.graph-full__legend { display: flex; flex-wrap: wrap; gap: var(--sp-4); padding: var(--sp-4) var(--sp-5); border-top: 1px solid var(--hairline); }
.graph-full__legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--ink-muted); }
.graph-full__legend-dot { width: 10px; height: 10px; border-radius: 50%; }

/* ─── JSON Link ─── */
.json-link { margin-top: var(--sp-5); padding: var(--sp-3) var(--sp-4); background: var(--surface-0); border: 1px dashed var(--hairline-strong); border-radius: var(--radius-xs); font-size: 12px; color: var(--ink-subtle); font-family: var(--font-mono); }
.json-link a { color: var(--accent); }

/* ─── Collapsible Details ─── */
.ref-summary { display: flex; align-items: center; gap: var(--sp-2); font-size: 12px; color: var(--ink-subtle); margin-bottom: var(--sp-4); }
.ref-summary__stat { font-family: var(--font-mono); font-weight: 600; color: var(--accent); }
.ref-summary__sep { color: var(--ink-faint); }

details.ref-section { margin-top: var(--sp-5); border-top: 1px solid var(--hairline); }
details.ref-section + details.ref-section { border-top: none; }
details.ref-section > summary {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-1); font-size: 13px; font-weight: 600;
  color: var(--ink-muted); cursor: pointer; list-style: none; user-select: none;
  transition: color 150ms;
}
details.ref-section > summary::-webkit-details-marker { display: none; }
details.ref-section > summary::before {
  content: '▸'; font-size: 10px; color: var(--ink-faint);
  width: 14px; text-align: center; flex-shrink: 0;
  transition: transform 150ms;
}
details.ref-section[open] > summary::before { transform: rotate(90deg); }
details.ref-section > summary:hover { color: var(--ink); }
details.ref-section > .ref-section__body { padding: 0 0 var(--sp-3) var(--sp-4); border-left: 2px solid var(--accent-muted); margin-left: 6px; }

details.ref-group { margin-bottom: var(--sp-1); }
details.ref-group > summary {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-1) var(--sp-2); font-size: 12px; font-weight: 500;
  color: var(--ink-subtle); cursor: pointer; list-style: none;
  border-radius: var(--radius-xs); transition: background 150ms, color 150ms;
}
details.ref-group > summary::-webkit-details-marker { display: none; }
details.ref-group > summary::before {
  content: '▸'; font-size: 9px; color: var(--ink-faint);
  width: 12px; text-align: center; flex-shrink: 0;
  transition: transform 150ms;
}
details.ref-group[open] > summary::before { transform: rotate(90deg); }
details.ref-group > summary:hover { background: var(--surface-2); color: var(--ink); }
details.ref-group > summary .ref-group__count { margin-left: auto; font-size: 10px; font-family: var(--font-mono); color: var(--ink-faint); }
details.ref-group > .ref-group__body { padding: var(--sp-1) 0 var(--sp-1) var(--sp-5); }

.ref-link {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: 3px var(--sp-2); font-size: 12px; color: var(--ink-muted);
  border-radius: var(--radius-xs); transition: background 150ms; cursor: pointer;
}
.ref-link:hover { background: var(--surface-2); color: var(--ink); }
.ref-link__arrow { color: var(--ink-faint); font-size: 10px; width: 14px; text-align: center; flex-shrink: 0; }
.ref-link__name { color: var(--accent); }

/* ─── Graph View Toggle ─── */
.graph-view-toggle { display: flex; gap: var(--sp-1); padding: 3px; background: var(--surface-0); border: 1px solid var(--hairline); border-radius: var(--radius); width: fit-content; margin-bottom: var(--sp-4); }
.graph-view-toggle button {
  padding: 5px 12px; font-size: 12px; font-weight: 500; font-family: var(--font-sans);
  border: none; border-radius: var(--radius-sm); background: transparent;
  color: var(--ink-muted); cursor: pointer; transition: background 150ms, color 150ms;
}
.graph-view-toggle button:hover { background: var(--surface-2); color: var(--ink); }
.graph-view-toggle button.active { background: var(--accent); color: #fff; }
.graph-view-toggle button:active { transform: scale(0.97); }

/* ─── Neural Network Graph ─── */
.neural-graph { border: 1px solid var(--hairline); border-radius: var(--radius); overflow: hidden; position: relative; }
.neural-graph svg { width: 100%; height: 520px; display: block; }
.neural-graph__label {
  font-size: 10px; font-weight: 600; fill: var(--ink-muted); text-transform: uppercase; letter-spacing: 0.05em;
}

/* ─── Showcase Divider ─── */
.showcase-divider { margin: var(--sp-12) 0; border: none; border-top: 1px solid var(--hairline); position: relative; }
.showcase-divider::after { content: attr(data-label); position: absolute; top: -9px; left: var(--sp-5); background: var(--canvas); padding: 0 var(--sp-3); font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-subtle); }

/* ─── Utility ─── */
.flex { display: flex; }
.flex-wrap { flex-wrap: wrap; }
.gap-2 { gap: var(--sp-2); }
.gap-3 { gap: var(--sp-3); }
.mt-4 { margin-top: var(--sp-4); }
.mt-6 { margin-top: var(--sp-6); }
.mb-4 { margin-bottom: var(--sp-4); }
"""
