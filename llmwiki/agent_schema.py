"""Generate AI agent schema files for multi-agent compatibility.

Creates instruction files so Claude Code, GitHub Copilot, Codex CLI,
Gemini CLI, and Cursor can all discover and use the knowledge base.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

_LLMWIKI_MARKER = "<!-- llmwiki:auto -->"


def generate_claude_md(project_name: str, wiki_path: str, stats: dict) -> str:
    """Generate CLAUDE.md content for Claude Code integration."""
    total_pages = stats.get("total_pages", 0)
    total_edges = stats.get("total_edges", 0)
    total_clusters = stats.get("total_clusters", 0)

    return f"""# llmwiki Knowledge Base for {project_name}

## Quick Reference

| Resource | Command / Path |
|----------|---------------|
| CLI search | `llmwiki search "<query>"` |
| SQLite DB | `sqlite3 {wiki_path}/llmwiki.db` |
| Full dump | `cat {wiki_path}/llms-full.txt` |
| Graph | `{wiki_path}/cross-references.json` |

## Stats

- **{total_pages}** pages, **{total_edges}** cross-references, **{total_clusters}** clusters

## Slash Commands

| Command | Action |
|---------|--------|
| `/wiki-query <q>` | `llmwiki search "<q>"` |
| `/wiki-build` | `llmwiki build` |
| `/wiki-lint` | `llmwiki lint` |

## SQL Query Examples

```bash
# Full-text search
sqlite3 {wiki_path}/llmwiki.db "SELECT title, snippet(pages_fts,1,'>>>','<<<','...',50) FROM pages_fts WHERE pages_fts MATCH 'workflow' ORDER BY rank LIMIT 10"

# Most important pages
sqlite3 {wiki_path}/llmwiki.db "SELECT title, importance_score FROM pages ORDER BY importance_score DESC LIMIT 20"

# Cross-references for a file
sqlite3 {wiki_path}/llmwiki.db "SELECT p.title, e.edge_type FROM edges e JOIN pages p ON e.from_id = p.id WHERE e.to_id LIKE '%MyClass%'"
```

## AI-Consumable Files

| File | Format | Use |
|------|--------|-----|
| `llmwiki.db` | SQLite + FTS5 | Structured queries |
| `llms.txt` | Plain text | Quick overview |
| `llms-full.txt` | Plain text | Full context dump |
| `cross-references.json` | JSON | Code relationships |
"""


def generate_agents_md(project_name: str, wiki_path: str, stats: dict) -> str:
    """Generate AGENTS.md for Codex CLI, Gemini, Copilot, Cursor, etc."""
    total_pages = stats.get("total_pages", 0)
    total_edges = stats.get("total_edges", 0)
    total_clusters = stats.get("total_clusters", 0)

    return f"""# llmwiki Knowledge Base for {project_name}

This project has a structured knowledge base with **{total_pages}** pages,
**{total_edges}** cross-references, and **{total_clusters}** topic clusters.

## How to Query

```bash
# CLI search
llmwiki search "<your question>"

# Direct SQL
sqlite3 {wiki_path}/llmwiki.db "SELECT title FROM pages WHERE title LIKE '%query%'"
```

## Key Files

- `{wiki_path}/llmwiki.db` — SQLite database with FTS5 full-text search
- `{wiki_path}/llms.txt` — Short project overview
- `{wiki_path}/llms-full.txt` — Full content for LLM context windows
- `{wiki_path}/cross-references.json` — Code artifact relationships
"""


def generate_copilot_instructions(project_name: str, wiki_path: str, stats: dict) -> str:
    """Generate .github/copilot-instructions.md content."""
    total_pages = stats.get("total_pages", 0)

    return f"""# Copilot Instructions for {project_name}

This project uses **llmwiki** to maintain a searchable knowledge base
with {total_pages} pages of project documentation and code analysis.

## Searching the Knowledge Base

```bash
llmwiki search "<query>"
```

## Key Paths

- Wiki database: `{wiki_path}/llmwiki.db`
- Overview: `{wiki_path}/llms.txt`
- Full dump: `{wiki_path}/llms-full.txt`
"""


def generate_gemini_md(project_name: str, wiki_path: str, stats: dict) -> str:
    """Generate GEMINI.md content."""
    total_pages = stats.get("total_pages", 0)

    return f"""# llmwiki Knowledge Base for {project_name}

Use `llmwiki search "<query>"` to search {total_pages} indexed pages.

Database: `{wiki_path}/llmwiki.db`
Overview: `{wiki_path}/llms.txt`
Full context: `{wiki_path}/llms-full.txt`
"""


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
        content = generator(project_name, wiki_path, stats)
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
