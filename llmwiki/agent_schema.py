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
    create: bool = False,
) -> list[str]:
    """Write agent schema files for all detected agents.

    With ``create=False`` (the default, used by `llmwiki build`), only
    files that already contain the llmwiki marker are refreshed — build
    never silently creates or appends to a project's instruction files.
    ``create=True`` (used by `llmwiki setup-agent`) creates/appends too.

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
        if not create and not _has_marker(filepath):
            continue  # build refreshes existing sections only
        content = generator(project_name, wiki_path, stats, agent_assist)
        _write_or_append(filepath, content)
        written.append(str(filepath))

    return written


def _has_marker(filepath: Path) -> bool:
    if not filepath.exists():
        return False
    try:
        return _LLMWIKI_MARKER in filepath.read_text(encoding="utf-8")
    except OSError:
        return False


def _write_or_append(filepath: Path, llmwiki_section: str) -> None:
    """Write or append the llmwiki section to a file.

    The section is ALWAYS wrapped in ``_LLMWIKI_MARKER`` comments —
    including on first creation — so every later run replaces the marked
    section in place instead of appending duplicates.
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
        filepath.write_text(marked.lstrip("\n"), encoding="utf-8")


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

    # Wiki-first line only when the user explicitly enabled agent_assist
    wiki_first_line = ""
    if agent_assist:
        wiki_first_line = (
            "Search the wiki BEFORE reading source files; "
            "read raw files only when the wiki doesn't answer.\n"
        )

    # Deliberately compact: this block lands in every conversation's
    # context, so it must cost almost nothing.
    return f"""## {project_name or "Project"} knowledge base (llmwiki)

{total_pages} pages, {total_edges} cross-refs indexed from this repo's code + docs (PDFs included).
{wiki_first_line}```bash
llmwiki search "<query>" --agent      # find pages (use: python -m llmwiki if not on PATH)
llmwiki get "<page-id>"               # full page content, source-stripped
llmwiki search "method:<name>" --agent  # locate a function/method
llmwiki status                        # check index freshness after editing files
```
Heed any "index is STALE" warning in output — then prefer raw files or run `llmwiki all`.
Save expensive derivations (cross-file logic, architecture) as `curated/notes/<slug>.md` per SCHEMA.md (cite `sources:`), then `llmwiki build` — curated pages outrank extracted ones.
`llmwiki synthesize` lists pages that still need curated coverage.
No CLI available? Read `{wiki_rel}/llms.txt` (index) or `{wiki_rel}/search-index.json` (entries[].body, truncated).
MCP (optional, if configured): tools `llmwiki_search`, `llmwiki_get_page`, `llmwiki_find_method`."""
