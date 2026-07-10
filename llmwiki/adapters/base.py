"""Base adapter interface and WikiPage data model."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WikiPage:
    """Standardized page output from any adapter."""

    slug: str
    title: str
    category: str
    source_path: str
    body: str
    language: str = ""
    tags: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    content_hash: str = ""

    def compute_hash(self) -> str:
        """Compute SHA-256 of the page body for change detection."""
        self.content_hash = hashlib.sha256(self.body.encode("utf-8")).hexdigest()[:16]
        return self.content_hash

    @staticmethod
    def _yaml_escape(value: str) -> str:
        """Escape a string for safe YAML double-quoted output."""
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")

    def to_frontmatter(self) -> str:
        """Render YAML frontmatter string."""
        esc = self._yaml_escape
        lines = [
            "---",
            f'title: "{esc(self.title)}"',
            f'slug: "{esc(self.slug)}"',
            f'category: "{esc(self.category)}"',
            f'source_path: "{esc(self.source_path)}"',
            f'language: "{esc(self.language)}"',
            f'content_hash: "{esc(self.content_hash)}"',
            f"tags: [{', '.join(self.tags)}]",
            f"references: [{', '.join(self.references)}]",
            "---",
        ]
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Render full markdown file: frontmatter + body."""
        if not self.content_hash:
            self.compute_hash()
        return self.to_frontmatter() + "\n\n" + self.body


class BaseAdapter(ABC):
    """All adapters implement this interface."""

    name: str = ""
    extensions: list[str] = []

    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Return True if this adapter can process the given file."""
        ...

    @abstractmethod
    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        """Extract WikiPage objects from the given file."""
        ...

    def discover(self, root: Path, exclude: list[str] | None = None) -> list[Path]:
        """Find all files this adapter should process under root."""
        exclude = exclude or []
        results = []
        for ext in self.extensions:
            for p in root.rglob(f"*{ext}"):
                if not any(ex in str(p) for ex in exclude):
                    results.append(p)
        return sorted(results)
