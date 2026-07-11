"""PDF adapter — converts PDFs to structured markdown preserving headings, tables, lists, and images."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import NamedTuple

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage


# ---------------------------------------------------------------------------
# Structured PDF-to-Markdown conversion
# ---------------------------------------------------------------------------

class _Span(NamedTuple):
    """A text span with font metadata."""
    text: str
    size: float
    flags: int  # bit 0=superscript, 1=italic, 2=serifed, 3=monospace, 4=bold
    font: str
    bbox: tuple  # (x0, y0, x1, y1)

    @property
    def is_bold(self) -> bool:
        return bool(self.flags & 16)

    @property
    def is_monospace(self) -> bool:
        if self.flags & 8:
            return True
        mono_names = ("courier", "consolas", "mono", "code", "menlo", "source code")
        return any(m in self.font.lower() for m in mono_names)


_BULLET_GLYPHS = frozenset(["l", "\uf0b7", "•", "·", "‐", "\u2022", "\u00b7"])
_COPYRIGHT_PATTERNS = re.compile(
    r"(©|copyright|\bconfidential\b|all rights reserved|proprietary|"
    r"sailpoint technologies|this document)", re.IGNORECASE
)


def _is_copyright_page(text: str) -> bool:
    """Heuristic: page is a copyright/disclaimer page if relatively short and matches patterns."""
    if len(text) > 5000:
        return False
    matches = len(_COPYRIGHT_PATTERNS.findall(text))
    return matches >= 3


def _detect_headers_footers(pages_spans: list[list[_Span]], page_height: float) -> set[str]:
    """Find text that recurs at top/bottom of pages — likely headers/footers."""
    top_texts: Counter[str] = Counter()
    bottom_texts: Counter[str] = Counter()
    top_threshold = 50.0
    bottom_threshold = page_height - 50.0

    for spans in pages_spans:
        page_top = set()
        page_bottom = set()
        for sp in spans:
            clean = sp.text.strip()
            if not clean or len(clean) < 2:
                continue
            if sp.bbox[1] < top_threshold:
                page_top.add(clean)
            elif sp.bbox[1] > bottom_threshold:
                page_bottom.add(clean)
        for t in page_top:
            top_texts[t] += 1
        for t in page_bottom:
            bottom_texts[t] += 1

    num_pages = len(pages_spans)
    threshold = max(2, num_pages * 0.15)
    recurring = set()
    for t, count in top_texts.items():
        if count >= threshold:
            recurring.add(t)
    for t, count in bottom_texts.items():
        if count >= threshold:
            recurring.add(t)
    # Also strip pure page numbers
    recurring.add("")
    return recurring


def _determine_body_size(all_spans: list[_Span]) -> float:
    """Most common font size = body text."""
    sizes: Counter[float] = Counter()
    for sp in all_spans:
        if sp.text.strip():
            sizes[round(sp.size, 1)] += len(sp.text.strip())
    if not sizes:
        return 10.0
    return sizes.most_common(1)[0][0]


def _heading_level(size: float, body_size: float, size_ranks: list[float]) -> int:
    """Map font size to heading level 1-4 based on rank among detected heading sizes."""
    if size in size_ranks:
        idx = size_ranks.index(size)
        return min(idx + 1, 4)
    return 4


def _is_bullet_marker(span: _Span, body_size: float) -> bool:
    """Detect bullet marker spans."""
    text = span.text.strip()
    if not text:
        return False
    # Wingdings font bullets (glyph 'l' = bullet in Wingdings)
    if "wingdings" in span.font.lower() and len(text) == 1:
        return True
    # Small glyph bullets
    if span.size < body_size * 0.8 and text in _BULLET_GLYPHS:
        return True
    # Direct bullet chars at any size
    if text in ("•", "·", "‣", "▪", "▸") and len(text) == 1:
        return True
    # Dash bullets
    if text in ("-", "–", "—") and len(text) == 1:
        return True
    return False


def _is_numbered_list(text: str) -> tuple[bool, str]:
    """Check if text starts with a numbered list pattern. Returns (is_numbered, rest_text)."""
    m = re.match(r"^(\d{1,3})\.\s+(.+)", text)
    if m:
        return True, text
    return False, text


def _clean_cell(text: str) -> str:
    """Clean table cell content for markdown."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\n", " ").replace("|", "\\|")).strip()


def _convert_pdf_structured(path: Path, output_dir: Path | None = None) -> str:
    """Convert PDF to well-formatted markdown with structure preservation.

    Args:
        path: Path to the PDF file.
        output_dir: Directory for extracted images. If None, images are skipped.

    Returns:
        Markdown string with headings, tables, lists, code blocks, and images.
    """
    import pymupdf

    doc = pymupdf.open(str(path))
    if doc.page_count == 0:
        doc.close()
        return f"*Empty PDF: {path.name}*"

    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", path.stem).strip("-").lower()
    slug = re.sub(r"-+", "-", slug)

    # --- First pass: collect all spans and detect structure ---
    pages_spans: list[list[_Span]] = []
    all_spans: list[_Span] = []
    page_height = doc[0].rect.height if doc.page_count > 0 else 800.0

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        page_sp: list[_Span] = []
        for block in blocks:
            if block.get("type") != 0:  # text blocks only
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    sp = _Span(
                        text=span.get("text", ""),
                        size=round(span.get("size", 10.0), 1),
                        flags=span.get("flags", 0),
                        font=span.get("font", ""),
                        bbox=tuple(span.get("bbox", (0, 0, 0, 0))),
                    )
                    page_sp.append(sp)
                    all_spans.append(sp)
        pages_spans.append(page_sp)

    body_size = _determine_body_size(all_spans)
    recurring = _detect_headers_footers(pages_spans, page_height)

    # Determine heading sizes: sizes > body*1.3 AND bold, ranked descending
    heading_sizes: Counter[float] = Counter()
    for sp in all_spans:
        if sp.text.strip() and sp.size > body_size * 1.3 and sp.is_bold:
            heading_sizes[round(sp.size, 1)] += 1

    size_ranks = sorted(heading_sizes.keys(), reverse=True)[:4]

    # --- Second pass: build markdown page by page ---
    md_parts: list[str] = []
    image_counter = 0

    # Detect copyright/TOC pages at start (skip first few pages that are disclaimers)
    skip_pages_set: set[int] = set()
    for i in range(min(4, doc.page_count)):
        page_text = doc[i].get_text("text")
        if _is_copyright_page(page_text):
            skip_pages_set.add(i)
        # Also skip TOC pages (short lines that are mostly page refs)
        lines = [l.strip() for l in page_text.split("\n") if l.strip()]
        if lines and lines[0].lower().startswith("contents"):
            skip_pages_set.add(i)
    # Skip title page if it's very short (just title + version)
    if doc.page_count > 3:
        page0_text = doc[0].get_text("text")
        if len(page0_text) < 300:
            skip_pages_set.add(0)

    for page_idx in range(doc.page_count):
        if page_idx in skip_pages_set:
            continue

        page = doc[page_idx]

        # --- Extract tables first to know which regions to skip ---
        table_rects: list[tuple] = []
        tables_md: list[tuple[float, str]] = []  # (y_position, markdown)
        try:
            tables = page.find_tables()
            for table in tables:
                bbox = table.bbox
                table_rects.append(bbox)
                rows = table.extract()
                if not rows or len(rows) < 1:
                    continue
                # Build markdown table
                headers = table.header.names if hasattr(table, 'header') and table.header else None
                if headers:
                    headers = [_clean_cell(h) if h else f"Col{i+1}" for i, h in enumerate(headers)]
                    data_rows = rows[1:] if len(rows) > 1 else []
                else:
                    headers = [_clean_cell(c) if c else f"Col{i+1}" for i, c in enumerate(rows[0])]
                    data_rows = rows[1:]

                col_count = len(headers)
                tbl_lines = []
                tbl_lines.append("| " + " | ".join(headers) + " |")
                tbl_lines.append("|" + "|".join(["---"] * col_count) + "|")
                for row in data_rows:
                    cells = [_clean_cell(c) if c else "" for c in row[:col_count]]
                    # Pad if fewer cells
                    while len(cells) < col_count:
                        cells.append("")
                    tbl_lines.append("| " + " | ".join(cells) + " |")
                tables_md.append((bbox[1], "\n".join(tbl_lines)))
        except Exception:
            pass

        # --- Extract images ---
        images_md: list[tuple[float, str]] = []
        if output_dir:
            try:
                for img_info in page.get_images(full=True):
                    xref = img_info[0]
                    width = img_info[2]
                    height = img_info[3]
                    if width < 50 or height < 50:
                        continue
                    try:
                        img_data = doc.extract_image(xref)
                        if not img_data or not img_data.get("image"):
                            continue
                        ext = img_data.get("ext", "png")
                        image_counter += 1
                        assets_dir = output_dir / "assets"
                        assets_dir.mkdir(parents=True, exist_ok=True)
                        img_name = f"{slug}_img{image_counter}.{ext}"
                        img_path = assets_dir / img_name
                        img_path.write_bytes(img_data["image"])
                        images_md.append((0.0, f"![](assets/{img_name})"))
                    except Exception:
                        continue
            except Exception:
                pass

        # --- Process text blocks ---
        blocks = page.get_text("dict")["blocks"]
        page_lines: list[tuple[float, str]] = []  # (y_pos, markdown_line)

        def _in_table_rect(bbox: tuple) -> bool:
            for tr in table_rects:
                if (bbox[1] >= tr[1] - 2 and bbox[3] <= tr[3] + 2
                        and bbox[0] >= tr[0] - 2 and bbox[2] <= tr[2] + 2):
                    return True
            return False

        def _block_is_bullet(block_lines: list) -> tuple[bool, str]:
            """Check if a block is a bullet item (glyph line + text line)."""
            if len(block_lines) < 2:
                return False, ""
            first_line_spans = block_lines[0].get("spans", [])
            if len(first_line_spans) == 1:
                sp = first_line_spans[0]
                if _is_bullet_marker(
                    _Span(sp["text"], round(sp["size"], 1), sp["flags"], sp["font"],
                          tuple(sp.get("bbox", (0,0,0,0)))),
                    body_size
                ):
                    # Collect text from remaining lines in this block
                    text_parts = []
                    for ln in block_lines[1:]:
                        for s in ln.get("spans", []):
                            text_parts.append(s.get("text", ""))
                    text = "".join(text_parts).strip()
                    if text:
                        return True, text
            return False, ""

        # Process blocks
        for block in blocks:
            if block.get("type") != 0:
                continue

            block_bbox = block.get("bbox", (0, 0, 0, 0))
            if _in_table_rect(block_bbox):
                continue

            block_lines = block.get("lines", [])
            if not block_lines:
                continue

            # Check if entire block is a bullet item
            is_bullet, bullet_text = _block_is_bullet(block_lines)
            if is_bullet:
                y_pos = block_bbox[1]
                # Skip recurring headers/footers
                if bullet_text not in recurring:
                    page_lines.append((y_pos, f"- {bullet_text}"))
                continue

            # Process individual lines in the block
            for line in block_lines:
                line_spans = []
                for span in line.get("spans", []):
                    sp = _Span(
                        text=span.get("text", ""),
                        size=round(span.get("size", 10.0), 1),
                        flags=span.get("flags", 0),
                        font=span.get("font", ""),
                        bbox=tuple(span.get("bbox", (0, 0, 0, 0))),
                    )
                    line_spans.append(sp)

                if not line_spans:
                    continue

                # Skip if inside table region
                line_bbox = line.get("bbox", (0, 0, 0, 0))
                if _in_table_rect(line_bbox):
                    continue

                # Skip recurring headers/footers
                full_line_text = "".join(s.text for s in line_spans).strip()
                if full_line_text in recurring:
                    continue
                # Skip page numbers
                if re.match(r"^\d{1,4}$", full_line_text):
                    continue

                if not full_line_text:
                    continue

                y_pos = line_bbox[1] if line_bbox else 0

                # --- Classify this line ---

                # Check for bullet marker with text on same line
                first_sp = line_spans[0]
                if _is_bullet_marker(first_sp, body_size):
                    rest = "".join(s.text for s in line_spans[1:]).strip()
                    if rest:
                        page_lines.append((y_pos, f"- {rest}"))
                    continue

                # Check for dash/bullet at start of text
                if full_line_text.startswith(("- ", "– ", "— ", "• ", "· ")):
                    content = full_line_text[2:].strip()
                    page_lines.append((y_pos, f"- {content}"))
                    continue

                # Check for numbered list
                is_num, _ = _is_numbered_list(full_line_text)
                if is_num:
                    page_lines.append((y_pos, full_line_text))
                    continue

                # Check for heading
                dominant_span = max(line_spans, key=lambda s: len(s.text))
                if (dominant_span.size > body_size * 1.3
                        and dominant_span.is_bold
                        and len(full_line_text) < 200):
                    level = _heading_level(round(dominant_span.size, 1), body_size, size_ranks)
                    page_lines.append((y_pos, f"\n{'#' * level} {full_line_text}\n"))
                    continue

                # Check for code (monospace) — skip very short spans (likely bullet glyphs)
                mono_chars = sum(len(s.text) for s in line_spans if s.is_monospace)
                total_chars = sum(len(s.text) for s in line_spans)
                stripped_text = full_line_text.strip()
                if (total_chars > 3 and mono_chars / total_chars > 0.7
                        and len(stripped_text) > 3):
                    page_lines.append((y_pos, f"```code\n{full_line_text}"))
                    continue
                # Single char monospace = sub-bullet marker (o, n, ●, etc.)
                if total_chars <= 3 and mono_chars > 0 and stripped_text in (
                    "o", "n", "l", "·", "●", "•", "▪", "■", "►", "‣", "-"
                ):
                    page_lines.append((y_pos, "  -"))
                    continue

                # Regular body text — apply inline formatting
                formatted = ""
                for sp in line_spans:
                    t = sp.text
                    if not t:
                        continue
                    if sp.is_bold and sp.size <= body_size * 1.3:
                        formatted += f"**{t}**"
                    else:
                        formatted += t
                # Collapse doubled bold markers
                formatted = re.sub(r"\*\*\*\*", "", formatted)
                page_lines.append((y_pos, formatted))

        # --- Merge lines: join paragraphs, group code blocks ---
        merged: list[str] = []
        i = 0
        while i < len(page_lines):
            _, line = page_lines[i]

            # Group consecutive code lines
            if line.startswith("```code\n"):
                code_lines = [line[len("```code\n"):]]
                i += 1
                while i < len(page_lines) and page_lines[i][1].startswith("```code\n"):
                    code_lines.append(page_lines[i][1][len("```code\n"):])
                    i += 1
                merged.append(f"```\n" + "\n".join(code_lines) + "\n```")
                continue

            # Headings stay as-is
            if line.strip().startswith("#"):
                merged.append(line)
                i += 1
                continue

            # List items stay as-is
            if line.startswith("- ") or re.match(r"^\d+\.\s", line):
                merged.append(line)
                i += 1
                continue

            # Paragraph: join consecutive body text lines
            para_parts = [line]
            i += 1
            while i < len(page_lines):
                _, next_line = page_lines[i]
                # Stop paragraph at headings, lists, code
                if (next_line.strip().startswith("#")
                        or next_line.startswith("- ")
                        or next_line.startswith("```code\n")
                        or re.match(r"^\d+\.\s", next_line)):
                    break
                # Check vertical distance — if gap > 1.5x body line height, new paragraph
                cur_y = page_lines[i - 1][0]
                next_y = page_lines[i][0]
                line_height = body_size * 1.4
                if next_y - cur_y > line_height * 1.8:
                    break
                para_parts.append(next_line)
                i += 1
            merged.append(" ".join(para_parts))

        # Insert tables at approximate positions
        for t_y, t_md in sorted(tables_md, key=lambda x: x[0]):
            # Find insertion point
            inserted = False
            for idx, m in enumerate(merged):
                if m.strip().startswith("#"):
                    continue
                inserted = True
                merged.insert(idx + 1, f"\n{t_md}\n")
                break
            if not inserted:
                merged.append(f"\n{t_md}\n")

        # Insert images
        for _, img_md in images_md:
            merged.append(f"\n{img_md}\n")

        if merged:
            md_parts.append("\n\n".join(merged))

    doc.close()

    # --- Post-processing ---
    result = "\n\n".join(md_parts)

    # Ensure headings have blank lines
    result = re.sub(r"([^\n])\n(#{1,6} )", r"\1\n\n\2", result)
    result = re.sub(r"(#{1,6} .+)\n([^\n])", r"\1\n\n\2", result)

    # Strip excessive blank lines
    result = re.sub(r"\n{4,}", "\n\n\n", result)

    # Clean up stray bold markers
    result = re.sub(r"\*\*\s*\*\*", "", result)

    return result.strip()


def _convert_pdf(path: Path) -> str:
    """Convert PDF to well-formatted markdown (legacy interface)."""
    return _convert_pdf_structured(path, output_dir=None)


@register
class PDFAdapter(BaseAdapter):
    """Converts PDF files to markdown wiki pages."""

    name = "pdf"
    extensions = [".pdf"]

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        images_dir = Path(config.get("images_dir", "raw/assets")) if config.get("images_dir") else None
        md_content = _convert_pdf_structured(path, images_dir)
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
