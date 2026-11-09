"""
GET ``/session`` and ``/session/close`` — the Study cockpit and the safe
Session closure (spec-v3-study-day §10.5, §10.6).

One open Session by engine invariant. The timer is **presentation only**:
a page load, navigation, inspection or timer expiry records no work
(IC-3, R6). Blocked SessionWork is labelled *blocked work* — a
session-scoped observation — and is never a Blocker (IC-10).
"""

from __future__ import annotations

from ...execution.records import open_session
from ._shared import _esc, _session_node_id, _table
from .forms import _resolve_blocker_form, _work_form_fields
from .shell import _page_head


def _session_rows(view, session) -> str:
    """The SessionWork history of the open Session — one honest table."""
    items = [w for w in view.work if w.session_id == session.id]
    if not items:
        return (
            '<div class="state state-empty">\n'
            '<p class="state-title">No work recorded yet</p>\n'
            '<p class="state-body">Nothing has been logged against this session. '
            "Logging work records the minutes and notes you choose — the timer "
            "never records anything by itself.</p>\n"
            "</div>\n"
        )
    rows = [
        [
            _esc(view.titles.get(item.node_id) or item.node_id),
            _esc(str(item.minutes)) if item.minutes is not None else "—",
            "blocked work" if item.blocked else "worked",
            _esc(item.notes or ""),
        ]
        for item in items
    ]
    return _table(["Skill", "Minutes", "What happened", "Notes"], rows)


def _blocked_work(view, session) -> str:
    """The blocked work of this Session — a session-scoped observation.

    Blocked work is **never** a Blocker (IC-10): it is what happened
    inside one session and it disappears with the session. A Blocker is
    the explicit persistent-stuckness record, shown separately below.
    """
    blocked = [
        w
        for w in view.work
        if w.session_id == session.id and w.blocked
    ]
    if not blocked:
        return ""
    rows = [
        [
            _esc(view.titles.get(item.node_id) or item.node_id),
            _esc(item.notes or "—"),
            _esc(str(item.created_at or "")),
        ]
        for item in blocked
    ]
    return (
        '<section class="section">\n'
        '<h2 class="section-title">Blocked work</h2>\n'
        '<p class="section-meta">Work that ended stuck inside this session. '
        "It is an observation about one session — it is not a blocker, and "
        "it creates no record of its own.</p>\n"
        + _table(["Skill", "What you noted", "When"], rows)
        + "</section>\n"
    )


def _create_blocker_offer(view, session) -> str:
    """After persistent blocked work, offer to record a Blocker.

    The offer is explicit and never a side effect: blocked work on its
    own creates nothing. A second open Blocker warns about likely
    duplication but is not forbidden.
    """
    blocked_nodes = {
        w.node_id for w in view.work if w.session_id == session.id and w.blocked
    }
    if not blocked_nodes:
        return ""
    already_open = {
        b.node_id for b in view.blockers if b.status == "open"
    }
    parts = []
    for node_id in sorted(blocked_nodes):
        title = view.titles.get(node_id) or node_id
        duplicate = (
            '<p class="banner advisory">A blocker is already open on this '
            "skill. Another one is allowed, but you may be recording the "
            "same stuckness twice.</p>\n"
            if node_id in already_open
            else ""
        )
        parts.append(
            '<details class="disclosure">\n'
            "<summary>Record a blocker for "
            f"{_esc(title)}</summary>\n"
            + duplicate
            + f'<form method="post" action="/nodes/{_esc(node_id)}/blockers">\n'
            '<input type="hidden" name="next" value="/session">\n'
            '<div class="form-row"><label>What is in the way</label>\n'
            '<input type="text" name="description" required></div>\n'
            '<p class="small mut">A blocker records persistent stuckness. It '
            "never resolves itself, never marks work complete and never "
            "passes a skill.</p>\n"
            '<button type="submit" class="btn secondary">Record this blocker'
            "</button>\n"
            "</form>\n"
            "</details>\n"
        )
    return (
        '<section class="section">\n'
        "<h2 class=\"section-title\">Still stuck?</h2>\n"
        '<p class="section-meta">If this keeps happening across sessions, '
        "record it as a blocker so it survives the session. Recording one is "
        "your explicit action.</p>\n"
        + "".join(parts)
        + "</section>\n"
    )


def _open_blockers(view) -> str:
    """The open Blockers of the Session's nodes — explicit records, not work."""
    open_blockers = [b for b in view.blockers if b.status == "open"]
    if not open_blockers:
        return (
            '<div class="state state-empty">\n'
            '<p class="state-title">No blockers</p>\n'
            '<p class="state-body">Nothing is recorded as persistently stuck. '
            "Blocked work inside a session is a session-scoped observation; it "
            "never creates a blocker on its own.</p>\n"
            "</div>\n"
        )
    rows = [
        [
            _esc(view.titles.get(b.node_id) or b.node_id),
            _esc(b.description),
            _resolve_blocker_form(b.id, "/session"),
        ]
        for b in open_blockers
    ]
    return _table(["Skill", "What is in the way", "Resolve"], rows)


def session_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/session` — the Study cockpit for the one open Session.

    The cockpit shows the Session, its chosen SkillNode, the SessionWork
    history, the open Blockers, and the next valid learner action. It
    records nothing on load: the timer is presentation only.
    """
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/session",
        current_view="session",
        path="/session",
    )
    if failure is not None:
        return failure

    session = open_session(view.sessions)
    if session is None:
        body = (
            head
            + '<section class="section">\n'
            + '<div class="state state-empty">\n'
            + '<p class="state-title">No session is open</p>\n'
            + '<p class="state-body">A session is opened by one explicit '
            "action — starting to study a skill. Nothing here opens one by "
            "itself, and closing one never happens by navigation.</p>\n"
            + '<p><a href="/">Back to Today</a></p>\n'
            + "</div>\n"
            + "</section>\n"
        )
        return "Study", body, 200

    node_id = _session_node_id(view, session)
    node_title = view.titles.get(node_id) or node_id
    work_rows = _session_rows(view, session)
    blockers = _open_blockers(view)
    blocked_work = _blocked_work(view, session)
    create_blocker = _create_blocker_offer(view, session)

    body = (
        head
        + '<section class="section">\n'
        + '<div class="section-head">\n'
        + f'<h2 class="section-title">{_esc(node_title)}</h2>\n'
        + '<p class="section-meta">Session open — the timer is presentation '
        "only and records nothing by itself.</p>\n"
        + "</div>\n"
        + '<div class="command-bar">\n'
        + '<div class="actions">\n'
        + f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Open this skill</a>\n'
        + '<a class="btn secondary" href="/session/close">Close the session</a>\n'
        + "</div>\n"
        + "</div>\n"
        + "</section>\n"
        + '<section class="section">\n'
        + '<h2 class="section-title">Work in this session</h2>\n'
        + '<p class="section-meta">Recording work saves the minutes and the '
        "notes you type, against this skill and this session. Nothing else "
        "is written: the timer never records, and looking at another skill "
        "never records anything either.</p>\n"
        + '<form method="post" action="/work">\n'
        + f'<input type="hidden" name="node_id" value="{_esc(node_id)}">\n'
        + '<input type="hidden" name="next" value="/session">\n'
        + f"{_work_form_fields()}"
        + '<button type="submit" class="btn primary">Record this work</button>\n'
        + "</form>\n"
        + "</section>\n"
        + '<section class="section">\n'
        + '<h2 class="section-title">Session work</h2>\n'
        + f"{work_rows}"
        + "</section>\n"
        + f"{blocked_work}"
        + f"{create_blocker}"
        + '<section class="section">\n'
        + '<h2 class="section-title">Blockers</h2>\n'
        + '<p class="section-meta">A blocker is persistent stuckness you '
        "recorded deliberately. It is a different thing from blocked work "
        "above.</p>\n"
        + f"{blockers}"
        + "</section>\n"
    )
    return "Study", body, 200


def session_close_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/session/close` — the safe Session closure panel.

    Closing is always a separate explicit action. It implies nothing: work
    is saved, and no skill is passed, no blocker resolved and no review
    completed (C05).
    """
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/session/close",
        current_view="session-close",
        path="/session/close",
    )
    if failure is not None:
        return failure

    session = open_session(view.sessions)
    if session is None:
        body = (
            head
            + '<section class="section">\n'
            + '<div class="state state-empty">\n'
            + '<p class="state-title">No session is open</p>\n'
            + '<p class="state-body">There is nothing to close.</p>\n'
            + "</div>\n"
            + "</section>\n"
        )
        return "Close session", body, 200

    items = [w for w in view.work if w.session_id == session.id]
    minutes = sum(w.minutes or 0 for w in items)
    node_id = _session_node_id(view, session)
    node_title = view.titles.get(node_id) or node_id

    body = (
        head
        + '<section class="section">\n'
        + '<h2 class="section-title">Close this session</h2>\n'
        + '<div class="rows">\n'
        + f'<div class="row"><span class="row-label">Skill</span>'
        f'<span class="row-value">{_esc(node_title)}</span></div>\n'
        + f'<div class="row"><span class="row-label">Work recorded</span>'
        f'<span class="row-value">{minutes} minutes</span></div>\n'
        + '<div class="row"><span class="row-label">Started</span>'
        f'<span class="row-value">{_esc(session.started_at)}</span></div>\n'
        + "</div>\n"
        + '<div class="banner advisory">Closing saves the work you recorded. '
        "It does not pass a skill, resolve a blocker or complete a review — "
        "those are separate, explicit actions.</div>\n"
        + '<form method="post" action="/session/close">\n'
        + '<input type="hidden" name="next" value="/">\n'
        + '<div class="command-bar"><div class="actions">'
        + '<button type="submit" class="btn primary">Close the session</button>'
        + '<a class="btn secondary" href="/session">Keep working</a>'
        + "</div></div>\n"
        + "</form>\n"
        + "</section>\n"
    )
    return "Close session", body, 200
