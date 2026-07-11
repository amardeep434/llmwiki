# LLMWiki DESIGN.md

A dark-first knowledge graph interface that makes 2000+ pages feel navigable and connected.

## Visual Theme & Atmosphere

**Philosophy:** Dense technical knowledge made navigable through spatial relationships — not a documentation site, a living knowledge system. Inspired by Obsidian's graph-centric approach, Linear's premium dark precision, and Supabase's emerald energy.

**Mood:** Focused, technical, interconnected. Every page exists in a web of relationships. The graph is always visible — you're never "lost" in isolated content.

**Density:** High information density (developer tool, not marketing page). Compact without feeling cramped. Whitespace is deliberate, not generous.

## Color Palette & Roles

```yaml
colors:
  # Accent
  accent: "#10b981"           # Emerald — links, active states, graph highlights
  accent-hover: "#34d399"     # Lighter emerald on hover
  accent-muted: "#065f46"     # Dark emerald for backgrounds
  accent-subtle: "#022c22"    # Very dark emerald tint
  
  # Dark theme (DEFAULT)
  canvas: "#0a0a0f"           # Near-black with slight blue tint
  surface-0: "#12121a"        # Card/panel background
  surface-1: "#1a1a25"        # Elevated surface (sidebar, nav)
  surface-2: "#22222e"        # Hover state background
  surface-3: "#2a2a38"        # Active/selected state
  
  # Text
  ink: "#e4e4e7"              # Primary text (zinc-200)
  ink-muted: "#a1a1aa"        # Secondary text (zinc-400)
  ink-subtle: "#71717a"       # Tertiary text (zinc-500)
  ink-faint: "#52525b"        # Disabled/placeholder (zinc-600)
  
  # Borders
  hairline: "#27272a"         # Subtle borders (zinc-800)
  hairline-strong: "#3f3f46"  # Prominent borders (zinc-700)
  
  # Semantic
  success: "#10b981"          # Same as accent
  warning: "#f59e0b"          # Amber
  error: "#ef4444"            # Red
  info: "#6366f1"             # Indigo
  
  # Graph node colors (by content type)
  node-java: "#f59e0b"        # Amber — Java source
  node-xml: "#6366f1"         # Indigo — XML/workflows
  node-beanshell: "#ec4899"   # Pink — BeanShell scripts
  node-docs: "#10b981"        # Emerald — documentation
  node-config: "#8b5cf6"      # Violet — config files
  node-tokens: "#f97316"      # Orange — token registry
  
  # Light theme overrides
  light:
    canvas: "#fafafa"
    surface-0: "#ffffff"
    surface-1: "#f4f4f5"
    surface-2: "#e4e4e7"
    surface-3: "#d4d4d8"
    ink: "#18181b"
    ink-muted: "#52525b"
    ink-subtle: "#71717a"
    hairline: "#e4e4e7"
    hairline-strong: "#d4d4d8"
```

## Typography Rules

```yaml
typography:
  # System font stack — no network requests
  font-sans: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
  font-mono: "'SF Mono', 'Cascadia Code', 'JetBrains Mono', Consolas, 'Liberation Mono', monospace"
  
  # Scale
  display:     { size: 28px, weight: 700, leading: 1.2, tracking: -0.02em }
  heading-1:   { size: 24px, weight: 600, leading: 1.3, tracking: -0.01em }
  heading-2:   { size: 20px, weight: 600, leading: 1.3, tracking: -0.01em }
  heading-3:   { size: 16px, weight: 600, leading: 1.4, tracking: 0 }
  heading-4:   { size: 14px, weight: 600, leading: 1.4, tracking: 0 }
  body:        { size: 14px, weight: 400, leading: 1.6, tracking: 0 }
  body-sm:     { size: 13px, weight: 400, leading: 1.5, tracking: 0 }
  caption:     { size: 12px, weight: 400, leading: 1.4, tracking: 0.01em }
  mono:        { size: 13px, weight: 400, leading: 1.5, tracking: 0 }
  
  # Usage rules
  # - Page titles: display
  # - Section headings in content: heading-1 through heading-4
  # - Body text, table cells: body
  # - Sidebar items, breadcrumbs, meta: body-sm
  # - Tags, badges, timestamps: caption
  # - Code blocks, inline code: mono
```

## Layout Principles

```yaml
layout:
  # Three-panel layout (Obsidian-style)
  sidebar-width: 260px           # Left sidebar (collapsible)
  graph-panel-width: 280px       # Right mini-graph panel (collapsible)
  content-min-width: 600px       # Main content area
  topbar-height: 48px            # Top navigation bar
  
  # Spacing scale (4px base)
  space-1: 4px
  space-2: 8px
  space-3: 12px
  space-4: 16px
  space-5: 20px
  space-6: 24px
  space-8: 32px
  space-10: 40px
  space-12: 48px
  
  # Grid
  # - Sidebar: fixed, collapsible at <1024px
  # - Content: fluid, fills remaining space
  # - Graph panel: fixed, collapsible at <1280px
  # - Cards: CSS grid, auto-fill, min 280px
  
  # Responsive breakpoints
  mobile: 640px    # Stack everything, hide sidebar + graph
  tablet: 1024px   # Hide sidebar, keep content + graph toggle
  desktop: 1280px  # Show all three panels
```

## Component Stylings

### Navigation (Top Bar)
- Background: `surface-1` with `backdrop-filter: blur(12px)`
- Height: 48px, `position: sticky; top: 0; z-index: 50`
- Brand: emerald icon + "LLMWiki" in heading-4 weight
- Links: `ink-muted` → `ink` on hover, `accent` when active
- Search trigger: pill-shaped, `surface-2` background, "⌘K" badge
- Theme toggle: icon button, subtle

### Navigation (Left Sidebar)
- Background: `surface-0`
- Width: 260px, collapsible with toggle button
- Content: collapsible tree of categories
- Tree items: `body-sm`, indent with 16px per level
- Active item: `accent-subtle` background, `accent` text
- Hover: `surface-2` background
- Section headers: `caption` size, `ink-subtle`, uppercase
- Scrollable independently from content

### Mini Graph Panel (Right)
- Background: `surface-0`
- Width: 280px, collapsible
- Contains: force-directed graph of current page's neighborhood (2-hop)
- Current page node: highlighted with `accent` border
- Connected nodes: colored by type (see node colors above)
- Click node → navigate to that page
- "Expand" button → navigate to full /graph.html

### Cards (Dashboard)
- Background: `surface-0`
- Border: 1px `hairline`
- Border-radius: 8px
- Padding: space-4
- Hover: border → `hairline-strong`, subtle translateY(-1px)
- No box-shadow (flat design)

### Page Detail
- Metadata bar: horizontal strip at top with type, language, tags, importance
- Tags: pill-shaped, `surface-2` background, `caption` size
- Content body: `body` typography, max-width 800px within content area
- Headings: `heading-1` through `heading-4` with anchor links
- Code blocks: `surface-0` background, `hairline` border, `mono` font, copy button
- Cross-references: compact list with → / ← arrows, colored by type
- Backlinks: section at bottom, links grouped by category

### Command Palette (⌘K)
- Modal overlay: `canvas` at 80% opacity backdrop
- Dialog: `surface-0`, 560px wide, rounded 12px, `hairline` border
- Input: full width, no border, `body` size, placeholder in `ink-subtle`
- Results: list items with icon + title + category badge
- Active result: `surface-2` background
- Keyboard hints: `caption` size at bottom

### Tables
- Header: `surface-1` background, `body-sm` weight 600, `ink-muted`
- Rows: alternate `canvas` / `surface-0` (subtle zebra)
- Hover: `surface-2`
- Borders: only horizontal `hairline` between rows
- Cell padding: space-2 vertical, space-3 horizontal

### Importance Bar
- Thin (3px) horizontal bar
- Background: `hairline`
- Fill: gradient from `accent-muted` to `accent`
- Width: percentage of importance score

## Depth & Elevation

Flat design — no box-shadows. Depth is communicated through:
- Surface color hierarchy (canvas < surface-0 < surface-1 < surface-2)
- Border presence/absence
- Subtle backdrop-filter blur on floating elements (nav, palette)

## Do's and Don'ts

### Do
- Use the graph panel to show spatial context for current page
- Show cross-reference counts prominently (they're the value proposition)
- Use color-coding consistently for content types
- Keep navigation predictable — sidebar tree matches URL structure
- Make search the fastest path to any content

### Don't
- Add decorative elements — every pixel should be informational
- Use color for decoration — color means TYPE or STATE
- Put important info below the fold without indication
- Make the user scroll to find basic metadata
- Use large hero sections — this is a tool, not a landing page

## Responsive Behavior

| Viewport | Layout |
|----------|--------|
| ≥1280px (desktop) | Sidebar + Content + Graph panel |
| 1024–1279px (tablet) | Content + collapsible sidebar toggle + graph toggle |
| <1024px (mobile) | Content only + hamburger for sidebar + bottom nav |

- Sidebar collapses to icon-only rail at tablet
- Graph panel hides at tablet (accessible via toggle button)
- At mobile: full-screen content, bottom tab bar (Home, Search, Graph, Menu)
- Tables become horizontally scrollable at mobile
- Command palette becomes full-screen at mobile

## Agent Prompt Guide

**Quick reference for AI code generation:**
- Canvas: `#0a0a0f`, Surface: `#12121a`, Accent: `#10b981`
- Font: system stack, 14px body, 13px mono
- Layout: sidebar(260px) + fluid content + graph(280px)
- All borders: 1px solid `#27272a`
- Rounded corners: 8px cards, 6px buttons, 4px inputs
- Transitions: 150ms ease-out for interactive states
- No shadows, no gradients (except accent importance bar)
