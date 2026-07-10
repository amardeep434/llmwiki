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
