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


def _redirect_with_notice(location: str, lines: list[str], kind: str) -> Redirect:
    """PRG redirect carrying translated human copy as the flash notice (T5 P3.5+D2).

    The URL is a copy surface: copy is fixed at its source by the one
    translation module (no flags, command names, exit classes, paths,
    record ids or ADR numbers) and never redacted at the address bar.
    Banner-kind tags ride the ``kind`` param, never the notice text.
    """
    from ..interface import translate_lines

    clean: list[str] = []
    for line in translate_lines(lines):
        line = re.sub(r"^\[(?:error|warning|advisory)\]\s*", "", line).strip()
        if line:
            clean.append(line)
    notice = "\n".join(clean)
    params = urlencode({"notice": notice, "kind": kind})
    separator = "&" if "?" in location else "?"
    return Redirect(location=f"{location}{separator}{params}")


def _safe_next(form: dict, fallback: str) -> str:
    """The host page a form POST returns to — local paths only."""
    target = (form.get("next") or [fallback])[0]
    if target.startswith("/") and not target.startswith("//"):
        return target
    return fallback


def _finish_write(
    next_url: str,
    lines: list[str],
    exit_code: int,
    *,
    refusal_url: str | None = None,
) -> Redirect:
    """Map a dispatched write's exit code per the locked T5 contract (§D1+S5).

    Every POST → 303 See Other + translated flash; no 4xx ever leaves a
    write. ``0`` → ok flash to ``next_url``; ``2`` (domain refusal) →
    warning flash to ``refusal_url`` (the acceptance step for pass/master,
    else ``next_url``); ``1`` (operational failure) → error flash to
    ``next_url`` pointing at /health for the detail.
    """
    if exit_code == 0:
        return _redirect_with_notice(next_url, lines, "ok")
    if exit_code == 2:
        return _redirect_with_notice(refusal_url or next_url, lines, "warning")
    lines = [*lines, "Something went wrong — see /health for the detail."]
    return _redirect_with_notice(next_url, lines, "error")


def post_pass(root, node_id: str, form: dict):
    """POST `/nodes/{id}/pass` — always 303 (T5 §D1).

    A successful pass returns to the **pass panel**, which then renders
    the *result*: what changed, and the visible Review-state consequence
    (R3). Redirecting straight to the node page would hide that
    consequence behind a flash the learner has to remember — the spec
    requires the pass result to show the Review change, not merely to
    have caused one.
    """
    exit_code, lines = _dispatch_web(root, "pass", node_id=node_id)
    return _finish_write(
        f"/nodes/{node_id}/pass",
        lines,
        exit_code,
        refusal_url=f"/nodes/{node_id}/pass",
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


def post_start(root, node_id: str, form: dict):
    next_url = _safe_next(form, f"/nodes/{node_id}")
    exit_code, lines = _dispatch_web(
        root, "start", node_id=node_id, template=_field(form, "template")
    )
    return _finish_write(next_url, lines, exit_code)


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
    return _finish_write(next_url, lines, exit_code)


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
    next_url = _safe_next(form, f"/nodes/{node_id}")
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
    return _finish_write(next_url, lines, exit_code)


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

