"""Tests for the ingestion pipeline."""

from pathlib import Path
from llmwiki.ingest import ingest_source, ingest_all
from llmwiki.config import create_default_config


class TestIngest:
    def test_ingest_source_creates_raw_files(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "Main.java").write_text("public class Main {}")
        (src / "README.md").write_text("# Project\n\nDescription.")
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        result = ingest_source(
            source_path=src, raw_dir=raw_dir,
            state_path=tmp_path / ".llmwiki-state.json", config={},
        )
        assert result["added"] > 0
        md_files = list(raw_dir.rglob("*.md"))
        assert len(md_files) >= 1

    def test_ingest_incremental_skips_unchanged(self, tmp_path):
        src = tmp_path / "project"
        src.mkdir()
        (src / "Main.java").write_text("public class Main {}")
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        state_path = tmp_path / ".llmwiki-state.json"
        r1 = ingest_source(src, raw_dir, state_path, {})
        assert r1["added"] >= 1
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
