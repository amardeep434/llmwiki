"""PDF adapter — converts PDFs to markdown via pymupdf4llm with pymupdf fallback."""

from __future__ import annotations

import re
from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage


def _convert_pdf(path: Path) -> str:
    """Convert PDF to markdown. Tries pymupdf4llm first, falls back to pymupdf raw extraction."""
    # Attempt 1: pymupdf4llm (best quality if it works)
    try:
        import pymupdf4llm
        result = pymupdf4llm.to_markdown(str(path))
        if result and len(result.strip()) > 100:
            return result
    except Exception:
        pass

    # Attempt 2: Raw pymupdf text extraction with markdown formatting
    try:
        import pymupdf
        doc = pymupdf.open(str(path))
        sections = []
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                if i == 0:
                    lines = text.strip().splitlines()
                    if lines:
                        sections.append(f"# {lines[0].strip()}\n")
                        sections.append("\n".join(lines[1:]))
                else:
                    sections.append(f"\n---\n*Page {i+1}*\n\n{text.strip()}")
        doc.close()
        return "\n\n".join(sections) if sections else f"*Empty PDF: {path.name}*"
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
