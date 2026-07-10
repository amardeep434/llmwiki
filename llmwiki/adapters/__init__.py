"""Adapter registry and auto-detection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llmwiki.adapters.base import BaseAdapter

_REGISTRY: dict[str, type[BaseAdapter]] = {}


def register(adapter_cls: type[BaseAdapter]) -> type[BaseAdapter]:
    """Register an adapter class by its name."""
    _REGISTRY[adapter_cls.name] = adapter_cls
    return adapter_cls


def get_adapter(name: str) -> BaseAdapter:
    """Get an adapter instance by name."""
    if name not in _REGISTRY:
        raise KeyError(f"Unknown adapter: {name}. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[name]()


def list_adapters() -> list[str]:
    """Return list of registered adapter names."""
    return sorted(_REGISTRY.keys())


def detect_adapters(root: Path) -> dict[str, list[Path]]:
    """Auto-detect which adapters are needed for a directory."""
    _ensure_all_loaded()
    result: dict[str, list[Path]] = {}
    for name, cls in _REGISTRY.items():
        adapter = cls()
        files = adapter.discover(root)
        if files:
            result[name] = files
    return result


def _ensure_all_loaded() -> None:
    """Import all built-in adapter modules to trigger registration."""
    _names = [
        "config_adapter", "generic_adapter", "markdown_adapter",
        "pdf_adapter", "source_code", "xml_adapter",
    ]
    for name in _names:
        try:
            __import__(f"llmwiki.adapters.{name}")
        except ImportError:
            pass
