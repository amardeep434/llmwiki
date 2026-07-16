"""Generate AI agent schema files for multi-agent compatibility.

Creates instruction files so Claude Code, GitHub Copilot, Codex CLI,
Gemini CLI, and Cursor can all discover and use the knowledge base.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

_LLMWIKI_MARKER = "<!-- llmwiki:auto -->"


def generate_claude_md(project_name: str, wiki_path: str, stats: dict, agent_assist: bool = False) -> str:
    """Generate CLAUDE.md content for Claude Code integration."""
    return _generate_agent_guide("CLAUDE.md", project_name, wiki_path, stats, agent_assist)


def generate_agents_md(project_name: str, wiki_path: str, stats: dict, agent_assist: bool = False) -> str:
    """Generate AGENTS.md for Codex CLI, Gemini, Copilot, Cursor, etc."""
    return _generate_agent_guide("AGENTS.md", project_name, wiki_path, stats, agent_assist)


def generate_copilot_instructions(project_name: str, wiki_path: str, stats: dict, agent_assist: bool = False) -> str:
    """Generate .github/copilot-instructions.md content."""
    return _generate_agent_guide("Copilot Instructions", project_name, wiki_path, stats, agent_assist)


def generate_gemini_md(project_name: str, wiki_path: str, stats: dict, agent_assist: bool = False) -> str:
    """Generate GEMINI.md content."""
    return _generate_agent_guide("GEMINI.md", project_name, wiki_path, stats, agent_assist)


def detect_agents(project_root: Path) -> list[str]:
    """Detect which AI agents are in use based on directory markers.

    Always includes ``agents_md``.  Checks for ``.claude/``, ``.github/``,
    ``.gemini/``, and ``.cursor/`` directories.
    """
    detected: list[str] = ["agents_md"]

    if (project_root / ".claude").exists() or (project_root / "CLAUDE.md").exists():
        detected.append("claude_md")
    if (project_root / ".github").exists():
        detected.append("copilot_instructions")
    if (project_root / ".gemini").exists() or (project_root / "GEMINI.md").exists():
        detected.append("gemini_md")
    if (project_root / ".cursor").exists():
        detected.append("cursor_rules")

    return detected


def write_agent_schemas(
    project_root: Path,
    wiki_path: str,
    project_name: str,
    stats: dict,
) -> list[str]:
    """Write agent schema files for all detected agents.

    Returns a list of file paths that were written.
    """
    detected = detect_agents(project_root)
    written: list[str] = []
    
    # Load config to check agent_assist setting
    agent_assist = False
    cfg_candidates = [
        project_root / ".llmwiki" / "llmwiki.json",
        project_root / "llmwiki.json",
    ]
    for cfg_path in cfg_candidates:
        if cfg_path.exists():
            try:
                import json
                config = json.loads(cfg_path.read_text(encoding="utf-8"))
                agent_assist = config.get("agent_assist", False)
                break
            except Exception:
                pass

    generators: dict[str, tuple[Path, Callable[..., str]]] = {
        "claude_md": (project_root / "CLAUDE.md", generate_claude_md),
        "agents_md": (project_root / "AGENTS.md", generate_agents_md),
        "copilot_instructions": (
            project_root / ".github" / "copilot-instructions.md",
            generate_copilot_instructions,
        ),
        "gemini_md": (project_root / "GEMINI.md", generate_gemini_md),
    }

    for agent_key, (filepath, generator) in generators.items():
        if agent_key not in detected:
            continue
        content = generator(project_name, wiki_path, stats, agent_assist)
        _write_or_append(filepath, content)
        written.append(str(filepath))

    return written


def _write_or_append(filepath: Path, llmwiki_section: str) -> None:
    """Write or append the llmwiki section to a file.

    - If the file exists and contains ``_LLMWIKI_MARKER``, replaces
      the marked section (idempotent update).
    - If the file exists without markers, appends the section.
    - If the file does not exist, creates it with just the section.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    marked = f"\n\n{_LLMWIKI_MARKER}\n{llmwiki_section}\n{_LLMWIKI_MARKER}\n"

    if filepath.exists():
        existing = filepath.read_text(encoding="utf-8")
        if _LLMWIKI_MARKER in existing:
            pattern = rf"{re.escape(_LLMWIKI_MARKER)}.*?{re.escape(_LLMWIKI_MARKER)}"
            updated = re.sub(pattern, marked.strip(), existing, flags=re.DOTALL)
            filepath.write_text(updated, encoding="utf-8")
        else:
            filepath.write_text(existing + marked, encoding="utf-8")
    else:
        filepath.write_text(llmwiki_section, encoding="utf-8")


def _generate_agent_guide(title: str, project_name: str, wiki_path: str, stats: dict, agent_assist: bool = False) -> str:
    """Generate a concise landing guide for an AI agent."""
    total_pages = stats.get("total_pages", 0)
    total_edges = stats.get("total_edges", 0)
    total_clusters = stats.get("total_clusters", 0)
    
    # Build the wiki-first section if agent_assist is enabled
    wiki_first_section = ""
    if agent_assist:
        wiki_first_section = """
## Knowledge Base (Wiki-First Mode)

BEFORE reading any source file, search the knowledge base:
  llmwiki search "<your question>" --context

This returns pre-processed summaries with cross-references and method lists.
Only read raw source files if the wiki search doesn't answer your question.

Available search modes:
- llmwiki search "<query>" --context   → full context for answering
- llmwiki search "<query>" --json      → structured JSON results  
- llmwiki search "method:<name>"       → find method/function declarations

"""
    
    return f"""# {title} for {project_name}

{total_pages} pages, {total_edges} cross-references, {total_clusters} clusters

## Wiki Navigation

HTML pages: `{wiki_path}/categories/<category>/<slug>.html`
Structured data: `<slug>.json` sibling next to each HTML page

## Key Files

| File | Purpose |
|------|---------|
| `{wiki_path}/search-index.json` | Client-side search index (title, category, tags, body preview) |
| `{wiki_path}/cross-references.json` | Knowledge graph with nodes, edges, clusters, and tags |
| `{wiki_path}/llmwiki.db` | SQLite FTS5 full-text search database |
| `{wiki_path}/llms.txt` | Page index (llmstxt.org spec) |
| `{wiki_path}/llms-full.txt` | Full content dump (≤5 MB) |
| `{wiki_path}/graph.jsonld` | JSON-LD knowledge graph (Schema.org) |
| `{wiki_path}/sitemap.xml` | Standard XML sitemap |
| `{wiki_path}/build-history.json` | Build audit trail |

## Lookup Order

1. `search-index.json` — quick title/tag/body substring lookups
2. `llmwiki.db` — FTS5 full-text queries: `SELECT … FROM pages_fts WHERE pages_fts MATCH '…'`
3. `cross-references.json` — graph traversal (nodes, edges, clusters, importance)
4. Per-page `.json` — full metadata + backlinks for a single page

## Quick Commands

```bash
llmwiki search "<query>"
sqlite3 {wiki_path}/llmwiki.db "SELECT title, importance_score FROM pages ORDER BY importance_score DESC LIMIT 20"
```
{wiki_first_section}
> AI exports (llms.txt, llms-full.txt, graph.jsonld, sitemap.xml) require `llmwiki export` or `llmwiki all` — they are not generated by `llmwiki build` alone.
"""
