"""
GET ``/evidence`` — the repository evidence index (spec-v3-study-day §11.2).

Repository-wide immutable-history index, complementary to the node-bound
workspace (``/nodes/{id}/evidence``). Default newest submission first,
stable secondary ordering by SkillNode ID and record ID. Filters are GET
parameters on this route, URL-addressable and history-bearing (IC-4).

There is **no bulk mutation** and **no edit or delete affordance** (HB-5):
records are immutable and corrections supersede. Selecting a record opens
the contextual inspector with the canonical record, its related SkillNode
and its event provenance.
"""

from __future__ import annotations

from .sections import NONE, section
from .shell import _page_head


def _superseded_ids(view) -> set[str]:
    """The record IDs a newer record supersedes — derived, never stored."""
    return {r.supersedes for r in view.records if r.supersedes}


def _standing(view, record) -> str:
    """The derived standing of one record: live, superseded, or rejected."""
    if record.id in _superseded_ids(view):
        return "superseded"
    return "live" if record.accepted else "rejected"


def _matches(record, view, node: str, outcome: str, standing: str) -> bool:
    if node and record.artifact_spec_id:
        spec = next(
            (s for s in view.specs if s.id == record.artifact_spec_id), None
        )
        if spec is None or spec.node_id != node:
            return False
    if outcome and outcome != record.accepted:
        return False
    if standing and standing != _standing(view, record):
        return False
    return True


def _filter_form(node: str, outcome: str, standing: str) -> str:
    """The labelled GET filters — the result set has its own URL."""
    node_options = '<option value="">Every skill</option>'
    outcome_options = (
        '<option value="">Any outcome</option>'
        f'<option value="True"{" selected" if outcome == "True" else ""}>'
        "accepted</option>"
        f'<option value="False"{" selected" if outcome == "False" else ""}>'
        "rejected</option>"
    )
    standing_options = '<option value="">Any standing</option>'
    for value in ("live", "superseded"):
        standing_options += (
            f'<option value="{value}"'
            f'{" selected" if standing == value else ""}>{value}</option>'
        )
    return (
        '<form class="filters" method="get" action="/evidence">\n'
        '<div class="form-row">'
        '<label for="evidence-node">Skill</label>'
        f'<select name="node" id="evidence-node">{node_options}</select></div>\n'
        '<div class="form-row">'
        '<label for="evidence-outcome">Outcome</label>'
        f'<select name="outcome" id="evidence-outcome">'
        f"{outcome_options}</select></div>\n"
        '<div class="form-row">'
        '<label for="evidence-standing">Standing</label>'
        f'<select name="standing" id="evidence-standing">'
        f"{standing_options}</select></div>\n"
        '<button type="submit">Apply filters</button>\n'
        "</form>\n"
    )


def evidence_index_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/evidence` — the repository-wide evidence history index."""
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/evidence",
        current_view="evidence-index",
        default_mode="operations",
        path="/evidence",
    )
    if failure is not None:
        return failure

    query = query or {}
    node = (query.get("node") or [""])[0].strip()
    outcome = (query.get("outcome") or [""])[0].strip()
    standing = (query.get("standing") or [""])[0].strip()

    records = [
        r for r in view.records if _matches(r, view, node, outcome, standing)
    ]
    records.sort(
        key=lambda r: (
            str(r.created_at or ""),
            r.artifact_spec_id,
            r.id,
        ),
        reverse=True,
    )

    if not records:
        body = (
            head
            + section(
                "",
                "",
                _filter_form(node, outcome, standing)
                + '<div class="state state-empty">\n'
                + '<p class="state-title">No evidence records</p>\n'
                + '<p class="state-body">Nothing has been submitted against '
                "this filter yet. A requirement being unmet is a fact about "
                "the curriculum, not a problem with you.</p>\n"
                + "</div>\n",
                frame=NONE,
            )
        )
        return "Evidence", body, 200
