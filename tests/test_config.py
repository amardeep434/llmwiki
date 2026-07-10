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
        cfg["pdf_sources"] = [{"path": "/docs/guides", "label": "Guides", "type": "auto"}]
        errors = validate_config(cfg)
        assert errors == []

    def test_config_defaults(self, tmp_path):
        cfg = create_default_config("Test", str(tmp_path))
        assert cfg["serve"]["port"] == 8765
        assert cfg["serve"]["host"] == "127.0.0.1"
        assert cfg["cross_references"]["enabled"] is True
