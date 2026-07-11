"""Tests for adapter registry."""

from llmwiki.adapters import list_adapters, get_adapter, _ensure_all_loaded


class TestRegistry:
    def test_list_adapters(self):
        _ensure_all_loaded()
        adapters = list_adapters()
        assert "source-code" in adapters
        assert "xml" in adapters
        assert "pdf" in adapters
        assert "markdown" in adapters
        assert "config" in adapters

    def test_get_adapter(self):
        _ensure_all_loaded()
        adapter = get_adapter("source-code")
        assert adapter.name == "source-code"

    def test_get_unknown_adapter(self):
        try:
            get_adapter("nonexistent-adapter-xyz")
            assert False, "Should raise KeyError"
        except KeyError:
            pass
