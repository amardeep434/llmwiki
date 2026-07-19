"""Tests for configuration loading and validation."""

import json
from pathlib import Path
from llmwiki.config import (
    load_config,
    create_default_config,
    validate_config,
    SENSITIVE_EXCLUDE,
)


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


class TestSensitiveFloor:
    def _write_config(self, tmp_path, extra=None):
        """Write a config whose source has NO security excludes."""
        cfg_data = {
            "project": {"name": "Test"},
            "sources": [{"path": str(tmp_path), "type": "auto", "exclude": ["node_modules"]}],
            "exclude_global": ["node_modules"],
        }
        if extra:
            cfg_data.update(extra)
        cfg_file = tmp_path / "llmwiki.json"
        cfg_file.write_text(json.dumps(cfg_data))
        return cfg_file

    def test_floor_merged_into_source_exclude(self, tmp_path):
        loaded = load_config(self._write_config(tmp_path))
        source_exclude = loaded["sources"][0]["exclude"]
        # User's own entry preserved.
        assert "node_modules" in source_exclude
        # Every sensitive pattern injected.
        for pattern in SENSITIVE_EXCLUDE:
            assert pattern in source_exclude

    def test_floor_merged_into_exclude_global(self, tmp_path):
        loaded = load_config(self._write_config(tmp_path))
        for pattern in SENSITIVE_EXCLUDE:
            assert pattern in loaded["exclude_global"]

    def test_floor_no_duplicates(self, tmp_path):
        loaded = load_config(self._write_config(tmp_path))
        source_exclude = loaded["sources"][0]["exclude"]
        assert source_exclude.count(".env") == 1

    def test_opt_out_flag_disables_floor(self, tmp_path):
        extra = {"security": {"allow_sensitive_files": True}}
        loaded = load_config(self._write_config(tmp_path, extra=extra))
        assert ".env" not in loaded["sources"][0]["exclude"]
        assert "*.pem" not in loaded["exclude_global"]

    def _discover_names(self, proj, exclude):
        from llmwiki.adapters import _ensure_all_loaded, _REGISTRY
        _ensure_all_loaded()
        discovered = []
        for adapter_cls in _REGISTRY.values():
            discovered.extend(adapter_cls().discover(proj, exclude=exclude))
        return {p.name for p in discovered}

    def test_sensitive_files_refused_at_discovery(self, tmp_path):
        """A config with no security excludes still refuses secret-bearing files.

        Uses real extensions the config adapter would otherwise ingest so the
        exclusion is genuinely exercised (unlike .env/.pem which no adapter
        claims by extension).
        """
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "secrets.json").write_text('{"token": "abc123def456"}\n')
        (proj / "aws_credentials.yaml").write_text("key: abc123def456\n")
        (proj / "config.json").write_text('{"port": 8080}\n')  # benign

        cfg_file = tmp_path / "llmwiki.json"
        cfg_file.write_text(json.dumps({
            "project": {"name": "Test"},
            "sources": [{"path": str(proj), "type": "auto", "exclude": []}],
        }))
        loaded = load_config(cfg_file)
        names = self._discover_names(proj, loaded["sources"][0]["exclude"])
        assert "secrets.json" not in names
        assert "aws_credentials.yaml" not in names
        assert "config.json" in names  # benign file still ingested

    def test_opt_out_allows_sensitive_files_at_discovery(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "secrets.json").write_text('{"token": "abc123def456"}\n')
        cfg_file = tmp_path / "llmwiki.json"
        cfg_file.write_text(json.dumps({
            "project": {"name": "Test"},
            "sources": [{"path": str(proj), "type": "auto", "exclude": []}],
            "security": {"allow_sensitive_files": True},
        }))
        loaded = load_config(cfg_file)
        names = self._discover_names(proj, loaded["sources"][0]["exclude"])
        assert "secrets.json" in names
