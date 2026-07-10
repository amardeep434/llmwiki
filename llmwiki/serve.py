"""Local HTTP server for the static site."""

from __future__ import annotations

import http.server
import socketserver
import sys
from pathlib import Path


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Suppress per-request logs."""
    def log_message(self, format, *args):
        pass


class _ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def serve_site(directory: str = "site", port: int = 8765, host: str = "127.0.0.1") -> int:
    """Serve the static site locally."""
    site_dir = Path(directory)
    if not site_dir.exists():
        print(f"Error: {directory}/ does not exist. Run `llmwiki build` first.", file=sys.stderr)
        return 2

    handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(site_dir), **kwargs)

    try:
        with _ReusableTCPServer((host, port), handler) as httpd:
            print(f"🌐 Serving at http://{host}:{port}/")
            print("   Press Ctrl+C to stop.")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopped.")
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0
