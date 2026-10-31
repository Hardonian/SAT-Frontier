"""Production REST API & Web Dashboard Server for SAT-Frontier Enterprise.

Zero external dependencies: uses Python standard library http.server and socketserver.
Serves interactive visualization dashboard and exposes REST endpoints for exact WMC auditing.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict

from .engine import EnterpriseReliabilityEngine
from .importers import load_topology
from .topology import EnterpriseTopology

WEB_DIR = Path(__file__).resolve().parent / "web"
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class EnterpriseApiHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler serving web dashboard and SLA REST API."""

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or "application/octet-stream"
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url_path = self.path.split("?")[0]
        if url_path in ("/", "/index.html"):
            self._serve_file(WEB_DIR / "index.html")
            return

        if url_path == "/api/v1/health":
            self._send_json({"status": "healthy", "version": "0.2.9"})
            return

        if url_path == "/api/v1/topologies":
            # List available topology files in instances/topologies
            topo_dir = ROOT_DIR / "instances" / "topologies"
            files = []
            if topo_dir.exists():
                for f in topo_dir.iterdir():
                    if f.suffix.lower() in (".graphml", ".gml", ".json", ".csv", ".tsv"):
                        files.append({"name": f.stem, "path": str(f.relative_to(ROOT_DIR)), "format": f.suffix})
            self._send_json({"topologies": files})
            return

        # Static assets
        safe_rel = url_path.lstrip("/")
        candidate = (WEB_DIR / safe_rel).resolve()
        if candidate.is_relative_to(WEB_DIR) and candidate.exists():
            self._serve_file(candidate)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, f"Path '{url_path}' not found")

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            req_data = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON request body"}, status=400)
            return

        url_path = self.path.split("?")[0]

        # Audit endpoint: two-terminal
        if url_path == "/api/v1/audit/two-terminal":
            try:
                topo_data = req_data.get("topology")
                source = req_data.get("source")
                target = req_data.get("target")
                if isinstance(topo_data, dict):
                    topo = EnterpriseTopology.from_dict(topo_data)
                elif isinstance(topo_data, str):
                    topo = load_topology(ROOT_DIR / topo_data)
                else:
                    self._send_json({"error": "Missing 'topology' object or path"}, status=400)
                    return

                engine = EnterpriseReliabilityEngine(topo)
                result = engine.audit_terminal_pair(source, target)
                self._send_json(result.to_dict())
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        if url_path == "/api/v1/audit/multi-commodity":
            try:
                topo_data = req_data.get("topology")
                commodities_input = req_data.get("commodities", [])
                commodities = [
                    (c["source"], c["target"], int(c.get("demand", 1)))
                    for c in commodities_input
                ]
                if isinstance(topo_data, dict):
                    topo = EnterpriseTopology.from_dict(topo_data)
                elif isinstance(topo_data, str):
                    topo = load_topology(ROOT_DIR / topo_data)
                else:
                    self._send_json({"error": "Missing 'topology' object or path"}, status=400)
                    return
                engine = EnterpriseReliabilityEngine(topo)
                result = engine.audit_multi_commodity_flow(commodities)
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        if url_path == "/api/v1/audit/weibull":
            try:
                topo_data = req_data.get("topology")
                source = req_data.get("source")
                target = req_data.get("target")
                beta = float(req_data.get("beta", 2.0))
                lam = float(req_data.get("lambda", 1e-4))
                if isinstance(topo_data, dict):
                    topo = EnterpriseTopology.from_dict(topo_data)
                elif isinstance(topo_data, str):
                    topo = load_topology(ROOT_DIR / topo_data)
                else:
                    self._send_json({"error": "Missing 'topology' object or path"}, status=400)
                    return
                engine = EnterpriseReliabilityEngine(topo)
                result = engine.audit_weibull_reliability(source, target, beta=beta, lambda_per_hour=lam)
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        if url_path == "/api/v1/audit/repairable":
            try:
                topo_data = req_data.get("topology")
                source = req_data.get("source")
                target = req_data.get("target")
                lam = float(req_data.get("lambda", 1e-4))
                mu = float(req_data.get("mu", 1e-2))
                if isinstance(topo_data, dict):
                    topo = EnterpriseTopology.from_dict(topo_data)
                elif isinstance(topo_data, str):
                    topo = load_topology(ROOT_DIR / topo_data)
                else:
                    self._send_json({"error": "Missing 'topology' object or path"}, status=400)
                    return
                engine = EnterpriseReliabilityEngine(topo)
                result = engine.audit_repairable_network(source, target, failure_rate_per_hour=lam, repair_rate_per_hour=mu)
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        if url_path == "/api/v1/audit/enclosure":
            try:
                topo_data = req_data.get("topology")
                source = req_data.get("source")
                target = req_data.get("target")
                max_paths = int(req_data.get("max_paths", 5))
                max_cuts = int(req_data.get("max_cuts", 5))
                if isinstance(topo_data, dict):
                    topo = EnterpriseTopology.from_dict(topo_data)
                elif isinstance(topo_data, str):
                    topo = load_topology(ROOT_DIR / topo_data)
                else:
                    self._send_json({"error": "Missing 'topology' object or path"}, status=400)
                    return
                engine = EnterpriseReliabilityEngine(topo)
                result = engine.audit_enclosure_bounds(source, target, max_paths=max_paths, max_cuts=max_cuts)
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        self.send_error(HTTPStatus.NOT_FOUND, f"API endpoint '{url_path}' not found")

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[EnterpriseServer] {self.address_string()} - {format % args}\n")


def run_server(host: str = "127.0.0.1", port: int = 8080):
    server = HTTPServer((host, port), EnterpriseApiHandler)
    print("=" * 65)
    print(f" SAT-Frontier Enterprise Web Dashboard & REST Server")
    print(f" Listening on: http://{host}:{port}/")
    print("=" * 65)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAT-Frontier Enterprise Web & REST Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)

