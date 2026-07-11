"""Cross-reference extraction from wiki page content."""

from __future__ import annotations

import re

_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
_JAVA_IMPORT_RE = re.compile(r"import\s+([\w.]+);")
_CLASS_REF_RE = re.compile(r"(?:new\s+|extends\s+|implements\s+)([\w.]+)")
# SailPoint API class references (common in docs and PDF content)
_SP_CLASS_RE = re.compile(r"\b(sailpoint\.\w+\.\w+)\b", re.IGNORECASE)
# Connector/application names commonly referenced in XML config
_CONNECTOR_RE = re.compile(
    r"\b(Active Directory|LDAP|JDBC|Delimited File|SAP|ServiceNow|SCIM|REST|SOAP)\b",
    re.IGNORECASE,
)


def extract_refs_from_body(body: str) -> list[str]:
    """Extract all cross-references from a page body."""
    refs: set[str] = set()
    refs.update(_WIKILINK_RE.findall(body))
    refs.update(_JAVA_IMPORT_RE.findall(body))
    refs.update(_CLASS_REF_RE.findall(body))
    # SailPoint package references
    refs.update(_SP_CLASS_RE.findall(body))
    # Connector name references
    refs.update(match.lower().replace(" ", "-") for match in _CONNECTOR_RE.findall(body))
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
