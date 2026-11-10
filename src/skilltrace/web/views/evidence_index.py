"""
GET ``/evidence`` — the repository evidence index (spec-v3-study-day §11.2).

Repository-wide immutable-history index, complementary to the node-bound
workspace (``/nodes/{id}/evidence``). Default newest submission first,
stable secondary ordering by SkillNode ID and record ID. Filters are GET
parameters on this route, URL-addressable and history-bearing (IC-4).

There is **no bulk mutation** and **no edit or delete affordance** (HB-5):
records are immutable and corrections supersede. Selecting a record opens the
contextual inspector with the canonical record, its related SkillNode and its
event provenance — the selection rides this route's ``?record=`` parameter, so
a shared or reloaded link reproduces exactly what was seen
(``views.inspector`` owns the inspector and has no route of its own).
"""

from __future__ import annotations

from urllib.parse import urlencode

from ._shared import _esc, _table, plural, record_standing
from .inspector import evidence_inspector, selected_value
from .sections import NONE, section
from .shell import _page_head

_STANDING_KINDS = {"live": "success", "superseded": "neutral", "rejected": "failure"}


def _matches(record, view, node: str, outcome: str, standing: str) -> bool:
    if node and record.artifact_spec_id:
        spec = next(
            (s for s in view.specs if s.id == record.artifact_spec_id), None
        )
        if spec is None or spec.node_id != node:
            return False
    if outcome and outcome != record.accepted:
        return False
    if standing and standing != record_standing(view, record):
        return False
    return True


def _node_options(view, node: str) -> str:
    """Every skill in the evidence history — the filter's own population.

    The population is the records the index actually holds, not the whole
    curriculum: offering 81 skills to filter a three-record history would be
    a control that mostly produces empty pages. ``node`` is always kept as an
    option, so a deep link's filter is still reflected in the control. Values
    are node ids (technical detail); labels are the readable titles (R1).
    """
    spec_by_id = {s.id: s for s in view.specs}
    node_ids = {
        spec.node_id
        for spec in (
            spec_by_id.get(record.artifact_spec_id) for record in view.records
        )
        if spec is not None
    }
    if node:
        node_ids.add(node)
    options = ['<option value="">Every skill</option>']
    for node_id in sorted(node_ids):
        title = view.titles.get(node_id) or node_id
        chosen = " selected" if node_id == node else ""
        options.append(
            f'<option value="{_esc(node_id)}"{chosen}>{_esc(title)}</option>'
        )
    return "".join(options)


def _filter_form(view, node: str, outcome: str, standing: str) -> str:
    """The labelled GET filters — the result set has its own URL."""
    node_options = _node_options(view, node)
    outcome_options = (
        '<option value="">Any outcome</option>'
        f'<option value="True"{" selected" if outcome == "True" else ""}>'
        "accepted</option>"
        f'<option value="False"{" selected" if outcome == "False" else ""}>'
        "rejected</option>"
    )
    standing_options = '<option value="">Any standing</option>'
    for value in ("live", "superseded", "rejected"):
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


def _gate_words(view, node_id: str) -> str:
    """The gate that judged the record, in words — never colour alone."""
    gate = view.gates_by_node.get(node_id)
    if gate is None:
        return '<span class="mut">No gate declared</span>'
    return "Objective gate" if gate.authority == "objective" else "Manual gate"


def _record_row(record, view, spec_by_id, *, selected: bool, filters: dict) -> list[str]:
    """One evidence record as a table row of canonical facts.

    The record id appears as technical detail inside ``<code>`` (R1: a
    readable SkillNode title is what stands in prose), and the row's only
    action is a link to the inspector — there is no edit or delete
    affordance anywhere (HB-5).
    """
    spec = spec_by_id.get(record.artifact_spec_id)
    node_id = spec.node_id if spec is not None else ""
    title = view.titles.get(node_id) or node_id
    skill = (
        f'<a href="/nodes/{_esc(node_id)}">{_esc(title)}</a>'
        if node_id
        else '<span class="mut">No skill</span>'
    )
    requirement = (
        _esc(spec.title)
        if spec is not None
        else '<span class="mut">Unresolved requirement</span>'
    )
    standing = record_standing(view, record)
    verdict = (
        f'<span class="status-label {"success" if record.accepted else "failure"}">'
        f'{"Accepted" if record.accepted else "Rejected"}</span>'
    )
    standing_label = (
        f'<span class="status-label {_STANDING_KINDS.get(standing, "neutral")}">'
        f"{_esc(standing)}</span>"
    )
    href = "/evidence?" + urlencode({**filters, "record": record.id})
    record_cell = f'<a href="{_esc(href)}">Inspect</a> <code>{_esc(record.id)}</code>'
    if selected:
        record_cell = '<span class="status-label info">Selected</span> ' + record_cell
    return [
        f'<span class="mono">{_esc(str(record.created_at or ""))}</span>',
        skill,
        requirement,
        _gate_words(view, node_id),
        verdict,
        standing_label,
        record_cell,
    ]


def _empty_state() -> str:
    """Nothing matched the filter — a fact about the curriculum, not the learner."""
    return (
        '<div class="state state-empty">\n'
        '<p class="state-title">No evidence records</p>\n'
        '<p class="state-body">Nothing has been submitted against this filter yet. '
        "A requirement being unmet is a fact about the curriculum, not a problem "
        "with you.</p>\n"
        "</div>\n"
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
    selected = selected_value(query)

    records = [r for r in view.records if _matches(r, view, node, outcome, standing)]
    records.sort(
        key=lambda r: (
            str(r.created_at or ""),
            r.artifact_spec_id,
            r.id,
        ),
        reverse=True,
    )

    # The selection is presentation context on this route: it renders whether
    # or not the record survived the filters, so a shared link is reproduced.
    inspector = evidence_inspector(view, selected, query=query) if selected else ""

    filters = {
        key: value
        for key, value in (("node", node), ("outcome", outcome), ("standing", standing))
        if value
    }

    if not records:
        body = (
            head
            + section(
                "",
                "",
                _filter_form(view, node, outcome, standing) + _empty_state(),
                frame=NONE,
            )
            + inspector
        )
        return "Evidence", body, 200

    spec_by_id = {s.id: s for s in view.specs}
    rows = [
        _record_row(
            record, view, spec_by_id, selected=record.id == selected, filters=filters
        )
        for record in records
    ]
    meta = (
        f"{len(records)} record{plural(len(records))}, newest first. "
        "Records are never edited or deleted; a correction supersedes."
    )
    body = (
        head
        + section(
            "Evidence history",
            meta,
            _filter_form(view, node, outcome, standing)
            + _table(
                [
                    "Submitted",
                    "Skill",
                    "Requirement",
                    "Gate",
                    "Outcome",
                    "Standing",
                    "Record",
                ],
                rows,
            ),
            anchor="history",
        )
        + inspector
    )
    return "Evidence", body, 200
