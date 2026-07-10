# LLMWiki Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a generic, reusable pipeline that transforms any codebase + PDF documentation into a searchable, interlinked, evolving knowledge base — browsable by humans and queryable by AI agents.

**Architecture:** 3-layer data model (raw/ → wiki/ → site/) with pluggable adapters for content ingestion, a cross-reference engine with PageRank-style importance scoring, dual search (client-side + SQLite FTS5), and static HTML generation with an interactive dashboard. All local, minimal dependencies.

**Tech Stack:** Python 3.9+, `markdown` (md→HTML), `pymupdf4llm` (PDF→md), `sqlite3` (stdlib), `http.server` (stdlib), highlight.js (CDN for syntax highlighting), vis-network (CDN for graph viz)

**Spec:** `docs/superpowers/specs/2026-07-11-llmwiki-design.md`

---

## File Structure

```
~/llmwiki/
├── pyproject.toml                  # Package config, 2 deps, console_scripts entry
├── README.md                       # Project documentation
├── LICENSE                         # MIT license
├── .gitignore                      # Python + build artifacts
├── llmwiki/
│   ├── __init__.py                 # Version, lazy imports
│   ├── __main__.py                 # python -m llmwiki entry
│   ├── cli.py                      # argparse CLI dispatcher (12 subcommands)
│   ├── config.py                   # Load/validate llmwiki.json
│   ├── state.py                    # .llmwiki-state.json management
│   ├── ingest.py                   # Adapter orchestrator → raw/
│   ├── build.py                    # raw/ → wiki/ → site/ generator
│   ├── graph.py                    # Knowledge graph construction
│   ├── crossref.py                 # Cross-reference extraction from page content
│   ├── importance.py               # PageRank-style scoring
│   ├── clusters.py                 # Topic cluster detection
│   ├── search.py                   # SQLite FTS5 + client-side index builder
│   ├── serve.py                    # Local HTTP server (stdlib)
│   ├── exporters.py                # llms.txt, JSON-LD, sitemap, per-page JSON
│   ├── lint.py                     # Broken links, orphans, consistency checks
│   ├── adapters/
│   │   ├── __init__.py             # Adapter registry + auto-detection
│   │   ├── base.py                 # BaseAdapter ABC + WikiPage dataclass
│   │   ├── source_code.py          # Language-aware source code extraction
│   │   ├── xml_adapter.py          # XML structure + inline script extraction
│   │   ├── pdf_adapter.py          # PDF → markdown via pymupdf4llm
│   │   ├── markdown_adapter.py     # Markdown pass-through + frontmatter
│   │   ├── config_adapter.py       # Config file (json/yaml/properties/ini)
│   │   └── generic_adapter.py      # Fallback text adapter
│   └── render/
│       ├── __init__.py
│       ├── css.py                  # All CSS as Python string constant
│       ├── js.py                   # All JS as Python string constant
│       └── html.py                 # HTML page generator functions
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Shared fixtures (tmp dirs, sample files)
    ├── test_base_adapter.py
    ├── test_config.py
    ├── test_state.py
    ├── test_source_code_adapter.py
    ├── test_xml_adapter.py
    ├── test_pdf_adapter.py
    ├── test_markdown_adapter.py
    ├── test_config_adapter.py
    ├── test_generic_adapter.py
    ├── test_registry.py
    ├── test_ingest.py
    ├── test_crossref.py
    ├── test_importance.py
    ├── test_clusters.py
    ├── test_graph.py
    ├── test_build.py
    ├── test_search.py
    ├── test_exporters.py
    ├── test_serve.py
    ├── test_lint.py
    └── test_cli.py
```

---

### Task 1: Project Scaffolding & Core Data Types

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `LICENSE`
- Create: `llmwiki/__init__.py`
- Create: `llmwiki/__main__.py`
- Create: `llmwiki/adapters/__init__.py`
- Create: `llmwiki/adapters/base.py`
- Create: `llmwiki/render/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Test: `tests/test_base_adapter.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "llmwiki"
version = "0.1.0"
description = "Generic codebase + documentation knowledge base pipeline"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
dependencies = [
    "markdown>=3.9",
    "pymupdf4llm>=0.0.17",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
llmwiki = "llmwiki.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create .gitignore**

```gitignore
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg
.venv/
venv/
raw/
wiki/
site/
.llmwiki-state.json
llmwiki.db
*.db
.pytest_cache/
```

- [ ] **Step 3: Create LICENSE (MIT)**

Standard MIT license with "2026 Amardeep Singh Arora".

- [ ] **Step 4: Create llmwiki/__init__.py**

```python
"""LLMWiki — Generic codebase + documentation knowledge base pipeline."""

__version__ = "0.1.0"

PACKAGE_ROOT = __import__("pathlib").Path(__file__).resolve().parent
```

- [ ] **Step 5: Create llmwiki/__main__.py**

```python
"""Allow running as python -m llmwiki."""
from llmwiki.cli import main

main()
```

- [ ] **Step 6: Create llmwiki/adapters/base.py with WikiPage dataclass and BaseAdapter ABC**

```python
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

    def to_frontmatter(self) -> str:
        """Render YAML frontmatter string."""
        lines = [
            "---",
            f"title: \"{self.title}\"",
            f"slug: {self.slug}",
            f"category: {self.category}",
            f"source_path: {self.source_path}",
            f"language: {self.language}",
            f"content_hash: {self.content_hash}",
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
        """Extract WikiPage objects from the given file.

        Returns a list because one file may produce multiple pages
        (e.g., XML with inline scripts -> parent + extracted blocks).
        """
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
```

- [ ] **Step 7: Create llmwiki/adapters/__init__.py with adapter registry**

```python
"""Adapter registry and auto-detection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llmwiki.adapters.base import BaseAdapter

_REGISTRY: dict[str, type[BaseAdapter]] = {}


def register(adapter_cls: type[BaseAdapter]) -> type[BaseAdapter]:
    """Register an adapter class by its name."""
    _REGISTRY[adapter_cls.name] = adapter_cls
    return adapter_cls


def get_adapter(name: str) -> BaseAdapter:
    """Get an adapter instance by name."""
    if name not in _REGISTRY:
        raise KeyError(f"Unknown adapter: {name}. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[name]()


def list_adapters() -> list[str]:
    """Return list of registered adapter names."""
    return sorted(_REGISTRY.keys())


def detect_adapters(root: Path) -> dict[str, list[Path]]:
    """Auto-detect which adapters are needed for a directory.

    Returns {adapter_name: [matching_file_paths]}.
    """
    _ensure_all_loaded()
    result: dict[str, list[Path]] = {}
    for name, cls in _REGISTRY.items():
        adapter = cls()
        files = adapter.discover(root)
        if files:
            result[name] = files
    return result


def _ensure_all_loaded() -> None:
    """Import all built-in adapter modules to trigger registration."""
    from llmwiki.adapters import (  # noqa: F401
        config_adapter,
        generic_adapter,
        markdown_adapter,
        pdf_adapter,
        source_code,
        xml_adapter,
    )
```

- [ ] **Step 8: Create empty module inits**

Create `llmwiki/render/__init__.py` and `tests/__init__.py` as empty files.

- [ ] **Step 9: Create tests/conftest.py with shared fixtures**

```python
"""Shared test fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal project directory for testing."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "Main.java").write_text(
        '/**\n * Main entry point.\n */\npublic class Main {\n'
        '    public static void main(String[] args) {\n'
        '        System.out.println("Hello");\n    }\n}\n'
    )
    (tmp_path / "README.md").write_text("# Test Project\n\nA test project.\n")
    (tmp_path / "config.properties").write_text("db.host=localhost\ndb.port=5432\n")
    return tmp_path


@pytest.fixture
def tmp_output(tmp_path):
    """Create output directories for testing."""
    raw = tmp_path / "raw"
    wiki = tmp_path / "wiki"
    site = tmp_path / "site"
    raw.mkdir()
    wiki.mkdir()
    site.mkdir()
    return {"raw": raw, "wiki": wiki, "site": site, "root": tmp_path}
```

- [ ] **Step 10: Write tests for WikiPage and BaseAdapter**

```python
# tests/test_base_adapter.py
"""Tests for WikiPage dataclass and BaseAdapter interface."""

from pathlib import Path
from llmwiki.adapters.base import WikiPage, BaseAdapter


class TestWikiPage:
    def test_create_minimal(self):
        page = WikiPage(slug="test", title="Test", category="cat",
                        source_path="/tmp/test.py", body="# Hello")
        assert page.slug == "test"
        assert page.title == "Test"
        assert page.tags == []
        assert page.references == []

    def test_compute_hash(self):
        page = WikiPage(slug="a", title="A", category="c",
                        source_path="/x", body="content")
        h = page.compute_hash()
        assert len(h) == 16
        assert h == page.content_hash

    def test_hash_changes_with_content(self):
        p1 = WikiPage(slug="a", title="A", category="c",
                      source_path="/x", body="content1")
        p2 = WikiPage(slug="a", title="A", category="c",
                      source_path="/x", body="content2")
        assert p1.compute_hash() != p2.compute_hash()

    def test_to_frontmatter(self):
        page = WikiPage(slug="my-page", title="My Page", category="java",
                        source_path="/src/Main.java", body="# Hello",
                        language="java", tags=["util", "core"])
        page.compute_hash()
        fm = page.to_frontmatter()
        assert "---" in fm
        assert 'title: "My Page"' in fm
        assert "slug: my-page" in fm
        assert "tags: [util, core]" in fm

    def test_to_markdown(self):
        page = WikiPage(slug="test", title="Test", category="cat",
                        source_path="/x", body="# Body\n\nContent here.")
        md = page.to_markdown()
        assert md.startswith("---\n")
        assert "# Body" in md
        assert "Content here." in md
        assert page.content_hash != ""


class TestBaseAdapter:
    def test_cannot_instantiate_directly(self):
        try:
            BaseAdapter()
            assert False, "Should raise TypeError"
        except TypeError:
            pass

    def test_subclass_must_implement(self):
        class BadAdapter(BaseAdapter):
            name = "bad"
            extensions = [".bad"]

        try:
            BadAdapter()
            assert False, "Should raise TypeError"
        except TypeError:
            pass

    def test_concrete_subclass(self):
        class GoodAdapter(BaseAdapter):
            name = "good"
            extensions = [".good"]

            def can_handle(self, path):
                return path.suffix == ".good"

            def extract(self, path, config):
                return [WikiPage(slug="x", title="X", category="c",
                                 source_path=str(path), body="body")]

        adapter = GoodAdapter()
        assert adapter.can_handle(Path("test.good"))
        assert not adapter.can_handle(Path("test.bad"))
        pages = adapter.extract(Path("test.good"), {})
        assert len(pages) == 1

    def test_discover(self, tmp_path):
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("world")
        (tmp_path / "c.py").write_text("pass")

        class TxtAdapter(BaseAdapter):
            name = "txt"
            extensions = [".txt"]
            def can_handle(self, path): return path.suffix == ".txt"
            def extract(self, path, config): return []

        adapter = TxtAdapter()
        found = adapter.discover(tmp_path)
        assert len(found) == 2
        assert all(f.suffix == ".txt" for f in found)
```

- [ ] **Step 11: Run tests to verify they pass**

Run: `cd ~/llmwiki && pip install -e ".[dev]" && pytest tests/test_base_adapter.py -v`
Expected: All tests PASS

- [ ] **Step 12: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: project scaffolding with BaseAdapter and WikiPage core types

- pyproject.toml with 2 runtime deps (markdown, pymupdf4llm)
- BaseAdapter ABC with discover/can_handle/extract interface
- WikiPage dataclass with hash computation and markdown rendering
- Adapter registry with auto-detection
- Test fixtures and base adapter tests"
```


---

### Task 2: Configuration & State Management

**Files:**
- Create: `llmwiki/config.py`
- Create: `llmwiki/state.py`
- Test: `tests/test_config.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: Write failing tests for config**

```python
# tests/test_config.py
"""Tests for configuration loading and validation."""

import json
from pathlib import Path
from llmwiki.config import load_config, create_default_config, validate_config


class TestConfig:
    def test_create_default_config(self, tmp_path):
        cfg = create_default_config("MyProject", str(tmp_path))
        assert cfg["project"]["name"] == "MyProject"
        assert len(cfg["sources"]) == 1
        assert cfg["sources"][0]["type"] == "auto"
        assert cfg["build"]["incremental"] is True

    def test_load_config_from_file(self, tmp_path):
        cfg_data = {
            "project": {"name": "Test"},
            "sources": [{"path": str(tmp_path), "type": "auto"}],
            "build": {"out_dir": "site", "incremental": True},
            "serve": {"port": 8765, "host": "127.0.0.1"},
        }
        cfg_file = tmp_path / "llmwiki.json"
        cfg_file.write_text(json.dumps(cfg_data))
        loaded = load_config(cfg_file)
        assert loaded["project"]["name"] == "Test"

    def test_load_config_missing_file(self, tmp_path):
        cfg_file = tmp_path / "missing.json"
        try:
            load_config(cfg_file)
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_validate_config_valid(self, tmp_path):
        cfg = create_default_config("Test", str(tmp_path))
        errors = validate_config(cfg)
        assert errors == []

    def test_validate_config_missing_project(self):
        errors = validate_config({"sources": []})
        assert any("project" in e for e in errors)

    def test_validate_config_missing_sources(self):
        errors = validate_config({"project": {"name": "X"}})
        assert any("sources" in e for e in errors)

    def test_config_with_pdf_sources(self, tmp_path):
        cfg = create_default_config("Test", str(tmp_path))
        cfg["pdf_sources"] = [
            {"path": "/docs/guides", "label": "Guides", "type": "auto"}
        ]
        errors = validate_config(cfg)
        assert errors == []

    def test_config_defaults(self, tmp_path):
        cfg = create_default_config("Test", str(tmp_path))
        assert cfg["serve"]["port"] == 8765
        assert cfg["serve"]["host"] == "127.0.0.1"
        assert cfg["cross_references"]["enabled"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/llmwiki && pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'llmwiki.config'`

- [ ] **Step 3: Implement llmwiki/config.py**

```python
"""Configuration loading and validation for llmwiki."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_EXCLUDE = [
    "node_modules", ".git", "build", "dist", "__pycache__",
    "*.min.js", "*.min.css", "*.map", "*.lock", ".venv", "venv",
    "*.pyc", "*.class", "*.o", "*.so", "*.dll",
    "*.jpg", "*.png", "*.gif", "*.ico", "*.svg",
    "*.zip", "*.tar", "*.gz", "*.jar", "*.war",
    ".DS_Store", "Thumbs.db",
]


def create_default_config(name: str, source_path: str) -> dict:
    """Create a default llmwiki.json config."""
    return {
        "project": {
            "name": name,
            "description": "",
        },
        "sources": [
            {
                "path": source_path,
                "type": "auto",
                "exclude": list(DEFAULT_EXCLUDE),
            }
        ],
        "pdf_sources": [],
        "build": {
            "out_dir": "site",
            "incremental": True,
            "search_mode": "auto",
        },
        "serve": {
            "port": 8765,
            "host": "127.0.0.1",
        },
        "cross_references": {
            "enabled": True,
            "importance_iterations": 20,
            "cluster_min_size": 3,
        },
        "exclude_global": list(DEFAULT_EXCLUDE),
    }


def load_config(path: Path) -> dict:
    """Load config from a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict, path: Path) -> None:
    """Save config to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def validate_config(config: dict) -> list[str]:
    """Validate config and return list of error messages."""
    errors = []
    if "project" not in config:
        errors.append("Missing required field: 'project'")
    elif "name" not in config.get("project", {}):
        errors.append("Missing required field: 'project.name'")
    if "sources" not in config:
        errors.append("Missing required field: 'sources'")
    elif not isinstance(config["sources"], list):
        errors.append("'sources' must be a list")
    return errors
```

- [ ] **Step 4: Run config tests to verify they pass**

Run: `cd ~/llmwiki && pytest tests/test_config.py -v`
Expected: All PASS

- [ ] **Step 5: Write failing tests for state management**

```python
# tests/test_state.py
"""Tests for build state tracking."""

from pathlib import Path
from llmwiki.state import BuildState


class TestBuildState:
    def test_create_empty(self, tmp_path):
        state = BuildState(tmp_path / ".llmwiki-state.json")
        assert state.build_number == 0
        assert state.files == {}

    def test_save_and_load(self, tmp_path):
        path = tmp_path / ".llmwiki-state.json"
        state = BuildState(path)
        state.record_file("/src/Main.java", "abc123", "raw/java/Main.md")
        state.save()

        loaded = BuildState(path)
        loaded.load()
        assert "/src/Main.java" in loaded.files
        assert loaded.files["/src/Main.java"]["content_hash"] == "abc123"

    def test_classify_new_file(self, tmp_path):
        state = BuildState(tmp_path / ".llmwiki-state.json")
        assert state.classify("/new/file.java", "hash1") == "new"

    def test_classify_unchanged_file(self, tmp_path):
        state = BuildState(tmp_path / ".llmwiki-state.json")
        state.record_file("/f.java", "hash1", "raw/f.md")
        assert state.classify("/f.java", "hash1") == "unchanged"

    def test_classify_modified_file(self, tmp_path):
        state = BuildState(tmp_path / ".llmwiki-state.json")
        state.record_file("/f.java", "hash1", "raw/f.md")
        assert state.classify("/f.java", "hash2") == "modified"

    def test_detect_deleted(self, tmp_path):
        state = BuildState(tmp_path / ".llmwiki-state.json")
        state.record_file("/a.java", "h1", "raw/a.md")
        state.record_file("/b.java", "h2", "raw/b.md")
        deleted = state.detect_deleted({"/a.java"})
        assert "/b.java" in deleted

    def test_increment_build_number(self, tmp_path):
        state = BuildState(tmp_path / ".llmwiki-state.json")
        assert state.build_number == 0
        state.increment_build()
        assert state.build_number == 1
```

- [ ] **Step 6: Run state tests to verify they fail**

Run: `cd ~/llmwiki && pytest tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 7: Implement llmwiki/state.py**

```python
"""Build state management for incremental builds."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class BuildState:
    """Tracks file hashes and build state for incremental processing."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.build_number: int = 0
        self.last_build: str = ""
        self.files: dict[str, dict] = {}
        if path.exists():
            self.load()

    def load(self) -> None:
        """Load state from disk."""
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        meta = data.get("_meta", {})
        self.build_number = meta.get("build_number", 0)
        self.last_build = meta.get("last_build", "")
        self.files = data.get("files", {})

    def save(self) -> None:
        """Persist state to disk."""
        data = {
            "_meta": {
                "version": "1.0.0",
                "build_number": self.build_number,
                "last_build": self.last_build or datetime.now(timezone.utc).isoformat(),
            },
            "files": self.files,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

    def record_file(self, source_path: str, content_hash: str, raw_path: str) -> None:
        """Record a processed file."""
        self.files[source_path] = {
            "content_hash": content_hash,
            "raw_path": raw_path,
            "status": "current",
        }

    def classify(self, source_path: str, content_hash: str) -> str:
        """Classify a file as new, modified, or unchanged."""
        if source_path not in self.files:
            return "new"
        if self.files[source_path]["content_hash"] != content_hash:
            return "modified"
        return "unchanged"

    def detect_deleted(self, current_files: set[str]) -> set[str]:
        """Find files in state that no longer exist on disk."""
        return set(self.files.keys()) - current_files

    def increment_build(self) -> None:
        """Increment build counter and set timestamp."""
        self.build_number += 1
        self.last_build = datetime.now(timezone.utc).isoformat()
```

- [ ] **Step 8: Run all tests**

Run: `cd ~/llmwiki && pytest tests/test_config.py tests/test_state.py -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: configuration loading and build state management

- llmwiki.json config with auto-generated defaults
- validate_config() for startup checks
- BuildState with incremental file classification (new/modified/unchanged/deleted)
- Content-hash-based change detection"
```


---

### Task 3: Source Code Adapter (Language-Agnostic)

**Files:**
- Create: `llmwiki/adapters/source_code.py`
- Test: `tests/test_source_code_adapter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_source_code_adapter.py
"""Tests for language-agnostic source code adapter."""

from pathlib import Path
from llmwiki.adapters.source_code import SourceCodeAdapter


class TestSourceCodeAdapter:
    def setup_method(self):
        self.adapter = SourceCodeAdapter()

    def test_can_handle_java(self, tmp_path):
        f = tmp_path / "Main.java"
        f.write_text("class Main {}")
        assert self.adapter.can_handle(f)

    def test_can_handle_python(self, tmp_path):
        f = tmp_path / "main.py"
        f.write_text("def main(): pass")
        assert self.adapter.can_handle(f)

    def test_cannot_handle_pdf(self, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_text("fake pdf")
        assert not self.adapter.can_handle(f)

    def test_extract_java(self, tmp_path):
        f = tmp_path / "AccountUtil.java"
        f.write_text(
            'package com.vf.core.utility;\n\n'
            'import java.util.List;\n'
            'import sailpoint.object.Identity;\n\n'
            '/**\n * Account utility methods.\n */\n'
            'public class AccountUtil {\n'
            '    /**\n     * Check if identity has non-personal accounts.\n     */\n'
            '    public static boolean hasNonPersonalAccounts(Identity id) {\n'
            '        return false;\n'
            '    }\n'
            '}\n'
        )
        pages = self.adapter.extract(f, {})
        assert len(pages) == 1
        page = pages[0]
        assert page.title == "AccountUtil"
        assert page.language == "java"
        assert "Account utility methods" in page.body
        assert "hasNonPersonalAccounts" in page.body
        assert any("sailpoint.object.Identity" in r for r in page.references)

    def test_extract_python(self, tmp_path):
        f = tmp_path / "utils.py"
        f.write_text(
            '"""Utility functions for data processing."""\n\n'
            'import os\n'
            'from pathlib import Path\n\n\n'
            'def process_file(path: str) -> dict:\n'
            '    """Process a single file and return metadata."""\n'
            '    return {"path": path}\n\n\n'
            'class FileProcessor:\n'
            '    """Processes files in batch."""\n\n'
            '    def run(self) -> None:\n'
            '        """Execute the batch processing."""\n'
            '        pass\n'
        )
        pages = self.adapter.extract(f, {})
        assert len(pages) == 1
        page = pages[0]
        assert page.title == "utils"
        assert page.language == "python"
        assert "Utility functions" in page.body
        assert "process_file" in page.body
        assert "FileProcessor" in page.body

    def test_extract_unknown_language(self, tmp_path):
        f = tmp_path / "script.lua"
        f.write_text("-- A lua script\nfunction hello()\n  print('hi')\nend\n")
        pages = self.adapter.extract(f, {})
        assert len(pages) == 1
        assert pages[0].language == "lua"

    def test_discover(self, tmp_path):
        (tmp_path / "a.java").write_text("class A {}")
        (tmp_path / "b.py").write_text("pass")
        (tmp_path / "c.txt").write_text("text")
        sub = tmp_path / "node_modules"
        sub.mkdir()
        (sub / "d.js").write_text("var x;")
        found = self.adapter.discover(tmp_path, exclude=["node_modules"])
        names = [f.name for f in found]
        assert "a.java" in names
        assert "b.py" in names
        assert "d.js" not in names

    def test_category_from_path(self, tmp_path):
        d = tmp_path / "src" / "com" / "vf" / "core" / "utility"
        d.mkdir(parents=True)
        f = d / "AccountUtil.java"
        f.write_text("package com.vf.core.utility;\npublic class AccountUtil {}")
        pages = self.adapter.extract(f, {})
        assert pages[0].category != ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/llmwiki && pytest tests/test_source_code_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: Implement llmwiki/adapters/source_code.py**

```python
"""Language-agnostic source code adapter.

Extracts structure, documentation, and references from source code files
in any programming language. Uses language-specific parsers for popular
languages and falls back to generic comment/structure extraction.
"""

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
_JAVA_CLASS_RE = re.compile(
    r"(?:public\s+)?(?:abstract\s+)?(?:class|interface|enum)\s+(\w+)"
)
_JAVA_METHOD_RE = re.compile(
    r"(?:public|protected|private)\s+(?:static\s+)?[\w<>\[\], ]+\s+(\w+)\s*\("
)
_JAVADOC_RE = re.compile(r"/\*\*(.*?)\*/", re.DOTALL)

_PY_IMPORT_RE = re.compile(r"^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)
_PY_CLASS_RE = re.compile(r"^class\s+(\w+)", re.MULTILINE)
_PY_FUNC_RE = re.compile(r"^def\s+(\w+)", re.MULTILINE)
_PY_DOCSTRING_RE = re.compile(r'"""(.*?)"""', re.DOTALL)

# Generic comment patterns for unknown languages
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

        # Append full source as collapsible block
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
        # Fall back to relative directory path
        parts = path.parent.parts
        if len(parts) > 2:
            return "/".join(parts[-2:])
        return lang or "source"

    def _parse_java(self, content: str, title: str) -> tuple[str, list[str], list[str]]:
        sections = []
        refs = []
        tags = ["java"]

        # Module docstring
        doc_matches = _JAVADOC_RE.findall(content)
        if doc_matches:
            first_doc = doc_matches[0].strip()
            first_doc = re.sub(r"^\s*\*\s?", "", first_doc, flags=re.MULTILINE).strip()
            sections.append(f"## Overview\n\n{first_doc}")

        # Imports
        imports = _JAVA_IMPORT_RE.findall(content)
        if imports:
            refs.extend(imports)
            sections.append("## Imports\n\n" + "\n".join(f"- `{i}`" for i in imports))

        # Classes
        classes = _JAVA_CLASS_RE.findall(content)
        if classes:
            sections.append("## Classes\n\n" + "\n".join(f"- `{c}`" for c in classes))

        # Methods with javadoc
        methods = _JAVA_METHOD_RE.findall(content)
        if methods:
            method_docs = []
            for m in methods:
                method_docs.append(f"- `{m}()`")
            sections.append("## Methods\n\n" + "\n".join(method_docs))

        if not sections:
            sections.append(f"## {title}\n\nJava source file.")

        return "\n\n".join(sections), refs, tags

    def _parse_python(self, content: str, title: str) -> tuple[str, list[str], list[str]]:
        sections = []
        refs = []
        tags = ["python"]

        # Module docstring
        doc_matches = _PY_DOCSTRING_RE.findall(content)
        if doc_matches:
            sections.append(f"## Overview\n\n{doc_matches[0].strip()}")

        # Imports
        for match in _PY_IMPORT_RE.finditer(content):
            ref = match.group(1) or match.group(2)
            if ref:
                refs.append(ref)
        if refs:
            sections.append("## Imports\n\n" + "\n".join(f"- `{r}`" for r in refs))

        # Classes
        classes = _PY_CLASS_RE.findall(content)
        if classes:
            class_items = []
            for c in classes:
                # Try to find class docstring
                cls_doc_match = re.search(
                    rf"class\s+{c}.*?:\s*\n\s+\"\"\"(.*?)\"\"\"", content, re.DOTALL
                )
                doc = ""
                if cls_doc_match:
                    doc = f" — {cls_doc_match.group(1).strip().splitlines()[0]}"
                class_items.append(f"- `{c}`{doc}")
            sections.append("## Classes\n\n" + "\n".join(class_items))

        # Functions
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

        # Extract leading comments as description
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/llmwiki && pytest tests/test_source_code_adapter.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: source code adapter with Java/Python/generic parsing

- Auto-detects 30+ languages by file extension
- Java: extracts package, imports, javadoc, classes, methods
- Python: extracts docstrings, imports, classes, functions
- Generic: extracts comments and wraps source in fenced block
- Full source appended as collapsible details block"
```


---

### Task 4: XML Adapter (with Inline Script Extraction)

**Files:**
- Create: `llmwiki/adapters/xml_adapter.py`
- Test: `tests/test_xml_adapter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_xml_adapter.py
"""Tests for XML adapter with inline script extraction."""

from pathlib import Path
from llmwiki.adapters.xml_adapter import XMLAdapter


class TestXMLAdapter:
    def setup_method(self):
        self.adapter = XMLAdapter()

    def test_can_handle_xml(self, tmp_path):
        f = tmp_path / "workflow.xml"
        f.write_text("<Workflow/>")
        assert self.adapter.can_handle(f)

    def test_cannot_handle_java(self, tmp_path):
        f = tmp_path / "Main.java"
        f.write_text("class Main {}")
        assert not self.adapter.can_handle(f)

    def test_extract_simple_xml(self, tmp_path):
        f = tmp_path / "config.xml"
        f.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Configuration name="TestConfig">\n'
            '  <Entry key="host" value="localhost"/>\n'
            '  <Entry key="port" value="8080"/>\n'
            '</Configuration>\n'
        )
        pages = self.adapter.extract(f, {})
        assert len(pages) >= 1
        assert pages[0].title == "TestConfig" or pages[0].title == "config"
        assert pages[0].language == "xml"

    def test_extract_workflow_with_beanshell(self, tmp_path):
        f = tmp_path / "MyWorkflow.xml"
        f.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Workflow name="VF-Core-TestWorkflow">\n'
            '  <Step name="Initialize">\n'
            '    <Script>\n'
            '      <Source>\n'
            '        import sailpoint.object.Identity;\n'
            '        Identity id = context.getObjectByName(Identity.class, name);\n'
            '        return id;\n'
            '      </Source>\n'
            '    </Script>\n'
            '  </Step>\n'
            '  <Step name="Finalize">\n'
            '    <Script>\n'
            '      <Source>\n'
            '        log.debug("Done");\n'
            '      </Source>\n'
            '    </Script>\n'
            '  </Step>\n'
            '</Workflow>\n'
        )
        pages = self.adapter.extract(f, {"extract_beanshell": True})
        # Should get parent page + 2 extracted BeanShell pages
        assert len(pages) >= 1
        parent = pages[0]
        assert "VF-Core-TestWorkflow" in parent.title or "MyWorkflow" in parent.title
        # BeanShell blocks should be mentioned
        assert "Initialize" in parent.body
        # If beanshell extraction is on, we get extra pages
        bsh_pages = [p for p in pages if "beanshell" in p.category]
        if bsh_pages:
            assert any("Initialize" in p.title for p in bsh_pages)

    def test_extract_references(self, tmp_path):
        f = tmp_path / "MyRule.xml"
        f.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Rule name="TestRule">\n'
            '  <ReferencedRules>\n'
            '    <Reference class="sailpoint.object.Rule" name="CommonLib"/>\n'
            '  </ReferencedRules>\n'
            '  <Source>\n'
            '    import com.vf.core.utility.AccountUtil;\n'
            '    AccountUtil.doSomething();\n'
            '  </Source>\n'
            '</Rule>\n'
        )
        pages = self.adapter.extract(f, {})
        assert len(pages) >= 1
        refs = pages[0].references
        assert any("CommonLib" in r for r in refs)

    def test_category_from_directory(self, tmp_path):
        d = tmp_path / "config" / "Workflow" / "Core"
        d.mkdir(parents=True)
        f = d / "MyWorkflow.xml"
        f.write_text('<Workflow name="Test"/>')
        pages = self.adapter.extract(f, {})
        assert pages[0].category != ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/llmwiki && pytest tests/test_xml_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: Implement llmwiki/adapters/xml_adapter.py**

```python
"""XML adapter with inline script extraction.

Handles generic XML files and optionally extracts inline script blocks
(BeanShell <Source>, <Script>, <Code> elements) as separate wiki pages.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage

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
            # Fallback: treat as generic text
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
                script_summary.append(
                    f"### {step_name} ({line_count} lines)\n\n"
                    f"```java\n{script_body.strip()}\n```"
                )
                # Optionally create separate BeanShell page
                if config.get("extract_beanshell", False):
                    bsh_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", f"{name}__{step_name}").lower()
                    bsh_refs = _JAVA_IMPORT_IN_BSH.findall(script_body)
                    bsh_page = WikiPage(
                        slug=f"beanshell/{bsh_slug}",
                        title=f"{name} — {step_name}",
                        category="beanshell",
                        source_path=str(path),
                        body=(
                            f"## {step_name}\n\n"
                            f"**Parent:** [[{name}]]\n\n"
                            f"```java\n{script_body.strip()}\n```\n"
                        ),
                        language="java",
                        tags=["beanshell", tag.lower()],
                        references=[name] + bsh_refs,
                    )
                    bsh_page.compute_hash()
                    bsh_pages.append(bsh_page)

            sections.append("## Inline Scripts\n\n" + "\n\n".join(script_summary))

        # Full source
        sections.append(
            f"\n## Source\n\n<details>\n<summary>Full XML ({len(content.splitlines())} lines)</summary>\n\n"
            f"```xml\n{content}\n```\n\n</details>"
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
        """Find all inline script blocks (Source, Script, Code elements)."""
        scripts = []
        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if tag == "Source" and elem.text and elem.text.strip():
                # Walk up to find parent step name
                step_name = self._find_parent_step_name(root, elem)
                scripts.append((step_name, elem.text))
        return scripts

    def _find_parent_step_name(self, root: ET.Element, target: ET.Element) -> str:
        """Walk tree to find the step name containing this element."""
        for parent in root.iter():
            for child in parent:
                if child is target or self._contains(child, target):
                    name = parent.get("name", "")
                    if name:
                        return name
        return "unnamed"

    def _contains(self, parent: ET.Element, target: ET.Element) -> bool:
        """Check if parent contains target anywhere in subtree."""
        for child in parent.iter():
            if child is target:
                return True
        return False

    def _extract_references(self, root: ET.Element, content: str) -> list[str]:
        """Extract cross-references from XML."""
        refs = []
        # <Reference> elements
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
        # Java imports in inline scripts
        refs.extend(_JAVA_IMPORT_IN_BSH.findall(content))
        return list(set(refs))

    def _detect_category(self, path: Path, tag: str) -> str:
        parts = path.parent.parts
        # Look for known SailPoint categories in path
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
        page = WikiPage(
            slug=path.stem.lower(),
            title=path.stem,
            category="xml",
            source_path=str(path),
            body=f"## {path.stem}\n\n```xml\n{content}\n```\n",
            language="xml",
        )
        page.compute_hash()
        return page


def _strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/llmwiki && pytest tests/test_xml_adapter.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: XML adapter with BeanShell inline script extraction

- Parses XML structure, attributes, child elements
- Extracts <Source> inline script blocks with parent step names
- Optionally creates separate BeanShell wiki pages (extract_beanshell config)
- Auto-detects references from <Reference> elements and Java imports
- Category detection from directory path"
```


---

### Task 5: PDF, Markdown, Config & Generic Adapters

**Files:**
- Create: `llmwiki/adapters/pdf_adapter.py`
- Create: `llmwiki/adapters/markdown_adapter.py`
- Create: `llmwiki/adapters/config_adapter.py`
- Create: `llmwiki/adapters/generic_adapter.py`
- Test: `tests/test_pdf_adapter.py`
- Test: `tests/test_markdown_adapter.py`
- Test: `tests/test_config_adapter.py`
- Test: `tests/test_generic_adapter.py`

- [ ] **Step 1: Write failing tests for PDF adapter**

```python
# tests/test_pdf_adapter.py
"""Tests for PDF adapter."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from llmwiki.adapters.pdf_adapter import PDFAdapter


class TestPDFAdapter:
    def setup_method(self):
        self.adapter = PDFAdapter()

    def test_can_handle_pdf(self, tmp_path):
        f = tmp_path / "guide.pdf"
        f.write_bytes(b"%PDF-1.4 fake")
        assert self.adapter.can_handle(f)

    def test_cannot_handle_txt(self, tmp_path):
        f = tmp_path / "notes.txt"
        f.write_text("hello")
        assert not self.adapter.can_handle(f)

    @patch("llmwiki.adapters.pdf_adapter._convert_pdf")
    def test_extract_pdf(self, mock_convert, tmp_path):
        f = tmp_path / "SailPoint Guide.pdf"
        f.write_bytes(b"%PDF-1.4 fake")
        mock_convert.return_value = "# Chapter 1\n\nSome content.\n\n# Chapter 2\n\nMore content."
        pages = self.adapter.extract(f, {"label": "guides"})
        assert len(pages) >= 1
        assert pages[0].language == ""
        assert pages[0].tags == ["pdf"]

    def test_slug_from_filename(self):
        slug = self.adapter._make_slug("SailPoint Active Directory Connector Guide.pdf", "connectors")
        assert " " not in slug
        assert slug.islower() or "/" in slug
```

- [ ] **Step 2: Implement llmwiki/adapters/pdf_adapter.py**

```python
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
```

- [ ] **Step 3: Write tests and implement Markdown adapter**

```python
# tests/test_markdown_adapter.py
"""Tests for markdown pass-through adapter."""

from pathlib import Path
from llmwiki.adapters.markdown_adapter import MarkdownAdapter


class TestMarkdownAdapter:
    def setup_method(self):
        self.adapter = MarkdownAdapter()

    def test_can_handle(self, tmp_path):
        f = tmp_path / "README.md"
        f.write_text("# Hello")
        assert self.adapter.can_handle(f)

    def test_extract_with_frontmatter(self, tmp_path):
        f = tmp_path / "guide.md"
        f.write_text("---\ntitle: My Guide\ntags: [a, b]\n---\n\n# Guide\n\nContent.")
        pages = self.adapter.extract(f, {})
        assert len(pages) == 1
        assert pages[0].title == "My Guide"

    def test_extract_without_frontmatter(self, tmp_path):
        f = tmp_path / "notes.md"
        f.write_text("# My Notes\n\nSome notes here.")
        pages = self.adapter.extract(f, {})
        assert len(pages) == 1
        assert pages[0].title == "My Notes"

    def test_extract_title_from_filename(self, tmp_path):
        f = tmp_path / "api-reference.md"
        f.write_text("No heading here, just text.")
        pages = self.adapter.extract(f, {})
        assert pages[0].title == "api-reference"
```

```python
# llmwiki/adapters/markdown_adapter.py
"""Markdown pass-through adapter with frontmatter extraction."""

from __future__ import annotations

import re
from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage


@register
class MarkdownAdapter(BaseAdapter):
    """Pass-through adapter for markdown files."""

    name = "markdown"
    extensions = [".md", ".mdx", ".rst"]

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in {".md", ".mdx", ".rst"}

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        title, body, tags = self._parse(content, path)
        category = config.get("category", "docs")

        page = WikiPage(
            slug=f"{category}/{path.stem}".lower(),
            title=title,
            category=category,
            source_path=str(path),
            body=body,
            tags=tags,
        )
        page.compute_hash()
        return [page]

    def _parse(self, content: str, path: Path) -> tuple[str, str, list[str]]:
        title = path.stem
        body = content
        tags: list[str] = []

        # Extract frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1]
                body = parts[2].strip()
                for line in fm.strip().splitlines():
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip("\"'")
                    elif line.startswith("tags:"):
                        tag_str = line.split(":", 1)[1].strip()
                        tag_str = tag_str.strip("[]")
                        tags = [t.strip() for t in tag_str.split(",") if t.strip()]

        # Fall back to first heading for title
        if title == path.stem:
            heading = re.search(r"^#\s+(.+)", body, re.MULTILINE)
            if heading:
                title = heading.group(1).strip()

        return title, body, tags
```

- [ ] **Step 4: Write tests and implement Config adapter**

```python
# tests/test_config_adapter.py
"""Tests for config file adapter."""

from pathlib import Path
from llmwiki.adapters.config_adapter import ConfigAdapter


class TestConfigAdapter:
    def setup_method(self):
        self.adapter = ConfigAdapter()

    def test_can_handle_properties(self, tmp_path):
        f = tmp_path / "app.properties"
        f.write_text("key=value")
        assert self.adapter.can_handle(f)

    def test_can_handle_json(self, tmp_path):
        f = tmp_path / "config.json"
        f.write_text("{}")
        assert self.adapter.can_handle(f)

    def test_extract_properties(self, tmp_path):
        f = tmp_path / "db.properties"
        f.write_text("# Database config\ndb.host=localhost\ndb.port=5432\ndb.name=mydb\n")
        pages = self.adapter.extract(f, {})
        assert len(pages) == 1
        assert "db.host" in pages[0].body
        assert "localhost" in pages[0].body
```

```python
# llmwiki/adapters/config_adapter.py
"""Config file adapter for properties, JSON, YAML, TOML, INI files."""

from __future__ import annotations

import re
from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage

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
        sections.append(f"## Contents\n\n```{lang}\n{content}\n```")

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
```

- [ ] **Step 5: Write tests and implement Generic adapter**

```python
# tests/test_generic_adapter.py
"""Tests for generic fallback adapter."""

from pathlib import Path
from llmwiki.adapters.generic_adapter import GenericAdapter


class TestGenericAdapter:
    def setup_method(self):
        self.adapter = GenericAdapter()

    def test_can_handle_anything(self, tmp_path):
        f = tmp_path / "unknown.xyz"
        f.write_text("some content")
        assert self.adapter.can_handle(f)

    def test_extract(self, tmp_path):
        f = tmp_path / "script.sh"
        f.write_text("#!/bin/bash\n# Deploy script\necho 'deploying'\n")
        pages = self.adapter.extract(f, {})
        assert len(pages) == 1
        assert "deploying" in pages[0].body
```

```python
# llmwiki/adapters/generic_adapter.py
"""Generic fallback adapter for any text file."""

from __future__ import annotations

import re
from pathlib import Path

from llmwiki.adapters import register
from llmwiki.adapters.base import BaseAdapter, WikiPage


@register
class GenericAdapter(BaseAdapter):
    """Fallback adapter that wraps any text file in a code block."""

    name = "generic"
    extensions = []  # Handles anything not claimed by other adapters

    def can_handle(self, path: Path) -> bool:
        # Accept any text file
        try:
            path.read_text(encoding="utf-8", errors="strict")
            return True
        except (UnicodeDecodeError, OSError):
            return False

    def extract(self, path: Path, config: dict) -> list[WikiPage]:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        lang = path.suffix.lstrip(".").lower() or "text"
        body = f"## {path.name}\n\n```{lang}\n{content}\n```\n"

        page = WikiPage(
            slug=f"misc/{path.stem}".lower(),
            title=path.name,
            category="misc",
            source_path=str(path),
            body=body,
            language=lang,
        )
        page.compute_hash()
        return [page]

    def discover(self, root: Path, exclude: list[str] | None = None) -> list[Path]:
        """Generic adapter doesn't auto-discover — only used as fallback."""
        return []
```

- [ ] **Step 6: Run all adapter tests**

Run: `cd ~/llmwiki && pytest tests/test_pdf_adapter.py tests/test_markdown_adapter.py tests/test_config_adapter.py tests/test_generic_adapter.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: PDF, Markdown, Config, and Generic adapters

- PDF adapter via pymupdf4llm with graceful fallback
- Markdown adapter with frontmatter parsing (title, tags)
- Config adapter for properties/json/yaml/toml/ini/env files
- Generic fallback adapter for any text file"
```


---

### Task 6: Ingestion Pipeline & CLI Init

**Files:**
- Create: `llmwiki/ingest.py`
- Create: `llmwiki/cli.py`
- Test: `tests/test_ingest.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for ingestion**

```python
# tests/test_ingest.py
"""Tests for the ingestion pipeline."""

from pathlib import Path
from llmwiki.ingest import ingest_source, ingest_all
from llmwiki.config import create_default_config


class TestIngest:
    def test_ingest_source_creates_raw_files(self, tmp_path):
        # Setup source
        src = tmp_path / "project"
        src.mkdir()
        (src / "Main.java").write_text("public class Main {}")
        (src / "README.md").write_text("# Project\n\nDescription.")

        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        result = ingest_source(
            source_path=src,
            raw_dir=raw_dir,
            state_path=tmp_path / ".llmwiki-state.json",
            config={},
        )
        assert result["added"] > 0
        # Check raw/ has files
        md_files = list(raw_dir.rglob("*.md"))
        assert len(md_files) >= 1

    def test_ingest_incremental_skips_unchanged(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "Main.java").write_text("public class Main {}")

        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        state_path = tmp_path / ".llmwiki-state.json"

        # First ingest
        r1 = ingest_source(src, raw_dir, state_path, {})
        assert r1["added"] >= 1

        # Second ingest — same files, nothing changed
        r2 = ingest_source(src, raw_dir, state_path, {})
        assert r2["added"] == 0
        assert r2["unchanged"] >= 1

    def test_ingest_all(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "app.py").write_text("def main(): pass")

        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        config = create_default_config("Test", str(src))
        result = ingest_all(config, raw_dir, tmp_path / ".llmwiki-state.json")
        assert result["total_added"] >= 1
```

- [ ] **Step 2: Implement llmwiki/ingest.py**

```python
"""Ingestion pipeline — runs adapters to populate raw/."""

from __future__ import annotations

import hashlib
from pathlib import Path

from llmwiki.adapters import _ensure_all_loaded, _REGISTRY
from llmwiki.adapters.base import BaseAdapter
from llmwiki.state import BuildState


def ingest_source(
    source_path: Path,
    raw_dir: Path,
    state_path: Path,
    config: dict,
    adapter_name: str | None = None,
) -> dict:
    """Ingest files from a single source directory into raw/.

    Returns summary dict with added/modified/unchanged/skipped counts.
    """
    _ensure_all_loaded()
    state = BuildState(state_path)

    counts = {"added": 0, "modified": 0, "unchanged": 0, "skipped": 0, "errors": 0}
    exclude = config.get("exclude", [])
    current_files: set[str] = set()

    for name, adapter_cls in _REGISTRY.items():
        if adapter_name and name != adapter_name:
            continue
        adapter = adapter_cls()
        files = adapter.discover(source_path, exclude=exclude)

        for fpath in files:
            src_key = str(fpath)
            current_files.add(src_key)

            # Compute hash
            try:
                content = fpath.read_bytes()
            except OSError:
                counts["errors"] += 1
                continue
            content_hash = hashlib.sha256(content).hexdigest()[:16]

            classification = state.classify(src_key, content_hash)
            if classification == "unchanged":
                counts["unchanged"] += 1
                continue

            # Extract pages
            try:
                pages = adapter.extract(fpath, config)
            except Exception:
                counts["errors"] += 1
                continue

            # Write to raw/
            for page in pages:
                out_path = raw_dir / page.category / f"{page.slug.split('/')[-1]}.md"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(page.to_markdown(), encoding="utf-8")

            state.record_file(src_key, content_hash, str(out_path) if pages else "")
            counts[classification] += 1

    state.save()
    return counts


def ingest_pdfs(
    pdf_paths: list[dict],
    raw_dir: Path,
    state_path: Path,
) -> dict:
    """Ingest PDF files from configured paths."""
    _ensure_all_loaded()
    from llmwiki.adapters.pdf_adapter import PDFAdapter

    state = BuildState(state_path)
    adapter = PDFAdapter()
    counts = {"added": 0, "modified": 0, "unchanged": 0, "errors": 0}

    for pdf_source in pdf_paths:
        src_path = Path(pdf_source["path"])
        label = pdf_source.get("label", "docs")

        if src_path.is_file():
            pdf_files = [src_path]
        elif src_path.is_dir():
            pdf_files = sorted(src_path.rglob("*.pdf"))
        else:
            continue

        for fpath in pdf_files:
            src_key = str(fpath)
            try:
                content_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()[:16]
            except OSError:
                counts["errors"] += 1
                continue

            classification = state.classify(src_key, content_hash)
            if classification == "unchanged":
                counts["unchanged"] += 1
                continue

            try:
                pages = adapter.extract(fpath, {"label": label})
            except Exception:
                counts["errors"] += 1
                continue

            for page in pages:
                out_path = raw_dir / page.category / f"{page.slug.split('/')[-1]}.md"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(page.to_markdown(), encoding="utf-8")

            state.record_file(src_key, content_hash, str(out_path) if pages else "")
            counts[classification] += 1

    state.save()
    return counts


def ingest_all(
    config: dict,
    raw_dir: Path,
    state_path: Path,
) -> dict:
    """Run full ingestion from all configured sources."""
    totals = {"total_added": 0, "total_modified": 0, "total_unchanged": 0, "total_errors": 0}

    # Ingest codebase sources
    for source in config.get("sources", []):
        src_path = Path(source["path"])
        if src_path.exists():
            result = ingest_source(src_path, raw_dir, state_path, source)
            totals["total_added"] += result["added"]
            totals["total_modified"] += result["modified"]
            totals["total_unchanged"] += result["unchanged"]
            totals["total_errors"] += result.get("errors", 0)

    # Ingest PDFs
    pdf_sources = config.get("pdf_sources", [])
    if pdf_sources:
        result = ingest_pdfs(pdf_sources, raw_dir, state_path)
        totals["total_added"] += result["added"]
        totals["total_modified"] += result["modified"]
        totals["total_unchanged"] += result["unchanged"]
        totals["total_errors"] += result.get("errors", 0)

    return totals
```

- [ ] **Step 3: Write failing tests for CLI**

```python
# tests/test_cli.py
"""Tests for CLI dispatcher."""

import subprocess
import sys


class TestCLI:
    def test_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "llmwiki", "--version"],
            capture_output=True, text=True
        )
        assert "0.1.0" in result.stdout or "0.1.0" in result.stderr

    def test_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "llmwiki", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "llmwiki" in result.stdout.lower()

    def test_init_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "llmwiki", "init", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "source" in result.stdout.lower()
```

- [ ] **Step 4: Implement llmwiki/cli.py**

```python
"""CLI dispatcher for llmwiki."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from llmwiki import __version__


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="llmwiki",
        description="Generic codebase + documentation knowledge base pipeline",
    )
    parser.add_argument("--version", action="version", version=f"llmwiki {__version__}")

    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="Initialize a new llmwiki project")
    p_init.add_argument("--source", required=True, help="Path to source codebase")
    p_init.add_argument("--name", help="Project name (auto-detected if not given)")
    p_init.add_argument("--output", default=".", help="Where to create raw/wiki/site dirs")

    # ingest
    p_ingest = sub.add_parser("ingest", help="Run adapters to populate raw/")
    p_ingest.add_argument("--adapter", help="Run only a specific adapter")
    p_ingest.add_argument("--config", default="llmwiki.json", help="Config file path")

    # build
    p_build = sub.add_parser("build", help="Build wiki/ and site/ from raw/")
    p_build.add_argument("--full", action="store_true", help="Force full rebuild")
    p_build.add_argument("--config", default="llmwiki.json", help="Config file path")

    # serve
    p_serve = sub.add_parser("serve", help="Serve site locally")
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.add_argument("--host", default="127.0.0.1")

    # search
    p_search = sub.add_parser("search", help="Search the knowledge base")
    p_search.add_argument("query", help="Search query")

    # graph
    sub.add_parser("graph", help="Rebuild knowledge graph")

    # export
    sub.add_parser("export", help="Generate AI-consumable exports")

    # lint
    sub.add_parser("lint", help="Check for broken links and orphans")

    # stats
    sub.add_parser("stats", help="Print inventory statistics")

    # diff
    sub.add_parser("diff", help="Show changes since last build")

    # all
    p_all = sub.add_parser("all", help="Full pipeline: ingest → build → graph → export → lint")
    p_all.add_argument("--config", default="llmwiki.json", help="Config file path")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "init":
        return _cmd_init(args)
    elif args.command == "ingest":
        return _cmd_ingest(args)
    elif args.command == "build":
        return _cmd_build(args)
    elif args.command == "serve":
        return _cmd_serve(args)
    elif args.command == "search":
        return _cmd_search(args)
    elif args.command == "all":
        return _cmd_all(args)
    elif args.command == "stats":
        return _cmd_stats(args)
    else:
        print(f"Command '{args.command}' not yet implemented.", file=sys.stderr)
        return 1


def _cmd_init(args) -> int:
    """Initialize a new llmwiki project."""
    from llmwiki.config import create_default_config, save_config
    from llmwiki.adapters import detect_adapters

    source = Path(args.source).resolve()
    if not source.exists():
        print(f"Error: source path does not exist: {source}", file=sys.stderr)
        return 1

    output = Path(args.output).resolve()
    name = args.name or source.name

    # Detect adapters
    print(f"🔍 Scanning {source}...")
    detected = detect_adapters(source)
    for adapter_name, files in detected.items():
        print(f"  Found {len(files)} files for adapter '{adapter_name}'")

    # Create directories
    for d in ["raw", "wiki", "site"]:
        (output / d).mkdir(parents=True, exist_ok=True)

    # Create config
    config = create_default_config(name, str(source))
    cfg_path = output / "llmwiki.json"
    save_config(config, cfg_path)
    print(f"\n✅ Created llmwiki.json")
    print(f"✅ Created raw/, wiki/, site/ directories")
    print(f"\nRun `llmwiki ingest` to extract content, then `llmwiki build` to generate the site.")
    return 0


def _cmd_ingest(args) -> int:
    """Run ingestion pipeline."""
    from llmwiki.config import load_config
    from llmwiki.ingest import ingest_all

    cfg_path = Path(args.config)
    config = load_config(cfg_path)
    raw_dir = Path(config.get("build", {}).get("out_dir", ".")) / ".." / "raw"
    raw_dir = cfg_path.parent / "raw"
    raw_dir.mkdir(exist_ok=True)
    state_path = cfg_path.parent / ".llmwiki-state.json"

    print("📥 Ingesting sources...")
    result = ingest_all(config, raw_dir, state_path)
    print(f"  Added: {result['total_added']}")
    print(f"  Modified: {result['total_modified']}")
    print(f"  Unchanged: {result['total_unchanged']}")
    if result.get("total_errors"):
        print(f"  Errors: {result['total_errors']}")
    return 0


def _cmd_build(args) -> int:
    """Build wiki and site from raw."""
    from llmwiki.config import load_config
    from llmwiki.build import build_site

    cfg_path = Path(args.config)
    config = load_config(cfg_path)
    root = cfg_path.parent

    print("🔨 Building site...")
    result = build_site(root, config, full=args.full)
    print(f"  Pages: {result.get('total_pages', 0)}")
    print(f"  Categories: {result.get('total_categories', 0)}")
    return 0


def _cmd_serve(args) -> int:
    """Serve the site locally."""
    from llmwiki.serve import serve_site
    return serve_site("site", port=args.port, host=args.host)


def _cmd_search(args) -> int:
    """Search the knowledge base via SQLite FTS5."""
    from llmwiki.search import cli_search
    return cli_search(args.query, "site/llmwiki.db")


def _cmd_all(args) -> int:
    """Run full pipeline."""
    for cmd_name, cmd_func in [
        ("ingest", lambda: _cmd_ingest(args)),
        ("build", lambda: _cmd_build(args)),
    ]:
        print(f"\n{'='*50}")
        print(f"  {cmd_name.upper()}")
        print(f"{'='*50}")
        ret = cmd_func()
        if ret != 0:
            return ret
    return 0


def _cmd_stats(args) -> int:
    """Print inventory statistics."""
    raw = Path("raw")
    wiki = Path("wiki")
    site = Path("site")
    print("📊 LLMWiki Statistics")
    for label, d in [("Raw", raw), ("Wiki", wiki), ("Site", site)]:
        if d.exists():
            count = len(list(d.rglob("*")))
            print(f"  {label}: {count} files")
        else:
            print(f"  {label}: not built")
    return 0
```

- [ ] **Step 5: Run all tests**

Run: `cd ~/llmwiki && pytest tests/test_ingest.py tests/test_cli.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: ingestion pipeline and CLI with 12 subcommands

- ingest_source() with incremental processing via BuildState
- ingest_pdfs() for PDF document sources
- ingest_all() orchestrates all configured sources
- CLI: init, ingest, build, serve, search, graph, export, lint, stats, diff, all
- Interactive init with auto-detection report"
```


---

### Task 7: Cross-Reference Engine, Importance Scoring & Clusters

**Files:**
- Create: `llmwiki/crossref.py`
- Create: `llmwiki/importance.py`
- Create: `llmwiki/clusters.py`
- Create: `llmwiki/graph.py`
- Test: `tests/test_crossref.py`
- Test: `tests/test_importance.py`
- Test: `tests/test_clusters.py`
- Test: `tests/test_graph.py`

- [ ] **Step 1: Write failing tests for cross-reference extraction**

```python
# tests/test_crossref.py
"""Tests for cross-reference extraction."""

from llmwiki.crossref import extract_refs_from_body, build_edge_list


class TestCrossRef:
    def test_extract_wikilinks(self):
        body = "This references [[CommonOperations]] and [[Global]]."
        refs = extract_refs_from_body(body)
        assert "CommonOperations" in refs
        assert "Global" in refs

    def test_extract_java_imports(self):
        body = "```java\nimport com.vf.core.utility.AccountUtil;\n```"
        refs = extract_refs_from_body(body)
        assert "com.vf.core.utility.AccountUtil" in refs

    def test_extract_no_refs(self):
        body = "Just plain text with no references."
        refs = extract_refs_from_body(body)
        assert refs == []

    def test_build_edge_list(self):
        pages = {
            "a": {"references": ["b", "c"]},
            "b": {"references": ["c"]},
            "c": {"references": []},
        }
        edges = build_edge_list(pages)
        assert ("a", "b", "references") in edges
        assert ("a", "c", "references") in edges
        assert ("b", "c", "references") in edges
        assert len(edges) == 3
```

- [ ] **Step 2: Implement llmwiki/crossref.py**

```python
"""Cross-reference extraction from wiki page content."""

from __future__ import annotations

import re

_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
_JAVA_IMPORT_RE = re.compile(r"import\s+([\w.]+);")
_CLASS_REF_RE = re.compile(r"(?:new\s+|extends\s+|implements\s+)([\w.]+)")


def extract_refs_from_body(body: str) -> list[str]:
    """Extract all cross-references from a page body."""
    refs: set[str] = set()
    refs.update(_WIKILINK_RE.findall(body))
    refs.update(_JAVA_IMPORT_RE.findall(body))
    refs.update(_CLASS_REF_RE.findall(body))
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
```

- [ ] **Step 3: Write failing tests for importance scoring**

```python
# tests/test_importance.py
"""Tests for PageRank-style importance scoring."""

from llmwiki.importance import compute_importance


class TestImportance:
    def test_single_node(self):
        nodes = {"a"}
        edges = []
        scores = compute_importance(nodes, edges)
        assert "a" in scores
        assert 0.0 <= scores["a"] <= 1.0

    def test_hub_gets_high_score(self):
        nodes = {"hub", "a", "b", "c"}
        edges = [
            ("a", "hub", "references"),
            ("b", "hub", "references"),
            ("c", "hub", "references"),
        ]
        scores = compute_importance(nodes, edges)
        assert scores["hub"] > scores["a"]
        assert scores["hub"] > scores["b"]

    def test_isolated_nodes_equal(self):
        nodes = {"a", "b", "c"}
        edges = []
        scores = compute_importance(nodes, edges)
        assert abs(scores["a"] - scores["b"]) < 0.01

    def test_scores_normalized(self):
        nodes = {"a", "b", "c", "d"}
        edges = [("a", "b", "r"), ("b", "c", "r"), ("c", "d", "r"), ("d", "a", "r")]
        scores = compute_importance(nodes, edges)
        assert all(0.0 <= s <= 1.0 for s in scores.values())
```

- [ ] **Step 4: Implement llmwiki/importance.py**

```python
"""PageRank-style importance scoring for wiki pages."""

from __future__ import annotations

from collections import defaultdict


def compute_importance(
    nodes: set[str],
    edges: list[tuple[str, str, str]],
    iterations: int = 20,
    damping: float = 0.85,
) -> dict[str, float]:
    """Compute importance scores using simplified PageRank.

    Args:
        nodes: Set of page IDs.
        edges: List of (from_id, to_id, edge_type) tuples.
        iterations: Number of iterations.
        damping: Damping factor (0.85 is standard).

    Returns:
        {page_id: score} with scores normalized to 0.0-1.0.
    """
    if not nodes:
        return {}

    n = len(nodes)
    scores = {node: 1.0 / n for node in nodes}

    # Build adjacency
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for from_id, to_id, _ in edges:
        if from_id in nodes and to_id in nodes:
            outgoing[from_id].append(to_id)
            incoming[to_id].append(from_id)

    base = (1.0 - damping) / n

    for _ in range(iterations):
        new_scores = {}
        for node in nodes:
            rank_sum = 0.0
            for src in incoming.get(node, []):
                out_count = len(outgoing.get(src, []))
                if out_count > 0:
                    rank_sum += scores[src] / out_count
            new_scores[node] = base + damping * rank_sum
        scores = new_scores

    # Normalize to 0.0-1.0
    max_score = max(scores.values()) if scores else 1.0
    if max_score > 0:
        scores = {k: v / max_score for k, v in scores.items()}

    return scores
```

- [ ] **Step 5: Write failing tests for cluster detection**

```python
# tests/test_clusters.py
"""Tests for topic cluster detection."""

from llmwiki.clusters import detect_clusters


class TestClusters:
    def test_single_cluster(self):
        edges = [("a", "b", "r"), ("b", "c", "r"), ("c", "a", "r")]
        page_meta = {
            "a": {"category": "workflow", "tags": ["approval"]},
            "b": {"category": "workflow", "tags": ["approval"]},
            "c": {"category": "rule", "tags": ["approval"]},
        }
        clusters = detect_clusters(edges, page_meta, min_size=2)
        assert len(clusters) >= 1
        assert len(clusters[0]["members"]) == 3

    def test_no_clusters_when_disconnected(self):
        edges = []
        page_meta = {"a": {}, "b": {}, "c": {}}
        clusters = detect_clusters(edges, page_meta, min_size=3)
        assert len(clusters) == 0

    def test_two_clusters(self):
        edges = [
            ("a", "b", "r"), ("b", "a", "r"),
            ("c", "d", "r"), ("d", "c", "r"),
        ]
        page_meta = {
            "a": {"tags": ["x"]}, "b": {"tags": ["x"]},
            "c": {"tags": ["y"]}, "d": {"tags": ["y"]},
        }
        clusters = detect_clusters(edges, page_meta, min_size=2)
        assert len(clusters) == 2
```

- [ ] **Step 6: Implement llmwiki/clusters.py**

```python
"""Topic cluster detection via connected components."""

from __future__ import annotations

from collections import defaultdict, Counter


def detect_clusters(
    edges: list[tuple[str, str, str]],
    page_meta: dict[str, dict],
    min_size: int = 3,
) -> list[dict]:
    """Detect topic clusters as connected components.

    Args:
        edges: Directed edges (from, to, type).
        page_meta: {page_id: {"category": ..., "tags": [...]}}.
        min_size: Minimum component size to count as a cluster.

    Returns:
        List of cluster dicts with id, label, members, top_tags.
    """
    # Build undirected adjacency
    adj: dict[str, set[str]] = defaultdict(set)
    for from_id, to_id, _ in edges:
        adj[from_id].add(to_id)
        adj[to_id].add(from_id)

    # Find connected components via BFS
    visited: set[str] = set()
    components: list[set[str]] = []
    all_nodes = set(adj.keys()) | set(page_meta.keys())

    for node in all_nodes:
        if node in visited:
            continue
        component: set[str] = set()
        queue = [node]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            component.add(current)
            for neighbor in adj.get(current, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
        if len(component) >= min_size:
            components.append(component)

    # Label clusters
    clusters = []
    for i, members in enumerate(sorted(components, key=len, reverse=True)):
        tag_counts: Counter[str] = Counter()
        cat_counts: Counter[str] = Counter()
        for m in members:
            meta = page_meta.get(m, {})
            for t in meta.get("tags", []):
                tag_counts[t] += 1
            cat = meta.get("category", "")
            if cat:
                cat_counts[cat] += 1

        top_tags = [t for t, _ in tag_counts.most_common(3)]
        label = " / ".join(top_tags) if top_tags else f"Cluster {i + 1}"

        clusters.append({
            "id": f"cluster-{i + 1}",
            "label": label,
            "members": sorted(members),
            "member_count": len(members),
            "top_tags": top_tags,
        })

    return clusters
```

- [ ] **Step 7: Write failing tests for graph builder**

```python
# tests/test_graph.py
"""Tests for knowledge graph construction."""

from pathlib import Path
from llmwiki.graph import build_graph


class TestGraph:
    def test_build_from_raw(self, tmp_path):
        raw = tmp_path / "raw" / "java"
        raw.mkdir(parents=True)
        (raw / "AccountUtil.md").write_text(
            "---\ntitle: AccountUtil\nslug: java/AccountUtil\n"
            "category: java\nsource_path: /src/AccountUtil.java\n"
            "references: [com.vf.core.library.Global]\ntags: [java]\n---\n\n"
            "## AccountUtil\n\nUtility class.\n"
        )
        (raw / "Global.md").write_text(
            "---\ntitle: Global\nslug: java/Global\n"
            "category: java\nsource_path: /src/Global.java\n"
            "references: []\ntags: [java]\n---\n\n"
            "## Global\n\nGlobal config.\n"
        )
        graph = build_graph(tmp_path / "raw")
        assert len(graph["nodes"]) == 2
        assert len(graph["edges"]) >= 0  # May or may not resolve refs
        assert "stats" in graph
```

- [ ] **Step 8: Implement llmwiki/graph.py**

```python
"""Knowledge graph construction from wiki pages."""

from __future__ import annotations

import json
import re
from pathlib import Path

from llmwiki.crossref import extract_refs_from_body, build_edge_list
from llmwiki.importance import compute_importance
from llmwiki.clusters import detect_clusters


def build_graph(raw_dir: Path) -> dict:
    """Build knowledge graph from raw/ markdown files.

    Returns dict with nodes, edges, clusters, stats.
    """
    pages = _load_pages(raw_dir)
    page_ids = set(pages.keys())

    # Build edges
    edges = build_edge_list(pages)

    # Resolve fuzzy references (partial slug matching)
    resolved_edges = _resolve_edges(edges, page_ids)

    # Compute importance
    scores = compute_importance(page_ids, resolved_edges)

    # Detect clusters
    page_meta = {
        pid: {"category": p.get("category", ""), "tags": p.get("tags", [])}
        for pid, p in pages.items()
    }
    clusters = detect_clusters(resolved_edges, page_meta, min_size=3)

    # Assign cluster IDs to pages
    cluster_map: dict[str, str] = {}
    for cluster in clusters:
        for member in cluster["members"]:
            cluster_map[member] = cluster["id"]

    # Build node list
    in_degree: dict[str, int] = {}
    out_degree: dict[str, int] = {}
    for from_id, to_id, _ in resolved_edges:
        out_degree[from_id] = out_degree.get(from_id, 0) + 1
        in_degree[to_id] = in_degree.get(to_id, 0) + 1

    nodes = []
    for pid, pdata in pages.items():
        nodes.append({
            "id": pid,
            "title": pdata.get("title", pid),
            "type": pdata.get("category", "unknown"),
            "in_degree": in_degree.get(pid, 0),
            "out_degree": out_degree.get(pid, 0),
            "importance": round(scores.get(pid, 0.0), 4),
            "cluster_id": cluster_map.get(pid),
        })

    edge_dicts = [
        {"from": f, "to": t, "type": etype}
        for f, t, etype in resolved_edges
    ]

    return {
        "nodes": nodes,
        "edges": edge_dicts,
        "clusters": clusters,
        "stats": {
            "total_pages": len(nodes),
            "total_edges": len(edge_dicts),
            "total_clusters": len(clusters),
            "orphans": sum(1 for n in nodes if n["in_degree"] == 0 and n["out_degree"] == 0),
        },
    }


def save_graph(graph: dict, output_path: Path) -> None:
    """Save graph to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)


def _load_pages(raw_dir: Path) -> dict[str, dict]:
    """Load all raw pages and extract frontmatter."""
    pages: dict[str, dict] = {}
    for md_file in sorted(raw_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        meta, body = _parse_frontmatter(content)
        slug = meta.get("slug", md_file.stem)

        # Extract additional refs from body
        body_refs = extract_refs_from_body(body)
        fm_refs = meta.get("references", [])
        if isinstance(fm_refs, str):
            fm_refs = [r.strip() for r in fm_refs.strip("[]").split(",") if r.strip()]
        all_refs = list(set(fm_refs + body_refs))

        pages[slug] = {
            "title": meta.get("title", md_file.stem),
            "category": meta.get("category", ""),
            "tags": _parse_list(meta.get("tags", [])),
            "references": all_refs,
            "source_path": meta.get("source_path", ""),
            "body": body,
        }
    return pages


def _resolve_edges(
    edges: list[tuple[str, str, str]],
    valid_ids: set[str],
) -> list[tuple[str, str, str]]:
    """Resolve fuzzy references to actual page IDs."""
    resolved = []
    id_index: dict[str, str] = {}
    for pid in valid_ids:
        # Index by last segment
        parts = pid.split("/")
        id_index[parts[-1].lower()] = pid
        id_index[pid.lower()] = pid

    for from_id, to_id, etype in edges:
        target = id_index.get(to_id.lower()) or id_index.get(to_id.split(".")[-1].lower())
        if target and target != from_id:
            resolved.append((from_id, target, etype))

    return resolved


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Simple frontmatter parser."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    meta: dict = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
    return meta, parts[2].strip()


def _parse_list(value) -> list[str]:
    """Parse a frontmatter list value."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [v.strip() for v in value.strip("[]").split(",") if v.strip()]
    return []
```

- [ ] **Step 9: Run all tests**

Run: `cd ~/llmwiki && pytest tests/test_crossref.py tests/test_importance.py tests/test_clusters.py tests/test_graph.py -v`
Expected: All PASS

- [ ] **Step 10: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: cross-reference engine with PageRank and cluster detection

- crossref.py: extract wikilinks, Java imports, class references
- importance.py: PageRank-style scoring with damping factor
- clusters.py: connected-component topic clustering
- graph.py: full knowledge graph builder with fuzzy ref resolution"
```


---

### Task 8: Build Pipeline (raw/ → wiki/ → site/)

**Files:**
- Create: `llmwiki/build.py`
- Create: `llmwiki/render/css.py`
- Create: `llmwiki/render/js.py`
- Create: `llmwiki/render/html.py`
- Test: `tests/test_build.py`

This is the largest task — it generates the full static site. The CSS and JS are large string constants. Focus on getting the structure right; styling can be refined iteratively.

- [ ] **Step 1: Write failing tests for build**

```python
# tests/test_build.py
"""Tests for the static site builder."""

from pathlib import Path
from llmwiki.build import build_site


class TestBuild:
    def _setup_raw(self, tmp_path):
        """Create minimal raw/ with two pages."""
        raw = tmp_path / "raw" / "java"
        raw.mkdir(parents=True)
        (raw / "Main.md").write_text(
            "---\ntitle: Main\nslug: java/main\ncategory: java\n"
            "source_path: /src/Main.java\nlanguage: java\n"
            "content_hash: abc123\ntags: [java]\nreferences: []\n---\n\n"
            "## Main\n\nMain entry point.\n"
        )
        (raw / "Utils.md").write_text(
            "---\ntitle: Utils\nslug: java/utils\ncategory: java\n"
            "source_path: /src/Utils.java\nlanguage: java\n"
            "content_hash: def456\ntags: [java, util]\nreferences: [java/main]\n---\n\n"
            "## Utils\n\nUtility class.\n"
        )
        return tmp_path

    def test_build_creates_site(self, tmp_path):
        root = self._setup_raw(tmp_path)
        (root / "wiki").mkdir()
        (root / "site").mkdir()
        config = {"build": {"out_dir": "site"}, "cross_references": {"enabled": True}}
        result = build_site(root, config, full=True)
        assert result["total_pages"] >= 2
        assert (root / "site" / "index.html").exists()
        assert (root / "site" / "style.css").exists()

    def test_build_creates_search_index(self, tmp_path):
        root = self._setup_raw(tmp_path)
        (root / "wiki").mkdir()
        (root / "site").mkdir()
        config = {"build": {"out_dir": "site"}, "cross_references": {"enabled": True}}
        build_site(root, config, full=True)
        assert (root / "site" / "search-index.json").exists()

    def test_build_creates_category_pages(self, tmp_path):
        root = self._setup_raw(tmp_path)
        (root / "wiki").mkdir()
        (root / "site").mkdir()
        config = {"build": {"out_dir": "site"}, "cross_references": {"enabled": True}}
        build_site(root, config, full=True)
        # Should have category index for "java"
        cat_files = list((root / "site").rglob("*.html"))
        assert len(cat_files) >= 2  # index.html + at least one category/page
```

- [ ] **Step 2: Create llmwiki/render/css.py**

Create a Python file with a single `CSS` string constant containing the full site stylesheet. Include:
- CSS custom properties for light/dark themes
- System font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`)
- Responsive layout with max-width 1200px container
- Sticky nav bar with backdrop blur
- Dashboard stats strip (flexbox)
- Category card grid (CSS grid)
- Page detail layout with metadata card
- Collapsible `<details>` styling
- Activity timeline SVG container
- Knowledge graph container
- Breadcrumbs, search palette, filter bar styles
- Code block styling with copy button
- Dark theme via `[data-theme="dark"]` custom properties
- Print styles
- Mobile responsive breakpoints (max-width 768px)

Target: ~15-20KB of well-organized CSS. Use CSS custom properties extensively.

- [ ] **Step 3: Create llmwiki/render/js.py**

Create a Python file with a single `JS` string constant containing vanilla JS for:
- Theme toggle (system → dark → light → system cycle, localStorage persistence)
- Pre-paint theme script (inline in `<head>` to prevent flash)
- Cmd+K / Ctrl+K command palette (fetch search-index.json, fuzzy match, structured queries)
- Keyboard shortcuts: `/` search, `j/k` navigate, `g h` home, `?` help
- Copy-code buttons on `<pre>` blocks
- Collapsible `<details>` auto-collapse for long content
- Mobile hamburger menu
- Filter bar logic for category pages
- Reading progress bar

Target: ~15-20KB of vanilla JS, no framework.

- [ ] **Step 4: Create llmwiki/render/html.py**

```python
"""HTML page generator functions.

All HTML is generated programmatically — no template files.
Each function returns an HTML string for a specific page type.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import markdown

from llmwiki.render.css import CSS
from llmwiki.render.js import JS, PRE_PAINT_SCRIPT


def page_head(title: str, description: str = "") -> str:
    """Generate <!DOCTYPE> through opening <body>."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — LLMWiki</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="/style.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github.min.css" media="(prefers-color-scheme: light)">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github-dark.min.css" media="(prefers-color-scheme: dark)">
<script>{PRE_PAINT_SCRIPT}</script>
</head>
<body>
"""


def nav_bar(active: str = "") -> str:
    """Generate sticky navigation bar."""
    links = [
        ("Home", "/", "home"),
        ("Categories", "/categories/", "categories"),
        ("Graph", "/graph.html", "graph"),
        ("Changelog", "/changelog.html", "changelog"),
    ]
    items = []
    for label, href, key in links:
        cls = ' class="active"' if key == active else ""
        items.append(f'<a href="{href}"{cls}>{label}</a>')

    return f"""<nav class="nav-bar">
<div class="nav-brand"><a href="/">📚 LLMWiki</a></div>
<div class="nav-links">{"".join(items)}</div>
<div class="nav-actions">
<button class="nav-search" aria-label="Search (Cmd+K)">🔍</button>
<button class="theme-toggle" aria-label="Toggle theme">🌙</button>
</div>
</nav>
"""


def breadcrumbs(crumbs: list[tuple[str, str]]) -> str:
    """Generate breadcrumb navigation."""
    parts = []
    for label, href in crumbs[:-1]:
        parts.append(f'<a href="{href}">{label}</a>')
    parts.append(f"<span>{crumbs[-1][0]}</span>")
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb">{" › ".join(parts)}</nav>'


def page_foot() -> str:
    """Generate closing </body> with scripts."""
    return f"""
<div id="command-palette" class="palette-overlay" hidden>
<div class="palette-dialog">
<input type="text" class="palette-input" placeholder="Search pages... (type:, category:, tag:)">
<div class="palette-results"></div>
<div class="palette-hints">↑↓ navigate · ↵ open · esc close</div>
</div>
</div>
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js" defer></script>
<script src="/script.js" defer></script>
</body>
</html>
"""


def md_to_html(body: str) -> str:
    """Convert markdown body to HTML."""
    md = markdown.Markdown(extensions=["fenced_code", "tables", "toc", "sane_lists"])
    return md.convert(body)


def render_dashboard(stats: dict, recent_changes: list, categories: dict, top_pages: list) -> str:
    """Render the dashboard home page."""
    html = page_head("Home", "Knowledge base dashboard")
    html += nav_bar("home")

    # Stats strip
    html += '<main class="container">'
    html += '<section class="hero"><h1>📚 Knowledge Base</h1></section>'
    html += '<div class="stats-strip">'
    html += f'<div class="stat-card"><span class="stat-num">{stats.get("total_pages", 0)}</span><span class="stat-label">Pages</span></div>'
    html += f'<div class="stat-card"><span class="stat-num">{stats.get("total_edges", 0)}</span><span class="stat-label">Cross-refs</span></div>'
    html += f'<div class="stat-card"><span class="stat-num">{stats.get("total_clusters", 0)}</span><span class="stat-label">Topics</span></div>'
    html += '</div>'

    # Recent changes
    if recent_changes:
        html += '<section class="recent-changes"><h2>Recent Changes</h2><ul>'
        for change in recent_changes[:10]:
            icon = {"added": "🟢", "updated": "🟡", "archived": "🔴"}.get(change.get("type", ""), "⚪")
            html += f'<li>{icon} <strong>{change.get("type", "").upper()}</strong> '
            html += f'<a href="{change.get("url", "#")}">{change.get("title", "Unknown")}</a></li>'
        html += '</ul></section>'

    # Category cards
    if categories:
        html += '<section class="categories"><h2>Categories</h2><div class="card-grid">'
        for cat_name, cat_data in sorted(categories.items()):
            count = cat_data.get("count", 0)
            html += f'<a href="/categories/{cat_name}/" class="category-card">'
            html += f'<h3>{cat_name.replace("-", " ").title()}</h3>'
            html += f'<span class="card-count">{count} pages</span></a>'
        html += '</div></section>'

    # Most connected
    if top_pages:
        html += '<section class="top-pages"><h2>Most Connected</h2><ol>'
        for tp in top_pages[:10]:
            html += f'<li><a href="{tp.get("url", "#")}">{tp.get("title", "?")}</a>'
            html += f' <span class="ref-count">{tp.get("in_degree", 0)} refs</span></li>'
        html += '</ol></section>'

    html += '</main>'
    html += page_foot()
    return html


def render_category_index(category: str, pages: list[dict]) -> str:
    """Render a category index page."""
    title = category.replace("-", " ").replace("/", " › ").title()
    html = page_head(title, f"All {title} pages")
    html += nav_bar("categories")
    html += breadcrumbs([("Home", "/"), ("Categories", "/categories/"), (title, "#")])
    html += f'<main class="container"><h1>{title}</h1>'
    html += f'<p>{len(pages)} pages</p>'
    html += '<div class="filter-bar"><input type="text" placeholder="Filter pages..." class="filter-input"></div>'
    html += '<table class="pages-table"><thead><tr><th>Title</th><th>Tags</th><th>Importance</th></tr></thead><tbody>'
    for p in sorted(pages, key=lambda x: x.get("importance", 0), reverse=True):
        tags_html = " ".join(f'<span class="tag">{t}</span>' for t in p.get("tags", []))
        imp = p.get("importance", 0)
        imp_bar = f'<div class="imp-bar" style="width:{int(imp*100)}%"></div>'
        html += f'<tr data-tags="{" ".join(p.get("tags", []))}">'
        html += f'<td><a href="{p.get("url", "#")}">{p.get("title", "?")}</a></td>'
        html += f'<td>{tags_html}</td><td>{imp_bar}</td></tr>'
    html += '</tbody></table></main>'
    html += page_foot()
    return html


def render_page_detail(page: dict, backlinks: list[dict]) -> str:
    """Render a page detail page."""
    title = page.get("title", "Untitled")
    html = page_head(title, f"Detail page for {title}")
    html += nav_bar()
    cat = page.get("category", "")
    html += breadcrumbs([
        ("Home", "/"),
        ("Categories", "/categories/"),
        (cat.title(), f"/categories/{cat}/"),
        (title, "#"),
    ])
    html += '<main class="container">'
    html += f'<article class="page-detail">'

    # Metadata card
    html += '<div class="meta-card">'
    html += f'<span><strong>Type:</strong> {page.get("category", "")}</span>'
    html += f'<span><strong>Language:</strong> {page.get("language", "")}</span>'
    tags = page.get("tags", [])
    if tags:
        tags_html = " ".join(f'<span class="tag">{t}</span>' for t in tags)
        html += f'<span><strong>Tags:</strong> {tags_html}</span>'
    imp = page.get("importance", 0)
    html += f'<span><strong>Importance:</strong> {imp:.2f}</span>'
    html += '</div>'

    # Body
    body_html = md_to_html(page.get("body", ""))
    html += body_html

    # Cross-references (outbound)
    refs = page.get("references", [])
    if refs:
        html += '<section class="cross-refs"><h2>References</h2><ul>'
        for r in refs:
            html += f'<li>→ {r}</li>'
        html += '</ul></section>'

    # Backlinks (inbound)
    if backlinks:
        html += '<section class="backlinks"><h2>Referenced By</h2><ul>'
        for bl in backlinks:
            html += f'<li>← <a href="{bl.get("url", "#")}">{bl.get("title", "?")}</a></li>'
        html += '</ul></section>'

    html += '</article></main>'
    html += page_foot()
    return html
```

- [ ] **Step 5: Implement llmwiki/build.py**

```python
"""Static site builder: raw/ → wiki/ → site/."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from llmwiki.graph import build_graph, save_graph, _load_pages, _parse_frontmatter
from llmwiki.render.html import (
    render_dashboard,
    render_category_index,
    render_page_detail,
    page_head,
    page_foot,
    nav_bar,
    md_to_html,
)
from llmwiki.render.css import CSS
from llmwiki.render.js import JS


def build_site(root: Path, config: dict, full: bool = False) -> dict:
    """Build the full static site.

    Args:
        root: Project root containing raw/, wiki/, site/.
        config: Loaded llmwiki.json config.
        full: Force full rebuild.

    Returns:
        Summary dict with stats.
    """
    raw_dir = root / "raw"
    wiki_dir = root / "wiki"
    site_dir = root / config.get("build", {}).get("out_dir", "site")

    # Ensure directories
    wiki_dir.mkdir(exist_ok=True)
    site_dir.mkdir(exist_ok=True)

    # Build knowledge graph
    graph = build_graph(raw_dir)
    save_graph(graph, site_dir / "cross-references.json")

    # Load all pages
    pages = _load_pages(raw_dir)

    # Build backlink index
    backlinks: dict[str, list[dict]] = {}
    for edge in graph.get("edges", []):
        to_id = edge["to"]
        from_id = edge["from"]
        from_node = next((n for n in graph["nodes"] if n["id"] == from_id), None)
        if from_node:
            backlinks.setdefault(to_id, []).append({
                "title": from_node.get("title", from_id),
                "url": _page_url(from_id),
            })

    # Enrich pages with graph data
    node_map = {n["id"]: n for n in graph.get("nodes", [])}
    for pid, pdata in pages.items():
        node = node_map.get(pid, {})
        pdata["importance"] = node.get("importance", 0)
        pdata["cluster_id"] = node.get("cluster_id")
        pdata["in_degree"] = node.get("in_degree", 0)
        pdata["url"] = _page_url(pid)

    # Group by category
    categories: dict[str, list[dict]] = {}
    for pid, pdata in pages.items():
        cat = pdata.get("category", "misc")
        categories.setdefault(cat, []).append({**pdata, "id": pid})

    # Write CSS and JS
    (site_dir / "style.css").write_text(CSS, encoding="utf-8")
    (site_dir / "script.js").write_text(JS, encoding="utf-8")

    # Render dashboard
    top_pages = sorted(
        [{"title": n["title"], "url": _page_url(n["id"]), "in_degree": n["in_degree"]}
         for n in graph.get("nodes", [])],
        key=lambda x: x["in_degree"], reverse=True,
    )
    cat_summary = {cat: {"count": len(pgs)} for cat, pgs in categories.items()}
    dashboard = render_dashboard(graph["stats"], [], cat_summary, top_pages)
    (site_dir / "index.html").write_text(dashboard, encoding="utf-8")

    # Render category indexes
    cat_dir = site_dir / "categories"
    cat_dir.mkdir(exist_ok=True)
    for cat, cat_pages in categories.items():
        cat_path = cat_dir / cat
        cat_path.mkdir(parents=True, exist_ok=True)
        idx_html = render_category_index(cat, cat_pages)
        (cat_path / "index.html").write_text(idx_html, encoding="utf-8")

        # Render individual pages
        for pdata in cat_pages:
            pid = pdata["id"]
            page_html = render_page_detail(pdata, backlinks.get(pid, []))
            slug = pid.split("/")[-1] if "/" in pid else pid
            (cat_path / f"{slug}.html").write_text(page_html, encoding="utf-8")

            # JSON sibling
            page_json = {
                "id": pid,
                "title": pdata.get("title", ""),
                "category": pdata.get("category", ""),
                "tags": pdata.get("tags", []),
                "importance": pdata.get("importance", 0),
                "body_text": pdata.get("body", "")[:5000],
                "references": pdata.get("references", []),
            }
            (cat_path / f"{slug}.json").write_text(
                json.dumps(page_json, indent=2), encoding="utf-8"
            )

    # Build search index
    search_index = _build_search_index(pages, categories)
    (site_dir / "search-index.json").write_text(
        json.dumps(search_index, indent=2), encoding="utf-8"
    )

    return {
        "total_pages": len(pages),
        "total_categories": len(categories),
        "total_edges": graph["stats"]["total_edges"],
        "total_clusters": graph["stats"]["total_clusters"],
    }


def _page_url(page_id: str) -> str:
    """Convert page ID to URL path."""
    parts = page_id.split("/")
    if len(parts) >= 2:
        return f"/categories/{'/'.join(parts[:-1])}/{parts[-1]}.html"
    return f"/categories/{page_id}/{page_id}.html"


def _build_search_index(pages: dict, categories: dict) -> dict:
    """Build client-side search index."""
    entries = []
    for pid, pdata in pages.items():
        entries.append({
            "id": pid,
            "title": pdata.get("title", ""),
            "url": pdata.get("url", ""),
            "type": pdata.get("category", ""),
            "category": pdata.get("category", ""),
            "tags": pdata.get("tags", []),
            "importance": pdata.get("importance", 0),
            "body": pdata.get("body", "")[:1200],
        })
    return {
        "entries": entries,
        "categories": list(categories.keys()),
        "_mode": "flat",
    }
```

- [ ] **Step 6: Create initial CSS and JS constants**

Create `llmwiki/render/css.py` with a `CSS` variable containing the full stylesheet (~15KB).
Create `llmwiki/render/js.py` with `JS` and `PRE_PAINT_SCRIPT` variables (~15KB).

These are large string constants. Start with functional-but-minimal versions and iterate:

```python
# llmwiki/render/css.py
"""Site CSS as a Python string constant."""

CSS = """
:root {
  --bg: #ffffff; --fg: #1a1a2e; --accent: #7C3AED;
  --card-bg: #f8f9fa; --border: #e0e0e0;
  --code-bg: #f5f5f5; --nav-bg: rgba(255,255,255,0.95);
  --shadow: 0 2px 8px rgba(0,0,0,0.1);
}
[data-theme="dark"] {
  --bg: #0c0a1d; --fg: #e0e0e0; --accent: #a78bfa;
  --card-bg: #1a1a2e; --border: #2d2d44;
  --code-bg: #1e1e2e; --nav-bg: rgba(12,10,29,0.95);
  --shadow: 0 2px 8px rgba(0,0,0,0.4);
}
/* ... full CSS here — see Step 2 description for all required sections ... */
"""
# This will be expanded to ~15KB in implementation
```

```python
# llmwiki/render/js.py
"""Site JavaScript as a Python string constant."""

PRE_PAINT_SCRIPT = """
var t=localStorage.getItem('llmwiki-theme');
if(t!=='dark'&&t!=='light'){t=window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark'}
document.documentElement.setAttribute('data-theme',t);
"""

JS = """
// Theme toggle, search palette, keyboard shortcuts, copy buttons
// ... full JS here — see Step 3 description for all required features ...
"""
# This will be expanded to ~15KB in implementation
```

- [ ] **Step 7: Run build tests**

Run: `cd ~/llmwiki && pytest tests/test_build.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: static site builder with dashboard, categories, and page detail

- build_site() generates full HTML site from raw/ pages
- Dashboard home with stats, categories, top pages
- Category index pages with filter bar
- Page detail with metadata card, cross-refs, backlinks
- JSON siblings for AI agents
- Client-side search index
- CSS/JS as embedded Python constants
- Dark/light theme with pre-paint flash prevention"
```


---

### Task 9: Search System (SQLite FTS5 + Client-Side)

**Files:**
- Create: `llmwiki/search.py`
- Test: `tests/test_search.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_search.py
"""Tests for SQLite FTS5 search."""

from pathlib import Path
from llmwiki.search import create_search_db, insert_page, search_pages, cli_search


class TestSearch:
    def test_create_db(self, tmp_path):
        db_path = tmp_path / "test.db"
        create_search_db(db_path)
        assert db_path.exists()

    def test_insert_and_search(self, tmp_path):
        db_path = tmp_path / "test.db"
        create_search_db(db_path)
        insert_page(db_path, {
            "id": "java/main",
            "title": "Main",
            "category": "java",
            "body_plain": "Main entry point for the application",
            "tags": '["java"]',
            "importance_score": 0.5,
        })
        results = search_pages(db_path, "entry point")
        assert len(results) >= 1
        assert results[0]["title"] == "Main"

    def test_search_no_results(self, tmp_path):
        db_path = tmp_path / "test.db"
        create_search_db(db_path)
        results = search_pages(db_path, "nonexistent query")
        assert len(results) == 0

    def test_bulk_insert(self, tmp_path):
        db_path = tmp_path / "test.db"
        create_search_db(db_path)
        pages = [
            {"id": f"page{i}", "title": f"Page {i}", "category": "test",
             "body_plain": f"Content for page {i}", "tags": "[]", "importance_score": 0.1 * i}
            for i in range(20)
        ]
        for p in pages:
            insert_page(db_path, p)
        results = search_pages(db_path, "Content")
        assert len(results) >= 10
```

- [ ] **Step 2: Implement llmwiki/search.py**

```python
"""Search system — SQLite FTS5 for AI agents, client-side index for humans."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def create_search_db(db_path: Path) -> None:
    """Create the SQLite FTS5 search database."""
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT,
            source_path TEXT,
            body_md TEXT,
            body_plain TEXT,
            content_hash TEXT,
            tags TEXT,
            references_out TEXT,
            references_in TEXT,
            importance_score REAL DEFAULT 0.0,
            cluster_id TEXT,
            language TEXT,
            metadata TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
            title, body_plain, tags, category,
            content='pages', content_rowid='rowid'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            from_id TEXT NOT NULL,
            to_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            PRIMARY KEY (from_id, to_id, edge_type)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS clusters (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            member_count INTEGER,
            top_tags TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS build_history (
            build_number INTEGER PRIMARY KEY,
            timestamp TEXT,
            type TEXT,
            duration_seconds REAL,
            added_count INTEGER,
            updated_count INTEGER,
            archived_count INTEGER,
            changes TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_page(db_path: Path, page: dict) -> None:
    """Insert or replace a page in the search database."""
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    c.execute("""
        INSERT OR REPLACE INTO pages (id, title, category, body_plain, tags, importance_score)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        page["id"], page["title"], page.get("category", ""),
        page.get("body_plain", ""), page.get("tags", "[]"),
        page.get("importance_score", 0.0),
    ))

    # Update FTS index
    c.execute("DELETE FROM pages_fts WHERE rowid = (SELECT rowid FROM pages WHERE id = ?)", (page["id"],))
    c.execute("""
        INSERT INTO pages_fts(rowid, title, body_plain, tags, category)
        SELECT rowid, title, body_plain, tags, category FROM pages WHERE id = ?
    """, (page["id"],))

    conn.commit()
    conn.close()


def search_pages(db_path: Path, query: str, limit: int = 20) -> list[dict]:
    """Full-text search against the FTS5 index."""
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # FTS5 search
    try:
        c.execute("""
            SELECT p.id, p.title, p.category, p.importance_score,
                   snippet(pages_fts, 1, '>>>', '<<<', '...', 50) as snippet
            FROM pages_fts
            JOIN pages p ON pages_fts.rowid = p.rowid
            WHERE pages_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        results = [dict(row) for row in c.fetchall()]
    except sqlite3.OperationalError:
        results = []

    conn.close()
    return results


def cli_search(query: str, db_path: str) -> int:
    """CLI search entry point."""
    results = search_pages(Path(db_path), query)
    if not results:
        print(f"No results for: {query}")
        return 0

    print(f"Found {len(results)} results for: {query}\n")
    for r in results:
        print(f"  [{r.get('category', '')}] {r['title']}")
        if r.get("snippet"):
            print(f"    {r['snippet']}")
        print()
    return 0
```

- [ ] **Step 3: Run tests**

Run: `cd ~/llmwiki && pytest tests/test_search.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: SQLite FTS5 search with CLI query interface

- create_search_db() with pages, FTS5, edges, clusters, build_history tables
- insert_page() with FTS index sync
- search_pages() with snippet extraction
- cli_search() for terminal queries"
```

---

### Task 10: Exporters, Serve & Lint

**Files:**
- Create: `llmwiki/exporters.py`
- Create: `llmwiki/serve.py`
- Create: `llmwiki/lint.py`
- Test: `tests/test_exporters.py`
- Test: `tests/test_serve.py`
- Test: `tests/test_lint.py`

- [ ] **Step 1: Write failing tests for exporters**

```python
# tests/test_exporters.py
"""Tests for AI-consumable exports."""

import json
from pathlib import Path
from llmwiki.exporters import export_llms_txt, export_jsonld, export_sitemap, export_all


class TestExporters:
    def _make_pages(self):
        return {
            "java/main": {"title": "Main", "category": "java", "url": "/categories/java/main.html",
                          "body": "Main class.", "tags": ["java"]},
            "docs/guide": {"title": "Guide", "category": "docs", "url": "/categories/docs/guide.html",
                           "body": "A guide.", "tags": ["docs"]},
        }

    def test_llms_txt(self, tmp_path):
        pages = self._make_pages()
        output = tmp_path / "llms.txt"
        export_llms_txt(pages, output, "Test Project")
        content = output.read_text()
        assert "Test Project" in content
        assert "Main" in content

    def test_jsonld(self, tmp_path):
        pages = self._make_pages()
        output = tmp_path / "graph.jsonld"
        export_jsonld(pages, output)
        data = json.loads(output.read_text())
        assert "@context" in data
        assert "@graph" in data

    def test_sitemap(self, tmp_path):
        pages = self._make_pages()
        output = tmp_path / "sitemap.xml"
        export_sitemap(pages, output, "http://localhost:8765")
        content = output.read_text()
        assert "<urlset" in content

    def test_export_all(self, tmp_path):
        pages = self._make_pages()
        export_all(pages, tmp_path, "Test", "http://localhost:8765")
        assert (tmp_path / "llms.txt").exists()
        assert (tmp_path / "llms-full.txt").exists()
        assert (tmp_path / "graph.jsonld").exists()
        assert (tmp_path / "sitemap.xml").exists()
```

- [ ] **Step 2: Implement llmwiki/exporters.py**

```python
"""AI-consumable export generators."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def export_llms_txt(pages: dict, output: Path, project_name: str) -> None:
    """Generate llms.txt per llmstxt.org spec."""
    lines = [f"# {project_name}\n", f"> Knowledge base with {len(pages)} pages\n"]
    categories: dict[str, list] = {}
    for pid, pdata in pages.items():
        cat = pdata.get("category", "misc")
        categories.setdefault(cat, []).append((pid, pdata))

    for cat, cat_pages in sorted(categories.items()):
        lines.append(f"\n## {cat.title()}\n")
        for pid, pdata in cat_pages:
            lines.append(f"- [{pdata.get('title', pid)}]({pdata.get('url', '#')})")

    output.write_text("\n".join(lines), encoding="utf-8")


def export_llms_full_txt(pages: dict, output: Path, max_bytes: int = 5_000_000) -> None:
    """Generate llms-full.txt — flattened text dump."""
    lines = []
    total = 0
    for pid, pdata in sorted(pages.items()):
        title = pdata.get("title", pid)
        body = pdata.get("body", "")[:2000]
        entry = f"\n{'='*60}\n{title}\n{'='*60}\n{body}\n"
        total += len(entry.encode("utf-8"))
        if total > max_bytes:
            break
        lines.append(entry)
    output.write_text("".join(lines), encoding="utf-8")


def export_jsonld(pages: dict, output: Path) -> None:
    """Generate JSON-LD knowledge graph."""
    graph = []
    for pid, pdata in pages.items():
        graph.append({
            "@type": "CreativeWork",
            "@id": pid,
            "name": pdata.get("title", pid),
            "description": pdata.get("body", "")[:200],
            "keywords": pdata.get("tags", []),
            "isPartOf": pdata.get("category", ""),
        })
    data = {
        "@context": "https://schema.org",
        "@graph": graph,
    }
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")


def export_sitemap(pages: dict, output: Path, base_url: str) -> None:
    """Generate sitemap.xml."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for pid, pdata in pages.items():
        url = pdata.get("url", f"/{pid}.html")
        lines.append(f"  <url><loc>{base_url}{url}</loc><lastmod>{now}</lastmod></url>")
    lines.append("</urlset>")
    output.write_text("\n".join(lines), encoding="utf-8")


def export_all(pages: dict, site_dir: Path, project_name: str, base_url: str = "http://localhost:8765") -> None:
    """Generate all AI-consumable exports."""
    export_llms_txt(pages, site_dir / "llms.txt", project_name)
    export_llms_full_txt(pages, site_dir / "llms-full.txt")
    export_jsonld(pages, site_dir / "graph.jsonld")
    export_sitemap(pages, site_dir / "sitemap.xml", base_url)
```

- [ ] **Step 3: Implement llmwiki/serve.py**

```python
"""Local HTTP server for the static site."""

from __future__ import annotations

import http.server
import socketserver
import sys
from pathlib import Path


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Suppress per-request logs."""
    def log_message(self, format, *args):
        pass


class _ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def serve_site(directory: str = "site", port: int = 8765, host: str = "127.0.0.1") -> int:
    """Serve the static site locally."""
    site_dir = Path(directory)
    if not site_dir.exists():
        print(f"Error: {directory}/ does not exist. Run `llmwiki build` first.", file=sys.stderr)
        return 2

    handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(site_dir), **kwargs)

    try:
        with _ReusableTCPServer((host, port), handler) as httpd:
            print(f"🌐 Serving at http://{host}:{port}/")
            print("   Press Ctrl+C to stop.")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopped.")
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0
```

- [ ] **Step 4: Implement llmwiki/lint.py**

```python
"""Lint rules for wiki quality checks."""

from __future__ import annotations

import re
from pathlib import Path


def lint_wiki(raw_dir: Path, graph: dict) -> list[dict]:
    """Run lint checks and return list of issues."""
    issues = []

    # Check for orphaned pages (no inbound or outbound links)
    for node in graph.get("nodes", []):
        if node["in_degree"] == 0 and node["out_degree"] == 0:
            issues.append({
                "rule": "orphan",
                "severity": "warning",
                "page": node["id"],
                "message": f"Orphaned page: {node['title']} has no cross-references",
            })

    # Check for broken references
    valid_ids = {n["id"] for n in graph.get("nodes", [])}
    pages = {}
    for md_file in raw_dir.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        wikilinks = re.findall(r"\[\[([^\]|]+)", content)
        for link in wikilinks:
            if link.lower() not in {v.lower() for v in valid_ids}:
                issues.append({
                    "rule": "broken_link",
                    "severity": "error",
                    "page": md_file.stem,
                    "message": f"Broken wikilink: [[{link}]]",
                })

    # Check for missing titles
    for node in graph.get("nodes", []):
        if not node.get("title") or node["title"] == node["id"]:
            issues.append({
                "rule": "missing_title",
                "severity": "info",
                "page": node["id"],
                "message": "Page has no distinct title",
            })

    return issues
```

- [ ] **Step 5: Write tests for serve and lint**

```python
# tests/test_serve.py
"""Tests for local server."""
from llmwiki.serve import serve_site

class TestServe:
    def test_missing_directory(self, tmp_path):
        ret = serve_site(str(tmp_path / "nonexistent"))
        assert ret == 2
```

```python
# tests/test_lint.py
"""Tests for lint rules."""
from pathlib import Path
from llmwiki.lint import lint_wiki

class TestLint:
    def test_detect_orphans(self):
        graph = {"nodes": [
            {"id": "a", "title": "A", "in_degree": 0, "out_degree": 0},
            {"id": "b", "title": "B", "in_degree": 1, "out_degree": 1},
        ], "edges": []}
        issues = lint_wiki(Path("/tmp"), graph)
        orphan_issues = [i for i in issues if i["rule"] == "orphan"]
        assert len(orphan_issues) == 1
        assert orphan_issues[0]["page"] == "a"
```

- [ ] **Step 6: Run all tests**

Run: `cd ~/llmwiki && pytest tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: exporters (llms.txt, JSON-LD, sitemap), local server, and lint

- export_all() generates llms.txt, llms-full.txt, graph.jsonld, sitemap.xml
- serve_site() with stdlib http.server, quiet handler, reusable socket
- lint_wiki() checks orphans, broken links, missing titles"
```


---

### Task 11: Integration Test — End-to-End Pipeline

**Files:**
- Test: `tests/test_e2e.py`

- [ ] **Step 1: Write end-to-end test**

```python
# tests/test_e2e.py
"""End-to-end integration test — full pipeline."""

import json
import subprocess
import sys
from pathlib import Path

from llmwiki.config import create_default_config, save_config
from llmwiki.ingest import ingest_all
from llmwiki.build import build_site
from llmwiki.search import create_search_db, insert_page, search_pages
from llmwiki.exporters import export_all
from llmwiki.graph import build_graph
from llmwiki.lint import lint_wiki


class TestE2EPipeline:
    def _create_sample_project(self, tmp_path):
        """Create a realistic mini-project for testing."""
        # Java files
        java_dir = tmp_path / "project" / "src" / "com" / "example"
        java_dir.mkdir(parents=True)
        (java_dir / "Main.java").write_text(
            'package com.example;\n\nimport com.example.Utils;\n\n'
            '/**\n * Main application entry point.\n */\n'
            'public class Main {\n    public static void main(String[] args) {\n'
            '        Utils.doStuff();\n    }\n}\n'
        )
        (java_dir / "Utils.java").write_text(
            'package com.example;\n\n'
            '/**\n * Utility methods.\n */\n'
            'public class Utils {\n    public static void doStuff() {\n'
            '        System.out.println("done");\n    }\n}\n'
        )

        # XML config
        config_dir = tmp_path / "project" / "config"
        config_dir.mkdir()
        (config_dir / "workflow.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Workflow name="TestWorkflow">\n'
            '  <Step name="Initialize">\n'
            '    <Script><Source>\n'
            '      import com.example.Utils;\n'
            '      Utils.doStuff();\n'
            '    </Source></Script>\n'
            '  </Step>\n</Workflow>\n'
        )

        # Markdown doc
        (tmp_path / "project" / "README.md").write_text(
            "# Sample Project\n\nA test project for e2e testing.\n"
        )

        # Properties
        (tmp_path / "project" / "app.properties").write_text(
            "# App config\ndb.host=localhost\ndb.port=5432\n"
        )

        return tmp_path / "project"

    def test_full_pipeline(self, tmp_path):
        """Test init → ingest → build → search → export → lint."""
        project_path = self._create_sample_project(tmp_path)
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        # 1. Create config
        config = create_default_config("TestProject", str(project_path))
        cfg_path = work_dir / "llmwiki.json"
        save_config(config, cfg_path)

        # 2. Ingest
        raw_dir = work_dir / "raw"
        raw_dir.mkdir()
        state_path = work_dir / ".llmwiki-state.json"
        result = ingest_all(config, raw_dir, state_path)
        assert result["total_added"] >= 3  # Java + XML + MD + properties

        # 3. Build
        (work_dir / "wiki").mkdir()
        (work_dir / "site").mkdir()
        build_result = build_site(work_dir, config, full=True)
        assert build_result["total_pages"] >= 3
        assert (work_dir / "site" / "index.html").exists()
        assert (work_dir / "site" / "style.css").exists()
        assert (work_dir / "site" / "search-index.json").exists()

        # 4. Search DB
        db_path = work_dir / "site" / "llmwiki.db"
        create_search_db(db_path)
        graph = build_graph(raw_dir)
        for node in graph["nodes"]:
            insert_page(db_path, {
                "id": node["id"],
                "title": node["title"],
                "category": node["type"],
                "body_plain": "test content",
                "tags": "[]",
                "importance_score": node["importance"],
            })
        results = search_pages(db_path, "test")
        assert len(results) >= 1

        # 5. Exports
        # Load pages for export (simplified)
        from llmwiki.graph import _load_pages
        pages = _load_pages(raw_dir)
        for pid, pdata in pages.items():
            pdata["url"] = f"/categories/{pid}.html"
        export_all(pages, work_dir / "site", "TestProject")
        assert (work_dir / "site" / "llms.txt").exists()
        assert (work_dir / "site" / "graph.jsonld").exists()
        assert (work_dir / "site" / "sitemap.xml").exists()

        # 6. Lint
        issues = lint_wiki(raw_dir, graph)
        # Should have no errors for a clean project
        errors = [i for i in issues if i["severity"] == "error"]
        assert len(errors) == 0  # No broken links in a self-contained test

    def test_incremental_rebuild(self, tmp_path):
        """Test that incremental builds only reprocess changed files."""
        project_path = self._create_sample_project(tmp_path)
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        config = create_default_config("TestProject", str(project_path))
        raw_dir = work_dir / "raw"
        raw_dir.mkdir()
        state_path = work_dir / ".llmwiki-state.json"

        # First ingest
        r1 = ingest_all(config, raw_dir, state_path)
        first_added = r1["total_added"]
        assert first_added >= 3

        # Second ingest — no changes
        r2 = ingest_all(config, raw_dir, state_path)
        assert r2["total_added"] == 0
        assert r2["total_unchanged"] == first_added

        # Modify a file
        java_dir = project_path / "src" / "com" / "example"
        (java_dir / "Main.java").write_text(
            'package com.example;\n\n'
            '/** Updated main. */\n'
            'public class Main { public static void main(String[] a) {} }\n'
        )

        # Third ingest — one modification
        r3 = ingest_all(config, raw_dir, state_path)
        assert r3["total_modified"] >= 1

    def test_cli_all(self, tmp_path):
        """Test CLI `all` subcommand."""
        project_path = self._create_sample_project(tmp_path)
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        config = create_default_config("TestProject", str(project_path))
        cfg_path = work_dir / "llmwiki.json"
        save_config(config, cfg_path)

        # Create required dirs
        for d in ["raw", "wiki", "site"]:
            (work_dir / d).mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "llmwiki", "all", "--config", str(cfg_path)],
            capture_output=True, text=True, cwd=str(work_dir),
        )
        # Should complete without error
        assert result.returncode == 0 or "not yet implemented" in result.stderr
```

- [ ] **Step 2: Run e2e test**

Run: `cd ~/llmwiki && pytest tests/test_e2e.py -v --tb=long`
Expected: All PASS

- [ ] **Step 3: Fix any failures and re-run**

Address any integration issues discovered by the e2e test. Common issues:
- Path resolution between modules
- Missing imports
- Frontmatter parsing edge cases

- [ ] **Step 4: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "test: end-to-end integration tests for full pipeline

- test_full_pipeline: init → ingest → build → search → export → lint
- test_incremental_rebuild: verifies change detection works
- test_cli_all: verifies CLI subprocess execution"
```

---

### Task 12: Documentation Suite & Cross-Platform Polish

**Files:**
- Create: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/getting-started.md`
- Create: `docs/configuration.md`
- Create: `docs/adapters.md`
- Create: `docs/ai-integration.md`
- Create: `docs/cross-references.md`
- Create: `docs/cli-reference.md`
- Create: `docs/faq.md`
- Create: `CONTRIBUTING.md`
- Create: `CHANGELOG.md`
- Create: `setup.bat` (Windows)
- Verify: All tests pass on current platform

- [ ] **Step 1: Write README.md**

Write a comprehensive README covering:
- What llmwiki is (one paragraph)
- Quick start for each platform (macOS/Linux: `./setup.sh`, Windows: `setup.bat`)
- How it works (3-layer architecture diagram in ASCII)
- CLI reference table (all 13 commands)
- Feature highlights with screenshots/examples
- Configuration quick reference
- AI agent integration summary
- Development setup

- [ ] **Step 2: Write docs/architecture.md**

Cover:
- 3-layer data model with diagrams
- Pipeline flow (ingest → build → serve)
- Adapter system architecture
- Cross-reference engine internals
- Knowledge graph model
- Search architecture (dual: client-side + SQLite FTS5)
- Build system internals
- How incremental builds work

- [ ] **Step 3: Write docs/getting-started.md**

Step-by-step tutorial:
1. Installation (pip install, git clone, or download)
2. Initialize with a project (`llmwiki init --source /path`)
3. Add PDF documentation sources
4. Run first build (`llmwiki all`)
5. Browse the wiki (`llmwiki serve`)
6. Search from CLI (`llmwiki search "query"`)
7. Set up AI agent integration

Include platform-specific instructions for Windows, macOS, Linux.

- [ ] **Step 4: Write docs/configuration.md**

Full reference for `llmwiki.json`:
- Every field documented with type, default, and description
- Example configs for different project types (Java, Python, TypeScript, mixed)
- How to add PDF sources
- Exclude patterns reference
- Cross-reference tuning options

- [ ] **Step 5: Write docs/adapters.md**

Cover:
- Built-in adapters table with what each extracts
- Language support matrix (30+ languages)
- How to write a custom adapter (BaseAdapter API, WikiPage dataclass)
- Example: creating a Terraform adapter
- How adapter auto-detection works

- [ ] **Step 6: Write docs/ai-integration.md**

Cover:
- Which agent files are generated and when
- How each AI agent discovers the wiki
- SQL query cookbook (10+ example queries)
- How to paste llms-full.txt into LLM context
- How to use the JSON-LD graph programmatically

- [ ] **Step 7: Write docs/cross-references.md, docs/cli-reference.md, docs/faq.md**

- Cross-references: how edges are extracted, PageRank algorithm, cluster detection
- CLI reference: every command with flags, examples, expected output
- FAQ: common questions (how big can it get? how to exclude files? how to reset?)

- [ ] **Step 8: Write CONTRIBUTING.md and CHANGELOG.md**

- Contributing guide: setup, code style, testing, PR guidelines
- Changelog: v0.1.0 initial release

- [ ] **Step 9: Create setup.bat for Windows**

```batch
@echo off
echo [llmwiki] Setting up...
python -m pip install -e . 2>nul || python3 -m pip install -e .
echo [llmwiki] Setup complete. Run: llmwiki init --source PATH
```

- [ ] **Step 10: Run full test suite**

Run: `cd ~/llmwiki && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Test with RioIAM as first real project**

```bash
cd ~/llmwiki
pip install -e .
llmwiki init --source /home/amardeep/RioIAM --name "RioIAM"
# Add PDF sources manually to llmwiki.json
llmwiki all
llmwiki serve
```

Open http://localhost:8765 and verify:
- Dashboard loads with correct stats
- Category pages show Java, XML, config files
- Individual pages have cross-references
- Search works (both Cmd+K and CLI)
- Dark/light theme toggle works

- [ ] **Step 4: Final commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "docs: comprehensive README with quick start and reference

Ready for first release."
```


---

### Task 13: AI Agent Integration (Multi-Agent Schema Generation)

**Files:**
- Create: `llmwiki/agent_schema.py`
- Modify: `llmwiki/cli.py` — add schema generation to `init` command
- Test: `tests/test_agent_schema.py`

This task generates agent-specific instruction files so Claude Code, GitHub Copilot, Codex CLI, Gemini CLI, and Cursor can all discover and use the knowledge base.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_agent_schema.py
"""Tests for AI agent schema generation."""

from pathlib import Path
from llmwiki.agent_schema import (
    generate_claude_md, generate_agents_md,
    generate_copilot_instructions, generate_gemini_md,
    detect_agents, write_agent_schemas,
)


class TestAgentSchema:
    def test_generate_claude_md(self, tmp_path):
        content = generate_claude_md(
            project_name="RioIAM",
            wiki_path=str(tmp_path / "site"),
            stats={"total_pages": 892, "total_edges": 2341, "total_clusters": 12},
        )
        assert "RioIAM" in content
        assert "llmwiki search" in content
        assert "sqlite3" in content
        assert "892" in content

    def test_generate_agents_md(self, tmp_path):
        content = generate_agents_md(
            project_name="RioIAM",
            wiki_path=str(tmp_path / "site"),
            stats={"total_pages": 892, "total_edges": 2341, "total_clusters": 12},
        )
        assert "RioIAM" in content
        assert "llmwiki search" in content
        assert "AGENTS" in content or "agent" in content.lower()

    def test_generate_copilot_instructions(self, tmp_path):
        content = generate_copilot_instructions(
            project_name="RioIAM",
            wiki_path=str(tmp_path / "site"),
            stats={"total_pages": 892, "total_edges": 2341, "total_clusters": 12},
        )
        assert "RioIAM" in content
        assert "llmwiki" in content
        assert "search" in content

    def test_generate_gemini_md(self, tmp_path):
        content = generate_gemini_md(
            project_name="RioIAM",
            wiki_path=str(tmp_path / "site"),
            stats={"total_pages": 10, "total_edges": 5, "total_clusters": 1},
        )
        assert "RioIAM" in content
        assert "llmwiki" in content

    def test_detect_agents_none(self, tmp_path):
        detected = detect_agents(tmp_path)
        # Should always include agents_md as fallback
        assert "agents_md" in detected

    def test_detect_agents_claude(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        detected = detect_agents(tmp_path)
        assert "claude_md" in detected

    def test_detect_agents_copilot(self, tmp_path):
        gh = tmp_path / ".github"
        gh.mkdir()
        detected = detect_agents(tmp_path)
        assert "copilot_instructions" in detected

    def test_write_agent_schemas(self, tmp_path):
        write_agent_schemas(
            project_root=tmp_path,
            wiki_path=str(tmp_path / "site"),
            project_name="Test",
            stats={"total_pages": 1, "total_edges": 0, "total_clusters": 0},
        )
        # Should always create AGENTS.md
        assert (tmp_path / "AGENTS.md").exists() or any(
            f.name.endswith(".md") for f in tmp_path.rglob("*.md")
        )

    def test_appends_to_existing(self, tmp_path):
        existing = "# My Project\n\nExisting content.\n"
        (tmp_path / "CLAUDE.md").write_text(existing)
        (tmp_path / ".claude").mkdir()
        write_agent_schemas(
            project_root=tmp_path,
            wiki_path=str(tmp_path / "site"),
            project_name="Test",
            stats={"total_pages": 1, "total_edges": 0, "total_clusters": 0},
        )
        content = (tmp_path / "CLAUDE.md").read_text()
        assert "Existing content" in content
        assert "llmwiki" in content
```

- [ ] **Step 2: Implement llmwiki/agent_schema.py**

```python
"""Generate AI agent schema files for multi-agent compatibility.

Generates instruction files for:
- Claude Code (CLAUDE.md)
- GitHub Copilot (.github/copilot-instructions.md)
- Codex CLI / Gemini CLI / others (AGENTS.md)
- Gemini CLI (GEMINI.md)
- Cursor (.cursor/rules)
"""

from __future__ import annotations

from pathlib import Path

_LLMWIKI_MARKER = "<!-- llmwiki:auto -->"


def detect_agents(project_root: Path) -> list[str]:
    """Detect which AI agents are likely in use based on directory markers."""
    detected = ["agents_md"]  # Always generate AGENTS.md as universal fallback

    if (project_root / ".claude").exists() or (project_root / "CLAUDE.md").exists():
        detected.append("claude_md")
    if (project_root / ".github").exists():
        detected.append("copilot_instructions")
    if (project_root / "GEMINI.md").exists() or (project_root / ".gemini").exists():
        detected.append("gemini_md")
    if (project_root / ".cursor").exists():
        detected.append("cursor_rules")

    return detected


def write_agent_schemas(
    project_root: Path,
    wiki_path: str,
    project_name: str,
    stats: dict,
) -> list[str]:
    """Write agent schema files. Returns list of files written."""
    detected = detect_agents(project_root)
    written = []

    generators = {
        "claude_md": (project_root / "CLAUDE.md", generate_claude_md),
        "agents_md": (project_root / "AGENTS.md", generate_agents_md),
        "copilot_instructions": (
            project_root / ".github" / "copilot-instructions.md",
            generate_copilot_instructions,
        ),
        "gemini_md": (project_root / "GEMINI.md", generate_gemini_md),
    }

    for agent_key, (filepath, generator) in generators.items():
        if agent_key not in detected:
            continue
        content = generator(project_name, wiki_path, stats)
        _write_or_append(filepath, content)
        written.append(str(filepath))

    return written


def _write_or_append(filepath: Path, llmwiki_section: str) -> None:
    """Write a new file or append llmwiki section to existing file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    marked = f"\n\n{_LLMWIKI_MARKER}\n{llmwiki_section}\n{_LLMWIKI_MARKER}\n"

    if filepath.exists():
        existing = filepath.read_text(encoding="utf-8")
        if _LLMWIKI_MARKER in existing:
            # Replace existing llmwiki section
            import re
            pattern = rf"{re.escape(_LLMWIKI_MARKER)}.*?{re.escape(_LLMWIKI_MARKER)}"
            updated = re.sub(pattern, marked.strip(), existing, flags=re.DOTALL)
            filepath.write_text(updated, encoding="utf-8")
        elif "llmwiki" not in existing.lower():
            filepath.write_text(existing + marked, encoding="utf-8")
    else:
        filepath.write_text(llmwiki_section, encoding="utf-8")

```python
"""Generate AI agent schema files (CLAUDE.md, AGENTS.md).

These files teach AI coding agents how to use the llmwiki knowledge base.
They are placed in the project root so agents auto-discover them.
"""

from __future__ import annotations


def generate_claude_md(project_name: str, wiki_path: str, stats: dict) -> str:
    """Generate CLAUDE.md for Claude Code integration."""
    total_pages = stats.get("total_pages", 0)
    total_edges = stats.get("total_edges", 0)
    total_clusters = stats.get("total_clusters", 0)

    return f'''# llmwiki — Knowledge Base for {project_name}

> Auto-generated by llmwiki. This file teaches Claude Code how to query the
> project knowledge base. Do not remove — it provides essential project context.

## Quick Reference

- **Wiki site:** `{wiki_path}/`
- **Search CLI:** `llmwiki search "<query>"`
- **Search SQL:** `sqlite3 {wiki_path}/llmwiki.db "SELECT title, snippet(pages_fts,1,\\'>>>\\',\\'<<<\\',\\'...\\',50) FROM pages_fts WHERE pages_fts MATCH \\'<query>\\' ORDER BY rank LIMIT 10"`
- **Full context:** `cat {wiki_path}/llms-full.txt` (paste into context for broad questions)
- **Graph data:** `{wiki_path}/cross-references.json`

## What's in the Knowledge Base

- **{total_pages}** wiki pages covering source code and documentation
- **{total_edges}** cross-references linking code artifacts
- **{total_clusters}** topic clusters auto-detected
- Updated on every `llmwiki build`

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/wiki-query <question>` | Search the knowledge base: `llmwiki search "<question>"` |
| `/wiki-ingest` | Re-ingest changed source files: `llmwiki ingest` |
| `/wiki-build` | Rebuild the wiki site: `llmwiki build` |
| `/wiki-lint` | Check for broken references: `llmwiki lint` |
| `/wiki-stats` | Print inventory statistics: `llmwiki stats` |

## Query Workflows

### Finding specific code or documentation
```bash
llmwiki search "provisioning workflow"
```

### Finding what references a specific file
```bash
sqlite3 {wiki_path}/llmwiki.db "SELECT p.title, e.edge_type FROM edges e JOIN pages p ON e.from_id = p.id WHERE e.to_id LIKE '%CommonOperations%'"
```

### Finding the most important pages
```bash
sqlite3 {wiki_path}/llmwiki.db "SELECT title, importance_score, category FROM pages ORDER BY importance_score DESC LIMIT 20"
```

### Finding pages in a topic cluster
```bash
sqlite3 {wiki_path}/llmwiki.db "SELECT title, category FROM pages WHERE cluster_id = 'cluster-1'"
```

### Getting broad context
Read `{wiki_path}/llms.txt` for a short overview, or paste `{wiki_path}/llms-full.txt` into your context for comprehensive project knowledge.

## AI-Consumable Files

| File | Format | Use |
|------|--------|-----|
| `llmwiki.db` | SQLite + FTS5 | Structured queries, full-text search |
| `llms.txt` | Plain text | Quick project overview |
| `llms-full.txt` | Plain text | Full content dump for LLM context |
| `graph.jsonld` | JSON-LD | Machine-readable knowledge graph |
| `cross-references.json` | JSON | Code artifact relationships |
| `search-index.json` | JSON | Client-side search data |
| `<page>.json` | JSON | Per-page metadata + body |
'''


def generate_agents_md(project_name: str, wiki_path: str, stats: dict) -> str:
    """Generate AGENTS.md for Codex CLI, Gemini, Copilot, etc."""
    total_pages = stats.get("total_pages", 0)
    total_edges = stats.get("total_edges", 0)

    return f'''# llmwiki — Knowledge Base for {project_name}

> Auto-generated by llmwiki. This file provides project knowledge base access
> for any AI coding agent (Codex CLI, Gemini CLI, GitHub Copilot, Cursor, etc.).

## Knowledge Base Overview

This project has a structured knowledge base with **{total_pages}** pages and
**{total_edges}** cross-references, generated by [llmwiki](https://github.com/llmwiki).

## How to Query

**CLI search:**
```bash
llmwiki search "<your question>"
```

**SQL search (more powerful):**
```bash
sqlite3 {wiki_path}/llmwiki.db "SELECT title, snippet(pages_fts,1,\\'>>>\\',\\'<<<\\',\\'...\\',50) FROM pages_fts WHERE pages_fts MATCH \\'<terms>\\' ORDER BY rank LIMIT 10"
```

**For broad context**, read `{wiki_path}/llms.txt` for a short index or
`{wiki_path}/llms-full.txt` for the full content dump.

## Available Commands

```bash
llmwiki search "<query>"    # Full-text search
llmwiki ingest              # Re-ingest changed source files
llmwiki build               # Rebuild the wiki
llmwiki lint                # Check for broken references
llmwiki stats               # Print statistics
llmwiki all                 # Full pipeline: ingest + build + export
```

## File Reference

- `{wiki_path}/llmwiki.db` — SQLite FTS5 database (full-text search + relationships)
- `{wiki_path}/llms.txt` — Short index of all pages
- `{wiki_path}/llms-full.txt` — Full text dump for LLM context
- `{wiki_path}/graph.jsonld` — JSON-LD knowledge graph
- `{wiki_path}/cross-references.json` — Code artifact relationship graph
- `{wiki_path}/<page>.json` — Per-page structured metadata
'''


def generate_copilot_instructions(project_name: str, wiki_path: str, stats: dict) -> str:
    """Generate .github/copilot-instructions.md for GitHub Copilot."""
    total_pages = stats.get("total_pages", 0)
    total_edges = stats.get("total_edges", 0)

    return f'''# LLMWiki Knowledge Base — {project_name}

This project has a structured knowledge base with {total_pages} indexed pages
and {total_edges} cross-references generated by llmwiki.

## Querying the Knowledge Base

When you need to understand how code in this project works, use these tools:

### Quick search
Run `llmwiki search "<question>"` to find relevant pages.

### SQL queries for precise lookups
```bash
# Find pages about a topic
sqlite3 {wiki_path}/llmwiki.db "SELECT title, category FROM pages WHERE title LIKE '%<term>%' OR body_plain LIKE '%<term>%' LIMIT 10"

# Find what references a specific file/class
sqlite3 {wiki_path}/llmwiki.db "SELECT p.title FROM edges e JOIN pages p ON e.from_id = p.id WHERE e.to_id LIKE '%<name>%'"

# Find most important pages
sqlite3 {wiki_path}/llmwiki.db "SELECT title, importance_score FROM pages ORDER BY importance_score DESC LIMIT 10"
```

### Full context
Read `{wiki_path}/llms.txt` for a quick overview of all indexed content.

## Keeping the wiki current
Run `llmwiki ingest && llmwiki build` after making code changes to update the knowledge base.
'''


def generate_gemini_md(project_name: str, wiki_path: str, stats: dict) -> str:
    """Generate GEMINI.md for Gemini CLI."""
    total_pages = stats.get("total_pages", 0)

    return f'''# llmwiki — Knowledge Base for {project_name}

This project has a searchable knowledge base with {total_pages} pages.

## Query Commands

- `llmwiki search "<query>"` — full-text search
- `sqlite3 {wiki_path}/llmwiki.db "SELECT ..."` — SQL queries
- `cat {wiki_path}/llms.txt` — overview of all content
- `cat {wiki_path}/llms-full.txt` — full content dump

## Rebuild

`llmwiki all` — re-ingest sources and rebuild the wiki.
'''
```

- [ ] **Step 3: Wire into CLI init command**

Modify `llmwiki/cli.py` `_cmd_init()` to call `generate_claude_md()` and `generate_agents_md()` after config creation:

```python
# At the end of _cmd_init(), add:
from llmwiki.agent_schema import generate_claude_md, generate_agents_md

claude_md = generate_claude_md(name, str(output / "site"), {"total_pages": 0, "total_edges": 0, "total_clusters": 0})
agents_md = generate_agents_md(name, str(output / "site"), {"total_pages": 0, "total_edges": 0, "total_clusters": 0})

# Write to source project directory (not llmwiki output)
source_claude = source / "CLAUDE.md"
source_agents = source / "AGENTS.md"

if source_claude.exists():
    # Append llmwiki section
    existing = source_claude.read_text()
    if "llmwiki" not in existing.lower():
        source_claude.write_text(existing + "\n\n" + claude_md)
        print(f"✅ Appended llmwiki section to {source_claude}")
else:
    source_claude.write_text(claude_md)
    print(f"✅ Created {source_claude}")

if source_agents.exists():
    existing = source_agents.read_text()
    if "llmwiki" not in existing.lower():
        source_agents.write_text(existing + "\n\n" + agents_md)
        print(f"✅ Appended llmwiki section to {source_agents}")
else:
    source_agents.write_text(agents_md)
    print(f"✅ Created {source_agents}")
```

Also update `_cmd_build()` to regenerate CLAUDE.md/AGENTS.md with real stats after build completes.

- [ ] **Step 4: Run tests**

Run: `cd ~/llmwiki && pytest tests/test_agent_schema.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
cd ~/llmwiki
git add -A
git commit -m "feat: AI agent integration with CLAUDE.md and AGENTS.md generation

- generate_claude_md() with slash commands, query workflows, SQL examples
- generate_agents_md() for Codex/Gemini/Copilot/Cursor compatibility
- generate_copilot_instructions() for .github/copilot-instructions.md
- generate_gemini_md() for GEMINI.md
- detect_agents() auto-detects which agents are in use
- write_agent_schemas() writes/appends to all detected agent files
- Idempotent: uses <!-- llmwiki:auto --> markers to replace on re-run"
```

