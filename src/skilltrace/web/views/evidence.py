"""
GET ``/nodes/{id}/evidence`` — the node requirements-and-history workspace
(spec-v3-study-day §10.9).

Two figures stay **distinct and visible before work begins** (R2):

* **evidence wanted** — the required and optional artifact specifications
  with their minimum counts;
* **evidence recorded** — the accepted live records, the rejected history
  and the superseded history.

They are never collapsed into one ambiguous number. Only accepted,
non-superseded records for **required** specs count toward derived pass
eligibility; an optional spec is never presented as an eligibility gap.

A manual gate demands an explicit Accept or Reject with no default
verdict. An objective gate shows the authoritative result and the gate-run
receipt where one exists. A gate that cannot run is an operational failure
that writes **no record**. A correction creates a new superseding record
with a required reason; the prior record stays visible and its derived
superseded status is shown on the record itself. There is no edit and no
delete anywhere (HB-5).
"""

from __future__ import annotations

from ...evidence.eligibility import compute_eligibility, live_accepted_count
from ._shared import _esc, _table
from .forms import _evidence_submit_form
from .shell import _page_head


def _wanted_rows(view, node_id: str) -> str:
    """The wanted side: every spec, required or optional, with its minimum."""
    specs = view.specs_by_node.get(node_id, [])
    if not specs:
        return (
            '<div class="state state-empty">\n'
            '<p class="state-title">Nothing is required here</p>\n'
            '<p class="state-body">This skill has no artifact specification, '
            "so there is no proof to gather before passing it.</p>\n"
            "</div>\n"
        )
    rows = []
    for spec in specs:
        required = spec.required
        rows.append(
            [
                _esc(spec.title or spec.id),
                "required" if required else "optional",
                _esc(str(spec.minimum_count)),
                _esc(str(live_accepted_count(view.records, spec.id))),
            ]
        )
    return _table(["What you show", "Kind", "Minimum", "Accepted"], rows)


def _recorded_rows(view, node_id: str) -> str:
    """The recorded side: accepted live, rejected, and superseded history."""
    spec_ids = {s.id for s in view.specs_by_node.get(node_id, [])}
    records = [r for r in view.records if r.artifact_spec_id in spec_ids]
    if not records:
        return (
            '<div class="state state-empty">\n'
            '<p class="state-title">Nothing recorded yet</p>\n'
            '<p class="state-body">No evidence has been submitted for this '
            "skill yet.</p>\n"
            "</div>\n"
        )
    superseded_ids = {r.supersedes for r in records if r.supersedes}
    rows = []
    for record in records:
        if record.id in superseded_ids:
            standing = "superseded"
        elif record.accepted:
            standing = "live"
        else:
            standing = "rejected"
        rows.append(
            [
                _esc(record.artifact_spec_id),
                "accepted" if record.accepted else "rejected",
                _esc(standing),
                _esc(record.location),
                _esc(str(record.created_at or "")),
            ]
        )
    return _table(
        ["Artifact", "Outcome", "Standing", "Location", "Submitted"], rows
    )


def node_evidence_body(
    root, node_id: str, query: dict | None = None
) -> tuple[str, str, int]:
    """GET `/nodes/{id}/evidence` — the requirements-and-history workspace."""
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path=f"/nodes/{node_id}/evidence",
        current_view="evidence",
        path=f"/nodes/{node_id}/evidence",
    )
    if failure is not None:
        return failure
    if node_id not in view.node_map:
        body = (
            head
            + '<section class="section">\n'
            + '<div class="state state-failure">\n'
            + '<p class="state-title">Unknown skill</p>\n'
            + '<p class="state-body">No skill with that identifier exists in '
            "the curriculum.</p>\n"
            + "</div>\n"
            + "</section>\n"
        )
        return "Evidence", body, 404

    state = view.store.state_of(node_id)
    eligibility = compute_eligibility(
        node_id,
        view.specs_by_node.get(node_id, []),
        has_gate=node_id in view.has_gate,
        records=view.records,
        node_state=state,
    )

    spec_ids = {s.id for s in view.specs_by_node.get(node_id, [])}
    records = [r for r in view.records if r.artifact_spec_id in spec_ids]
    superseded_ids = {r.supersedes for r in records if r.supersedes}
    accepted_live = len(
        [r for r in records if r.accepted and r.id not in superseded_ids]
    )
    rejected = len([r for r in records if not r.accepted])
    superseded = len([r for r in records if r.id in superseded_ids])

    wanted = len(
        [s for s in view.specs_by_node.get(node_id, []) if s.minimum_count > 0]
    )
    # The eligibility derivation says which required proofs are still
    # unmet. It is the fact behind "what is left to do", so it is stated
    # rather than computed twice.
    unmet = [reason for reason in eligibility.reasons]

    gate = view.gates_by_node.get(node_id)
    gate_line = "No checking method is set up for this skill."
    if gate is not None and gate.command:
        gate_line = (
            "An automatic check decides the verdict. Its result and receipt "
            "are recorded with the evidence."
        )
    elif gate is not None:
        gate_line = (
            "You state the verdict when you submit. There is no default "
            "verdict — accepting and rejecting are separate choices."
        )

    body = (
        head
        + '<section class="section">\n'
        + '<div class="section-head">\n'
        + f'<h2 class="section-title">{_esc(view.node_map[node_id].title)}</h2>\n'
        + '<p class="section-meta">What is required, and what is on record.</p>\n'
        + "</div>\n"
        + '<div class="rows">\n'
        + '<div class="row"><span class="row-label">Evidence wanted</span>'
        f'<span class="row-value">{wanted} required</span></div>\n'
        + '<div class="row"><span class="row-label">Evidence recorded</span>'
        f'<span class="row-value">{accepted_live} accepted, {rejected} '
        f"rejected, {superseded} superseded</span></div>\n"
        + "</div>\n"
        + (
            '<div class="banner advisory">Still to do on this skill:\n'
            + "".join(f"<p>{_esc(reason)}</p>\n" for reason in unmet)
            + "</div>\n"
            if unmet
            else ""
        )
        + "</section>\n"
        + '<section class="section">\n'
        + '<h2 class="section-title">Evidence wanted</h2>\n'
        + f"{_wanted_rows(view, node_id)}"
        + "</section>\n"
        + '<section class="section">\n'
        + '<h2 class="section-title">Evidence recorded</h2>\n'
        + f"{_recorded_rows(view, node_id)}"
        + "</section>\n"
        + '<section class="section">\n'
        + '<h2 class="section-title">Submit evidence</h2>\n'
        + f'<p class="section-meta">{_esc(gate_line)}</p>\n'
        + f"{_evidence_submit_form(view, node_id)}"
        + "</section>\n"
    )
    return "Evidence", body, 200
