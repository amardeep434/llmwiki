import json
import pytest
from pathlib import Path
from llmwiki.agent_toggle import enable_agent, disable_agent, get_agent_status


def test_enable_agent(tmp_path):
    cfg = {"project": {"name": "Test"}, "sources": []}
    cfg_path = tmp_path / "llmwiki.json"
    cfg_path.write_text(json.dumps(cfg))
    enable_agent(cfg_path)
    result = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert result["agent_assist"] is True


def test_disable_agent(tmp_path):
    cfg = {"project": {"name": "Test"}, "sources": [], "agent_assist": True}
    cfg_path = tmp_path / "llmwiki.json"
    cfg_path.write_text(json.dumps(cfg))
    disable_agent(cfg_path)
    result = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert result["agent_assist"] is False


def test_get_status_enabled(tmp_path):
    cfg = {"project": {"name": "Test"}, "sources": [], "agent_assist": True}
    cfg_path = tmp_path / "llmwiki.json"
    cfg_path.write_text(json.dumps(cfg))
    assert get_agent_status(cfg_path) is True


def test_get_status_default_disabled(tmp_path):
    cfg = {"project": {"name": "Test"}, "sources": []}
    cfg_path = tmp_path / "llmwiki.json"
    cfg_path.write_text(json.dumps(cfg))
    assert get_agent_status(cfg_path) is False
