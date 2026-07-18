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


def generate_copilot_agent(project_name: str, wiki_path: str, stats: dict, agent_assist: bool = False) -> str:
    """Generate .github/agents/llmwiki.agent.md content with YAML frontmatter."""
    total_pages = stats.get("total_pages", 0)
    total_edges = stats.get("total_edges", 0)

    body = f"""---
description: >-
  Search the {project_name} LLMWiki knowledge base ({total_pages} pages, {total_edges} cross-references).
  Use this agent when you need project-specific knowledge, architecture context, or API details
  before reading raw source files.
tools:
  - "llmwiki_search"
---

# LLMWiki Knowledge Base Agent for {project_name}

You are a knowledge base assistant. Use the `llmwiki_search` tool to answer questions
about {project_name} before reading raw source files.

## How to Search

Call the `llmwiki_search` tool with relevant keywords, method names, or concepts.
The tool returns page titles, categories, and snippets from the wiki.

## Lookup Order

1. Search the wiki first with `llmwiki_search`
2. Only read raw source files if the wiki doesn't answer the question
3. Use cross-references in search results to find related topics

## Quick CLI Commands

```bash
llmwiki search "<query>"
llmwiki search "<query>" --context
llmwiki search "method:<name>"
```
"""
    return body


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
        detected.append("copilot_agent")
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
        "copilot_agent": (
            project_root / ".github" / "agents" / "llmwiki.agent.md",
            generate_copilot_agent,
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
            match = re.search(pattern, existing, flags=re.DOTALL)
            if match:
                updated = existing[:match.start()] + marked.strip() + existing[match.end():]
            else:
                updated = existing + marked
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

    # Convert absolute wiki_path to a relative form for display
    # (absolute Windows paths cause models to shell out with hardcoded paths)
    wiki_rel = wiki_path.replace("\\", "/")
    # Try to make it relative by stripping common prefixes
    for prefix in (".llmwiki/site", ".llmwiki\\site"):
        if prefix in wiki_rel:
            wiki_rel = ".llmwiki/site"
            break

    # Build the wiki-first section if agent_assist is enabled
    wiki_first_section = ""
    if agent_assist:
        wiki_first_section = """
## Knowledge Base (Wiki-First Mode)

BEFORE reading any source file, search the knowledge base using the
`wiki_search` MCP tool (preferred) or CLI:
  llmwiki search "<your question>" --context

This returns pre-processed summaries with cross-references and method lists.
Only read raw source files if the wiki search doesn't answer your question.

"""

    return f"""# {title} for {project_name}

{total_pages} pages, {total_edges} cross-references, {total_clusters} clusters

## How to Search the Wiki

Try each method in order. Use the first one that works:

### 1. MCP tool (preferred in IDE — VS Code, Cursor, JetBrains)
Call the `wiki_search` or `llmwiki_search` MCP tool with your query.
Returns structured results directly. No file parsing needed.

### 2. CLI command (works in any terminal — Copilot CLI, IDE terminal, shell)
Run in terminal:
```bash
llmwiki search "<query>" --agent
llmwiki search "<method-name>" --method
```
Always use `--agent` flag for token-efficient output (IDs + method signatures).
The `--method` flag searches specifically for method/function declarations.
Do NOT use sqlite3 — it may not be installed. Use `llmwiki` commands instead.

To get full page content after finding a result:
```bash
llmwiki get "<page-id>"
```
Returns structured content with method signatures extracted — no source file reading needed.

For advanced DB queries:
```bash
llmwiki query "SELECT title, category FROM pages_fts WHERE pages_fts MATCH '<term>'" --json
```
Read-only. Do NOT use sqlite3 directly — use `llmwiki query` instead.

### 3. Read search-index.json (last resort — no tools available)
Read `{wiki_rel}/search-index.json` and search the `.entries[]` array.
Each entry has: `id`, `title`, `category`, `tags`, `body` (first 1200 chars).

## Key Files (reference only)

| File | Purpose |
|------|---------|
| `{wiki_rel}/search-index.json` | Search index — entries in `.entries[]` array |
| `{wiki_rel}/cross-references.json` | Knowledge graph (nodes, edges, clusters) |
| `{wiki_rel}/llmwiki.db` | SQLite FTS5 database (use `llmwiki query`, not sqlite3) |
{wiki_first_section}
> llms.txt, llms-full.txt, graph.jsonld, sitemap.xml require `llmwiki export` — not generated by `llmwiki build` alone.
"""
