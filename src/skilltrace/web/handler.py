"""Request routing for the local serve shell (Tier-1 slices T2/T3).

The router is deliberately thin glue (ADR 0006): method + path dispatch, with
the page bodies living in ``views.py``. Every read reloads truth fresh —
``load_context_lenient(root)`` per request, no cache, no file-watch — so CLI
and editor edits appear on refresh. Routes per the G3#67 table: ``/`` (today),
``/next``, ``/nodes/{id}``, ``/health``; writes are not wired yet (T4).
Escaping discipline is owned by the view layer's transform (every interpolated
value passes through ``_esc``). There is no static-file routing at all;
styling is the one inline ``<style>`` block. ``data/*`` exports are never read.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote

from .views import health_body, home_body, next_body, node_body, page  # noqa: F401 — page re-exported


class SkillTraceHandler(BaseHTTPRequestHandler):
    """GET router for the serve shell. The resolved root rides on the server."""

    def do_GET(self) -> None:  # noqa: N802 — stdlib contract
        path, _, query_string = self.path.partition("?")
        if path != "/":
            path = path.rstrip("/")
        if path == "":
            path = "/"
        query = parse_qs(query_string)

        if path == "/":
            title, body, status = home_body(self.server.root)
        elif path == "/next":
            title, body, status = next_body(self.server.root, query)
        elif path.startswith("/nodes/"):
            node_id = unquote(path[len("/nodes/"):])
            title, body, status = node_body(self.server.root, node_id)
        elif path == "/health":
            title, body, status = health_body(self.server.root)
        else:
            title, body, status = (
                "Not found",
                '<p>Unknown route. Try <a href="/">Today</a>.</p>',
                404,
            )

        self._send(page(title, body), status=status)

    def _send(self, html_text: str, *, status: int = 200) -> None:
        payload = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)
