"""Markdown pass-through adapter with frontmatter extraction."""

from __future__ import annotations

import re
from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage


@register
class MarkdownAdapter(BaseAdapter):
    """Pass-through adapter for markdown files."""

    name = "markdown"
    extensions = [".md", ".mdx", ".rst"]

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in {".md", ".mdx", ".rst"}

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        title, body, tags = self._parse(content, path)
        category = config.get("category", "docs")

        page = WikiPage(
            slug=f"{category}/{path.stem}".lower(),
            title=title,
            category=category,
            source_path=str(path),
            body=body,
            tags=tags,
        )
        page.compute_hash()
        return [page]

    def _parse(self, content: str, path: Path) -> tuple[str, str, list[str]]:
        title = path.stem
        body = content
        tags: list[str] = []

        # Extract frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1]
                body = parts[2].strip()
                for line in fm.strip().splitlines():
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip("\"'")
                    elif line.startswith("tags:"):
                        tag_str = line.split(":", 1)[1].strip()
                        tag_str = tag_str.strip("[]")
                        tags = [t.strip() for t in tag_str.split(",") if t.strip()]

        # Fall back to first heading for title
        if title == path.stem:
            heading = re.search(r"^#\s+(.+)", body, re.MULTILINE)
            if heading:
                title = heading.group(1).strip()

        return title, body, tags
