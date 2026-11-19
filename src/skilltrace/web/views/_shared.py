"""
Cross-cutting page primitives (ADR 0009): escaping, field
parsing, tables, the shared banner, and GET-side flash rendering.

``_esc`` and ``plural`` are re-exported from the sublayer's text
micro-utilities (``interface.text``, #315) rather than defined here: the page
layer has no escaper of its own, so every page body in this package escapes
through the one door.
"""

from __future__ import annotations

import re

from ...context import JoinedView
from ...execution.overdue import utc_today
from ...resources.status import derive_status
from ..interface import esc as _esc
from ..interface import plural as plural  # explicit re-export (PEP 484) — see docstring

#: The assurance the discovery surfaces share when an empty result is a fact
#: about the curriculum, not the learner (R7): stated once here, so ``/next``
#: and ``/find`` can never disagree about who the fact is about. Today's day
#: state is about *availability* rather than the curriculum, so it keeps its
#: own wording; this constant covers the curriculum-fact case only.
ASSURANCE = "That is a fact about the curriculum, not about you."


def _curriculum_unreadable_section(
    *, verb: str, reload_href: str, reload_label: str
) -> str:
    """The could-not-compute state for a curriculum whose source is missing.

    One section for every discovery surface, so an unreadable source reads
    the same on ``/next`` and ``/find`` — never merged with the empty state
    (SC-00a). Only the surface's own verb ('search' / 'rank') and its way
    back differ; the caller checks the source and appends this.
    """
    return (
        '<section class="section">\n'
        '<div class="state state-failure">\n'
        '<p class="state-title">The curriculum could not be read</p>\n'
        '<p class="state-body">The graph/nodes/ directory that holds the '
        f"curriculum is missing, so there is nothing to {verb} and no fact "
        "is claimed about the curriculum. Nothing about your progress "
        "changed.</p>\n"
        '<p><a href="/health">Open Health</a> for the detail — or '
        "restore the directory and "
        f'<a href="{_esc(reload_href)}">{_esc(reload_label)}</a>.</p>\n'
        "</div>\n"
        "</section>\n"
    )


def _output_banners(lines: list[str], *, default_class: str = "advisory") -> str:
    """Captured handler output as banners — through the P3.1 translation seam.

    Every line flows through the interface sublayer's forbidden-vocabulary
    translation (no surface bypasses it): CLI voice is rewritten as the
    human act, and the CLI banner kinds map onto the sublayer's semantic
    classes (the alias classes never reach a page). Escaping stays total.
    """
    from ..interface import banners

    class_map = {"ok": "success", "warning": "warn", "error": "err"}
    kind = class_map.get(default_class, "attention")
    parts: list[str] = []
    for banner_kind, banner_text in banners(lines, default_class=kind):
        css = banner_kind or kind
        parts.append(f'<p class="banner {_esc(css)}">{_esc(banner_text)}</p>')
    return "".join(parts)


def _flash_tuples(query: dict) -> list[tuple[str, str]]:
    """Flash banners carried across a redirect as (css, text) tuples."""
    from ..interface import banners

    text = (query.get("notice") or [""])[0]
    if not text:
        return []
    kind = (query.get("kind") or ["ok"])[0]
    if kind not in {"ok", "warning", "error"}:
        kind = "ok"
    class_map = {"ok": "success", "warning": "warn", "error": "err"}
    css = class_map.get(kind, "attention")
    return [
        (banner_kind or css, banner_text)
        for banner_kind, banner_text in banners(text.splitlines(), default_class=css)
    ]


def _linkify_health(escaped_text: str) -> str:
    """Point operational failures at /health (P3.5) — the one link in a flash."""
    return escaped_text.replace("/health", '<a href="/health">/health</a>')


def _flash_html(query: dict, dismiss_path: str = "/") -> str:
    """Flash banners carried across a redirect in the query string (T5 §F+P3.5).

    Every banner is translated human copy from the one translation module
    (fixed at its source, never redacted at the address bar). Dismissal is
    a plain link to the path without the query string; operational failures
    point at /health.
    """
    parts: list[str] = []
    for css, text in _flash_tuples(query):
        banner = _linkify_health(_esc(text))
        parts.append(f'<p class="banner {_esc(css)}">{banner}</p>\n')
    if parts:
        parts.append(
            f'<p class="flash-dismiss"><a href="{_esc(dismiss_path)}">Dismiss</a></p>\n'
        )
    return "".join(parts)


def _field(form: dict, key: str) -> str | None:
    values = form.get(key)
    if not values or not values[0].strip():
        return None
    return values[0]


def _int_field(form: dict, key: str) -> tuple[int | None, str | None]:
    raw = _field(form, key)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{key} must be an integer."


def _degraded_banner(view: JoinedView) -> str:
    """Advisory notice when lenient layers degraded — reads as empty only."""
    if not view.degraded:
        return ""
    names = ", ".join(sorted(set(view.degraded)))
    return (
        '<p class="banner advisory">Some supporting details failed to load and read '
        f"as empty ({_esc(names)}) — everything you can do here still works, and a "
        "refusal on click remains the truth. The health roll-up carries the detail.</p>"
    )


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _sentence_case(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if text.isupper():
        lowered = text.lower()
        return lowered[0].upper() + lowered[1:]
    return text


_CANONICAL_STATE_LABELS = {
    "locked": "Locked",
    "available": "Available",
    "active": "Active",
    "passed": "Passed",
    "mastered": "Mastered",
    "ready to start": "Available",
    "in progress": "Active",
}


def _normalize_pill_label(label: str) -> str:
    lowered = label.strip().lower()
    return _CANONICAL_STATE_LABELS.get(lowered, label)


def _parse_int(query: dict, key: str, default: int) -> int | None:
    values = query.get(key)
    if not values:
        return default
    try:
        return int(values[0])
    except ValueError:
        return None


def _table(headers: list[str], rows: list[list[str]]) -> str:
    """A data table with a caption and header cells (AX-4).

    Every table keeps its row/column association: the header cells are
    real ``<th>`` elements and the caption names what the table is, so
    the meaning survives a screen reader and a 200% zoom.
    """
    head = "".join(f'<th scope="col">{h}</th>' for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows
    )
    caption = f"<caption>{_esc(' / '.join(headers))}</caption>"
    return (
        f'<table class="data">{caption}'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    )



def superseded_ids(view) -> set[str]:
    """The record ids a newer record supersedes — derived, never stored.

    Supersession is a pointer on the *newer* record (``supersedes``), so the
    older record's standing is derived on read. One helper serves every
    surface that shows standing, so two pages cannot disagree about whether
    a record still counts.
    """
    return {r.supersedes for r in view.records if r.supersedes}


def record_standing(view, record) -> str:
    """One record's derived standing: ``live``, ``superseded`` or ``rejected``.

    A rejection is an honest outcome, not a command failure, and a
    superseded record keeps its place in history — neither is ever deleted
    (HB-5).
    """
    if record.id in superseded_ids(view):
        return "superseded"
    return "live" if record.accepted else "rejected"


def _session_node_id(view, session) -> str:
    """The SkillNode an open Session is bound to.

    A ``Session`` record carries no node id of its own: the bound node is
    the one the session's work was logged against. Every surface that
    shows the open Session derives it here, so Today and the Study
    cockpit cannot drift apart — and with no work logged, there is no
    bound node yet, which is the honest answer rather than a guess.
    """
    items = [w for w in view.work if w.session_id == session.id]
    for item in reversed(items):
        if item.node_id in view.node_map:
            return item.node_id
    return ""


def resources_with_status(view, node_id: str):
    """The ``LearningResource`` records for a skill, each with derived status.

    One derivation for every surface that lists study material: the node
    page and the cockpit's Blocker options cannot disagree about whether a
    resource is verified, stale or broken. The date is the canonical
    read-surface funnel (:func:`skilltrace.execution.overdue.utc_today`),
    so the snapshot harnesses pin it exactly as they pin every other
    derived-today fact.
    """
    window = view.policy.resource_stale_after_days
    today = utc_today()
    return [
        (
            resource,
            derive_status(resource, today=today, stale_after_days=window),
        )
        for resource in view.resources_by_node.get(node_id, [])
    ]
