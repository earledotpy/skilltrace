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
    """POST `/nodes/{id}/pass` — always 303 (T5 §D1): ok to the node page,
    refusal back to the pass step as a warning flash, failure with /health."""
    exit_code, lines = _dispatch_web(root, "pass", node_id=node_id)
    return _finish_write(
        f"/nodes/{node_id}",
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

