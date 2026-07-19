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

# Security floor: files and directories that must never be ingested because
# they routinely hold secrets. Applied at load time regardless of a config's
# own exclude lists so frozen/legacy configs are protected without migration.
# Glob entries (with * or ?) match filenames; plain names match path
# components (used for secret-bearing directories like .ssh / .aws / .gnupg).
SENSITIVE_EXCLUDE = [
    ".env", ".env.*",
    "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore",
    "id_rsa*", "id_ed25519*", "id_dsa*",
    ".netrc", ".npmrc", ".pypirc",
    "*credentials*", "*secret*", "*.tfstate",
    ".ssh", ".aws", ".gnupg",
]


def _merge_sensitive_floor(existing: list) -> list:
    """Return existing excludes plus any missing SENSITIVE_EXCLUDE entries.

    New objects are returned rather than mutating the input, preserving the
    caller's list and any user-defined order (floor entries appended at end).
    """
    seen = set(existing)
    merged = list(existing)
    for pattern in SENSITIVE_EXCLUDE:
        if pattern not in seen:
            merged.append(pattern)
    return merged


def _apply_sensitive_floor(config: dict) -> dict:
    """Merge the sensitive-file floor into every source and the global list.

    This is a security floor: it runs at load time and cannot be weakened by
    what a user's llmwiki.json happens to contain. The only escape hatch is an
    explicit ``"security": {"allow_sensitive_files": true}`` opt-out, for the
    rare project that genuinely needs to document such files.
    """
    if config.get("security", {}).get("allow_sensitive_files"):
        return config

    updated = dict(config)
    updated["exclude_global"] = _merge_sensitive_floor(config.get("exclude_global", []) or [])
    updated["sources"] = [
        {**source, "exclude": _merge_sensitive_floor(source.get("exclude", []) or [])}
        for source in config.get("sources", [])
    ]
    return updated


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
        config = json.load(f)
    # Enforce the sensitive-file floor at load time so every downstream
    # consumer (ingest, discovery, CLI) inherits the protection.
    return _apply_sensitive_floor(config)


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
