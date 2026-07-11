# LLMWiki Session Handoff — UI Polish & Remaining Work

**Date:** 2026-07-11
**Session Duration:** 8+ hours
**Project Location:** `~/llmwiki/` (git repo, 35+ commits)
**Test Site Data:** `/tmp/rioiam-wiki/` (2,206 pages from RioIAM codebase)
**UI Preview (approved design):** `/tmp/llmwiki-preview.html` (93KB, the APPROVED reference)

---

## What Was Built (Complete & Working)

### Core Pipeline
- **6 adapters**: source-code (30+ langs), xml (with BeanShell extraction), pdf (pymupdf font-based), markdown, config, generic
- **PDF converter**: Font-based heading detection, table extraction via `find_tables()`, bullet/sub-bullet glyph handling, image extraction, header/footer stripping
- **Cross-reference engine**: Title-mention matching (9,874 edges, 100% page connectivity), PageRank importance scoring, connected-component clustering
- **Build pipeline**: raw/ → wiki/ → site/ with incremental builds via content-hash state tracking
- **Search**: SQLite FTS5 database + client-side JSON search index (3.1MB)
- **AI exports**: llms.txt, llms-full.txt, graph.jsonld, sitemap.xml, per-page JSON siblings
- **Theme system**: Swappable themes via CSS variables. Built-in: emerald-dark (default), vodafone. `llmwiki build --theme vodafone` or config.
- **Agent integration**: Auto-generates CLAUDE.md, AGENTS.md, .github/copilot-instructions.md, GEMINI.md
- **Token registry**: Auto-scans for %%TOKEN%% patterns, generates documentation page
- **CLI**: 15 commands (init, ingest, build, serve, search, graph, export, lint, stats, themes, clean, diff, all + --force, --theme flags)

### Tests
- **110 tests passing** (including E2E, PDF conversion with real files)
- All tests at `~/llmwiki/tests/`

### Documentation
- README, 7 docs/ guides, CONTRIBUTING, CHANGELOG, DESIGN.md — all updated to current state
- Spec: `docs/superpowers/specs/2026-07-11-llmwiki-design.md`
- Plan: `docs/superpowers/plans/2026-07-11-llmwiki-implementation.md`

---

## UI: Approved Design vs Current State

### The Approved Reference
**File:** `/tmp/llmwiki-preview.html` (93KB self-contained HTML)
- Three-panel layout: sidebar + content + graph panel
- Dark-first with emerald accent (#10b981)
- System font stack
- 4 page views: Dashboard, Category Index, Page Detail, Full Graph
- Theme switcher: Emerald ↔ Vodafone, Dark ↔ Light
- Neural network graph view (static SVG mockup)

### What's Implemented (in `llmwiki/render/`)
- `css.py` — ~405 lines, CSS from preview (mostly accurate)
- `js.py` — ~770 lines, theme engine, command palette, neural graph, mini graph
- `html.py` — ~1,200 lines, all page generators

### What's Broken / Missing (UI Issues)

#### 1. Sidebar Numbers Garbled (CRITICAL)
**Symptom:** Numbers like `1122` render as `1188`, `744` as `788` in the browser.
**HTML is correct** — verified via curl. The RENDERING is wrong.
**Attempted fixes:** Changed font from mono to sans, removed `font-variant-numeric: tabular-nums`, increased size to 12px. None fixed it.
**Likely cause:** Emoji icons (📜, 📋, 📚) before the count spans may be affecting text rendering context. Or a CSS rule I haven't found is overriding the font.
**How to debug:** Open browser DevTools → inspect `.sidebar__item-count` → check computed font-family and font-size. Check if disabling the emoji icons fixes the number rendering.

#### 2. Dashboard Stats Strip Not Rendering
**The `render_dashboard()` function generates stats** but they're not appearing in the output HTML.
**Check:** `grep "stat__value" /tmp/rioiam-wiki/site/index.html` returns nothing — the stats section HTML might not be making it into the page.
**Location:** `llmwiki/render/html.py`, search for `stats_strip` or `stat__value` in the dashboard renderer.

#### 3. Recent Changes Feed Missing
**`render_dashboard()` accepts `recent_changes` parameter** but it's always empty `[]`.
**Root cause:** `build.py` passes `[]` for recent_changes. It should compare current build to previous state and compute what changed.
**Fix:** In `build.py`, before building, load the previous `.llmwiki-state.json`, compare to current state, build a list of changes (added/modified/removed pages), pass to dashboard renderer.

#### 4. Changelog Page Empty
**No build history entries** because `build-history.json` either doesn't exist or isn't being written/read properly.
**Check:** `cat /tmp/rioiam-wiki/site/build-history.json` and `cat /tmp/rioiam-wiki/build-history.json` — one of these should have entries.
**Fix:** Ensure `build_site()` writes to `build-history.json` AND the changelog renderer reads it.

#### 5. Neural Network Graph Not Matching Video
**The video reference:** `/home/amardeep/Downloads/m2-res_1080p.mp4` — Anthropic "Obsidian Brain" neural network visualization.
**What it shows:** Vertical columns (layers) with hundreds of nodes, curved glowing edges flowing between layers, dark cosmic background.
**Current state:** Canvas-based renderer exists but categorization uses `n.type` field which may not be giving enough distinct columns. Also the glow/visual quality is far from the video.
**What's needed:** WebGL-based renderer for the glow effects, more columns/detail, animated edges. This is a multi-day project to match the video exactly.

#### 6. Sidebar Tier-2 Behavior
**Symptom:** Clicking tier-2 items (· Beanshell) navigates to the category page instead of expanding inline. The `·` dot was previously a `▸` arrow which falsely suggested expandability.
**Current state:** Tier-2 items are `<a>` links — clicking navigates (correct behavior). But users expect expand/collapse.
**Decision needed:** Should tier-2 items expand inline (showing pages) or navigate?

#### 7. Category Page Sidebar Shows Wrong "All Pages" Count
**Symptom:** "All Pages (1122)" on the BeanShell category page instead of "All Pages (2206)".
**Cause:** The sidebar is being generated per-page with the CURRENT category's count, not the global total.
**Fix:** Pass `total_pages` to the sidebar renderer separately from the category page count.

#### 8. Hardcoded Data Issues
- Dashboard card descriptions are static strings in `_CONTENT_TYPE_META`
- The "Clusters" section always shows 1 giant cluster (clustering algorithm doesn't work well with 9,874 edges)
- Some category names display as raw paths (e.g., "Emailtemplate › Core › Manageaccount")

---

## Architecture Notes for Next Session

### File Structure
```
~/llmwiki/
├── llmwiki/
│   ├── render/
│   │   ├── css.py          # CSS as Python string constant (CSS variable)
│   │   ├── js.py           # JS as Python string constant (JS variable + PRE_PAINT_SCRIPT)
│   │   ├── html.py         # HTML generator functions (no template files)
│   │   └── themes/         # Theme definitions (emerald_dark.py, vodafone.py)
│   ├── adapters/            # 6 adapter modules + base.py + registry __init__.py
│   ├── build.py            # Main build orchestrator (raw→wiki→site)
│   ├── graph.py            # Knowledge graph builder
│   ├── crossref.py         # Cross-reference extraction
│   ├── importance.py       # PageRank scoring
│   ├── clusters.py         # Connected-component clustering
│   ├── search.py           # SQLite FTS5
│   ├── ingest.py           # Adapter orchestrator
│   ├── cli.py              # CLI dispatcher
│   ├── config.py           # llmwiki.json config
│   ├── state.py            # Build state tracking
│   ├── serve.py            # Local HTTP server
│   ├── exporters.py        # AI-consumable exports
│   ├── lint.py             # Quality checks
│   └── agent_schema.py     # CLAUDE.md/AGENTS.md generation
├── tests/                   # 110 tests
├── docs/                    # 10 documentation files
├── DESIGN.md               # UI design system specification
└── pyproject.toml           # 2 deps: markdown, pymupdf
```

### Key Suggestion for Next Session
**Stop using Python string constants for CSS/JS.** Instead:
1. Create `llmwiki/render/static/style.css` and `llmwiki/render/static/script.js` as actual files
2. Build reads and injects them (or copies to site/)
3. This allows editing CSS/JS with proper syntax highlighting, browser DevTools live reload, and direct testing

### How to Run
```bash
cd ~/llmwiki && pip install -e .                     # Install
cd /tmp/rioiam-wiki && llmwiki all --config llmwiki.json   # Build
llmwiki serve --port 8765                            # Serve at http://127.0.0.1:8765
```

### How to Test
```bash
cd ~/llmwiki && pytest tests/ -v                     # 110 tests
```

### How to Force Rebuild
```bash
llmwiki clean --all && llmwiki all --config llmwiki.json
```

---

## Priority Order for Next Session

1. **Fix sidebar number rendering** (DevTools investigation needed)
2. **Dashboard stats + recent changes** (wire live data)
3. **Move CSS/JS out of Python strings** (enables proper dev workflow)
4. **Visual polish iteration** (with browser feedback loop)
5. **Neural graph enhancement** (if time permits)
6. **Changelog with real build history**
