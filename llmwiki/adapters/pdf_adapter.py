"""PDF adapter — converts PDFs to markdown via pymupdf4llm."""

from __future__ import annotations

import re
from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage


def _convert_pdf(path: Path) -> str:
    """Convert PDF to markdown using pymupdf4llm."""
    try:
        import pymupdf4llm
        return pymupdf4llm.to_markdown(str(path))
    except ImportError:
        return f"*PDF conversion requires pymupdf4llm. Install with: `pip install pymupdf4llm`*\n\nFile: {path.name}"
    except Exception as e:
        return f"*Error converting PDF: {e}*\n\nFile: {path.name}"


@register
class PDFAdapter(BaseAdapter):
    """Converts PDF files to markdown wiki pages."""

    name = "pdf"
    extensions = [".pdf"]

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        md_content = _convert_pdf(path)
        title = path.stem.replace("-", " ").replace("_", " ")
        label = config.get("label", "docs")
        slug = self._make_slug(path.name, label)

        page = WikiPage(
            slug=slug,
            title=title,
            category=label,
            source_path=str(path),
            body=md_content,
            language="",
            tags=["pdf"],
        )
        page.compute_hash()
        return [page]

    def _make_slug(self, filename: str, label: str) -> str:
        stem = Path(filename).stem
        safe = re.sub(r"[^a-zA-Z0-9_-]", "-", stem).strip("-")
        safe = re.sub(r"-+", "-", safe).lower()
        label_safe = re.sub(r"[^a-zA-Z0-9_-]", "-", label).lower()
        return f"{label_safe}/{safe}"
