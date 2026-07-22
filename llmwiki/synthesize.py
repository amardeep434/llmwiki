"""Phase S synthesis layer — decide what curated knowledge needs writing.

llmwiki never calls an LLM itself. Its job in the synthesis loop is to (a)
hand the resident coding agent the conventions for curated pages (SCHEMA.md),
and (b) compute a work manifest: which extracted pages lack a hand-written
explanation, and which curated pages have gone stale because a source they
cite changed. The agent then writes/refreshes the pages; llmwiki validates and
indexes them.

The staleness helpers here are shared with lint (``stale-claim`` rule) so a
single definition of "a curated page is older than its sources" governs both
the work manifest and the lint gate.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from llmwiki.graph import _load_curated_pages, _parse_frontmatter


# The conventions handed to the agent. Kept as a module constant so tests can
# assert on it and `llmwiki init` can write it verbatim.
SCHEMA_MD = """# Curated Knowledge Conventions (llmwiki)

Curated pages live in `curated/**/*.md`. They are hand/agent-written and
llmwiki NEVER generates or deletes them (unlike `raw/`). Write here only what
is wiki-exclusive: cross-file explanations, architecture, provisioning/data
flows, and saved Q&A — knowledge that exists nowhere else in the codebase.

## Page types (frontmatter `type:`)

- **module**  — how one code module/file works and why (cross-references its raw page).
- **concept** — an idea that spans several files (e.g. "how provisioning flows").
- **entity**  — a domain object/record and its lifecycle.
- **note**    — a saved derivation or Q&A worth not re-deriving.

## Required frontmatter

```
---
title: "How provisioning flows"
type: concept                                 # module | concept | entity | note
sources: [rule/core/x, application/core/y]    # page ids this page derives from
synthesized_at: 2026-07-20T10:00:00Z          # ISO 8601 timestamp, you set it
tags: [provisioning]
---
```

## Rules

- **Citation**: every factual claim about the codebase must trace to a page id
  in `sources:`. Read each source first with `llmwiki get <id>`.
- **Size**: keep a page ≤150 lines. Split large topics into linked pages.
- **Linking**: reference other pages with `[[page-id]]`.
- **Contradictions**: when two sources disagree, flag it inline with a
  `> CONTRADICTION:` blockquote rather than silently picking one.
- **Freshness**: `synthesized_at` records when you wrote the page. If a cited
  source's raw page changes afterwards, `llmwiki synthesize` / `llmwiki lint`
  will flag the page as stale — refresh it and bump `synthesized_at`.
"""

TODO_FILENAME = "synthesis-todo.md"


# ---------------------------------------------------------------------------
# Staleness helpers (shared with lint)
# ---------------------------------------------------------------------------


def _iso_to_epoch(ts: str | None) -> float | None:
    """Parse an ISO 8601 timestamp to epoch seconds, or None if unparseable."""
    if not ts:
        return None
    try:
        cleaned = ts.strip().replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.timestamp()
    except (ValueError, AttributeError):
        return None


def build_source_mtime_map(raw_dir: Path) -> dict[str, float]:
    """Map each raw page id (slug) to the mtime of its `raw/` markdown file.

    Used to answer "did a source change after this curated page was written?".
    A light frontmatter scan rather than a full page load keeps it cheap.
    """
    mtimes: dict[str, float] = {}
    if not raw_dir.exists():
        return mtimes
    for md_file in raw_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, _ = _parse_frontmatter(content)
        slug = meta.get("slug", md_file.stem)
        try:
            mtimes[slug] = md_file.stat().st_mtime
        except OSError:
            continue
    return mtimes


def changed_sources(
    synthesized_at: str | None,
    sources: list[str],
    mtime_map: dict[str, float],
) -> list[str]:
    """Return the cited source ids whose raw file changed after synthesis."""
    syn = _iso_to_epoch(synthesized_at)
    if syn is None:
        # Unknown synthesis time: every locatable source counts as "changed"
        # so the page surfaces for a refresh.
        return [s for s in sources if s in mtime_map]
    return [s for s in sources if mtime_map.get(s, 0.0) > syn]


def is_curated_stale(
    synthesized_at: str | None,
    sources: list[str],
    mtime_map: dict[str, float],
) -> bool:
    """True when a curated page is older than a source it cites.

    A missing/unparseable ``synthesized_at`` counts as stale: without a
    trustworthy timestamp we cannot prove the page reflects its sources.
    """
    syn = _iso_to_epoch(synthesized_at)
    if syn is None:
        return True
    return any(mtime_map.get(s, 0.0) > syn for s in sources)


# ---------------------------------------------------------------------------
# Work-list computation
# ---------------------------------------------------------------------------


def compute_work_list(wiki_root: Path, config: dict, budget: int = 10) -> list[dict]:
    """Build a prioritised list of curated pages to write or refresh.

    Priority order:
      1. ``refresh`` — existing curated pages whose cited sources changed.
      2. ``create``  — highest-importance extracted pages not yet cited by any
         curated page.

    Total items are capped at ``budget`` with refresh items kept first, so an
    agent working a small budget always fixes drift before adding coverage.
    Each item is ``{kind, target, sources, reason}``.
    """
    raw_dir = wiki_root / "raw"
    curated_dir = wiki_root / "curated"
    out_name = config.get("build", {}).get("out_dir", "site")
    xref_path = wiki_root / out_name / "cross-references.json"

    curated_pages = _load_curated_pages(curated_dir)
    mtime_map = build_source_mtime_map(raw_dir)

    # Every source id already covered by some curated page. Ids are compared
    # case-insensitively to match graph edge resolution and the curated lint,
    # so a citation with different casing still counts as coverage (no dup
    # create item).
    covered: set[str] = set()
    for page in curated_pages.values():
        covered.update(s.lower() for s in page.get("sources", []))

    # 1. Refresh items (highest priority).
    refresh_items: list[dict] = []
    for pid in sorted(curated_pages):
        page = curated_pages[pid]
        sources = page.get("sources", [])
        if not sources:
            continue  # uncited pages are a lint concern, not a refresh target
        if not is_curated_stale(page.get("synthesized_at"), sources, mtime_map):
            continue
        stale_srcs = changed_sources(page.get("synthesized_at"), sources, mtime_map)
        if stale_srcs:
            reason = "sources changed since synthesis: " + ", ".join(stale_srcs)
        else:
            reason = "missing/unparseable synthesized_at — cannot verify freshness"
        refresh_items.append({
            "kind": "refresh",
            "target": f"{pid}.md",
            "sources": sources,
            "reason": reason,
        })

    # 2. Create items — uncovered high-importance extracted pages.
    create_items: list[dict] = []
    nodes = _load_xref_nodes(xref_path)
    nodes.sort(key=lambda n: n.get("importance", 0.0), reverse=True)
    for node in nodes:
        cat = str(node.get("type", "") or "")
        if cat.startswith("curated/") or cat.startswith("tokens") or cat == "tokens":
            continue
        nid = node.get("id", "")
        if not nid or nid.lower() in covered:
            continue
        suggested_type = "module" if node.get("language") else "concept"
        slug = nid.split("/")[-1]
        create_items.append({
            "kind": "create",
            "target": f"curated/{suggested_type}s/{slug}.md",
            "sources": [nid],
            "reason": (
                f"high-importance {cat or 'page'} "
                f"(importance {node.get('importance', 0.0):.3f}) "
                "not yet covered by any curated page"
            ),
        })

    # Clamp: a negative budget would make the [:budget] slice drop items from
    # the end instead of capping (CLI help says "Max work items").
    return (refresh_items + create_items)[:max(0, budget)]


def _load_xref_nodes(xref_path: Path) -> list[dict]:
    """Load graph nodes from a built cross-references.json (empty if absent)."""
    if not xref_path.exists():
        return []
    try:
        data = json.loads(xref_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    nodes = data.get("nodes", [])
    return nodes if isinstance(nodes, list) else []


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def format_work_list(items: list[dict]) -> str:
    """Human-readable manifest for stdout."""
    if not items:
        return "nothing needs synthesis"
    lines = [f"{len(items)} synthesis work item(s):", ""]
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. [{item['kind']}] {item['target']}")
        lines.append(f"     sources: {', '.join(item['sources']) or '(none)'}")
        lines.append(f"     reason:  {item['reason']}")
    return "\n".join(lines)


def render_todo(items: list[dict]) -> str:
    """Per-item instructions written to synthesis-todo.md for the agent."""
    lines = [
        "# Synthesis TODO",
        "",
        "Generated by `llmwiki synthesize`. Each item names a curated page to",
        "write or refresh. Follow the conventions in `SCHEMA.md`.",
        "",
    ]
    for i, item in enumerate(items, 1):
        srcs = item["sources"]
        lines.append(f"## {i}. [{item['kind']}] `{item['target']}`")
        lines.append("")
        lines.append(f"- Reason: {item['reason']}")
        lines.append(f"- Sources: {', '.join(srcs) or '(none)'}")
        lines.append("- Steps:")
        for src in srcs:
            lines.append(f'    1. `llmwiki get "{src}"` — read the source page.')
        lines.append(f"    2. Write `{item['target']}` per `SCHEMA.md` "
                     "(cite every claim in `sources:`, set `synthesized_at`).")
        lines.append("    3. `llmwiki lint && llmwiki build` — validate and index.")
        lines.append("")
    return "\n".join(lines)
