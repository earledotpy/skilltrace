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


def _template_select(templates: set[str], empty_label: str) -> str:
    options = "".join(f'<option value="{_esc(t)}">{_esc(t)}</option>' for t in sorted(templates))
    return (
        f'<select name="template"><option value="">{_esc(empty_label)}</option>{options}</select>'
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
            '<p class="mut">A session is already open — '
            "close it before starting another.</p>"
        )
    button_label = button_label or "Start this session"
    return (
        '<div class="form-row"><label>Session template</label>'
        f"{_template_select(view.policy.session_templates, '(none)')}"
        '<p class="small mut">A preset session shape — (none) starts a blank session.</p></div>'
        f"{advisory}"
        '<div class="actions">'
        f'<form method="post" action="/nodes/{_esc(node_id)}/start">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">'
        f'<button type="submit" class="btn primary">{_esc(button_label)}</button></form>'
        '<span class="mut">marks this skill '
        "<strong>active</strong> — progress never moves backward.</span>"
        "</div>"
    )


def _work_form_fields() -> str:
    return (
        '<div class="form-row"><label>Notes</label>'
        '<textarea name="notes"></textarea>'
        '<p class="small mut">What you did — shown in history and the week view.</p></div>'
        '<div class="form-row"><label>Minutes '
        '<input type="number" name="minutes" min="1" style="max-width:7rem"></label>'
        '<p class="small mut">How long you worked, in minutes.</p></div>'
        '<div class="form-row inline-check">'
        '<label><input type="checkbox" name="blocked" value="1"> ended stuck '
        "(blocked requires notes)</label></div>"
    )


def _resolve_blocker_form(blocker_id: str, next_url: str = "/") -> str:
    """Resolve affordance on each open-blocker row (G5): summary required."""
    return (
        "<details><summary>Resolve</summary>"
        f'<form method="post" action="/blockers/{_esc(blocker_id)}/resolve">'
        f'<input type="hidden" name="next" value="{_esc(next_url)}">'
        '<div class="form-row"><label>Resolution summary</label>'
        '<input type="text" name="summary" required>'
        '<p class="small mut">What unblocked you — one line for the record.</p></div>'
        '<button type="submit" class="btn secondary">Clear blocker</button></form></details>'
    )


def _evidence_submit_form(view: JoinedView, node_id: str) -> str:
    """Evidence submit (G5) — the CLI's fields, judged at submission.

    The no-op form is *omitted* (v2.4 S4): a node with no artifact spec or
    no gate renders the explanation only — a form the domain would always
    refuse never renders. Spec select auto-resolves when the node has
    exactly one spec; accept/reject radios render only on manual-gate
    nodes; the supersede flow hides behind an advanced toggle.
    """
    specs = view.specs_by_node.get(node_id, [])
    gate = view.gates_by_node.get(node_id)

    if not specs:
        return ""
    if gate is None:
        return ""

    if len(specs) == 1:
        spec_field = f'<input type="hidden" name="spec" value="{_esc(specs[0].id)}">'
    else:
        options = "".join(
            f'<option value="{_esc(s.id)}">{_esc(s.title or s.id)}</option>' for s in specs
        )
        spec_field = (
            '<div class="form-row"><label>Artifact spec</label>'
            f'<select name="spec">{options}</select>'
            '<p class="small mut">Which artifact definition this proof satisfies.</p></div>'
        )

    if gate.command:
        verdict_field = (
            '<p class="mut">Objective gate — running it decides the verdict.</p>'
        )
    else:
        verdict_field = (
            '<div class="form-row"><label>Gate verdict (manual)</label>'
            '<span class="inline-check">'
            '<label><input type="radio" name="verdict" value="accept"> accept</label> '
            '<label><input type="radio" name="verdict" value="reject"> reject</label>'
            "</span>"
            '<p class="small mut">Your judgment on this proof — accept moves it forward.</p></div>'
        )

    record_ids = [r.id for r in view.records if r.artifact_spec_id in {s.id for s in specs}]
    datalist = ""
    if record_ids:
        options = "".join(f'<option value="{_esc(rid)}"></option>' for rid in record_ids)
        datalist = f'<datalist id="records-{_esc(node_id)}">{options}</datalist>'
    supersedes_field = (
        "<details><summary>Advanced: correct an earlier record</summary>"
        '<div class="form-row"><label>Supersedes</label>'
        f'<input type="text" name="supersedes" list="records-{_esc(node_id)}">{datalist}'
        '<p class="small mut">Id of the record this corrects — records are never edited.</p></div>'
        '<div class="form-row"><label>Reason (required with supersedes)</label>'
        '<input type="text" name="reason">'
        '<p class="small mut">Why the earlier record is being replaced.</p></div>'
        "</details>"
    )

    return (
        "<details><summary>Submit evidence</summary>"
        '<form method="post" action="/nodes/'
        + _esc(node_id)
        + '/evidence">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">'
        '<div class="form-row"><label>Location (repo-relative path or URL)</label>'
        '<input type="text" name="location" required>'
        '<p class="small mut">Where the proof lives.</p></div>'
        f"{spec_field}"
        '<div class="form-row"><label>Note (optional)</label>'
        '<input type="text" name="note">'
        '<p class="small mut">Context a reviewer needs to judge this proof.</p></div>'
        f"{verdict_field}"
        f"{supersedes_field}"
        '<button type="submit" class="btn secondary">Submit evidence</button>'
        "</form>"
        '<p class="mut">Acceptance freezes at submission — the gate '
        "verdict renders loudly; records are immutable and corrected by "
        "superseding, never edited.</p></details>"
    )

