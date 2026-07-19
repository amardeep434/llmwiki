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
        assert "892" in content

    def test_generated_guide_is_compact(self, tmp_path):
        # The block lands in every conversation's context — keep it small.
        content = generate_claude_md("RioIAM", str(tmp_path / "site"),
            {"total_pages": 892, "total_edges": 2341, "total_clusters": 12})
        assert len(content.splitlines()) <= 20

    def test_generated_guide_mentions_module_fallback(self, tmp_path):
        content = generate_agents_md("X", str(tmp_path / "site"),
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0})
        assert "python -m llmwiki" in content

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
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0},
            create=True)
        agent_file = tmp_path / ".github" / "agents" / "llmwiki.agent.md"
        assert agent_file.exists()
        content = agent_file.read_text(encoding="utf-8")
        assert "llmwiki_search" in content

    def test_write_agent_schemas(self, tmp_path):
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0},
            create=True)
        assert (tmp_path / "AGENTS.md").exists()

    def test_no_create_does_not_touch_unmarked_files(self, tmp_path):
        """Build (create=False) must never create or append to files."""
        existing = "# My Project\n\nExisting content.\n"
        (tmp_path / "CLAUDE.md").write_text(existing)
        (tmp_path / ".claude").mkdir()
        written = write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0})
        assert written == []
        assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == existing
        assert not (tmp_path / "AGENTS.md").exists()

    def test_no_create_refreshes_marked_files(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0},
            create=True)
        # Build-style refresh with new stats, no create
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 999, "total_edges": 0, "total_clusters": 0})
        content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert "999" in content
        assert content.count("<!-- llmwiki:auto -->") == 2

    def test_appends_to_existing(self, tmp_path):
        existing = "# My Project\n\nExisting content.\n"
        (tmp_path / "CLAUDE.md").write_text(existing)
        (tmp_path / ".claude").mkdir()
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0},
            create=True)
        content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert "Existing content" in content
        assert "llmwiki" in content
        # Appended section must be marked so future runs replace, not duplicate
        assert content.count("<!-- llmwiki:auto -->") == 2

    def test_first_write_includes_markers(self, tmp_path):
        """Fresh files must be created with markers (idempotency)."""
        (tmp_path / ".claude").mkdir()
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0},
            create=True)
        content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert content.count("<!-- llmwiki:auto -->") == 2

    def test_idempotent_update(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 1, "total_edges": 0, "total_clusters": 0},
            create=True)
        # Run again with different stats
        write_agent_schemas(tmp_path, str(tmp_path / "site"), "Test",
            {"total_pages": 999, "total_edges": 0, "total_clusters": 0},
            create=True)
        second_content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert "999" in second_content
        # Should NOT have duplicate sections
        assert second_content.count("<!-- llmwiki:auto -->") == 2  # open + close markers
