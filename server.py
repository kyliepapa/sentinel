"""Serve the Sentinel dashboard and expose the saved device inventory."""

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from database import list_devices


ROOT = Path(__file__).parent
DATABASE = ROOT / "data" / "sentinel.db"


class SentinelHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        path = urlparse(self.path).path
        if path == "/api/devices":
            self.send_json(self.devices_payload())
            return

        relative = "index.html" if path == "/" else path.lstrip("/")
        file_path = (ROOT / relative).resolve()
        if ROOT not in file_path.parents or not file_path.is_file():
            self.send_error(404, "Not found")
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def devices_payload(self) -> dict:
        devices = list_devices(str(DATABASE)) if DATABASE.exists() else []
        scanned_at = max((device["last_seen"] for device in devices), default=None)
        return {
            "devices": devices,
            "scanned_at": scanned_at,
            "source": "database.py",
        }

    def send_json(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), SentinelHandler)
    print("Sentinel is running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSentinel stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
