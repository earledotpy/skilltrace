"""
GET ``/session`` and ``/session/close`` — the Study cockpit and the safe
Session closure (spec-v3-study-day §10.5, §10.6).

One open Session by engine invariant. The timer is **presentation only**:
a page load, navigation, inspection or timer expiry records no work
(IC-3, R6). Blocked SessionWork is labelled *blocked work* — a
session-scoped observation — and is never a Blocker (IC-10).
"""

from __future__ import annotations

from datetime import datetime

from ...evidence.eligibility import compute_eligibility
from ...execution.records import open_session
from ...execution.staleness import stale_session_hours
from . import _clock
from ._shared import _CANONICAL_STATE_LABELS, _esc, _session_node_id, _table, plural
from .evidence import evidence_figures
from .forms import _resolve_blocker_form, _work_form_fields
from .sections import BARE, INLINE, section
from .shell import _page_head


def _open_hours(session, *, now: datetime) -> float | None:
    """How long the Session has been open — a derived figure, never a record.

    ``None`` when the stored start is unparseable: the page states no
    elapsed time rather than inventing one (a bad timestamp is ``validate``'s
    concern, not a reason to crash the cockpit).
    """
    try:
        started = datetime.fromisoformat(session.started_at)
    except (TypeError, ValueError):
        return None
    if started.tzinfo is None:
        started = started.replace(tzinfo=now.tzinfo)
    elapsed = (now - started).total_seconds()
    if elapsed < 0:
        # A start in the future cannot yield a truthful open time; state no
        # figure rather than a zero dressed as fact (SC-00a).
        return None
    return elapsed / 3600


def _duration(hours: float) -> str:
    """A calm human duration — orientation, never a measurement of work."""
    if hours < 1:
        return "under an hour"
    whole = int(hours)
    if whole >= 48:
        days = whole // 24
        return f"{days} {plural(days, 'day', 'days')}"
    return f"{whole} hour{plural(whole)}"


def _session_minutes(view, session) -> int:
    """The minutes recorded in this Session — one sum for every surface."""
    return sum(w.minutes or 0 for w in view.work if w.session_id == session.id)


def _open_for_label(session, *, now: datetime) -> str:
    """The honest elapsed-time label — ``unknown`` when it cannot be derived."""
    hours = _open_hours(session, now=now)
    return _duration(hours) if hours is not None else "unknown"


def _stale(root, session, *, now: datetime) -> float | None:
    """The open hours when the Session is past the policy window, else None.

    Staleness is derived (CONTEXT.md): it warns and never blocks work or
    closure. The threshold is seed data (``policy/workload.yaml``), read
    through the one engine helper.
    """
    hours = _open_hours(session, now=now)
    if hours is None:
        return None
    return hours if hours >= stale_session_hours(root) else None


def _stale_banner(stale_hours: float | None) -> str:
    """The stale warning: noticeable, honest, and never a dead end."""
    if stale_hours is None:
        return ""
    return (
        '<div class="banner advisory">\n'
        f"<p>This session has been open for {_esc(_duration(stale_hours))}. It "
        "may be one you forgot to close. Nothing is blocked by that: you can "
        "keep recording work, or close it with the time you actually stopped "
        "so the record stays honest.</p>\n"
        "</div>\n"
    )


def _pass_facts(view, node_id: str, state: str) -> tuple[str, str]:
    """The cockpit's eligibility fact and its next valid action (§10.5).

    Eligibility is derived on demand (never stored), and passing is always a
    separate, explicit decision on its own panel — this row says what is
    true, never what to assert.
    """
    if not node_id:
        return "—", "Next: close this session — it has no skill to work."
    if state in ("passed", "mastered"):
        return (
            f"Already {_CANONICAL_STATE_LABELS[state].lower()} — closing changes nothing",
            "Next: open the evidence workspace, or close this session. "
            "Closing changes no progress.",
        )
    if state == "locked":
        return (
            "Locked — no work or pass is possible",
            "Next: close this session — this skill cannot take work.",
        )
    eligible = compute_eligibility(
        node_id,
        view.specs_by_node.get(node_id, []),
        has_gate=node_id in view.has_gate,
        records=view.records,
        node_state=state,
    ).eligible
    if eligible:
        return (
            "Ready — passing is a separate decision",
            'Next: keep working, or decide on the '
            f'<a href="/nodes/{_esc(node_id)}/pass">pass panel</a>. '
            "Closing does neither.",
        )
    return (
        "Not yet",
        "Next: record the work you did below, or open the evidence "
        "workspace.",
    )


def _session_facts(view, session, node_id: str, *, now: datetime) -> str:
    """The cockpit's timer, totals and next action — presentation only.

    The elapsed figure is rendered once, server-side. It is not a
    ``SessionWork`` field, never becomes work, and no page load, navigation,
    inspection or elapsed time records anything (IC-3, R6).
    """
    state = view.store.state_of(node_id) if node_id else ""
    eligibility, next_action = _pass_facts(view, node_id, state)
    open_for = _open_for_label(session, now=now)
    return (
        '<div class="rows">\n'
        '<div class="row"><span class="row-label">Timer</span>'
        f'<span class="row-value">Open for {_esc(open_for)}</span></div>\n'
        '<div class="row"><span class="row-label">Work recorded</span>'
        f'<span class="row-value">{_session_minutes(view, session)} minutes'
        "</span></div>\n"
        '<div class="row"><span class="row-label">Pass eligibility</span>'
        f'<span class="row-value">{_esc(eligibility)}</span></div>\n'
        "</div>\n"
        '<p class="small mut">The elapsed time is shown for orientation only. '
        "It is never recorded and never becomes work; only the work you log "
        "below is saved.</p>\n"
        f'<p class="small mut">{next_action}</p>\n'
    )


def _evidence_section(view, node_id: str) -> str:
    """The evidence requirements for the bound SkillNode (R2, R7).

    Wanted and recorded stay two labelled figures, derived once
    (:func:`evidence.evidence_figures`) so the cockpit and the evidence
    workspace cannot disagree. The full history stays one link away.
    """
    if not node_id:
        return ""
    specs = view.specs_by_node.get(node_id, [])
    if not specs:
        inner = (
            '<div class="state state-empty">\n'
            '<p class="state-title">Nothing is required here</p>\n'
            '<p class="state-body">This skill has no artifact specification, '
            "so there is no proof to gather before passing it.</p>\n"
            "</div>\n"
        )
    else:
        figures = evidence_figures(view, node_id)
        inner = (
            '<div class="rows">\n'
            '<div class="row"><span class="row-label">Evidence wanted</span>'
            f'<span class="row-value">{figures.wanted} required</span></div>\n'
            '<div class="row"><span class="row-label">Evidence recorded</span>'
            f'<span class="row-value">{figures.accepted_live} accepted, '
            f"{figures.rejected} rejected, {figures.superseded} superseded"
            "</span></div>\n"
            "</div>\n"
        )
    inner += (
        '<div class="command-bar"><div class="actions">'
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}/evidence">'
        "Open the evidence workspace</a>"
        "</div></div>\n"
    )
    return section(
        "Evidence for this skill",
        "What the proof asks for, before any work begins.",
        inner,
        frame=INLINE,
    )


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
    return section(
        "Blocked work",
        "Work that ended stuck inside this session. It is an observation "
        "about one session — it is not a blocker, and it creates no record "
        "of its own.",
        _table(["Skill", "What you noted", "When"], rows),
        frame=INLINE,
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
            '<div class="form-row"><label for="blocker-description">'
            "What is in the way</label>\n"
            '<input type="text" name="description" id="blocker-description" '
            "required></div>\n"
            '<p class="small mut">A blocker records persistent stuckness. It '
            "never resolves itself, never marks work complete and never "
            "passes a skill.</p>\n"
            '<button type="submit" class="btn secondary">Record this blocker'
            "</button>\n"
            "</form>\n"
            "</details>\n"
        )
    return section(
        "Still stuck?",
        "If this keeps happening across sessions, record it as a blocker so "
        "it survives the session. Recording one is your explicit action.",
        "".join(parts),
        frame=INLINE,
    )


def _blocker_section(view) -> str:
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
    node_title = view.titles.get(node_id) or node_id or "Your session"
    now = _clock.now_utc()
    stale_hours = _stale(root, session, now=now)
    work_rows = _session_rows(view, session)
    blockers = _blocker_section(view)
    blocked_work = _blocked_work(view, session)
    create_blocker = _create_blocker_offer(view, session)
    skill_link = (
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">'
        "Open this skill</a>\n"
        if node_id
        else ""
    )
    if node_id:
        work_section = section(
            "Work in this session",
            "Recording work saves the minutes and the notes you type, against "
            "this skill and this session. Blocked work also needs a note "
            "saying where you got stuck. Nothing else is written: the timer "
            "never records, and looking at another skill never records "
            "anything either.",
            '<form method="post" action="/work">\n'
            f'<input type="hidden" name="node_id" value="{_esc(node_id)}">\n'
            '<input type="hidden" name="next" value="/session">\n'
            f"{_work_form_fields()}"
            '<button type="submit" class="btn primary">Record this work'
            "</button>\n"
            "</form>\n",
            frame=INLINE,
        )
    else:
        # A session with no work has no bound skill (corrupt or hand-edited
        # data). Never render a form the domain would always refuse: name
        # the state and offer the one safe move.
        work_section = section(
            "Work in this session",
            "",
            '<div class="state state-refusal">\n'
            '<p class="state-title">No skill is bound to this session</p>\n'
            '<p class="state-body">Work is recorded against the skill a '
            "session is bound to, and this session has none on record. Close "
            "it and start again from Today; nothing already saved is lost."
            "</p>\n"
            '<p><a href="/session/close">Close this session</a> or '
            '<a href="/">go to Today</a>.</p>\n'
            "</div>\n",
            frame=INLINE,
        )

    body = (
        head
        + _stale_banner(stale_hours)
        + section(
            node_title,
            "Session open — the timer is presentation only and records "
            "nothing by itself.",
            '<div class="command-bar">\n'
            '<div class="actions">\n'
            f"{skill_link}"
            '<a class="btn secondary" href="/session/close">'
            "Close the session</a>\n"
            "</div>\n"
            "</div>\n"
            '<p class="small mut">A second session cannot be started while '
            "this one is open: record work here against the skill it is bound "
            "to, or close this session first. Nothing on this page closes or "
            "replaces it.</p>\n",
        )
        + section(
            "This session",
            "",
            _session_facts(view, session, node_id, now=now),
            frame=INLINE,
        )
        + work_section
        + section(
            "Session work",
            "",
            f"{work_rows}",
            frame=BARE,
        )
        + f"{blocked_work}"
        + f"{create_blocker}"
        + _evidence_section(view, node_id)
        + section(
            "Blockers",
            "A blocker is persistent stuckness you recorded deliberately. It "
            "is a different thing from blocked work above.",
            f"{blockers}",
            frame=INLINE,
        )
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

    node_id = _session_node_id(view, session)
    node_title = view.titles.get(node_id) or node_id or "Your session"
    now = _clock.now_utc()
    stale_hours = _stale(root, session, now=now)
    open_for_line = _open_for_label(session, now=now)

    # §10.6: the panel discloses what remains after closure — the unresolved
    # Blockers, the asserted state, and the evidence standing. None of them
    # changes by closing.
    state = view.store.state_of(node_id) if node_id else ""
    open_blockers = [
        b
        for b in view.blockers
        if b.status == "open" and b.node_id == node_id
    ]
    if open_blockers:
        blockers_fact = (
            f"{len(open_blockers)} open — closing resolves none of them"
        )
    else:
        blockers_fact = "None open"
    state_fact = (
        f"{_CANONICAL_STATE_LABELS.get(state, state)} — unchanged by closing"
        if state
        else "—"
    )
    if node_id and view.specs_by_node.get(node_id):
        figures = evidence_figures(view, node_id)
        evidence_fact = (
            f"{figures.accepted_live} accepted, {figures.rejected} rejected, "
            f"{figures.superseded} superseded — unchanged by closing"
        )
    else:
        evidence_fact = "Nothing is required"

    end_field = ""
    if stale_hours is not None:
        end_field = (
            '<div class="form-row"><label for="session-end">'
            "When did you actually stop? (optional)</label>"
            '<input type="text" name="end" id="session-end" '
            'placeholder="2026-11-16T18:30:00+00:00">'
            '<p class="small mut">Leave it blank to record the time you close '
            "it now. A time in the future, or before the session started, is "
            "refused — and nothing you recorded is lost.</p></div>\n"
        )

    body = (
        head
        + _stale_banner(stale_hours)
        + '<section class="section">\n'
        + '<h2 class="section-title">Close this session</h2>\n'
        + '<div class="rows">\n'
        + f'<div class="row"><span class="row-label">Skill</span>'
        f'<span class="row-value">{_esc(node_title)}</span></div>\n'
        + f'<div class="row"><span class="row-label">Open for</span>'
        f'<span class="row-value">{_esc(open_for_line)}</span></div>\n'
        + f'<div class="row"><span class="row-label">Work recorded</span>'
        f'<span class="row-value">{_session_minutes(view, session)} minutes'
        "</span></div>\n"
        + '<div class="row"><span class="row-label">Started</span>'
        f'<span class="row-value">{_esc(session.started_at)}</span></div>\n'
        + '<div class="row"><span class="row-label">Open blockers</span>'
        f'<span class="row-value">{_esc(blockers_fact)}</span></div>\n'
        + '<div class="row"><span class="row-label">State after closing</span>'
        f'<span class="row-value">{_esc(state_fact)}</span></div>\n'
        + '<div class="row"><span class="row-label">Evidence afterwards</span>'
        f'<span class="row-value">{_esc(evidence_fact)}</span></div>\n'
        + "</div>\n"
        + '<div class="banner advisory">Closing saves the work you recorded. '
        "It does not pass a skill, resolve a blocker or complete a review — "
        "those are separate, explicit actions.</div>\n"
        + '<form method="post" action="/session/close">\n'
        + '<input type="hidden" name="next" value="/">\n'
        + end_field
        + '<div class="command-bar"><div class="actions">'
        + '<button type="submit" class="btn primary">Close the session</button>'
        + '<a class="btn secondary" href="/session">Keep working</a>'
        + "</div></div>\n"
        + "</form>\n"
        + "</section>\n"
    )
    return "Close session", body, 200
