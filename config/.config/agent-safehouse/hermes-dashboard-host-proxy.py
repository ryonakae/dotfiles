#!/usr/bin/env python3
"""Small localhost-only reverse proxy for Hermes Dashboard.

Tailscale Serve preserves the external Host header. Hermes Dashboard rejects
that when it is bound to 127.0.0.1, so this proxy rewrites Host to the upstream
loopback address while keeping the dashboard itself localhost-only.
"""

from __future__ import annotations

import http.client
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

LISTEN_HOST = os.environ.get("HERMES_DASHBOARD_PROXY_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("HERMES_DASHBOARD_PROXY_PORT", "9120"))
UPSTREAM_HOST = os.environ.get("HERMES_DASHBOARD_UPSTREAM_HOST", "127.0.0.1")
UPSTREAM_PORT = int(os.environ.get("HERMES_DASHBOARD_UPSTREAM_PORT", "9119"))

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802
        self._proxy()

    def do_POST(self) -> None:  # noqa: N802
        self._proxy()

    def do_PUT(self) -> None:  # noqa: N802
        self._proxy()

    def do_PATCH(self) -> None:  # noqa: N802
        self._proxy()

    def do_DELETE(self) -> None:  # noqa: N802
        self._proxy()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._proxy()

    def _proxy(self) -> None:
        body = None
        length = self.headers.get("Content-Length")
        if length:
            body = self.rfile.read(int(length))

        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP and key.lower() != "host"
        }
        headers["Host"] = f"{UPSTREAM_HOST}:{UPSTREAM_PORT}"

        target = self.path
        parsed = urlsplit(target)
        if parsed.scheme and parsed.netloc:
            target = parsed.path or "/"
            if parsed.query:
                target += "?" + parsed.query

        conn = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=30)
        try:
            conn.request(self.command, target, body=body, headers=headers)
            resp = conn.getresponse()
            payload = resp.read()

            self.send_response(resp.status, resp.reason)
            for key, value in resp.getheaders():
                if key.lower() not in HOP_BY_HOP and key.lower() != "content-length":
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        finally:
            conn.close()

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
    print(
        f"Hermes Dashboard proxy → http://{LISTEN_HOST}:{LISTEN_PORT} "
        f"=> http://{UPSTREAM_HOST}:{UPSTREAM_PORT}",
        flush=True,
    )
    server.serve_forever()
