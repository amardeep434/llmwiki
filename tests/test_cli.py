"""Tests for CLI dispatcher."""

import subprocess
import sys


class TestCLI:
    def test_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "llmwiki", "--version"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert "0.1.0" in result.stdout or "0.1.0" in result.stderr

    def test_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "llmwiki", "--help"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert result.returncode == 0
        assert "llmwiki" in result.stdout.lower()

    def test_init_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "llmwiki", "init", "--help"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert result.returncode == 0
        assert "source" in result.stdout.lower()
