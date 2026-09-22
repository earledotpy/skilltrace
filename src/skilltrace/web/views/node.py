"""
GET ``/nodes/{id}`` — the node page, its actions card and the
drill-down disclosure (ADR 0009).

"""

from __future__ import annotations

from pathlib import Path

from ...commands.node_detail import (
    derive_node_detail,
    derive_node_drilldown,
)
from ...context import JoinedView
from ..interface.cards import (
    view_by_name,
    ActiveViewState,
)
from ..interface.handoff import handoff_html
from ..interface.render import render_rich_cards
from ..interface.translate import (
    rich_cards as _rich_cards_from_model,
)
from ._shared import (
    _degraded_banner,
    _esc,
    _table,
)
from .shell import (
    _page_head,
    _status_page,
)
from .forms import (
    _evidence_submit_form,
    _resolve_blocker_form,
    _start_confirm_form,
    _work_form_fields,
)
from .steps import (
    _STATUS_PILL_CLASSES,
)


def node_body(root, node_id: str, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/nodes/{id}` — brief-first, state-aware collapse (T4 §H).

    Pass requirements are stated once; the no-op evidence form is omitted;
    the one permitted raw id renders as small muted secondary text, and the
    page carries the single mono use. Nothing is marked current on node
    pages (T4 §H): the chrome renders with no active view.
    """
    view, head, failure = _page_head(
        root, query, dismiss_path=f"/nodes/{node_id}"
    )
    if failure is not None:
        return failure

    model = derive_node_detail(view, node_id)
    if model is None:
        body, status = _status_page(404, f"Unknown node {node_id}.", root)
        return "Not found", body, status

    actions = _node_actions_card(view, node_id)
    drill = _drill_down_card(node_id, view, Path(root), model)
    title = view.node_map[node_id].title

    secondary_id = f'<p class="small mut">{_esc(node_id)}</p>\n'
    cards, banners = _rich_cards_from_model(model.cards, titles=view.titles)
    body = (
        head
        + _degraded_banner(view)
        + secondary_id
        + render_rich_cards(
            cards,
            banners,
            state=ActiveViewState(view=view_by_name("node")),
        )
        + actions
        + drill
    )
    return title, body, 200


def _node_actions_card(view: JoinedView, node_id: str) -> str:
    """Node-detail write surface (G5): pass/master modals + daily-write forms.

    Structural omission per ADR 0007 §Validation (Amendment 2026-09-11) +
    P4.1: pass on a ``locked`` node and master on a node that is not
    ``passed`` are *omitted* — absent markup, never rendered-then-refused
    and never pre-disabled. Judgment eligibility stays live elsewhere.
    """
    open_blockers = [
        b for b in view.blockers if b.node_id == node_id and b.status == "open"
    ]
    node_url = f"/nodes/{node_id}"
    # The resolve write path stays reachable per affordance: the blocker id
    # rides only in the form's POST action (a write path, never visible
    # copy), beside the human description.
    blocker_section = (
        "<ul>"
        + "".join(
            f"<li>{_esc(b.description)} "
            + _resolve_blocker_form(b.id, node_url)
            + "</li>"
            for b in open_blockers
        )
        + "</ul>"
        if open_blockers
        else '<p class="mut">No open blockers.</p>'
    )
    title = view.titles.get(node_id, node_id)
    state = view.store.state_of(node_id)
    actions = ""
    if state != "locked":  # structural wall: pass on locked is omitted
        actions += (
            f'<a class="btn" href="/nodes/{_esc(node_id)}/pass">'
            f"Mark {_esc(title)} passed&hellip;</a>"
        )
    if state == "passed":  # structural wall: master requires passed
        actions += (
            f'<a class="btn master" href="/nodes/{_esc(node_id)}/master">'
            f"Mark {_esc(title)} mastered&hellip;</a>"
        )
    actions_html = f'<div class="actions">{actions}</div>' if actions else ""
    start_label = "Start this session"
    return (
        '<div class="card">\n'
        '<div class="kicker">Write actions</div>\n'
        + actions_html
        + f"\n<details open><summary>{_esc(start_label)}</summary>"
        f"{_start_confirm_form(view, node_id)}\n</details>\n"
        "<details><summary>Log work</summary>"
        '<form method="post" action="/work">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">'
        f"{_work_form_fields()}"
        '<button type="submit" class="btn secondary">Add work item</button></form></details>\n'
        "<details><summary>I'm stuck — create a blocker</summary>"
        '<form method="post" action="/nodes/'
        + _esc(node_id)
        + '/blockers">'
        f'<input type="hidden" name="next" value="/nodes/{_esc(node_id)}">'
        '<div class="form-row"><label>Description (the obstacle)</label>'
        '<input type="text" name="description" required>'
        '<p class="small mut">One concrete obstacle — what is stopping you?</p></div>'
        '<button type="submit" class="btn secondary">Create blocker</button></form></details>\n'
        f"{_evidence_submit_form(view, node_id)}\n"
        "<details><summary>Open blockers on this skill</summary>"
        f"{blocker_section}</details>\n"
        "</div>\n"
    )


def _drill_down_card(
    node_id: str,
    view: JoinedView,
    root: Path,
    model,
    *,
    clock=None,
) -> str:
    """Read-only factual drill-downs. No Mentor vocabulary here — tables only.

    Per-node facts come from ``DrilldownModel`` produced by
    ``commands.node_detail.derive_node_drilldown`` — the web layer
    no longer imports the per-handler private helpers from
    ``commands.node_detail``, and it no longer re-derives facts the
    CLI's ``derive_node_detail`` already produced.
    """
    drilldown = derive_node_drilldown(node_id, view, model, clock=clock)

    evidence_rows = [
        [_esc(title), _esc(kind), _esc(req), _esc(minimum), _esc(accepted)]
        for (title, kind, req, minimum, accepted) in drilldown.evidence_rows
    ]
    record_rows = [
        [_esc(rid), _esc(verdict), _esc(standing), _esc(loc)]
        for (rid, verdict, standing, loc) in drilldown.record_rows
    ]
    attempt_rows = [
        [_esc(aid), _esc(outcome), _esc(date)]
        for (aid, outcome, date) in drilldown.attempt_rows
    ]
    resource_rows = []
    for (rid, where, status) in drilldown.resource_rows:
        pill_class = _STATUS_PILL_CLASSES.get(status, "")
        resource_rows.append(
            [
                _esc(rid),
                f'<a href="{_esc(where)}">{_esc(where)}</a>' if where.startswith("http") else _esc(where),
                f'<span class="pill {pill_class}">{_esc(status)}</span>',
            ]
        )
    review_rows = [
        [_esc(rid), _esc(status), _esc(due), _esc(outcome)]
        for (rid, status, due, outcome) in drilldown.review_rows
    ]
    work_rows = [
        [_esc(sid), _esc(minutes if minutes is not None else "—"), _esc(notes)]
        for (sid, minutes, notes) in drilldown.work_rows
    ]
    blocker_rows = [
        [_esc(bid), _esc(status), _esc(desc)]
        for (bid, status, desc) in drilldown.blocker_rows
    ]
    remediation_rows = [
        [_esc(rid), _esc(status), _esc(desc)]
        for (rid, status, desc) in drilldown.remediation_rows
    ]
    prereq_rows = [
        [
            f'<a href="/nodes/{_esc(pid)}">{_esc(title)}</a>',
            _esc(pstate),
            "no — must pass first" if unsatisfied else "yes",
        ]
        for (pid, title, pstate, unsatisfied) in drilldown.prereq_rows
    ]
    unlock_rows = [
        [f'<a href="/nodes/{_esc(uid)}">{_esc(title)}</a>']
        for (uid, title) in drilldown.unlock_rows
    ]
    # Display newest first.
    event_rows = [
        [_esc(ts)[:19], _esc(cmd)]
        for (ts, cmd) in reversed(drilldown.event_rows)
    ][:10]

    def section(label: str, inner: str) -> str:
        return f"<details>\n<summary>{label}</summary>\n{inner}\n</details>\n"

    parts = ['<div class="card">\n<div class="kicker">Drill-down — read-only facts</div>\n']
    node_title = view.titles.get(node_id, node_id)
    attempt_handoff = (
        handoff_html("Recording a practice attempt", node_title) if attempt_rows else ""
    )
    parts.append(
        section(
            "Evidence",
            f"<p>{_esc(drilldown.gate_line)}</p>"
            + (_table(["Spec", "Kind", "Requirement", "Minimum", "Live accepted"], evidence_rows) if evidence_rows else '<p class="mut">No artifact specs.</p>')
            + (_table(["Record", "Verdict", "Standing", "Location"], record_rows) if record_rows else "")
            + (_table(["Attempt", "Outcome", "Date"], attempt_rows) if attempt_rows else "")
            + attempt_handoff,
        )
    )
    resource_handoff = ""
    if any(status in ("broken", "stale") for (_, _, status) in drilldown.resource_rows):
        resource_handoff = handoff_html("Checking a resource", node_title)
    parts.append(
        section(
            "Resources",
            (_table(["Resource", "Where", "Verification"], resource_rows)
            if resource_rows
            else '<p class="mut">(no resources linked to this skill)</p>')
            + resource_handoff,
        )
    )
    if review_rows:
        parts.append(section("Reviews", _table(["Review", "Status", "Scheduled", "Outcome"], review_rows) + handoff_html("Scheduling or completing a review", node_title)))
    execution_inner = ""
    if work_rows:
        execution_inner += _table(["Session", "Minutes", "Notes"], work_rows)
    if blocker_rows:
        execution_inner += _table(["Blocker", "Status", "Description"], blocker_rows)
    if remediation_rows:
        execution_inner += _table(["Remediation", "Status", "Description"], remediation_rows)
        execution_inner += handoff_html("Recording or completing remediation", node_title)
    if execution_inner:
        parts.append(section("Sessions, blockers, remediation", execution_inner))
    graph_inner = ""
    if prereq_rows:
        graph_inner += _table(["Hard prerequisite", "State", "Satisfied?"], prereq_rows)
    if unlock_rows:
        graph_inner += "<p>This unlocks:</p>" + _table(["Unlocks"], unlock_rows)
    if graph_inner:
        parts.append(section("Graph edges", graph_inner))
    if event_rows:
        parts.append(
            section(
                "Events (audit log)",
                _table(["Timestamp (UTC)", "Command"], event_rows)
                + '<p class="mut">Audit-only history — never read back to compute state.</p>',
            )
        )
    parts.append("</div>\n")
    return "".join(parts)

