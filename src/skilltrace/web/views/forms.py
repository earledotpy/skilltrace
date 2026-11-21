"""
The single-step write forms (ADR 0009): template pickers, start
confirms, work fields, blocker and evidence forms.

"""

from __future__ import annotations

from ...context import JoinedView
from ...execution.records import open_session
from ._shared import (
    _esc,
)

#: What an explicit start records — one copy, announced before every start
#: affordance (Today and the node page) and restated by the start form. R6
#: forbids silent timing: this names the Session, its first SessionWork row,
#: and the asserted state, and says what is *not* recorded.
START_ANNOUNCEMENT = (
    "Starting opens a session, records the start of this session against "
    "this skill, and marks the skill active. No minutes or notes are "
    "recorded until you log work, and progress never moves backward."
)


def _template_select(templates: set[str], empty_label: str) -> str:
    options = "".join(f'<option value="{_esc(t)}">{_esc(t)}</option>' for t in sorted(templates))
    return (
        '<select name="template" id="session-template">'
        f'<option value="">{_esc(empty_label)}</option>{options}</select>'
    )


def _start_confirm_form(
    view: JoinedView, node_id: str, *, button_label: str = "Start this session"
) -> str:
    """The lightweight single-click start confirm (G5) — never a heavyweight modal.

    Copy states the forward-only permanence; locked reason and an already-open
    session stay visible as advisory text while the button stays enabled.
    """
    state = view.store.state_of(node_id)
    open_now = open_session(view.sessions)
    advisory = ""
    if state == "locked":
        advisory = (
            '<p class="mut">Currently locked (unsatisfied hard prerequisite) — '
            "satisfy prerequisites before starting.</p>"
        )
    elif open_now is not None:
        advisory = (
            '<p class="mut">A session is already open. Add work to it, or '
            "close it first.</p>"
        )
    button_label = button_label or "Start this session"
    return (
        '<div class="form-row">'
        '<label for="session-template">Session template</label>'
        f"{_template_select(view.policy.session_templates, '(none)')}"
        '<p class="small mut">A preset session shape — (none) starts a blank session.</p></div>'
        f"{advisory}"
        '<div class="actions">'
        f'<form method="post" action="/nodes/{_esc(node_id)}/start">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">'
        f'<button type="submit" class="btn primary">{_esc(button_label)}</button></form>'
        f'<span class="mut">{_esc(START_ANNOUNCEMENT)}</span>'
        "</div>"
    )


def _work_form_fields() -> str:
    return (
        '<div class="form-row"><label for="work-notes">Notes</label>'
        '<textarea name="notes" id="work-notes"></textarea>'
        '<p class="small mut">What you did — shown in history and the week view.</p></div>'
        '<div class="form-row"><label for="work-minutes">Minutes</label>'
        '<input type="number" name="minutes" id="work-minutes" min="1" '
        'style="max-width:7rem">'
        '<p class="small mut">How long you worked, in minutes.</p></div>'
        '<div class="form-row inline-check">'
        '<label><input type="checkbox" name="blocked" value="1"> ended stuck '
        "(blocked requires notes)</label></div>"
    )


def _resolve_blocker_form(blocker_id: str, next_url: str = "/") -> str:
    """Resolve affordance on each open-blocker row (G5): summary required."""
    field = f"blocker-summary-{blocker_id}"
    return (
        "<details><summary>Resolve</summary>"
        f'<form method="post" action="/blockers/{_esc(blocker_id)}/resolve">'
        f'<input type="hidden" name="next" value="{_esc(next_url)}">'
        f'<div class="form-row"><label for="{_esc(field)}">Resolution summary</label>'
        f'<input type="text" name="summary" id="{_esc(field)}" required>'
        '<p class="small mut">What unblocked you — one line for the record.</p></div>'
        '<button type="submit" class="btn secondary">Clear blocker</button></form></details>'
    )


def _spec_field(view: JoinedView, node_id: str, *, field_id: str) -> str:
    """The artifact-spec control, or the one spec as hidden context."""
    specs = view.specs_by_node.get(node_id, [])
    if len(specs) == 1:
        return f'<input type="hidden" name="spec" value="{_esc(specs[0].id)}">'
    options = "".join(
        f'<option value="{_esc(s.id)}">{_esc(s.title or s.id)}</option>'
        for s in specs
    )
    return (
        '<div class="form-row">'
        f'<label for="{_esc(field_id)}">Artifact spec</label>'
        f'<select name="spec" id="{_esc(field_id)}">{options}</select>'
        '<p class="small mut">Which artifact definition this proof satisfies.</p>'
        "</div>"
    )


def _location_field(*, field_id: str) -> str:
    return (
        '<div class="form-row">'
        f'<label for="{_esc(field_id)}">Location (repo-relative path or URL)</label>'
        f'<input type="text" name="location" id="{_esc(field_id)}" required>'
        '<p class="small mut">Where the proof lives.</p></div>'
    )


def _note_field(*, field_id: str) -> str:
    return (
        '<div class="form-row">'
        f'<label for="{_esc(field_id)}">Note (optional)</label>'
        f'<input type="text" name="note" id="{_esc(field_id)}">'
        '<p class="small mut">Context a reviewer needs to judge this proof.</p>'
        "</div>"
    )


def _manual_verdict_field() -> str:
    """The mandatory manual verdict — no radio is selected by default.

    ``required`` makes the browser demand a choice before the form leaves the
    page, and the engine still refuses a submission that arrives without one.
    A rejection is a recorded judgment, not a command failure.
    """
    return (
        '<div class="form-row"><label>Your verdict (required)</label>'
        '<span class="inline-check">'
        '<label><input type="radio" name="verdict" value="accept" required> '
        "Accept</label> "
        '<label><input type="radio" name="verdict" value="reject" required> '
        "Reject</label>"
        "</span>"
        '<p class="small mut">There is no default verdict. Either choice writes '
        "an immutable record; a rejection is an honest record, not a failure.</p>"
        "</div>"
    )


def _evidence_submit_form(view: JoinedView, node_id: str) -> str:
    """Evidence submit (G5) — the CLI's fields, judged at submission.

    The no-op form is *omitted* (v2.4 S4): a node with no artifact spec or
    no gate renders the explanation only — a form the domain would always
    refuse never renders. Spec select auto-resolves when the node has
    exactly one spec; accept/reject radios render only on manual-gate
    nodes, and neither is preselected.
    """
    specs = view.specs_by_node.get(node_id, [])
    gate = view.gates_by_node.get(node_id)

    if "records" in view.degraded:
        return (
            '<p class="mut">Evidence cannot be submitted while the history '
            'cannot be read. <a href="/health">Open Health</a> for the '
            "detail, then reload this workspace.</p>"
        )
    if not specs:
        return ""
    if gate is None:
        return ""

    if gate.command:
        verdict_field = (
            '<p class="mut">Objective gate — running it decides the verdict. '
            "If the check cannot run, no record is written.</p>"
        )
    else:
        verdict_field = _manual_verdict_field()

    return (
        "<details><summary>Submit evidence</summary>"
        '<form method="post" action="/nodes/'
        + _esc(node_id)
        + '/evidence">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}/evidence">'
        + _location_field(field_id=f"evidence-location-{node_id}")
        + _spec_field(view, node_id, field_id=f"evidence-spec-{node_id}")
        + _note_field(field_id=f"evidence-note-{node_id}")
        + verdict_field
        + '<button type="submit" class="btn secondary">Submit evidence</button>'
        "</form>"
        '<p class="mut">Acceptance freezes at submission — the gate '
        "verdict renders loudly; records are immutable and corrected by "
        "superseding, never edited.</p></details>"
    )


def _evidence_correction_form(view: JoinedView, node_id: str) -> str:
    """The separate **Correct earlier evidence** action (R3, HB-5).

    A correction is a *new* submission that supersedes an earlier record and
    must state why. The prior record stays visible with its derived
    superseded standing; there is no edit or delete path. The action is kept
    out of the normal submit form so it reads as its own decision, not an
    advanced option on a fresh submission.
    """
    specs = view.specs_by_node.get(node_id, [])
    gate = view.gates_by_node.get(node_id)
    if "records" in view.degraded:
        return (
            '<p class="mut">A correction cannot be offered while the history '
            'cannot be read. <a href="/health">Open Health</a> for the '
            "detail, then reload this workspace.</p>"
        )
    if not specs or gate is None:
        return ""

    spec_ids = {spec.id for spec in specs}
    superseded = {r.supersedes for r in view.records if r.supersedes}
    # Only an accepted, still-live record can be corrected. A rejected record
    # stays rejected as honest history; the way forward from a rejection is a
    # new attempt, not a correction that would rewrite its standing.
    records = [
        record
        for record in view.records
        if record.artifact_spec_id in spec_ids
        and record.accepted
        and record.id not in superseded
    ]
    if not records:
        return (
            '<p class="mut">There is no accepted earlier record to correct. '
            "Submit evidence first, or make a new attempt; a rejected record "
            "stays in history as rejected.</p>"
        )

    options = "".join(
        f'<option value="{_esc(record.id)}">'
        f"{_esc(record.location)} — "
        f"{'accepted' if record.accepted else 'rejected'}, "
        f"{_esc(str(record.created_at or 'undated'))}</option>"
        for record in sorted(records, key=lambda r: (r.created_at or "", r.id))
    )
    record_field = (
        '<div class="form-row">'
        '<label for="correction-record">Earlier record to correct</label>'
        f'<select name="supersedes" id="correction-record" required>'
        f'<option value="">Choose a record</option>{options}</select>'
        '<p class="small mut">The record this correction replaces. It stays '
        "in history and is shown as superseded.</p></div>"
    )
    reason_field = (
        '<div class="form-row">'
        '<label for="correction-reason">Reason (required)</label>'
        '<input type="text" name="reason" id="correction-reason" required>'
        '<p class="small mut">Why the earlier record is being replaced.</p>'
        "</div>"
    )
    verdict_field = (
        '<p class="mut">Objective gate — running it decides the corrected '
        "record's verdict.</p>"
        if gate.command
        else _manual_verdict_field()
    )

    return (
        '<details class="disclosure"><summary>Correct earlier evidence</summary>'
        '<form method="post" action="/nodes/'
        + _esc(node_id)
        + '/evidence">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}/evidence">'
        + record_field
        + reason_field
        + _location_field(field_id=f"correction-location-{node_id}")
        + _spec_field(view, node_id, field_id=f"correction-spec-{node_id}")
        + _note_field(field_id=f"correction-note-{node_id}")
        + verdict_field
        + '<button type="submit" class="btn secondary">Submit correction'
        "</button></form>"
        '<p class="mut">A correction is a new record; the earlier record is '
        "never edited or deleted.</p></details>"
    )

