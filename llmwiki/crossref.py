"""Cross-reference extraction from wiki page content.

Only generic patterns (wiki links, imports, class references) are built
in. Domain-specific reference patterns — product APIs, connector names,
framework idioms — belong in config so one project's vocabulary never
pollutes another project's graph:

    "cross_references": {
        "custom_patterns": ["\\\\b(sailpoint\\\\.\\\\w+\\\\.\\\\w+)\\\\b"]
    }

Each custom pattern is a regex whose first group (or whole match) is
added as a reference.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Target must contain at least one word character: PDFs occasionally carry
# literal [[()]]-style bracket runs that are not links (Phase V finding).
_WIKILINK_RE = re.compile(r"\[\[([^\]|]*\w[^\]|]*)(?:\|[^\]]+)?\]\]")
_JAVA_IMPORT_RE = re.compile(r"import\s+([\w.]+);")
_CLASS_REF_RE = re.compile(r"(?:new\s+|extends\s+|implements\s+)([\w.]+)")


def compile_custom_patterns(patterns: list[str] | None) -> list[re.Pattern]:
    """Compile config-supplied regex patterns, skipping invalid ones."""
    compiled: list[re.Pattern] = []
    for raw in patterns or []:
        try:
            compiled.append(re.compile(raw, re.IGNORECASE))
        except re.error as e:
            logger.warning("Invalid cross_references.custom_patterns entry %r: %s", raw, e)
    return compiled


def extract_refs_from_body(body: str, custom_patterns: list[re.Pattern] | None = None) -> list[str]:
    """Extract all cross-references from a page body."""
    refs: set[str] = set()
    refs.update(_WIKILINK_RE.findall(body))
    refs.update(_JAVA_IMPORT_RE.findall(body))
    refs.update(_CLASS_REF_RE.findall(body))
    for pattern in custom_patterns or []:
        for match in pattern.findall(body):
            value = match if isinstance(match, str) else next((g for g in match if g), "")
            if value:
                refs.add(value.lower().replace(" ", "-"))
    # Filter out common Java stdlib
    refs = {r for r in refs if not r.startswith(("java.", "javax.", "org.w3c.", "org.xml."))}
    return sorted(refs)


def build_edge_list(pages: dict[str, dict]) -> list[tuple[str, str, str]]:
    """Build directed edge list from page references.

    Args:
        pages: {page_id: {"references": [ref_id, ...]}}

    Returns:
        List of (from_id, to_id, edge_type) tuples.
    """
    edges = []
    for page_id, page_data in pages.items():
        for ref in page_data.get("references", []):
            edges.append((page_id, ref, "references"))
    return edges
