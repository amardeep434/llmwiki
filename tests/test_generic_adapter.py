"""Tests for generic fallback adapter."""

from pathlib import Path
from llmwiki.adapters.generic_adapter import GenericAdapter


class TestGenericAdapter:
    def setup_method(self):
        self.adapter = GenericAdapter()

    def test_can_handle_anything(self, tmp_path):
        f = tmp_path / "unknown.xyz"
        f.write_text("some content")
        assert self.adapter.can_handle(f)

    def test_extract(self, tmp_path):
        f = tmp_path / "script.sh"
        f.write_text("#!/bin/bash\n# Deploy script\necho 'deploying'\n")
        pages = self.adapter.extract(f, {})
        assert len(pages) == 1
        assert "deploying" in pages[0].body
