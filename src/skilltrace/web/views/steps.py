"""
The pass/master confirmation panels (ADR 0009): heavyweight
confirmation exclusive to the acceptance steps.

"""

from __future__ import annotations

from ...commands.eligibility import passed_at_of
from ...context import JoinedView
from ...evidence.eligibility import (
    compute_eligibility,
    live_accepted_count,
)
from ...policy.mastery import compute_mastery_eligibility
from ...resources.status import VerificationStatus
from ._shared import (
    _esc,
    _output_banners,
    _table,
)
from .shell import (
    _modal_dismiss,
    _modal_shell,
    _page_head,
    _status_page,
)


_STATUS_PILL_CLASSES = {
    VerificationStatus.BROKEN.value: "broken",
    VerificationStatus.STALE.value: "stale",
    VerificationStatus.VERIFIED.value: "verified",
}


def pass_modal_body(
    root, node_id: str, query: dict | None = None
) -> tuple[str, str, int]:
    """GET `/nodes/{id}/pass` — the pass confirmation panel (T5 §B+§F).

    Every render recomputes eligibility from a fresh lenient join; nothing is
    pre-disabled. Confirming POSTs and re-runs the guarded write against
    freshly loaded truth, so a stale panel can never assert what eligibility
    no longer supports. Copy states what changes, its side effects, and no
    engine internals (specs by human title, never raw spec ids).
    """
    view, head, failure = _page_head(
        root, query, dismiss_path=_modal_dismiss(node_id, "Confirm pass")
    )
    if failure is not None:
        return failure
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    state = view.store.state_of(node_id)
    eligibility = compute_eligibility(
        node_id,
        view.specs_by_node.get(node_id, []),
        has_gate=node_id in view.has_gate,
        records=view.records,
        node_state=state,
    )

    gate = view.gates_by_node.get(node_id)
    if gate is None:
        authority_line = "No checking method is set up — evidence cannot count here yet."
    elif gate.command:
        authority_line = "Checked automatically — verification confirms your evidence."
    else:
        authority_line = "Checked by you — you state the verdict when you submit."

    titles_by_spec = {
        s.id: (s.title or s.id) for s in view.specs_by_node.get(node_id, [])
    }
    spec_rows = [
        [
            _esc(titles_by_spec.get(s.spec_id, s.spec_id)),
            _esc(s.minimum_count),
            _esc(s.accepted_count),
            "met" if s.met else "below minimum",
        ]
        for s in eligibility.specs
    ]
    spec_table = (
        _table(["What you show", "Minimum", "Live accepted", "Standing"], spec_rows)
        if spec_rows
        else '<p class="mut">No required proof is defined for this skill.</p>'
    )

    verdict_html = _output_banners(
        ["This skill is ready to mark as passed, on this fresh read."]
        if eligibility.eligible
        else list(eligibility.reasons),
        default_class="ok" if eligibility.eligible else "warning",
    )

    not_backed = ""
    if eligibility.passed_but_not_backed:
        not_backed = (
            '<p class="banner warning">Already passed but no longer backed by live '
            "proof — the pass stands regardless, never moves backward.</p>"
        )

    cadence = view.policy.cadence
    if cadence.schedule_reviews_after_pass and cadence.intervals:
        days = ", ".join(str(interval.days_after_pass) for interval in cadence.intervals)
        review_note = (
            '<p class="banner advisory">Marking as passed schedules '
            f"reviews for {days} days after the pass.</p>"
        )
    else:
        review_note = (
            '<p class="banner advisory">No reviews are scheduled automatically — '
            "reviews stay manual.</p>"
        )

    node_title = view.node_map[node_id].title
    inner = (
        f"<p>How this is checked: {authority_line}</p>"
        f"{spec_table}"
        "<p><strong>Eligibility</strong></p>"
        f"{verdict_html}"
        f"{not_backed}"
        "<p>Marking as passed records this skill as passed. "
        "Passed never moves backward.</p>"
        f"{review_note}"
        f'<form method="post" action="/nodes/{_esc(node_id)}/pass">'
        '<div class="actions">'
        f'<button type="submit" class="btn">Mark {_esc(node_title)} passed</button>'
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
        "</div></form>"
    )
    return _modal_shell(view, node_id, "Confirm pass", inner, head=head)


def _mastery_facts_html(view: JoinedView, node_id: str) -> tuple[str, str]:
    """Fresh mastery facts table + eligibility banners, shared by both steps (T5 §F).

    Recomputed from a fresh join on every render — step 2 re-renders the
    node and facts freshly rather than trusting step 1's read (P4.4).
    """
    state = view.store.state_of(node_id)
    values = view.policy.mastery
    passed_at = passed_at_of(view.store, node_id)
    mastery = compute_mastery_eligibility(
        node_id,
        current_state=state,
        passed_at=passed_at,
        specs=view.specs_by_node.get(node_id, []),
        records=view.records,
        reviews=view.reviews,
        values=values,
    )
    accepted_total = sum(
        live_accepted_count(view.records, s.id)
        for s in view.specs_by_node.get(node_id, [])
    )
    fact_rows = [
        ["Passed on", _esc(str(passed_at)[:10]) if passed_at else "—"],
        [
            "Live proof accepted",
            f"{accepted_total} of {values.min_accepted_evidence} required",
        ],
        [
            "Review spacing",
            f"a satisfactory completed review at least "
            f"{values.min_days_pass_to_review} day(s) after the pass",
        ],
    ]
    verdict_html = _output_banners(
        ["This skill is ready for the permanent confirm, on this fresh read."]
        if mastery.eligible
        else list(mastery.reasons),
        default_class="ok" if mastery.eligible else "warning",
    )
    return _table(["Fact", "Value"], fact_rows), verdict_html


def master_body(
    root, node_id: str, query: dict | None = None
) -> tuple[str, str, int]:
    """GET `/nodes/{id}/master` — step 1 of 2: mastery facts (T5 §B+§F+P4.1)."""
    view, head, failure = _page_head(
        root, query, dismiss_path=_modal_dismiss(node_id, "Step 1 — Mastery facts")
    )
    if failure is not None:
        return failure
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    state = view.store.state_of(node_id)
    facts_table, verdict_html = _mastery_facts_html(view, node_id)

    if state == "locked" or state != "passed":
        # P4.1 structural omission: Continue is omitted on a structural wall —
        # locked, or anything that is not passed — and the wall is shown with
        # its unmet prerequisites in plain words.
        if state == "locked":
            wall_note = (
                '<p class="mut">Continue is unavailable — this skill is locked '
                "until its prerequisites are passed.</p>"
            )
        else:
            wall_note = (
                '<p class="mut">Continue is unavailable — mastery needs '
                "a passed skill first.</p>"
            )
        actions = (
            '<div class="actions">'
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
            "</div>"
        )
    else:
        # Judgment eligibility stays live with advisory text beside the action.
        wall_note = (
            '<p class="mut">Mastery needs a passed skill with accepted proof '
            "and a satisfactory spaced review.</p>"
        )
        actions = (
            '<div class="actions">'
            + f'<a class="btn master" href="/nodes/{_esc(node_id)}/master/confirm">'
            "Continue to permanent confirm &rarr;</a>"
            + f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">Cancel</a>'
            "</div>"
        )

    inner = (
        '<div class="kicker">Mastery facts</div>'
        + facts_table
        + "<p><strong>Eligibility</strong></p>"
        + verdict_html
        + wall_note
        + actions
    )
    return _modal_shell(view, node_id, "Step 1 — Mastery facts", inner, head=head)


def master_confirm_body(
    root, node_id: str, query: dict | None = None
) -> tuple[str, str, int]:
    """GET `/nodes/{id}/master/confirm` — step 2 of 2: permanence (T5 §B+§F+P4.4)."""
    view, head, failure = _page_head(
        root, query, dismiss_path=_modal_dismiss(node_id, "Step 2 — This is permanent")
    )
    if failure is not None:
        return failure
    if node_id not in view.node_map:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    node_title = view.node_map[node_id].title
    facts_table, verdict_html = _mastery_facts_html(view, node_id)
    inner = (
        '<div class="kicker">Mastery facts — checked again just now</div>'
        + facts_table
        + verdict_html
        + '<p class="banner warning"><strong>This is permanent.</strong> '
        "Mastered never moves backward — this is permanent. "
        "A later unsatisfactory review creates pressure, but the state never "
        "moves backward. Confirm only if you intend this skill to remain mastered "
        "forever.</p>"
        f'<form method="post" action="/nodes/{_esc(node_id)}/master/confirm">'
        '<div class="actions">'
        f'<button type="submit" class="btn master">Mark {_esc(node_title)} mastered</button>'
        f'<a class="btn secondary" href="/nodes/{_esc(node_id)}/master">Back</a>'
        "</div></form>"
    )
    return _modal_shell(view, node_id, "Step 2 — This is permanent", inner, head=head)

