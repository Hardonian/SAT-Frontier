"""Desktop Launcher and Packaging for SAT-Frontier Enterprise Dashboard.

Provides a self-contained zero-dependency desktop application runtime:
- Spins up local HTTP server on an available localhost port
- Verifies server health via /api/v1/health
- Automatically launches the system browser to the interactive dashboard
- Handles graceful shutdown and headless testing modes
"""
from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from http.server import HTTPServer
from typing import Optional, Tuple

from .server import EnterpriseApiHandler


def find_free_port(start_port: int = 8080, max_attempts: int = 50) -> int:
    """Find a free TCP port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError(f"Could not find a free port in range {start_port}..{start_port + max_attempts}")


class DesktopApp:
    """Desktop runner managing server lifecycle and browser launching."""

    def __init__(self, host: str = "127.0.0.1", port: Optional[int] = None):
        self.host = host
        self.port = port or find_free_port()
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self._running = False

    def start_background(self) -> str:
        """Start server in a background thread and return base URL."""
        self.server = HTTPServer((self.host, self.port), EnterpriseApiHandler)
        self._running = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        # Wait for health endpoint
        url = f"http://{self.host}:{self.port}/"
        health_url = f"{url}api/v1/health"
        for _ in range(50):
            try:
                with urllib.request.urlopen(health_url, timeout=0.5) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                time.sleep(0.05)
        return url

    def stop(self) -> None:
        """Stop background server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            self.thread = None
        self._running = False

    def run(self, open_browser: bool = True) -> None:
        """Run desktop application synchronously until interrupted."""
        base_url = self.start_background()
        print("=" * 70)
        print(" SAT-Frontier Enterprise Desktop Dashboard")
        print(f" Dashboard URL: {base_url}")
        print(" Press Ctrl+C to exit.")
        print("=" * 70)

        if open_browser:
            webbrowser.open(base_url)

        try:
            while self._running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nExiting desktop application...")
        finally:
            self.stop()


def main():
    parser = argparse.ArgumentParser(description="SAT-Frontier Enterprise Desktop Launcher")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help="Port (default: automatic free port)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open web browser")
    args = parser.parse_args()

    app = DesktopApp(host=args.host, port=args.port)
    app.run(open_browser=not args.no_browser)


if __name__ == "__main__":
    main()

