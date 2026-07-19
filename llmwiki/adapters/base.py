"""Base adapter interface and WikiPage data model."""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


def _sanitize_slug_segment(segment: str) -> str:
    """Lowercase a single slug segment, mapping non-alphanumerics to ``-``."""
    segment = re.sub(r"[^a-zA-Z0-9_-]", "-", segment)
    segment = re.sub(r"-+", "-", segment)
    return segment.strip("-").lower()


def make_slug(path: Path, source_root: Path | None, category: str) -> str:
    """Build a page slug/id that is unique within a single source tree.

    The slug is ``<category>/<relative-path-without-extension>``. Deriving the
    trailing segments from the path *relative to the source root* means two
    files sharing a stem in different directories get distinct ids — the fix
    for the silent-overwrite bug where ``a/utils.py`` and ``b/utils.py`` both
    collapsed to ``<category>/utils``. Files sitting directly at the source
    root collapse to ``<category>/<stem>``, matching historical ids so flat
    projects (and the tests that pin their ids) are unaffected.

    ``source_root`` is ``None`` when an adapter is driven via a direct
    ``extract()`` call (unit tests, ad-hoc use); in that case fall back to the
    stem-only form, preserving pre-existing behaviour.
    """
    if source_root is not None:
        try:
            rel = Path(path).relative_to(source_root)
        except ValueError:
            rel = Path(Path(path).name)
        segments = [*rel.parts[:-1], rel.stem]
    else:
        segments = [Path(path).stem]
    rel_segments = [_sanitize_slug_segment(s) for s in segments if s]
    cat_segments = [
        _sanitize_slug_segment(s) for s in str(category).split("/") if s
    ]
    # Categories are often derived from the same directory segments (e.g. the
    # XML adapter maps config/Application/Core → category Application/Core).
    # Without de-duplication the id doubles up as
    # application/core/config/application/core/<file> — unreadable and painful
    # to pass to `llmwiki get` (found in Phase V on a real SailPoint repo).
    # Drop the first occurrence of the category run from the relative dirs.
    rel_dirs, rel_leaf = rel_segments[:-1], rel_segments[-1:]
    if cat_segments and len(cat_segments) <= len(rel_dirs):
        for i in range(len(rel_dirs) - len(cat_segments) + 1):
            if rel_dirs[i:i + len(cat_segments)] == cat_segments:
                rel_dirs = rel_dirs[:i] + rel_dirs[i + len(cat_segments):]
                break
    rel_slug = "/".join(rel_dirs + rel_leaf)
    cat_slug = "/".join(cat_segments)
    slug = f"{cat_slug}/{rel_slug}" if cat_slug else rel_slug
    return slug.strip("-/")


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


def _safe_fence(content: str) -> str:
    """Return a backtick fence string longer than any run in content."""
    max_run = 0
    current = 0
    for ch in content:
        if ch == '`':
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    return '`' * max(3, max_run + 1)


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
                if not self._is_excluded(p, root, exclude):
                    results.append(p)
        return sorted(results)

    @staticmethod
    def _is_excluded(path: Path, root: Path, exclude: list[str]) -> bool:
        """Check if path should be excluded.

        Glob patterns (containing * or ?) match against the filename.
        Plain names match against individual path components relative to root.
        """
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        parts = set(rel.parts)

        for pattern in exclude:
            if "*" in pattern or "?" in pattern:
                if path.match(pattern):
                    return True
            else:
                if pattern in parts:
                    return True
        return False
