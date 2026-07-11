"""XML adapter with inline script extraction.

Handles generic XML files and optionally extracts inline script blocks
(BeanShell <Source>, <Script>, <Code> elements) as separate wiki pages.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage, _safe_fence

_JAVA_IMPORT_IN_BSH = re.compile(r"import\s+([\w.]+);")
_REF_NAME_RE = re.compile(r'name="([^"]+)"')


@register
class XMLAdapter(BaseAdapter):
    """Extracts structure and inline scripts from XML files."""

    name = "xml"
    extensions = [".xml", ".xsl", ".xslt", ".xsd", ".wsdl"]

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in {".xml", ".xsl", ".xslt", ".xsd", ".wsdl"}

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return [self._fallback_page(path, content)]

        tag = _strip_ns(root.tag)
        name = root.get("name", path.stem)
        category = self._detect_category(path, tag)
        refs = self._extract_references(root, content)
        tags = [tag.lower()]

        # Build body
        sections = []
        sections.append(f"## {name}\n\n**Type:** {tag}")

        # Extract key attributes
        attrs = {k: v for k, v in root.attrib.items() if k != "name"}
        if attrs:
            attr_lines = [f"- **{k}:** {v}" for k, v in attrs.items()]
            sections.append("## Attributes\n\n" + "\n".join(attr_lines))

        # Extract structure summary
        children = list(root)
        if children:
            child_summary = []
            for child in children:
                ctag = _strip_ns(child.tag)
                cname = child.get("name", "")
                label = f"`<{ctag}>`"
                if cname:
                    label += f" name=\"{cname}\""
                child_summary.append(f"- {label}")
            sections.append("## Structure\n\n" + "\n".join(child_summary[:50]))

        # Extract inline scripts
        scripts = self._find_scripts(root)
        bsh_pages: list[WikiPage] = []
        if scripts:
            script_summary = []
            for step_name, script_body in scripts:
                line_count = len(script_body.strip().splitlines())
                fence = _safe_fence(script_body)
                script_summary.append(
                    f"### {step_name} ({line_count} lines)\n\n"
                    f"{fence}java\n{script_body.strip()}\n{fence}"
                )
                # Optionally create separate BeanShell page
                if config.get("extract_beanshell", False):
                    bsh_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", f"{name}__{step_name}").lower()
                    bsh_refs = _JAVA_IMPORT_IN_BSH.findall(script_body)
                    bsh_fence = _safe_fence(script_body)
                    bsh_page = WikiPage(
                        slug=f"beanshell/{bsh_slug}",
                        title=f"{name} — {step_name}",
                        category="beanshell",
                        source_path=str(path),
                        body=(
                            f"## {step_name}\n\n"
                            f"**Parent:** [[{name}]]\n\n"
                            f"{bsh_fence}java\n{script_body.strip()}\n{bsh_fence}\n"
                        ),
                        language="java",
                        tags=["beanshell", tag.lower()],
                        references=[name] + bsh_refs,
                    )
                    bsh_page.compute_hash()
                    bsh_pages.append(bsh_page)

            sections.append("## Inline Scripts\n\n" + "\n\n".join(script_summary))

        # Full source
        xml_fence = _safe_fence(content)
        sections.append(
            f"\n## Source\n\n<details>\n<summary>Full XML ({len(content.splitlines())} lines)</summary>\n\n"
            f"{xml_fence}xml\n{content}\n{xml_fence}\n\n</details>"
        )

        body = "\n\n".join(sections)
        parent = WikiPage(
            slug=self._make_slug(path, category),
            title=name,
            category=category,
            source_path=str(path),
            body=body,
            language="xml",
            tags=tags,
            references=refs,
        )
        parent.compute_hash()
        return [parent] + bsh_pages

    def _find_scripts(self, root: ET.Element) -> list[tuple[str, str]]:
        """Find all inline script blocks (Source elements)."""
        scripts = []
        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if tag == "Source" and elem.text and elem.text.strip():
                step_name = self._find_parent_step_name(root, elem)
                scripts.append((step_name, elem.text))
        return scripts

    def _find_parent_step_name(self, root: ET.Element, target: ET.Element) -> str:
        """Walk up from target to find the closest named ancestor."""
        parent_map = {child: parent for parent in root.iter() for child in parent}
        current = target
        while current in parent_map:
            current = parent_map[current]
            name = current.get("name", "")
            if name and current is not root:
                return name
        # Fall back to root name
        return root.get("name", "unnamed")

    def _extract_references(self, root: ET.Element, content: str) -> list[str]:
        """Extract cross-references from XML."""
        refs = []
        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if tag in ("Reference", "ReferencedRules"):
                name = elem.get("name", "")
                if name:
                    refs.append(name)
                for child in elem:
                    cname = child.get("name", "")
                    if cname:
                        refs.append(cname)
        refs.extend(_JAVA_IMPORT_IN_BSH.findall(content))
        return list(set(refs))

    def _detect_category(self, path: Path, tag: str) -> str:
        parts = path.parent.parts
        for i, part in enumerate(parts):
            if part in ("config", "src", "pluginsrc"):
                remaining = parts[i + 1:]
                if remaining:
                    return "/".join(remaining)
        if len(parts) >= 2:
            return "/".join(parts[-2:])
        return tag.lower()

    def _make_slug(self, path: Path, category: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "-", path.stem)
        cat_safe = re.sub(r"[^a-zA-Z0-9_/-]", "-", category)
        return f"{cat_safe}/{safe}".lower().strip("-/")

    def _fallback_page(self, path: Path, content: str) -> WikiPage:
        fence = _safe_fence(content)
        page = WikiPage(
            slug=path.stem.lower(),
            title=path.stem,
            category="xml",
            source_path=str(path),
            body=f"## {path.stem}\n\n{fence}xml\n{content}\n{fence}\n",
            language="xml",
        )
        page.compute_hash()
        return page


def _strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag
