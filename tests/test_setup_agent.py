import json
from pathlib import Path
from llmwiki.setup_agent import (
    detect_ides, generate_vscode_mcp, generate_cursor_mcp,
    generate_jetbrains_mcp, generate_windsurf_mcp,
    generate_copilot_extension, setup_all,
)


def test_detect_ides(tmp_path):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".cursor").mkdir()
    result = detect_ides(tmp_path)
    assert "vscode" in result
    assert "cursor" in result
    assert "jetbrains" not in result


def test_detect_ides_empty(tmp_path):
    assert detect_ides(tmp_path) == []


def test_generate_vscode_mcp(tmp_path):
    generate_vscode_mcp(tmp_path)
    cfg = json.loads((tmp_path / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
    assert "llmwiki" in cfg["servers"]
    assert cfg["servers"]["llmwiki"]["command"] == "llmwiki"
    assert "mcp" in cfg["servers"]["llmwiki"]["args"]


def test_generate_cursor_mcp(tmp_path):
    generate_cursor_mcp(tmp_path)
    cfg = json.loads((tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
    assert "llmwiki" in cfg["mcpServers"]


def test_generate_jetbrains_mcp(tmp_path):
    generate_jetbrains_mcp(tmp_path)
    cfg = json.loads((tmp_path / ".idea" / "ai-mcp.json").read_text(encoding="utf-8"))
    assert "llmwiki" in cfg["mcpServers"]


def test_generate_windsurf_mcp(tmp_path):
    generate_windsurf_mcp(tmp_path)
    cfg = json.loads((tmp_path / ".windsurf" / "mcp.json").read_text(encoding="utf-8"))
    assert "llmwiki" in cfg["mcpServers"]


def test_generate_copilot_extension(tmp_path):
    generate_copilot_extension(tmp_path)
    ext = tmp_path / ".github" / "extensions" / "llmwiki-search" / "extension.mjs"
    assert ext.exists()
    content = ext.read_text(encoding="utf-8")
    assert "llmwiki_search" in content
    assert "llmwiki search" in content
    assert "joinSession" in content
    assert "@github/copilot-sdk/extension" in content
    assert "commands:" in content or "commands" in content
    assert "wikisearch" in content


def test_setup_all(tmp_path):
    created = setup_all(tmp_path)
    assert len(created) == 5
    assert (tmp_path / ".vscode" / "mcp.json").exists()
    assert (tmp_path / ".cursor" / "mcp.json").exists()


def test_setup_selective(tmp_path):
    created = setup_all(tmp_path, targets=["vscode", "cursor"])
    assert len(created) == 2
    assert (tmp_path / ".vscode" / "mcp.json").exists()
    assert not (tmp_path / ".idea" / "ai-mcp.json").exists()
