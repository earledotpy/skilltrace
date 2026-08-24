"""Request handler + HTML assembly for the local serve shell (Tier-1 slice T2).

The router is deliberately thin glue (ADR 0006): method + path dispatch, with
routes landing slice by slice per the G3#67 route table. Every read reloads
truth fresh — ``load_context_lenient(root)`` per request, no cache, no
file-watch — so CLI and editor edits appear on refresh. The health strip
reports through the same engine derivations as ``skilltrace health``
(``ProgressStore.state_summary`` / ``verification_summary``) so there is one
voice and no parallel vocabulary. Escaping discipline is owned here (ADR 0006):
every interpolated value passes through ``_esc``. There is no static-file
routing at all; styling is the one inline ``<style>`` block in ``page``.
``data/*`` exports are never read here.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

from ..context import JoinedView, load_context_lenient
from ..resources.status import stale_after_days, verification_summary


def _esc(value: object) -> str:
    """Escape every interpolated value — the one door into page HTML."""
    return html.escape(str(value), quote=True)


_STYLE = """
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 46rem;
         padding: 0 1rem; line-height: 1.5; }
  h1 { font-size: 1.4rem; } h2 { font-size: 1.1rem; margin-top: 1.6rem; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: 0.35rem 0.5rem; border-bottom: 1px solid #8884; }
  .mut { color: #888; font-size: 0.85rem; }
  ul { padding-left: 1.2rem; }
"""


def page(title: str, body: str) -> str:
    """Wrap a body in the single shared layout (one inline style block)."""
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{_esc(title)} — SkillTrace</title>\n"
        f"<style>{_STYLE}</style>\n</head>\n<body>\n"
        f"<h1>{_esc(title)}</h1>\n{body}\n</body>\n</html>\n"
    )


def _index_body() -> str:
    return (
        "<p>SkillTrace is serving your repo. Daily views (today, next, node "
        "detail) land in the next build slices.</p>\n"
        "<h2>Live routes</h2>\n<ul>\n"
        '<li><a href="/health">/health</a> — roll-up strip, read fresh per '
        "request</li>\n</ul>\n"
        '<p class="mut">Loopback only. Writes are not wired yet — use the CLI '
        "(<code>pass</code>/<code>master</code> stay explicit learner commands).</p>\n"
    )


def _health_body(view: JoinedView, root) -> str:
    """The health strip, derived from one fresh lenient join.

    Layer counts come straight from the view's collections; the progress-store
    and resource-verification lines reuse the engine's shared summary helpers
    so serve and `skilltrace health` can never disagree.
    """
    today = datetime.now(timezone.utc).date()
    res_summary = verification_summary(
        view.resources, today=today, stale_after_days=stale_after_days(root)
    )

    rows = [
        ("Graph", f"{len(view.nodes)} nodes, {len(view.edges)} edges"),
        (
            "Evidence",
            f"{len(view.specs)} specs, {len(view.gates)} gates, "
            f"{len(view.records)} records, {len(view.attempts)} attempts",
        ),
        (
            "Execution",
            f"{len(view.sessions)} sessions, {len(view.work)} work items, "
            f"{len(view.blockers)} blockers, {len(view.remediations)} remediation "
            f"actions, {len(view.reviews)} reviews",
        ),
        ("Policy", f"{len(view.policies)} policy file(s)"),
        ("Resources", f"{len(view.resources)} resource(s); {res_summary}"),
        ("Progress store", view.store.state_summary()),
    ]
    body = "<table>\n" + "".join(
        f"<tr><th>{_esc(label)}</th><td>{_esc(value)}</td></tr>\n"
        for label, value in rows
    ) + "</table>\n"
    body += (
        '<p class="mut">Read fresh from the truth files at request time — '
        "CLI edits appear on refresh.</p>"
    )
    return body


class SkillTraceHandler(BaseHTTPRequestHandler):
    """GET router for the serve shell. The resolved root rides on the server."""

    def do_GET(self) -> None:  # noqa: N802 — stdlib contract
        path = self.path.split("?", 1)[0]
        if path != "/":
            path = path.rstrip("/")
        if path == "":
            path = "/"
        if path == "/":
            self._send(page("SkillTrace", _index_body()))
        elif path == "/health":
            view = load_context_lenient(self.server.root)
            self._send(page("Health", _health_body(view, self.server.root)))
        else:
            self._send(
                page("Not found", "<p>Unknown route. Try <a href=\"/health\">/health</a>.</p>"),
                status=404,
            )

    def _send(self, html_text: str, *, status: int = 200) -> None:
        payload = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)
