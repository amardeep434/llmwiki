"""Agent assist toggle — enable/disable wiki-first behavior."""
from __future__ import annotations
import json
from pathlib import Path


def enable_agent(cfg_path: Path) -> None:
    """Enable wiki-first agent behavior."""
    config = json.loads(cfg_path.read_text(encoding="utf-8"))
    config["agent_assist"] = True
    cfg_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def disable_agent(cfg_path: Path) -> None:
    """Disable wiki-first agent behavior."""
    config = json.loads(cfg_path.read_text(encoding="utf-8"))
    config["agent_assist"] = False
    cfg_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def get_agent_status(cfg_path: Path) -> bool:
    """Check if agent assist is enabled."""
    config = json.loads(cfg_path.read_text(encoding="utf-8"))
    return config.get("agent_assist", False)
