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
