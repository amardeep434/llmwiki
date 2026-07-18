"""Tests for AI agent schema generation."""

from pathlib import Path
from llmwiki.agent_schema import (
    generate_claude_md, generate_agents_md,
    generate_copilot_instructions, generate_copilot_agent,
    generate_gemini_md,
    detect_agents, write_agent_schemas,
)


class TestAgentSchema:
    def test_generate_claude_md(self, tmp_path):
        content = generate_claude_md("RioIAM", str(tmp_path / "site"),
            {"total_pages": 892, "total_edges": 2341, "total_clusters": 12})
        assert "RioIAM" in content
        assert "llmwiki search" in content
        assert "sqlite3" in content
        assert "892" in content

    def test_generate_agents_md(self, tmp_path):
        content = generate_agents_md("RioIAM", str(tmp_path / "site"),
            {"total_pages": 892, "total_edges": 2341, "total_clusters": 12})
        assert "RioIAM" in content
        assert "llmwiki search" in content

    def test_generate_copilot_instructions(self, tmp_path):
        content = generate_copilot_instructions("RioIAM", str(tmp_path / "site"),
            {"total_pages": 892, "total_edges": 2341, "total_clusters": 12})
        assert "RioIAM" in content
        assert "llmwiki" in content

    def test_generate_gemini_md(self, tmp_path):
        content = generate_gemini_md("RioIAM", str(tmp_path / "site"),
            {"total_pages": 10, "total_edges": 5, "total_clusters": 1})
        assert "RioIAM" in content

    def test_detect_agents_none(self, tmp_path):
        detected = detect_agents(tmp_path)
        assert "agents_md" in detected

    def test_detect_agents_claude(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        detected = detect_agents(tmp_path)
        assert "claude_md" in detected

    def test_detect_agents_copilot(self, tmp_path):
        (tmp_path / ".github").mkdir()
        detected = detect_agents(tmp_path)
        assert "copilot_instructions" in detected
        assert "copilot_agent" in detected

    def test_generate_copilot_agent(self, tmp_path):
        content = generate_copilot_agent("RioIAM", str(tmp_path / "site"),
            {"total_pages": 50, "total_edges": 120, "total_clusters": 5})
        assert "---" in content
        assert "description:" in content
        assert "tools:" in content
        assert "llmwiki_search" in content
        assert "RioIAM" in content
        assert "50 pages" in content

    def test_write_agent_schemas_creates_copilot_agent(self, tmp_path):
        (tmp_path / ".github").mkdir()
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0})
        agent_file = tmp_path / ".github" / "agents" / "llmwiki.agent.md"
        assert agent_file.exists()
        content = agent_file.read_text()
        assert "llmwiki_search" in content

    def test_write_agent_schemas(self, tmp_path):
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0})
        assert (tmp_path / "AGENTS.md").exists()

    def test_appends_to_existing(self, tmp_path):
        existing = "# My Project\n\nExisting content.\n"
        (tmp_path / "CLAUDE.md").write_text(existing)
        (tmp_path / ".claude").mkdir()
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0})
        content = (tmp_path / "CLAUDE.md").read_text()
        assert "Existing content" in content
        assert "llmwiki" in content

    def test_idempotent_update(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0})
        first_content = (tmp_path / "CLAUDE.md").read_text()
        # Run again with different stats
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 999, "total_edges": 0, "total_clusters": 0})
        second_content = (tmp_path / "CLAUDE.md").read_text()
        assert "999" in second_content
        # Should NOT have duplicate sections
        assert second_content.count("<!-- llmwiki:auto -->") == 2  # open + close markers
