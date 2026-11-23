"""
The only browser mutation path (ADR 0009): the nine POST handlers
plus the write plumbing — nest-dispatch, exit-code mapping, and the
redirect-after-POST flash — through the same process-wide registry the
CLI resolves.

"""

from __future__ import annotations

import re
from argparse import Namespace
from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode

from ...dispatch import (
    Context,
    dispatch,
)
from ._shared import (
    _field,
    _int_field,
)
from .steps import PASS_PANEL_ANCHOR


@dataclass
class Redirect:
    """A POST outcome that sends 303 See Other — redirect-after-POST."""

    location: str


def _dispatch_web(root, command_name: str, **arg_fields) -> tuple[int, list[str]]:
    """Nest-dispatch one registry command in-process with ``source: "web"``.

    The registry is imported lazily (``cli`` imports this package at startup),
    and it is *the* process-wide ``REGISTRY`` — the same registration the CLI
    resolves, so handlers, kinds, automation labels, audit events, and refusal
    semantics cannot drift from the command line (G2#66's one-write-path rule).
    Handler stdout is captured so refusals can render verbatim; the
    ``CommandResult.exit_code`` is the whole contract.
    """
    from ...cli import REGISTRY

    command = REGISTRY.get(command_name)
    if command is None:  # pragma: no cover — every wired name is registered
        raise KeyError(f"no such command in the registry: {command_name}")
    ctx = Context(root=Path(root), args=Namespace(**arg_fields), source="web")
    buffer = StringIO()
    with redirect_stdout(buffer):
        exit_code = dispatch(command, ctx)
    return exit_code, buffer.getvalue().splitlines()


def _redirect_with_notice(
    location: str,
    lines: list[str],
    kind: str,
    *,
    params: dict | None = None,
    fragment: str = "",
) -> Redirect:
    """PRG redirect carrying translated human copy as the flash notice (T5 P3.5+D2).

    The URL is a copy surface: copy is fixed at its source by the one
    translation module (no flags, command names, exit classes, paths,
    record ids or ADR numbers) and never redacted at the address bar.
    Banner-kind tags ride the ``kind`` param, never the notice text.

    ``params`` carries the learner's own context across the redirect (the
    presentation mode, say) so a refusal lands back where they were, not
    on a bare page. The extra parameters never carry copy. ``fragment``
    names the region of the destination the browser should land on, so the
    result or the refusal is where the learner starts (IC-5, AX-7).
    """
    from ..interface import translate_lines

    clean: list[str] = []
    for line in translate_lines(lines):
        line = re.sub(r"^\[(?:error|warning|advisory)\]\s*", "", line).strip()
        if line:
            clean.append(line)
    notice = "\n".join(clean)
    query = {"notice": notice, "kind": kind}
    for key, value in (params or {}).items():
        if value:
            query[key] = value
    separator = "&" if "?" in location else "?"
    location = f"{location}{separator}{urlencode(query)}"
    if fragment:
        location = f"{location}#{fragment}"
    return Redirect(location=location)


def _safe_next(form: dict, fallback: str) -> str:
    """The host page a form POST returns to — local paths only."""
    target = (form.get("next") or [fallback])[0]
    if target.startswith("/") and not target.startswith("//"):
        return target
    return fallback


def _context_params(form: dict) -> dict:
    """The learner's own context, carried across a redirect.

    The presentation mode is presentation context, not domain state
    (spec-v3-study-day IA-1): a learner who was reading in one mode and
    is refused lands back in that same mode, on the same step. Only the
    declared modes are carried — a crafted form cannot smuggle anything
    else into the URL.
    """
    from .shell import MODES

    mode = _field(form, "mode")
    if mode in MODES:
        return {"mode": mode}
    return {}


def _finish_write(
    next_url: str,
    lines: list[str],
    exit_code: int,
    *,
    refusal_url: str | None = None,
    failure_detail: str | None = None,
    params: dict | None = None,
    fragment: str = "",
) -> Redirect:
    """Map a dispatched write's exit code per the locked T5 contract (§D1+S5).

    Every POST → 303 See Other + translated flash; no 4xx ever leaves a
    write. ``0`` → ok flash to ``next_url``; ``2`` (domain refusal) →
    warning flash to ``refusal_url`` (the acceptance step for pass/master,
    else ``next_url``); ``1`` (operational failure) → error flash to
    ``next_url`` pointing at /health for the detail, or at the caller's own
    precise recovery line when it supplies one (IC-8). ``params`` carries
    the learner's context across the redirect; ``fragment`` names the
    region of the destination the browser lands on.
    """
    if exit_code == 0:
        return _redirect_with_notice(
            next_url, lines, "ok", params=params, fragment=fragment
        )
    if exit_code == 2:
        return _redirect_with_notice(
            refusal_url or next_url,
            lines,
            "warning",
            params=params,
            fragment=fragment,
        )
    if failure_detail:
        lines = [*lines, failure_detail]
    else:
        lines = [*lines, "Something went wrong — see /health for the detail."]
    return _redirect_with_notice(
        next_url, lines, "error", params=params, fragment=fragment
    )


def post_pass(root, node_id: str, form: dict):
    """POST `/nodes/{id}/pass` — always 303 (T5 §D1).

    A successful pass returns to the **pass panel**, which then renders
    the *result*: what changed, and the visible Review-state consequence
    (R3). Redirecting straight to the node page would hide that
    consequence behind a flash the learner has to remember — the spec
    requires the pass result to show the Review change, not merely to
    have caused one.

    A refusal lands on the same panel, not on the host page: the facts are
    refreshed there and the next valid route is named (IC-8, R5). The
    learner's presentation mode rides along, so a refusal returns them to
    the context they were in.
    """
    exit_code, lines = _dispatch_web(root, "pass", node_id=node_id)
    return _finish_write(
        f"/nodes/{node_id}/pass",
        lines,
        exit_code,
        refusal_url=f"/nodes/{node_id}/pass",
        params=_context_params(form),
        fragment=PASS_PANEL_ANCHOR,
    )


def post_master_confirm(root, node_id: str, form: dict):
    """POST `/nodes/{id}/master/confirm` — always 303 (T5 §D1+P4.4)."""
    exit_code, lines = _dispatch_web(root, "master", node_id=node_id)
    return _finish_write(
        f"/nodes/{node_id}",
        lines,
        exit_code,
        refusal_url=f"/nodes/{node_id}/master/confirm",
    )


def _start_refusal_url(root, next_url: str) -> str:
    """Where a refused start lands — recovery must need no hint ladder (R5).

    A second start is refused while a Session is open. The refusal explains
    the two real options, and this sends the learner to the cockpit that
    holds them: record work on the skill the Session is bound to, or close
    the Session. With no open Session (a locked node), the node page is the
    safe place — it states the lock and offers no override.

    A failed load is not a reason to guess: the form's own host page stays.
    """
    from ...context import load_context_lenient
    from ...execution.records import open_session

    try:
        current = open_session(load_context_lenient(root).sessions)
    except Exception:  # noqa: BLE001 — recovery routing must never fail a refusal
        return next_url
    return "/session" if current is not None else next_url


def post_start(root, node_id: str, form: dict):
    next_url = _safe_next(form, f"/nodes/{node_id}")
    exit_code, lines = _dispatch_web(
        root, "start", node_id=node_id, template=_field(form, "template")
    )
    return _finish_write(
        next_url,
        lines,
        exit_code,
        refusal_url=_start_refusal_url(root, next_url) if exit_code == 2 else None,
    )


def post_work(root, form: dict):
    next_url = _safe_next(form, "/")
    node_id = _field(form, "node_id")
    minutes, minutes_error = _int_field(form, "minutes")
    if not node_id:
        return _redirect_with_notice(next_url, ["work requires a node id."], "warning")
    if minutes_error:
        return _redirect_with_notice(next_url, [minutes_error], "warning")
    exit_code, lines = _dispatch_web(
        root,
        "work",
        node_id=node_id,
        blocked=_field(form, "blocked") is not None,
        notes=_field(form, "notes"),
        minutes=minutes,
    )
    return _finish_write(next_url, lines, exit_code)


def post_session_close(root, form: dict):
    next_url = _safe_next(form, "/")
    exit_code, lines = _dispatch_web(root, "session close", end=_field(form, "end"))
    # A refused close (a future end, or an end before the start) returns to
    # the close panel with the session facts refreshed: the SessionWork is
    # never discarded and closure stays available (§10.6).
    return _finish_write(
        next_url, lines, exit_code, refusal_url="/session/close"
    )


def post_blocker_create(root, node_id: str, form: dict):
    next_url = _safe_next(form, f"/nodes/{node_id}")
    exit_code, lines = _dispatch_web(
        root, "blocker create", node_id=node_id, description=_field(form, "description")
    )
    return _finish_write(next_url, lines, exit_code)


def post_blocker_resolve(root, blocker_id: str, form: dict):
    next_url = _safe_next(form, "/")
    exit_code, lines = _dispatch_web(
        root, "blocker resolve", blocker_id=blocker_id, summary=_field(form, "summary")
    )
    return _finish_write(next_url, lines, exit_code)


def post_evidence(root, node_id: str, form: dict):
    next_url = _safe_next(form, f"/nodes/{node_id}/evidence")
    location = _field(form, "location")
    if not location:
        return _redirect_with_notice(
            next_url,
            ["Recording evidence needs the artifact location."],
            "warning",
        )
    verdict = _field(form, "verdict")
    exit_code, lines = _dispatch_web(
        root,
        "evidence submit",
        node_id=node_id,
        spec=_field(form, "spec"),
        location=location,
        note=_field(form, "note"),
        accept=verdict == "accept",
        reject=verdict == "reject",
        supersedes=_field(form, "supersedes"),
        reason=_field(form, "reason"),
    )
    # A gate that cannot run is an operational failure, not a verdict: no
    # record is written, and the recovery is precise enough to act on
    # without a trip through the CLI (IC-8).
    failure_detail = (
        "Nothing was recorded. Check the artifact location and that the "
        "automatic check can run, then submit again from the evidence "
        "workspace."
    )
    return _finish_write(
        next_url,
        lines,
        exit_code,
        failure_detail=failure_detail if exit_code == 1 else None,
    )


def post_review_schedule(root, form: dict):
    """POST `/reviews/schedule` — the explicit scheduling action.

    A Review is scheduled **only** here: a retention suggestion may offer
    this action but never appears as already scheduled or overdue. The
    dispatcher's exit class is the outcome; a refusal writes no record.
    """
    next_url = _safe_next(form, "/reviews")
    node_id = _field(form, "node_id")
    date = _field(form, "date")
    if not node_id:
        return _redirect_with_notice(
            next_url, ["Scheduling a review needs a skill."], "warning"
        )
    if not date:
        return _redirect_with_notice(
            next_url, ["Scheduling a review needs a date."], "warning"
        )
    exit_code, lines = _dispatch_web(
        root, "review schedule", node_id=node_id, date=date
    )
    return _finish_write(next_url, lines, exit_code)


def post_review_complete(root, review_id: str, form: dict):
    """POST `/reviews/{id}/complete` — an explicit outcome plus a summary.

    Completing a Review is independent of the Session that started it. It
    never demotes asserted progress and never masters a node: an
    unsatisfactory outcome creates pressure only.
    """
    next_url = _safe_next(form, "/reviews")
    outcome = _field(form, "outcome")
    summary = _field(form, "summary")
    if outcome not in ("satisfactory", "unsatisfactory"):
        return _redirect_with_notice(
            next_url,
            ["Completing a review needs an explicit outcome."],
            "warning",
        )
    if not summary:
        return _redirect_with_notice(
            next_url,
            ["Completing a review needs a result summary."],
            "warning",
        )
    exit_code, lines = _dispatch_web(
        root,
        "review complete",
        review_id=review_id,
        outcome=outcome,
        summary=summary,
    )
    return _finish_write(next_url, lines, exit_code)


def post_review_cancel(root, review_id: str, form: dict):
    """POST `/reviews/{id}/cancel` — a reason is required; history is kept."""
    next_url = _safe_next(form, "/reviews")
    reason = _field(form, "reason")
    if not reason:
        return _redirect_with_notice(
            next_url, ["Cancelling a review needs a reason."], "warning"
        )
    exit_code, lines = _dispatch_web(
        root, "review cancel", review_id=review_id, reason=reason
    )
    return _finish_write(next_url, lines, exit_code)


def post_portfolio_export(root, form: dict):
    """POST `/portfolio/export` — the explicit export action.

    The export writes a dated disposable bundle; the preview beside it is
    non-writing. A refusal or failure writes no partial destination and
    preserves the selection for recovery.
    """
    next_url = _safe_next(form, "/portfolio")
    fmt = _field(form, "format") or "md"
    if fmt not in {"md", "html", "json"}:
        return _redirect_with_notice(
            "/portfolio", ["That export format is not available."], "warning"
        )
    options = {
        "node": form.get("node") or None,
        "track": _field(form, "track"),
        "include_active": "include_active" in form,
        "include_rejected": "include_rejected" in form,
        "include_superseded": "include_superseded" in form,
        "include_paths": "include_paths" in form,
        "include_notes": "include_notes" in form,
        "include_blockers": "include_blockers" in form,
        "include_reviews": "include_reviews" in form,
        "include_free_text": "include_free_text" in form,
        "include_urls": "include_urls" in form,
        "format": fmt,
        "output": None,
    }
    exit_code, lines = _dispatch_web(root, "portfolio export", **options)
    return _finish_write(next_url, lines, exit_code)


def post_analytics_export(root, form: dict):
    """POST `/analytics/export` — delegate export to the canonical CLI command."""
    theme = _field(form, "theme") or "all"
    fmt = _field(form, "format") or "md"
    group_by = _field(form, "group_by") or "prefix"
    raw_days = _field(form, "days")
    try:
        days = int(raw_days) if raw_days else None
    except ValueError:
        return _redirect_with_notice(
            "/analytics", ["The review window must be a number of days."], "warning"
        )
    if theme not in {"all", "velocity", "blockers", "reviews", "evidence"}:
        return _redirect_with_notice(
            "/analytics", ["That theme is not available."], "warning"
        )
    if fmt not in {"md", "html", "json"} or group_by not in {"prefix", "track"}:
        return _redirect_with_notice(
            "/analytics", ["That export shape is not available."], "warning"
        )
    exit_code, lines = _dispatch_web(
        root,
        "analytics export",
        theme=theme,
        format=fmt,
        days=days,
        group_by=group_by,
        state=[],
        output=None,
    )
    return _finish_write("/analytics", lines, exit_code)

