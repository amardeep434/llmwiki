"""Build state management for incremental builds."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class BuildState:
    """Tracks file hashes and build state for incremental processing."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.build_number: int = 0
        self.last_build: str = ""
        self.files: dict[str, dict] = {}
        if path.exists():
            self.load()

    def load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        meta = data.get("_meta", {})
        self.build_number = meta.get("build_number", 0)
        self.last_build = meta.get("last_build", "")
        self.files = data.get("files", {})

    def save(self) -> None:
        data = {
            "_meta": {
                "version": "1.0.0",
                "build_number": self.build_number,
                "last_build": self.last_build or datetime.now(timezone.utc).isoformat(),
            },
            "files": self.files,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

    def record_file(self, source_path: str, content_hash: str, raw_path: str) -> None:
        self.files[source_path] = {"content_hash": content_hash, "raw_path": raw_path, "status": "current"}

    def classify(self, source_path: str, content_hash: str) -> str:
        if source_path not in self.files:
            return "new"
        if self.files[source_path]["content_hash"] != content_hash:
            return "modified"
        return "unchanged"

    def detect_deleted(self, current_files: set[str]) -> set[str]:
        return set(self.files.keys()) - current_files

    def increment_build(self) -> None:
        self.build_number += 1
        self.last_build = datetime.now(timezone.utc).isoformat()
