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

from dataclasses import dataclass

from ...evidence.eligibility import compute_eligibility, live_accepted_count
from ._shared import _esc, _table
from .forms import _evidence_correction_form, _evidence_submit_form
from .receipts import receipt_disclosure
from .sections import (
    BARE,
    EMPTY,
    FAILURE,
    INLINE,
    LIMITED,
    Markup,
    Rows,
    Section,
    State,
)
from .shell import _page_head


@dataclass(frozen=True)
class EvidenceFigures:
    """The evidence figures for one SkillNode — one named derivation.

    Wanted and recorded are deliberately **different facts** (R2): the wanted
    side counts only required specifications and their minimum records, while
    the recorded side splits the history into accepted-and-live, rejected and
    superseded. Optional specifications never make the wanted figure larger,
    so an optional artifact can never read as an eligibility gap.
    """

    wanted_specs: int
    wanted_records: int
    optional_specs: int
    accepted_live: int
    rejected: int
    superseded: int

    @property
    def wanted(self) -> int:
        """The required-specification count (the older, terse reading)."""
        return self.wanted_specs


def evidence_figures(view, node_id: str) -> EvidenceFigures:
    """The evidence figures for one SkillNode — one derivation (R7).

    The Study cockpit, the close panel, the node detail and the evidence
    workspace all read this, so no two surfaces state different numbers for
    one skill. Only required specs define what is wanted; only accepted,
    non-superseded records count as recorded-live.
    """
    specs = view.specs_by_node.get(node_id, [])
    required = [s for s in specs if s.required]
    optional = [s for s in specs if not s.required]
    spec_ids = {s.id for s in specs}
    records = [r for r in view.records if r.artifact_spec_id in spec_ids]
    superseded_ids = {r.supersedes for r in records if r.supersedes}
    return EvidenceFigures(
        wanted_specs=len(required),
        wanted_records=sum(s.minimum_count for s in required),
        optional_specs=len(optional),
        accepted_live=len(
            [r for r in records if r.accepted and r.id not in superseded_ids]
        ),
        rejected=len([r for r in records if not r.accepted]),
        superseded=len([r for r in records if r.id in superseded_ids]),
    )


def _wanted_rows(view, node_id: str) -> str:
    """The wanted side: every spec, required or optional, with its minimum."""
    if "specs" in view.degraded:
        return (
            State(
                FAILURE,
                "The evidence requirements could not be loaded",
                "The artifact specifications did not load, so nothing is "
                "claimed about what this skill wants. Your progress is "
                "unaffected.",
            ).render()
            + '<p><a href="/health">Open Health</a> for the detail.</p>\n'
        )
    specs = view.specs_by_node.get(node_id, [])
    if not specs:
        return State(
            EMPTY,
            "Nothing is required here",
            "This skill has no artifact specification, so there is no proof "
            "to gather before passing it.",
        ).render()
    records_unreadable = "records" in view.degraded
    rows = []
    for spec in specs:
        required = spec.required
        accepted = (
            '<span class="mut">Unavailable</span>'
            if records_unreadable
            else _esc(str(live_accepted_count(view.records, spec.id)))
        )
        rows.append(
            [
                _esc(spec.title or spec.id),
                "required" if required else "optional",
                _esc(str(spec.minimum_count)),
                accepted,
                "yes" if required else "no",
            ]
        )
    return (
        _table(
            [
                "What you show",
                "Kind",
                "Minimum",
                "Accepted",
                "Counts toward passing",
            ],
            rows,
        )
        + '<p class="section-meta">Only required specifications count toward '
        "passing. An optional specification is additional, never an "
        "eligibility gap.</p>\n"
    )


def _recorded_rows(view, node_id: str) -> str:
    """The recorded side: accepted live, rejected, and superseded history."""
    if "records" in view.degraded:
        return (
            State(
                FAILURE,
                "The evidence history could not be loaded",
                "The evidence records did not load, so nothing is claimed "
                "about what is on record. Your progress is unaffected.",
            ).render()
            + '<p><a href="/health">Open Health</a> for the detail, then '
            "reload this workspace.</p>\n"
        )
    spec_ids = {s.id for s in view.specs_by_node.get(node_id, [])}
    records = [r for r in view.records if r.artifact_spec_id in spec_ids]
    if not records:
        return State(
            EMPTY,
            "Nothing recorded yet",
            "No evidence has been submitted for this skill yet. The wanted "
            "requirements above stay visible while you work.",
        ).render()
    spec_titles = {
        spec.id: (spec.title or spec.id)
        for spec in view.specs_by_node.get(node_id, [])
    }
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
                _esc(spec_titles.get(record.artifact_spec_id, record.artifact_spec_id)),
                "accepted" if record.accepted else "rejected",
                _esc(standing),
                _esc(record.location),
                _esc(str(record.created_at or "")),
            ]
        )
    return _table(
        ["Artifact", "Outcome", "Standing", "Location", "Submitted"], rows
    )


def _still_to_do(view, eligibility) -> str:
    """Structural reasons evidence cannot count yet, in readable words.

    Unmet minimums are the *limited* state below (which names the artifact
    titles and the threshold). This note carries the two structural facts
    that are not a count: no gate, or no required spec.
    """
    if "records" in view.degraded or "specs" in view.degraded:
        return ""
    notes: list[str] = []
    if not eligibility.has_gate:
        notes.append(
            "No checking method is set up, so no evidence can count toward "
            "passing this skill yet."
        )
    if not eligibility.has_required_spec:
        notes.append(
            "This skill defines no required artifact, so there is no "
            "requirement to meet."
        )
    if not notes:
        return ""
    return (
        '<div class="banner advisory">Before evidence can count here:\n'
        + "".join(f"<p>{_esc(note)}</p>\n" for note in notes)
        + "</div>\n"
    )


def _limited_state(view, eligibility) -> str:
    """The limited state: records exist, a required minimum is not met yet."""
    unmet = [spec for spec in eligibility.specs if not spec.met]
    if not unmet:
        return ""
    titles = {
        spec.id: (spec.title or spec.id)
        for spec in view.specs_by_node.get(eligibility.node_id, [])
    }
    parts = "; ".join(
        f"{titles.get(spec.spec_id, spec.spec_id)} needs "
        f"{spec.minimum_count}, {spec.accepted_count} accepted"
        for spec in unmet
    )
    return State(
        LIMITED,
        "Some required evidence is still short",
        f"{parts}. The records on file stand; the requirement is simply not "
        "met yet.",
    ).render()


def _receipts_section(view, node_id: str) -> str:
    """The gate-run receipts recorded with this skill's objective evidence.

    A receipt is shown for every record that carries one. Manual records and
    pre-receipt objective records carry none, and the workspace never invents
    one.
    """
    spec_ids = {s.id for s in view.specs_by_node.get(node_id, [])}
    records = [
        record
        for record in view.records
        if record.artifact_spec_id in spec_ids and record.gate_run
    ]
    if not records:
        return ""
    blocks = []
    for record in sorted(records, key=lambda r: (r.created_at or "", r.id)):
        verdict = "accepted" if record.accepted else "rejected"
        blocks.append(
            receipt_disclosure(
                record,
                summary=(
                    f"Receipt for {record.location} — {verdict}, "
                    f"submitted {record.created_at or 'an unrecorded time'}"
                ),
            )
        )
    return Section(
        "How the gate judged",
        "The receipt recorded with each automatic verdict: how the check ran, "
        "what it read, and its result.",
        (Markup("".join(blocks)),),
        frame=INLINE,
    ).render()


def _summary_facts(view, node_id: str, figures: EvidenceFigures) -> str:
    """The two visible evidence figures — wanted and recorded, never merged."""
    if "specs" in view.degraded:
        wanted = "Could not be read — see Health"
    else:
        wanted = (
            f"{figures.wanted_specs} required specification"
            f"{'' if figures.wanted_specs == 1 else 's'}, "
            f"{figures.wanted_records} record"
            f"{'' if figures.wanted_records == 1 else 's'} wanted"
        )
        if figures.optional_specs:
            wanted += (
                f"; {figures.optional_specs} optional specification"
                f"{'' if figures.optional_specs == 1 else 's'}, not counted"
            )
    if "records" in view.degraded:
        recorded = "Could not be read — see Health"
    else:
        recorded = (
            f"{figures.accepted_live} accepted, "
            f"{figures.rejected} rejected, "
            f"{figures.superseded} superseded"
        )
    return Rows(
        (
            ("Evidence wanted", wanted),
            ("Evidence recorded", recorded),
        ),
        separated=True,
    ).render()


def _gate_line(view, node_id: str) -> str:
    """How this skill's evidence is judged, in learner-first words."""
    if "gates" in view.degraded:
        return (
            "The checking method could not be loaded, so no submission is "
            "offered until it is available again. Open Health for the detail."
        )
    gate = view.gates_by_node.get(node_id)
    if gate is None:
        return "No checking method is set up for this skill."
    if gate.command:
        return (
            "An automatic check decides the verdict. Its result and receipt "
            "are recorded with the evidence; if the check cannot run, no "
            "record is written."
        )
    return (
        "You state the verdict when you submit. There is no default verdict "
        "— accepting and rejecting are separate choices, and either one "
        "writes an immutable record."
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

    figures = evidence_figures(view, node_id)
    spec_ids = {spec.id for spec in view.specs_by_node.get(node_id, [])}
    has_records = any(
        record.artifact_spec_id in spec_ids for record in view.records
    )
    # Empty and limited are different facts: a threshold can only be "not met
    # yet" when there is a recorded value to compare against.
    limited = (
        _limited_state(view, eligibility)
        if "records" not in view.degraded and has_records
        else ""
    )

    body = (
        head
        + Section(
            view.node_map[node_id].title,
            "What is required, and what is on record.",
            (
                Markup(_summary_facts(view, node_id, figures)),
                Markup(_still_to_do(view, eligibility)),
            ),
        ).render()
        + Section(
            "Evidence wanted", "", (Markup(_wanted_rows(view, node_id)),), frame=BARE
        ).render()
        + Section(
            "Evidence recorded",
            "",
            (Markup(_recorded_rows(view, node_id) + limited),),
            frame=BARE,
        ).render()
        + _receipts_section(view, node_id)
        + Section(
            "Submit evidence",
            _gate_line(view, node_id),
            (Markup(_evidence_submit_form(view, node_id)),),
            frame=INLINE,
        ).render()
        + Section(
            "Correct earlier evidence",
            "A correction is a new record that supersedes an earlier one. "
            "Nothing is edited or deleted.",
            (Markup(_evidence_correction_form(view, node_id)),),
            frame=INLINE,
            anchor="correct-evidence",
        ).render()
    )
    return "Evidence", body, 200
