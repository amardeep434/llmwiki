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
from llmwiki.graph import build_graph, _load_pages
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

        # XML config with BeanShell Source block
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

        # Properties file
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
        assert result["total_added"] >= 3, f"Expected ≥3 added, got {result}"

        # 3. Build
        (work_dir / "wiki").mkdir()
        (work_dir / "site").mkdir(exist_ok=True)
        build_result = build_site(work_dir, config, full=True)
        assert build_result["total_pages"] >= 3, f"Expected ≥3 pages, got {build_result}"
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
                "body_plain": "test content for search",
                "tags": "[]",
                "importance_score": node["importance"],
            })
        results = search_pages(db_path, "test")
        assert len(results) >= 1, "Search should return at least 1 result"

        # 5. Exports
        pages = _load_pages(raw_dir)
        for pid, pdata in pages.items():
            pdata["url"] = f"/categories/{pid}.html"
        export_all(pages, work_dir / "site", "TestProject")
        assert (work_dir / "site" / "llms.txt").exists()
        assert (work_dir / "site" / "graph.jsonld").exists()
        assert (work_dir / "site" / "sitemap.xml").exists()

        # 6. Lint
        issues = lint_wiki(raw_dir, graph)
        errors = [i for i in issues if i["severity"] == "error"]
        assert len(errors) == 0, f"Expected 0 errors, got: {errors}"

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
        assert first_added >= 3, f"Expected ≥3 added, got {r1}"

        # Second ingest — no changes
        r2 = ingest_all(config, raw_dir, state_path)
        assert r2["total_added"] == 0, f"Expected 0 added on re-ingest, got {r2}"
        assert r2["total_unchanged"] == first_added, (
            f"Expected {first_added} unchanged, got {r2}"
        )

        # Modify a file
        java_dir = project_path / "src" / "com" / "example"
        (java_dir / "Main.java").write_text(
            'package com.example;\n\n'
            '/** Updated main. */\n'
            'public class Main { public static void main(String[] a) {} }\n'
        )

        # Third ingest — one modification
        r3 = ingest_all(config, raw_dir, state_path)
        assert r3["total_modified"] >= 1, f"Expected ≥1 modified, got {r3}"

    def test_cli_all(self, tmp_path):
        """Test CLI `all` subcommand via subprocess."""
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
            capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(work_dir),
        )
        # Should complete without error
        assert result.returncode == 0, (
            f"CLI exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
