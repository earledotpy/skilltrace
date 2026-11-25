"""
GET ``/reviews`` — the Reviews destination (spec-v3-study-day §10.10 and
§11.3; SL6, the P1.9 replacement).

One queue, ordered: overdue → scheduled by date → unsatisfactory follow-up
→ completed and cancelled history. Retention suggestions occupy a
**separately labelled advisory group** and create no record until the
learner schedules a Review — a suggestion is never shown as scheduled or
overdue (§11.3), and scheduling is always the learner's own explicit
action (§10.10).

Completing a Review is independent of the Session that started it and
requires an explicit outcome plus a result summary. Cancelling requires a
reason and preserves the cancelled history. Neither action demotes
asserted progress or masters a node: an unsatisfactory outcome creates
pressure only (HB-3).

Three non-success states are distinct and never merged (SC-00a):

* **no review-worthy node** — nothing is passed or mastered, so no check
  could ever watch anything: the empty state says why and preserves
  discovery;
* **no scheduled records** — skills a check could watch exist, but none
  has been scheduled: the state retains the values that do exist (the
  review-worthy skills and their suggested checks) and states the fact;
* **failed retention derivation** — the retention model's policy or its
  derivation did not load: the could-not-compute state claims nothing
  about the suggested checks (never zeroes) and points at Health, while
  the scheduled records — records, not derivations — stay readable.

Retention is spoken of as **retention status** learner-facing; the
canonical **Memory state** and **Retention confidence** are Operations
detail and never read as learner-facing certainty (§4 terminology
contract).
"""

from __future__ import annotations

from ...execution.overdue import is_overdue, utc_today
from ._shared import _esc, _table
from .sections import BARE, INLINE, section
from .shell import _page_head

# --- the facts --------------------------------------------------------------- #


def _review_worthy_nodes(view) -> list[str]:
    """The passed or mastered skills — the only things a check can watch.

    A Review is a check on a passed or mastered node, never on a node with
    nothing to retain (CONTEXT.md); the retention model's own
    ``RETAINED_STATES`` is the one rule, so this page and the derivation
    cannot disagree about what is checkable.
    """
    from ...policy.retention_model import RETAINED_STATES

    worthy: list[str] = []
    for node in sorted(view.nodes, key=lambda n: n.id):
        entry = view.store.entries.get(node.id)
        state = entry.state if entry is not None else view.store.state_of(node.id)
        if state in RETAINED_STATES:
            worthy.append(node.id)
    return worthy


def _retention_suggestions(view, today) -> list:
    """The derived advisory retention suggestions — never in the queue.

    Raises when the derivation cannot run: a missing policy seed or a
    failed derivation is the caller's could-not-compute state, never a
    silent empty claim (SC-00a).
    """
    seed = view.policy.retention
    if seed is None:
        raise LookupError("the retention model's policy did not load")
    from ...policy.retention_model import derive_memory_states

    states = [
        s
        for s in derive_memory_states(
            nodes=view.nodes,
            store=view.store,
            reviews=view.reviews,
            seed=seed,
            today=today,
        )
        if s.below_threshold
    ]
    states.sort(key=lambda s: s.confidence)
    return states


# --- the queue --------------------------------------------------------------- #


def _overdue_section(view, today) -> str:
    overdue = [
        r
        for r in view.reviews
        if r.status == "scheduled" and is_overdue(r, today=today)
    ]
    if not overdue:
        return ""
    rows = [
        [
            _esc(view.titles.get(r.node_id) or r.node_id),
            _esc(r.scheduled_for),
            _review_actions(r),
        ]
        for r in sorted(overdue, key=lambda r: r.scheduled_for)
    ]
    return section(
        "Overdue",
        "These checks are past their date. They are waiting on you.",
        _table(["Skill", "Due", "Do it"], rows),
        frame=INLINE,
    )


def _scheduled_section(view, today) -> str:
    scheduled = [
        r
        for r in view.reviews
        if r.status == "scheduled" and not is_overdue(r, today=today)
    ]
    if not scheduled:
        return ""
    rows = [
        [
            _esc(view.titles.get(r.node_id) or r.node_id),
            _esc(r.scheduled_for),
            _review_actions(r),
        ]
        for r in sorted(scheduled, key=lambda r: r.scheduled_for)
    ]
    return section(
        "Scheduled",
        "",
        _table(["Skill", "Due", "Do it"], rows),
        frame=BARE,
    )


def _unsatisfactory_section(view) -> str:
    """The unsatisfactory follow-up band — pressure, never demotion (§11.3).

    A completed check whose outcome was unsatisfactory is pulled out of
    history into its own band: it is the failure-side pressure the retention
    loop exists to surface, and the copy says what it never does — demote a
    passed skill or master one (HB-3).
    """
    stuck = [
        r
        for r in view.reviews
        if r.status == "completed" and r.outcome == "unsatisfactory"
    ]
    if not stuck:
        return ""
    rows = [
        [
            _esc(view.titles.get(r.node_id) or r.node_id),
            _esc(r.completed_at or ""),
            _esc(r.result_summary or ""),
        ]
        for r in sorted(stuck, key=lambda r: r.completed_at or "", reverse=True)
    ]
    return section(
        "Did not stick",
        "These checks came back unsatisfactory. That creates pressure to "
        "revisit the skill — it never demotes a skill you have passed and "
        "never masters one. Scheduling another check is your action.",
        _table(["Skill", "Completed", "What did not stick"], rows),
        frame=INLINE,
    )


def _history_section(view) -> str:
    history = [
        r
        for r in view.reviews
        if r.status == "cancelled"
        or (r.status == "completed" and r.outcome != "unsatisfactory")
    ]
    if not history:
        return ""
    rows = []
    for review in sorted(history, key=lambda r: r.scheduled_for, reverse=True):
        if review.status == "completed":
            detail = review.result_summary or ""
            label = f"completed — {review.outcome or 'no outcome'}"
        else:
            detail = review.cancel_reason or ""
            label = "cancelled"
        rows.append(
            [
                _esc(view.titles.get(review.node_id) or review.node_id),
                _esc(label),
                _esc(detail),
                _esc(review.completed_at or review.cancelled_at or ""),
            ]
        )
    return section(
        "History",
        "",
        _table(["Skill", "What happened", "Detail", "When"], rows),
        frame=BARE,
    )


def _review_actions(review) -> str:
    """The explicit complete and cancel actions for one scheduled Review."""
    rid = _esc(review.id)
    return (
        '<details class="disclosure"><summary>Complete or cancel</summary>'
        f'<form method="post" action="/reviews/{rid}/complete">'
        '<input type="hidden" name="next" value="/reviews">'
        '<div class="form-row"><label>Outcome</label>'
        '<span class="inline-check">'
        '<label><input type="radio" name="outcome" value="satisfactory"> '
        "satisfactory</label> "
        '<label><input type="radio" name="outcome" value="unsatisfactory"> '
        "unsatisfactory</label>"
        "</span></div>"
        '<div class="form-row"><label>Result summary</label>'
        '<input type="text" name="summary" required></div>'
        '<button type="submit" class="btn primary">Complete this review</button>'
        "</form>"
        f'<form method="post" action="/reviews/{rid}/cancel">'
        '<input type="hidden" name="next" value="/reviews">'
        '<div class="form-row"><label>Reason</label>'
        '<input type="text" name="reason" required></div>'
        '<button type="submit" class="btn secondary">Cancel this review</button>'
        "</form></details>"
    )


# --- the explicit scheduling action ------------------------------------------ #


def _schedule_section(view, worthy: list[str]) -> str:
    """The one scheduling action on this destination (RT-12, §11.3).

    A Review is created only here or from a passed skill's page — never by
    a suggestion, a sweep or a timer. The form lists only the skills a
    check *can* watch (passed or mastered), so the engine's own refusal
    stays the truth for anything else.
    """
    if not worthy:
        return ""
    options = "".join(
        f'<option value="{_esc(node_id)}">'
        f"{_esc(view.titles.get(node_id) or node_id)}</option>"
        for node_id in worthy
    )
    form = (
        '<form method="post" action="/reviews/schedule">\n'
        '<input type="hidden" name="next" value="/reviews">\n'
        '<div class="form-row"><label for="schedule-node">Skill</label>'
        '<select id="schedule-node" name="node_id" required>'
        '<option value="" selected disabled>Choose a skill</option>'
        f"{options}</select></div>\n"
        '<div class="form-row"><label for="schedule-date">Due date</label>'
        '<input id="schedule-date" type="date" name="date" required></div>\n'
        '<button type="submit" class="btn secondary">Schedule this check</button>\n'
        "</form>\n"
    )
    return section(
        "Schedule a check",
        "Scheduling is always your explicit action. A check watches a skill "
        "you have passed or mastered; nothing schedules itself, and a "
        "suggested check is never scheduled or overdue.",
        form,
        frame=BARE,
    )


# --- the states --------------------------------------------------------------- #


def _nothing_to_check_state() -> str:
    """Empty: no review-worthy node — nothing a check could watch (SC-00a)."""
    return (
        '<div class="state state-empty">\n'
        '<p class="state-title">Nothing to check yet</p>\n'
        '<p class="state-body">A check watches a skill you have passed or '
        "mastered and asks you to recall it later. Nothing is passed yet, "
        "so there is nothing for a check to watch. Everything you have "
        "already finished stays finished.</p>\n"
        '<p><a href="/find">Find a skill</a> or <a href="/next">see what to '
        "study next</a>.</p>\n"
        "</div>\n"
    )


def _no_records_state(*, suggestions: bool) -> str:
    """Limited: skills worth checking exist, but none is scheduled (SC-00a).

    The values that do exist are retained — the skills a check could watch,
    and any suggested checks below — and the fact is stated: the queue is
    empty because scheduling is the learner's own action, not because the
    loop is closed.
    """
    body = (
        "A check is created only by your own scheduling action — nothing "
        "schedules itself, and a suggested check is never scheduled or "
        "overdue."
    )
    if suggestions:
        body += " Suggested checks are below: advisory only, never scheduled."
    return (
        '<div class="state state-limited">\n'
        '<p class="state-title">No checks are scheduled</p>\n'
        f'<p class="state-body">{_esc(body)}</p>\n'
        "</div>\n"
    )


def _records_failure_section() -> str:
    """Could-not-compute: the review records did not load (SC-00a).

    The records behind the queue are unknown — never claimed as empty,
    never zeroed — and the suggested checks are left unclaimed too, since
    the derivation reads the same records.
    """
    return (
        '<section class="section">\n'
        '<div class="state state-failure">\n'
        '<p class="state-title">The review records did not load</p>\n'
        '<p class="state-body">The records behind the checks you scheduled '
        "did not load, so nothing is claimed about them — not even a "
        "count. Nothing about your progress changed.</p>\n"
        '<p><a href="/health">Open Health</a> for the detail, or try again '
        "in a moment.</p>\n"
        "</div>\n"
        "</section>\n"
    )


def _derivation_failure_state() -> str:
    """Could-not-compute: the retention derivation failed (SC-00a).

    Only the *advisory* half fails — the scheduled records above are
    records, not derivations, and stay readable. Nothing is claimed about
    the suggested checks, not even that there are none.
    """
    return (
        '<div class="state state-failure">\n'
        '<p class="state-title">Suggested checks could not be worked out</p>\n'
        '<p class="state-body">The retention model did not load, so nothing '
        "is claimed about suggested checks — not even that there are none. "
        "Your scheduled checks and their history are your records and are "
        "unaffected.</p>\n"
        '<p><a href="/health">Open Health</a> for the detail, or try again '
        "in a moment.</p>\n"
        "</div>\n"
    )


# --- the advisory group -------------------------------------------------------- #


def _suggestions_section(suggestions: list, view) -> str:
    """The advisory retention group — clearly not the scheduled queue.

    ``suggestions`` is the already-derived list: the caller owns the
    failure branch, so a derivation that could not run renders the
    could-not-compute state instead of this group (SC-00a).
    """
    if not suggestions:
        return ""
    rows = []
    for state in suggestions:
        node_id = getattr(state, "node_id", "")
        suggested = getattr(state, "suggested_next_review", None)
        when = (
            suggested.isoformat()
            if hasattr(suggested, "isoformat")
            else _esc(str(suggested or ""))
        )
        rows.append(
            [
                f'<a href="/nodes/{_esc(node_id)}">'
                f"{_esc(view.titles.get(node_id) or node_id)}</a>",
                "fading — a check is suggested",
                _esc(when),
                _schedule_form(node_id),
            ]
        )
    return section(
        "Suggested checks",
        "Advisory only. Nothing here is scheduled or overdue, and nothing "
        "here creates a record — scheduling a check is always your explicit "
        "action.",
        _table(["Skill", "Retention status", "Suggested for", "Schedule"], rows),
        frame=INLINE,
    )


def _schedule_form(node_id: str) -> str:
    return (
        '<details class="disclosure"><summary>Schedule</summary>'
        '<form method="post" action="/reviews/schedule">'
        '<input type="hidden" name="next" value="/reviews">'
        f'<input type="hidden" name="node_id" value="{_esc(node_id)}">'
        '<div class="form-row"><label>Due date</label>'
        '<input type="date" name="date" required></div>'
        '<button type="submit" class="btn secondary">Schedule this check</button>'
        "</form></details>"
    )


# --- the page ------------------------------------------------------------------ #


def reviews_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/reviews` — the one Review queue."""
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/reviews",
        current_view="reviews",
        path="/reviews",
    )
    if failure is not None:
        return failure

    today = utc_today()

    if "reviews" in view.degraded:
        # The records behind the queue did not load: claim nothing about
        # them — never "no checks are scheduled", never a zero (SC-00a).
        # The suggested checks read the same records, so they are left
        # unclaimed with the queue.
        return "Reviews", head + _records_failure_section(), 200

    worthy = _review_worthy_nodes(view)
    due = _overdue_section(view, today)
    scheduled = _scheduled_section(view, today)

    try:
        suggestions = _retention_suggestions(view, today)
        derivation_failed = False
    except Exception:  # noqa: BLE001 — an advisory derivation, never the page
        suggestions = []
        derivation_failed = True

    if due or scheduled:
        queue = due + scheduled
    elif worthy:
        queue = _no_records_state(suggestions=bool(suggestions))
    else:
        queue = _nothing_to_check_state()

    advisory = (
        _derivation_failure_state() if derivation_failed
        else _suggestions_section(suggestions, view)
    )

    body = (
        head
        + queue
        + _schedule_section(view, worthy)
        + advisory
        + _unsatisfactory_section(view)
        + _history_section(view)
    )
    return "Reviews", body, 200
