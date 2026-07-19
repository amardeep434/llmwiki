"""Configuration loading and validation for llmwiki."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_EXCLUDE = [
    # .llmwiki first: the wiki must never ingest its own output
    ".llmwiki", "node_modules", ".git", "build", "dist", "__pycache__",
    "*.min.js", "*.min.css", "*.map", "*.lock", ".venv", "venv",
    "*.pyc", "*.class", "*.o", "*.so", "*.dll",
    "*.jpg", "*.png", "*.gif", "*.ico", "*.svg",
    "*.zip", "*.tar", "*.gz", "*.jar", "*.war",
    ".DS_Store", "Thumbs.db",
]


def create_default_config(name: str, source_path: str) -> dict:
    """Create a default llmwiki.json config."""
    return {
        "project": {"name": name, "description": "", "base_url": "http://localhost:8765"},
        "sources": [{"path": source_path, "type": "auto", "exclude": list(DEFAULT_EXCLUDE)}],
        "pdf_sources": [],
        "build": {
            "out_dir": "site",
            "incremental": True,
            "base_url": "http://localhost:8765",
        },
        # "build.search_mode" reserved for future use (e.g. "fts5", "trigram")
        "serve": {"port": 8765, "host": "127.0.0.1"},
        "cross_references": {"enabled": True, "importance_iterations": 20, "cluster_min_size": 3},
        "exclude_global": list(DEFAULT_EXCLUDE),
    }


def load_config(path: Path) -> dict:
    """Load config from a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict, path: Path) -> None:
    """Save config to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def validate_config(config: dict) -> list[str]:
    """Validate config and return list of error messages."""
    errors = []
    if "project" not in config:
        errors.append("Missing required field: 'project'")
    elif "name" not in config.get("project", {}):
        errors.append("Missing required field: 'project.name'")
    if "sources" not in config:
        errors.append("Missing required field: 'sources'")
    elif not isinstance(config["sources"], list):
        errors.append("'sources' must be a list")
    return errors
