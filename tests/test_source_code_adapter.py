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
