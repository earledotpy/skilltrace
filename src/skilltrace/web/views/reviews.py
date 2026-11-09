"""
GET ``/reviews`` — the Reviews destination (spec-v3-study-day §10.10 and
§11.3).

One queue, ordered: overdue → scheduled by date → unsatisfactory or
failed follow-up → completed and cancelled history. Retention suggestions
occupy a **separately labelled advisory group** and create no record until
the learner schedules a Review — a suggestion is never shown as scheduled
or overdue.

Completing a Review is independent of the Session that started it and
requires an explicit outcome plus a result summary. Cancelling requires a
reason and preserves the cancelled history. Neither demotes asserted
progress or masters a node: an unsatisfactory outcome creates pressure
only.
"""

from __future__ import annotations

from ...execution.overdue import is_overdue, utc_today
from ._shared import _esc, _table
from .sections import BARE, INLINE, section
from .shell import _page_head


def _retention_suggestions(view, today) -> list:
    """The derived advisory retention suggestions — never in the queue."""
    seed = view.policy.retention
    if seed is None:
        return []
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


def _history_section(view) -> str:
    history = [r for r in view.reviews if r.status in ("completed", "cancelled")]
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


def _suggestions_section(view, today) -> str:
    """The advisory retention group — clearly not the scheduled queue."""
    suggestions = _retention_suggestions(view, today)
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
    due = _overdue_section(view, today)
    scheduled = _scheduled_section(view, today)
    history = _history_section(view)
    suggestions = _suggestions_section(view, today)

    if not due and not scheduled:
        queue = (
            '<section class="section">\n'
            '<div class="state state-empty">\n'
            '<p class="state-title">No checks are scheduled</p>\n'
            '<p class="state-body">A retention check is created only by your '
            "own scheduling action. Suggested checks below are advisory — they "
            "are not scheduled and not overdue.</p>\n"
            "</div>\n"
            "</section>\n"
        )
    else:
        queue = due + scheduled

    body = head + queue + suggestions + history
    return "Reviews", body, 200
