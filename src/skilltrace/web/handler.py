"""Request routing for the local serve shell (Tier-1 slices T2/T3/T4+T5).

The router is deliberately thin glue (ADR 0006): method + path dispatch, with
the page bodies living in the ``views/`` package (ADR 0009). Every read
reloads truth fresh — ``load_context_lenient(root)`` per request, no cache,
no file-watch — so CLI and editor edits appear on refresh.

The route table is **flat and mode-neutral** (docs/spec-v3-study-day.md §6):
seventeen destinations, each existing exactly once. Mode is presentation
context carried by a URL parameter, never by a path prefix; the contextual
inspector has no route of its own and its selected context rides a
parameter of the route that owns it. Reads are GET-only; writes are standard
form POSTs that nest-dispatch through the registry in-process and answer
303 + translated flash in every case (ok, refusal as a warning flash back
to the acceptance step, operational failure as an error flash pointing at
the health roll-up). Escaping discipline is owned by the view layer's card
renderer (every interpolated value passes through ``_esc``). There is no
static-file routing at all; styling is the one inline ``<style>`` block.
``data/*`` exports are never read.
"""

from __future__ import annotations

import re
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote

from . import views
from .views import (
    Redirect,
    analytics_body,
    evidence_index_body,
    finder_body,
    graph_body,
    health_body,
    home_body,
    master_body,
    master_confirm_body,
    next_body,
    node_body,
    node_evidence_body,
    operations_body,
    page,
    pass_modal_body,
    portfolio_body,
    post_analytics_export,
    post_blocker_create,
    post_blocker_resolve,
    post_evidence,
    post_master_confirm,
    post_pass,
    post_portfolio_export,
    post_review_cancel,
    post_review_complete,
    post_review_schedule,
    post_session_close,
    post_start,
    post_work,
    reviews_body,
    session_body,
    session_close_body,
)

_NODE_PASS_RE = re.compile(r"^/nodes/(.+?)/pass$")
_NODE_MASTER_CONFIRM_RE = re.compile(r"^/nodes/(.+?)/master/confirm$")
_NODE_MASTER_RE = re.compile(r"^/nodes/(.+?)/master$")
_NODE_START_RE = re.compile(r"^/nodes/(.+?)/start$")
_NODE_BLOCKERS_RE = re.compile(r"^/nodes/(.+?)/blockers$")
_BLOCKER_RESOLVE_RE = re.compile(r"^/blockers/(.+?)/resolve$")
_NODE_EVIDENCE_RE = re.compile(r"^/nodes/(.+?)/evidence$")
_GRAPH_NODE_RE = re.compile(r"^/graph/(.+)$")
_REVIEW_ID_RE = re.compile(r"^/reviews/(.+?)/(complete|cancel)$")


class SkillTraceHandler(BaseHTTPRequestHandler):
    """GET/POST router for the serve shell. The resolved root rides on the server."""

    def do_GET(self) -> None:  # noqa: N802 — stdlib contract
        path, _, query_string = self.path.partition("?")
        path = self._normalize(path)
        query = parse_qs(query_string)

        master_confirm = _NODE_MASTER_CONFIRM_RE.match(path)
        master_step = _NODE_MASTER_RE.match(path)
        pass_modal = _NODE_PASS_RE.match(path)
        node_evidence = _NODE_EVIDENCE_RE.match(path)
        graph_node = _GRAPH_NODE_RE.match(path)
        review_action = _REVIEW_ID_RE.match(path)
        if path == "/":
            title, body, status = home_body(self.server.root, query)
        elif path == "/next":
            title, body, status = next_body(self.server.root, query)
        elif path == "/find":
            title, body, status = finder_body(self.server.root, query)
        elif path == "/session":
            title, body, status = session_body(self.server.root, query)
        elif path == "/session/close":
            title, body, status = session_close_body(self.server.root, query)
        elif path == "/evidence":
            title, body, status = evidence_index_body(self.server.root, query)
        elif path == "/reviews":
            title, body, status = reviews_body(self.server.root, query)
        elif path == "/operations":
            title, body, status = operations_body(self.server.root, query)
        elif path == "/graph":
            title, body, status = graph_body(self.server.root, query)
        elif path == "/health":
            title, body, status = health_body(self.server.root, query)
        elif path == "/analytics":
            title, body, status = analytics_body(self.server.root, query)
        elif path == "/portfolio":
            title, body, status = portfolio_body(self.server.root, query)
        elif path == "/portfolio/preview":
            title, body, status = portfolio_body(self.server.root, query)
        elif review_action is not None:
            # The review action routes are write paths; a GET renders the
            # reviews destination so a stray link is never a dead end.
            title, body, status = reviews_body(self.server.root, query)
        elif master_confirm is not None:
            title, body, status = master_confirm_body(
                self.server.root, unquote(master_confirm.group(1)), query
            )
        elif master_step is not None:
            title, body, status = master_body(
                self.server.root, unquote(master_step.group(1)), query
            )
        elif pass_modal is not None:
            title, body, status = pass_modal_body(
                self.server.root, unquote(pass_modal.group(1)), query
            )
        elif node_evidence is not None:
            title, body, status = node_evidence_body(
                self.server.root, unquote(node_evidence.group(1)), query
            )
        elif graph_node is not None:
            title, body, status = graph_body(
                self.server.root, query, node_id=unquote(graph_node.group(1))
            )
        elif path.startswith("/nodes/"):
            node_id = self._node_id_from_detail(path)
            title, body, status = node_body(self.server.root, node_id, query)
        else:
            title, body, status = self._not_found()

        self._send(page(title, body, mode=self._mode(query)), status=status)

    def do_POST(self) -> None:  # noqa: N802 — stdlib contract
        length = int(self.headers.get("Content-Length") or 0)
        form = parse_qs(
            self.rfile.read(length).decode("utf-8"), keep_blank_values=True
        )
        path = self._normalize(self.path)

        result = self._route_post(path, form)
        if isinstance(result, Redirect):
            self._redirect(result.location)
        else:
            title, body, status = result
            self._send(page(title, body, mode=self._mode(form)), status=status)

    def _route_post(self, path: str, form: dict):
        root = self.server.root
        if path == "/work":
            return post_work(root, form)
        if path == "/session/close":
            return post_session_close(root, form)
        if path == "/analytics/export":
            return post_analytics_export(root, form)
        if path == "/portfolio/export":
            return post_portfolio_export(root, form)
        if path == "/reviews/schedule":
            return post_review_schedule(root, form)
        review_action = _REVIEW_ID_RE.match(path)
        if review_action is not None:
            review_id = unquote(review_action.group(1))
            if review_action.group(2) == "complete":
                return post_review_complete(root, review_id, form)
            return post_review_cancel(root, review_id, form)
        start_match = _NODE_START_RE.match(path)
        if start_match is not None:
            return post_start(root, unquote(start_match.group(1)), form)
        pass_match = _NODE_PASS_RE.match(path)
        if pass_match is not None:
            return post_pass(root, unquote(pass_match.group(1)), form)
        master_match = _NODE_MASTER_CONFIRM_RE.match(path)
        if master_match is not None:
            return post_master_confirm(root, unquote(master_match.group(1)), form)
        blockers_match = _NODE_BLOCKERS_RE.match(path)
        if blockers_match is not None:
            return post_blocker_create(root, unquote(blockers_match.group(1)), form)
        resolve_match = _BLOCKER_RESOLVE_RE.match(path)
        if resolve_match is not None:
            return post_blocker_resolve(
                root, unquote(resolve_match.group(1)), form
            )
        evidence_match = _NODE_EVIDENCE_RE.match(path)
        if evidence_match is not None:
            return post_evidence(root, unquote(evidence_match.group(1)), form)
        return self._not_found()

    @staticmethod
    def _normalize(path: str) -> str:
        if path != "/":
            path = path.rstrip("/")
        return path or "/"

    @staticmethod
    def _node_id_from_detail(path: str) -> str:
        return path[len("/nodes/"):]

    @staticmethod
    def _mode(params: dict) -> str:
        """The presentation mode a request asked for, if any."""
        from .views.shell import _mode_from

        return _mode_from(params)

    def _not_found(self) -> tuple[str, str, int]:
        """Every non-route answers with the one unified error body (T4 §H)."""
        return views.not_found_body(self.server.root)

    def _send(self, html_text: str, *, status: int = 200) -> None:
        payload = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _redirect(self, location: str) -> None:
        payload = (
            f'<!doctype html><html lang="en"><body>'
            f'<p>Saved. <a href="{location}">Continue</a>.</p></body></html>'
        ).encode("utf-8")
        self.send_response(303)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)
