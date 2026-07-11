"""Config file adapter for properties, JSON, YAML, TOML, INI files."""

from __future__ import annotations

from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage, _safe_fence

_CONFIG_EXTS = {".json", ".yaml", ".yml", ".toml", ".properties", ".ini", ".env", ".cfg"}


@register
class ConfigAdapter(BaseAdapter):
    """Documents configuration files."""

    name = "config"
    extensions = list(_CONFIG_EXTS)

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _CONFIG_EXTS

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        lang = path.suffix.lstrip(".").lower()
        if lang in ("yml",):
            lang = "yaml"

        sections = [f"## {path.name}\n\n**Type:** {lang} configuration"]

        # Extract comments as description
        comments = []
        for line in content.splitlines()[:10]:
            if line.startswith("#") or line.startswith("//"):
                comments.append(line.lstrip("#/ ").strip())
        if comments:
            sections.append("## Description\n\n" + " ".join(comments))

        # Full content
        fence = _safe_fence(content)
        sections.append(f"## Contents\n\n{fence}{lang}\n{content}\n{fence}")

        page = WikiPage(
            slug=f"config/{path.stem}".lower(),
            title=path.name,
            category="config",
            source_path=str(path),
            body="\n\n".join(sections),
            language=lang,
            tags=["config", lang],
        )
        page.compute_hash()
        return [page]
