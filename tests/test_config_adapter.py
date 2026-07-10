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
