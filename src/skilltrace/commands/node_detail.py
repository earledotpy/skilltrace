"""`skilltrace node <node_id>` — the Mentor-voice node detail view (issue #41).

Per the #30 resolution: conversational brief + guided Where to learn / How to
proceed + Do this next. Joins curriculum (node frontmatter) + progress (state) +
evidence (specs/gates/records for eligibility) + resources (per-node reverse
index) + edges (prerequisites/unlocks) + execution (open session, open blockers)
for one node. Every available / locked / active / passed / mastered node
surfaces a clear reason, evidence gate, resource path, and next action —
expressed in Mentor shape, not a labeled dossier or raw ID dump.

Per the v1.x deepening (issue #144): the per-handler `_brief_locked` /
`_brief_available` / `_brief_passed` / ... ladders, the two divergent
`_state_label` tables, and the per-handler `_resource_lines` copies
collapse to `mentor.prose.brief_for` / `state_phrase` / `resource_lines`.
The derivation returns a typed `NodeModel` carrying the canonical
`MentorSection`s plus the per-node facts the web layer needs (it stops
importing private helpers).

Read-only: the dispatcher appends no audit event. Exit code reports whether the
*question* was answered: operational failures (unknown node, unloadable data)
exit non-zero; any rendered view exits 0.

Reuses `src/skilltrace/render.py` (stdlib-pure, no rich/ANSI) as the shared
render helper per #32. First of the remaining v0.9 output build order from
the friction-log resolution: **node -> today -> enrich next -> reports**.
"""

from __future__ import annotations

from dataclasses import dataclass

from .. import render
from ..context import JoinedView, load_context_lenient
from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence.eligibility import compute_eligibility, live_accepted_count
from ..execution.blockers import Blocker
from ..execution.sessions import open_session
from ..graph.edges import EdgeLoadError, GraphEdge
from ..graph.nodes import NodeLoadError, SkillNode
from ..graph.state import ProgressStoreError
from ..mentor.prose import (
    MentorSection,
    NodeFacts,
    NodeState,
    brief_for,
    resource_lines,
    state_phrase,
)


def unsatisfied_prereqs(
    node_id: str, edges: list[GraphEdge], store
) -> list[tuple[str, str]]:
    """Return (prereq_node_id, prereq_state) for each unsatisfied hard prereq.

    The web layer consumes the result off the ``NodeModel``; this
    public helper is also used by the drill-down card as a fallback
    when the model is unavailable.
    """
    result = []
    for edge in edges:
        if (
            edge.active
            and edge.edge_type == "hard_prerequisite"
            and edge.target == node_id
        ):
            prereq_state = store.state_of(edge.source)
            if prereq_state not in ("passed", "mastered"):
                result.append((edge.source, prereq_state))
    return result


def unlocked_by(node_id: str, edges: list[GraphEdge]) -> list[str]:
    """Return node IDs that this node is a hard prerequisite for (what it unlocks).

    Same dual access as ``unsatisfied_prereqs``: web reads it from
    ``NodeModel.unlocked_by``; the public helper is the fallback.
    """
    return [
        edge.target
        for edge in edges
        if edge.active
        and edge.edge_type == "hard_prerequisite"
        and edge.source == node_id
    ]


def _open_blockers_for_node(
    node_id: str, blockers: list[Blocker]
) -> list[Blocker]:
    """Open blockers on this specific node."""
    return [b for b in blockers if b.node_id == node_id and b.status == "open"]


def _evidence_summary(
    node_id: str,
    specs,
    has_gate: bool,
    records,
) -> str:
    """One-line evidence standing for How to proceed."""
    node_specs = [s for s in specs if s.node_id == node_id and s.required]
    if not node_specs:
        if not has_gate:
            return "This skill has no evidence gate and no required artifacts."
        return "No required artifact specs defined."

    parts = []
    for spec in node_specs:
        accepted = live_accepted_count(records, spec.id)
        parts.append(
            f"{accepted} of {spec.minimum_count} {spec.title}"
        )
    summary = "; ".join(parts)

    result = compute_eligibility(
        node_id,
        [s for s in specs if s.node_id == node_id],
        has_gate=has_gate,
        records=records,
        node_state="available",  # state-independent for the count
    )
    if result.eligible:
        return f"{summary} (pass-eligible -- you can mark this passed when ready)."
    return f"{summary}."


def _unlocks_context(
    node_id: str, edges: list[GraphEdge], titles: dict[str, str]
) -> str | None:
    """Trailing context: what passing this node opens."""
    unlocks = unlocked_by(node_id, edges)
    if not unlocks:
        return None
    names = [titles.get(uid, uid) for uid in unlocks]
    if len(names) == 1:
        return f"Passing this opens the door to {names[0]}."
    if len(names) <= 3:
        listing = ", ".join(names[:-1]) + f", and {names[-1]}"
        return f"Passing this opens the door to {listing}."
    return (
        f"Passing this opens the door to {len(names)} skills,"
        f" including {names[0]} and {names[1]}."
    )


# --- Shared derivation (CLI and web render the same lines) --------------------


@dataclass
class NodeModel:
    """The Mentor-voice node-detail derivation shared by `node` and the serve page.

    ``lines`` is the canonical Mentor output; the per-node facts ride
    alongside so the web drill-down card consumes them directly
    instead of re-deriving or importing private helpers.
    """

    lines: list[str]
    node: SkillNode
    state: str
    state_label: str
    unsatisfied: list[tuple[str, str]]
    unlocked_by: list[str]
    evidence_standing: str
    sections: list[MentorSection]


def derive_node_detail(joined, node_id: str) -> NodeModel | None:
    """Assemble the Mentor-voice model for one node from a loaded JoinedView.

    Returns ``None`` when the node is unknown. Both ``skilltrace node`` and
    the serve shell's ``/nodes/{id}`` page consume this model, so the two
    surfaces cannot drift apart.
    """
    edges = joined.edges
    store = joined.store
    specs = joined.specs
    records = joined.records

    node_map = joined.node_map
    if node_id not in node_map:
        return None
    node = node_map[node_id]

    has_gate = node_id in joined.has_gate
    node_resources = joined.resources_by_node.get(node_id, [])

    current_session = open_session(joined.sessions)
    has_open_session = current_session is not None

    node_blockers = _open_blockers_for_node(node_id, joined.blockers)

    titles = joined.titles
    state = store.state_of(node_id)
    state_label = state_phrase(NodeState(state))
    unsatisfied = unsatisfied_prereqs(node_id, edges, store)
    unlocked = unlocked_by(node_id, edges)

    facts = NodeFacts(
        node=node,
        state=NodeState(state),
        specs=list(specs),
        records=list(records),
        has_gate=has_gate,
        resource_lines=resource_lines(node_resources),
        unsatisfied_prereqs=list(unsatisfied),
        unlocked_by=list(unlocked),
        blockers_for_node=list(node_blockers),
        has_open_session=has_open_session,
        titles=dict(titles),
    )

    # The state-keyed dispatch produces the brief + do-this-next
    # sections. The "node" perspective is the most detailed.
    sections = brief_for(NodeState(state), facts, "node")

    # Insert the "Where to learn" resource block (canonical).
    resource_section = MentorSection(
        heading="Where to learn", lines=resource_lines(node_resources)
    )

    # Insert the eligibility-aware evidence line as "How to proceed" for
    # non-locked states (locked gets the prereq-aware variant directly
    # from brief_for).
    if NodeState(state) is NodeState.LOCKED:
        proceed_section = next(s for s in sections if s.heading == "How to proceed")
    else:
        proceed_text = _evidence_summary(node_id, specs, has_gate, records)
        proceed_section = MentorSection(heading="How to proceed", lines=[proceed_text])

    sections = [
        next(s for s in sections if s.heading == "Brief"),
        resource_section,
        proceed_section,
        next(s for s in sections if s.heading == "Do this next"),
    ]

    # Trailing context (what this unlocks).
    context_text = _unlocks_context(node_id, edges, titles)
    if context_text:
        sections.append(MentorSection(heading="Context", lines=[context_text]))

    lines: list[str] = []
    lines.append(render.section_kicker("This skill"))
    lines.extend(render.section_title_state(node.title, state_label))
    for section in sections:
        if section.heading == "Brief":
            lines.extend(render.section_brief(section.lines[0]))
        elif section.heading == "Where to learn":
            lines.extend(render.section_where_to_learn(section.lines))
        elif section.heading == "How to proceed":
            lines.extend(render.section_how_to_proceed(section.lines[0]))
        elif section.heading == "Do this next":
            lines.extend(render.section_do_this_next(section.lines[0]))
        elif section.heading == "Context":
            lines.extend(render.section_context(section.lines[0]))

    evidence_standing = _evidence_summary(node_id, specs, has_gate, records)

    return NodeModel(
        lines=lines,
        node=node,
        state=state,
        state_label=state_label,
        unsatisfied=unsatisfied,
        unlocked_by=unlocked,
        evidence_standing=evidence_standing,
        sections=sections,
    )


def node_detail(ctx: Context) -> CommandResult:
    """Load all layers via the JoinedView lenient seam and render the Mentor view."""
    root = ctx.root
    node_id = ctx.args.node_id

    try:
        joined = load_context_lenient(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"node: FAILED -- {exc}")
        return CommandResult(exit_code=1)

    model = derive_node_detail(joined, node_id)
    if model is None:
        print(f"node: FAILED -- unknown node {node_id}.")
        return CommandResult(exit_code=1)

    for line in model.lines:
        print(line)

    return CommandResult(exit_code=0)


# --- Drill-down derivation (web drill-down card) -----------------------------


@dataclass(frozen=True)
class DrilldownModel:
    """Structured drill-down facts the web card renders as HTML tables.

    The view consumes this and never re-derives per-node facts from
    the joined view directly — the seam is ``derive_node_drilldown``
    next to ``derive_node_detail``. Pure of I/O and printing.
    """

    gate_line: str
    evidence_rows: list[tuple[str, str, str, int, int]]  # title, kind, required, min, accepted
    record_rows: list[tuple[str, str, str, str]]  # id, verdict, standing, location
    attempt_rows: list[tuple[str, str, str]]  # id, outcome, date
    resource_rows: list[tuple[str, str, str]]  # id, where, status
    review_rows: list[tuple[str, str, str, str]]
    work_rows: list[tuple[str, int | None, str]]
    blocker_rows: list[tuple[str, str, str]]
    remediation_rows: list[tuple[str, str, str]]
    prereq_rows: list[tuple[str, str, bool]]  # title, state, unsatisfied
    unlock_rows: list[str]
    event_rows: list[tuple[str, str]]  # timestamp, command


def derive_node_drilldown(
    node_id: str,
    view: JoinedView,
    model: NodeModel,
    *,
    today=None,
    clock=None,
) -> DrilldownModel:
    """Assemble the read-only factual drill-down rows for one node.

    Pure of printing. The web view consumes this and emits HTML; the
    CLI has no need for a drill-down view. ``today`` defaults to
    ``None``; the web layer passes ``utc_today(clock=ctx.clock)`` so
    the dispatcher's clock override threads through resource-status
    derivation.
    """
    from ..execution.overdue import utc_today

    if today is None:
        today = utc_today(clock=clock)
    store = view.store
    specs = view.specs_by_node.get(node_id, [])
    records_for_specs = [
        r for r in view.records if r.artifact_spec_id in {s.id for s in specs}
    ]
    superseded_ids = {r.supersedes for r in view.records if r.supersedes}

    evidence_rows: list[tuple[str, str, str, int, int]] = [
        (
            s.title,
            s.artifact_kind,
            "required" if s.required else "optional",
            s.minimum_count,
            live_accepted_count(view.records, s.id),
        )
        for s in specs
    ]
    record_rows: list[tuple[str, str, str, str]] = [
        (
            r.id,
            "accepted" if r.accepted else "rejected",
            "superseded" if r.id in superseded_ids else "live",
            r.location,
        )
        for r in records_for_specs
    ]
    attempt_rows: list[tuple[str, str, str]] = [
        (a.id, a.outcome, str(a.created_at)[:10])
        for a in view.attempts
        if a.node_id == node_id
    ]

    gate_line = "No validation gate."
    if node_id in view.has_gate:
        gate = view.gates_by_node.get(node_id)
        authority = gate.command if gate.command else f"{gate.authority} (learner-stated verdict)"
        gate_line = f"Gate: {gate.id} — {authority}."

    from ..resources.status import derive_status

    window = view.policy.resource_stale_after_days
    resource_rows: list[tuple[str, str, str]] = []
    for r in view.resources_by_node.get(node_id, []):
        status = derive_status(r, today=today, stale_after_days=window).value
        where = r.url or r.local_path or ""
        resource_rows.append((r.id, where, status))

    review_rows: list[tuple[str, str, str, str]] = [
        (
            rv.id,
            rv.status,
            str(rv.scheduled_for)[:10],
            rv.outcome or rv.cancel_reason or "",
        )
        for rv in view.reviews
        if rv.node_id == node_id
    ]
    work_rows: list[tuple[str, int | None, str]] = [
        (
            w.session_id,
            w.minutes,
            w.notes or "",
        )
        for w in view.work
        if w.node_id == node_id
    ]
    blocker_rows: list[tuple[str, str, str]] = [
        (b.id, b.status, b.description)
        for b in view.blockers
        if b.node_id == node_id
    ]
    remediation_rows: list[tuple[str, str, str]] = [
        (ra.id, ra.status, ra.description)
        for ra in view.remediations
        if ra.node_id == node_id
    ]

    unsatisfied_set = {(pid, pstate) for pid, pstate in model.unsatisfied}
    prereq_rows: list[tuple[str, str, bool]] = []
    for edge in view.edges:
        if edge.active and edge.edge_type == "hard_prerequisite" and edge.target == node_id:
            pid = edge.source
            pstate = store.state_of(pid)
            title = view.titles.get(pid, pid)
            prereq_rows.append((title, pstate, (pid, pstate) in unsatisfied_set))

    unlock_rows: list[str] = [
        view.titles.get(uid, uid) for uid in model.unlocked_by
    ]

    # Original-order preservation within a node — events are audit-only
    # and never read to compute state (CONTEXT.md). We pass them in
    # original-order; the web layer reverses them for display
    # (most-recent-first).
    node_events = list(view.events_by_node.get(node_id, []))
    event_rows: list[tuple[str, str]] = [
        (str(e.get("timestamp", "")), str(e.get("command", "")))
        for e in node_events
    ]

    return DrilldownModel(
        gate_line=gate_line,
        evidence_rows=evidence_rows,
        record_rows=record_rows,
        attempt_rows=attempt_rows,
        resource_rows=resource_rows,
        review_rows=review_rows,
        work_rows=work_rows,
        blocker_rows=blocker_rows,
        remediation_rows=remediation_rows,
        prereq_rows=prereq_rows,
        unlock_rows=unlock_rows,
        event_rows=event_rows,
    )


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="node",
            kind=Kind.READ_ONLY,
            handler=node_detail,
            help="Show the Mentor-voice detail view for one node.",
        )
    )
