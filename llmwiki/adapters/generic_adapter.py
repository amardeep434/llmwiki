"""Generic fallback adapter for any text file."""

from __future__ import annotations

import re
from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage


@register
class GenericAdapter(BaseAdapter):
    """Fallback adapter that wraps any text file in a code block."""

    name = "generic"
    extensions = []  # Handles anything not claimed by other adapters

    def can_handle(self, path: Path) -> bool:
        # Accept any text file
        try:
            path.read_text(encoding="utf-8", errors="strict")
            return True
        except (UnicodeDecodeError, OSError):
            return False

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        lang = path.suffix.lstrip(".").lower() or "text"
        body = f"## {path.name}\n\n```{lang}\n{content}\n```\n"

        page = WikiPage(
            slug=f"misc/{path.stem}".lower(),
            title=path.name,
            category="misc",
            source_path=str(path),
            body=body,
            language=lang,
        )
        page.compute_hash()
        return [page]

    def discover(self, root: Path, exclude: list[str] | None = None) -> list[Path]:
        """Generic adapter doesn't auto-discover — only used as fallback."""
        return []
