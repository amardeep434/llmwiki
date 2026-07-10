"""Language-agnostic source code adapter."""

from __future__ import annotations

import re
from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage

LANG_MAP: dict[str, str] = {
    ".java": "java", ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".jsx": "javascript", ".go": "go", ".rs": "rust",
    ".cs": "csharp", ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp",
    ".rb": "ruby", ".kt": "kotlin", ".swift": "swift", ".scala": "scala",
    ".php": "php", ".sh": "bash", ".bash": "bash", ".zsh": "bash",
    ".sql": "sql", ".r": "r", ".lua": "lua", ".pl": "perl",
    ".ex": "elixir", ".exs": "elixir", ".hs": "haskell", ".clj": "clojure",
    ".dart": "dart", ".groovy": "groovy", ".m": "objectivec",
}

_JAVA_IMPORT_RE = re.compile(r"^import\s+([\w.]+);", re.MULTILINE)
_JAVA_CLASS_RE = re.compile(r"(?:public\s+)?(?:abstract\s+)?(?:class|interface|enum)\s+(\w+)")
_JAVA_METHOD_RE = re.compile(r"(?:public|protected|private)\s+(?:static\s+)?[\w<>\[\], ]+\s+(\w+)\s*\(")
_JAVADOC_RE = re.compile(r"/\*\*(.*?)\*/", re.DOTALL)

_PY_IMPORT_RE = re.compile(r"^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)
_PY_CLASS_RE = re.compile(r"^class\s+(\w+)", re.MULTILINE)
_PY_FUNC_RE = re.compile(r"^def\s+(\w+)", re.MULTILINE)
_PY_DOCSTRING_RE = re.compile(r'"""(.*?)"""', re.DOTALL)

_LINE_COMMENT_RE = re.compile(r"^\s*(?://|#|--)\s*(.*)", re.MULTILINE)
_BLOCK_COMMENT_RE = re.compile(r"/\*(.*?)\*/", re.DOTALL)


@register
class SourceCodeAdapter(BaseAdapter):
    """Extracts structure and documentation from source code files."""

    name = "source-code"
    extensions = list(LANG_MAP.keys())

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in LANG_MAP

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            return []

        lang = LANG_MAP.get(path.suffix.lower(), "")
        title = path.stem
        category = self._detect_category(path, content, lang)

        if lang == "java":
            body, refs, tags = self._parse_java(content, title)
        elif lang == "python":
            body, refs, tags = self._parse_python(content, title)
        else:
            body, refs, tags = self._parse_generic(content, title, lang)

        body += f"\n\n## Source Code\n\n<details>\n<summary>Full source ({len(content.splitlines())} lines)</summary>\n\n```{lang}\n{content}\n```\n\n</details>\n"

        page = WikiPage(
            slug=self._make_slug(path, category),
            title=title,
            category=category,
            source_path=str(path),
            body=body,
            language=lang,
            tags=tags,
            references=refs,
        )
        page.compute_hash()
        return [page]

    def _detect_category(self, path: Path, content: str, lang: str) -> str:
        if lang == "java":
            pkg_match = re.search(r"^package\s+([\w.]+);", content, re.MULTILINE)
            if pkg_match:
                return pkg_match.group(1).replace(".", "/")
        parts = path.parent.parts
        if len(parts) > 2:
            return "/".join(parts[-2:])
        return lang or "source"

    def _parse_java(self, content: str, title: str) -> tuple[str, list[str], list[str]]:
        sections = []
        refs = []
        tags = ["java"]

        doc_matches = _JAVADOC_RE.findall(content)
        if doc_matches:
            first_doc = doc_matches[0].strip()
            first_doc = re.sub(r"^\s*\*\s?", "", first_doc, flags=re.MULTILINE).strip()
            sections.append(f"## Overview\n\n{first_doc}")

        imports = _JAVA_IMPORT_RE.findall(content)
        if imports:
            refs.extend(imports)
            sections.append("## Imports\n\n" + "\n".join(f"- `{i}`" for i in imports))

        classes = _JAVA_CLASS_RE.findall(content)
        if classes:
            sections.append("## Classes\n\n" + "\n".join(f"- `{c}`" for c in classes))

        methods = _JAVA_METHOD_RE.findall(content)
        if methods:
            sections.append("## Methods\n\n" + "\n".join(f"- `{m}()`" for m in methods))

        if not sections:
            sections.append(f"## {title}\n\nJava source file.")

        return "\n\n".join(sections), refs, tags

    def _parse_python(self, content: str, title: str) -> tuple[str, list[str], list[str]]:
        sections = []
        refs = []
        tags = ["python"]

        doc_matches = _PY_DOCSTRING_RE.findall(content)
        if doc_matches:
            sections.append(f"## Overview\n\n{doc_matches[0].strip()}")

        for match in _PY_IMPORT_RE.finditer(content):
            ref = match.group(1) or match.group(2)
            if ref:
                refs.append(ref)
        if refs:
            sections.append("## Imports\n\n" + "\n".join(f"- `{r}`" for r in refs))

        classes = _PY_CLASS_RE.findall(content)
        if classes:
            class_items = []
            for c in classes:
                cls_doc_match = re.search(rf"class\s+{c}.*?:\s*\n\s+\"\"\"(.*?)\"\"\"", content, re.DOTALL)
                doc = ""
                if cls_doc_match:
                    doc = f" — {cls_doc_match.group(1).strip().splitlines()[0]}"
                class_items.append(f"- `{c}`{doc}")
            sections.append("## Classes\n\n" + "\n".join(class_items))

        funcs = _PY_FUNC_RE.findall(content)
        top_funcs = [f for f in funcs if not f.startswith("_") or f == "__init__"]
        if top_funcs:
            sections.append("## Functions\n\n" + "\n".join(f"- `{f}()`" for f in top_funcs))

        if not sections:
            sections.append(f"## {title}\n\nPython source file.")

        return "\n\n".join(sections), refs, tags

    def _parse_generic(self, content: str, title: str, lang: str) -> tuple[str, list[str], list[str]]:
        sections = []
        tags = [lang] if lang else []

        comments = _LINE_COMMENT_RE.findall(content[:2000])
        block_comments = _BLOCK_COMMENT_RE.findall(content[:2000])
        if block_comments:
            desc = block_comments[0].strip()
            desc = re.sub(r"^\s*\*\s?", "", desc, flags=re.MULTILINE).strip()
            sections.append(f"## Overview\n\n{desc}")
        elif comments:
            sections.append(f"## Overview\n\n{' '.join(comments[:5])}")

        if not sections:
            sections.append(f"## {title}\n\nSource file ({lang or 'unknown language'}).")

        return "\n\n".join(sections), [], tags

    def _make_slug(self, path: Path, category: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "-", path.stem)
        cat_safe = re.sub(r"[^a-zA-Z0-9_-]", "-", category)
        return f"{cat_safe}/{safe}".lower().strip("-/")
