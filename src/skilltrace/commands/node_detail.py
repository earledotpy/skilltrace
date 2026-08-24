"""`skilltrace node <node_id>` — the Mentor-voice node detail view (issue #41).

Per the #30 resolution: conversational brief + guided Where to learn / How to
proceed + Do this next. Joins curriculum (node frontmatter) + progress (state) +
evidence (specs/gates/records for eligibility) + resources (per-node reverse
index) + edges (prerequisites/unlocks) + execution (open session, open blockers)
for one node. Every available / locked / active / passed / mastered node
surfaces a clear reason, evidence gate, resource path, and next action —
expressed in Mentor shape, not a labeled dossier or raw ID dump.

Read-only: the dispatcher appends no audit event. Exit code reports whether the
*question* was answered: operational failures (unknown node, unloadable data)
exit non-zero; any rendered view exits 0.

Reuses `src/skilltrace/render.py` (stdlib-pure, no rich/ANSI) as the shared
render helper per #32. First of the remaining v0.9 output build order from
the friction-log resolution: **node -> today -> enrich next -> reports**.
"""

from __future__ import annotations

from pathlib import Path

from .. import render
from ..context import load_context_lenient
from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence.eligibility import compute_eligibility, live_accepted_count
from ..evidence.specs import ArtifactSpec
from ..execution.blockers import Blocker
from ..execution.sessions import open_session
from ..graph.edges import EdgeLoadError, GraphEdge
from ..graph.nodes import NodeLoadError, SkillNode
from ..graph.state import ProgressStoreError
from ..resources.registry import LearningResource


# --- Mentor voice prose generators -------------------------------------------
# Each returns the text for one section of the Mentor shape, given the joined
# data. The shape is: kicker, title+state, brief, Where to learn, How to
# proceed, Do this next, trailing context. State-specific prose is generated
# here; render.py owns the line formatting.


def _state_label(state: str) -> str:
    """Human-readable state label for the pill line."""
    return {
        "locked": "Locked",
        "available": "Ready to start",
        "active": "In progress",
        "passed": "Passed",
        "mastered": "Mastered",
    }.get(state, state.capitalize())


def _unsatisfied_prereqs(
    node_id: str, edges: list[GraphEdge], store
) -> list[tuple[str, str]]:
    """Return (prereq_node_id, prereq_state) for each unsatisfied hard prereq."""
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


def _unlocked_by(node_id: str, edges: list[GraphEdge]) -> list[str]:
    """Return node IDs that this node is a hard prerequisite for (what it unlocks)."""
    return [
        edge.target
        for edge in edges
        if edge.active
        and edge.edge_type == "hard_prerequisite"
        and edge.source == node_id
    ]


def _evidence_summary(
    node_id: str,
    specs: list[ArtifactSpec],
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


def _resource_lines(resources: list[LearningResource]) -> list[str]:
    """Format resource lines for the Where to learn section."""
    if not resources:
        return ["(no resources linked to this skill)"]
    lines = []
    for r in resources:
        name = r.id.replace("-", " ").title()
        if r.url:
            lines.append(f"{name} -- {r.url}")
        elif r.local_path:
            lines.append(f"{name} -- {r.local_path}")
        else:
            lines.append(name)
    return lines


def _open_blockers_for_node(
    node_id: str, blockers: list[Blocker]
) -> list[Blocker]:
    """Open blockers on this specific node."""
    return [b for b in blockers if b.node_id == node_id and b.status == "open"]


def _brief_available(
    node: SkillNode,
    specs: list[ArtifactSpec],
    has_gate: bool,
    records,
    node_blockers: list[Blocker],
) -> str:
    """Conversational brief for a Ready to start node."""
    text = (
        f"You're clear to begin {node.title} -- nothing is blocking you."
    )
    node_specs = [s for s in specs if s.node_id == node.id and s.required]
    if node_specs:
        total_needed = sum(s.minimum_count for s in node_specs)
        text += (
            f" It needs {total_needed} accepted submission(s) to pass."
            " You decide when the work is good enough, not an AI."
        )
    if node_blockers:
        text += (
            f" (Note: you have {len(node_blockers)} open blocker(s)"
            " -- advisory only, not blocking you from studying.)"
        )
    return text


def _brief_locked(
    node: SkillNode,
    unsatisfied: list[tuple[str, str]],
    titles: dict[str, str],
) -> str:
    """Conversational brief for a Locked node."""
    if not unsatisfied:
        return (
            f"{node.title} is locked, but no unsatisfied hard prerequisites"
            " were found -- run `skilltrace sync` to refresh readiness."
        )
    prereq_parts = []
    for prereq_id, prereq_state in unsatisfied:
        prereq_title = titles.get(prereq_id, prereq_id)
        prereq_label = _state_label(prereq_state)
        prereq_parts.append(f"{prereq_title} ({prereq_label.lower()})")

    if len(prereq_parts) == 1:
        return (
            f"{node.title} is locked: {prereq_parts[0]} still comes first."
            " No evidence can be submitted here until that dependency is cleared."
        )
    listing = "; ".join(prereq_parts)
    return (
        f"{node.title} is locked behind {len(prereq_parts)} prerequisites:"
        f" {listing}. Those must be passed before this skill opens."
    )


def _brief_active(
    node: SkillNode,
    specs: list[ArtifactSpec],
    has_gate: bool,
    records,
    has_open_session: bool,
    node_blockers: list[Blocker],
) -> str:
    """Conversational brief for an In progress node."""
    text = f"You're already working on {node.title}."
    if has_open_session:
        text += " A study session is open."
    node_specs = [s for s in specs if s.node_id == node.id and s.required]
    if node_specs:
        for spec in node_specs:
            accepted = live_accepted_count(records, spec.id)
            text += (
                f" You have {accepted} of {spec.minimum_count}"
                f" {spec.title}."
            )
    elig = compute_eligibility(
        node.id,
        [s for s in specs if s.node_id == node.id],
        has_gate=has_gate,
        records=records,
        node_state="active",
    )
    if elig.eligible:
        text += " You're pass-eligible -- you can mark this passed when ready."
    if node_blockers:
        for b in node_blockers:
            text += f" Blocker: {b.description}."
    return text


def _brief_passed(node: SkillNode) -> str:
    """Conversational brief for a Passed node."""
    return (
        f"{node.title} is passed -- all evidence requirements are met."
        " You can continue toward mastery with spaced reviews, or move"
        " on to the skills this unlocks."
    )


def _brief_mastered(node: SkillNode) -> str:
    """Conversational brief for a Mastered node."""
    return (
        f"{node.title} is mastered."
        " You've demonstrated deep, retained understanding of this skill."
    )


def _action_available(node: SkillNode) -> str:
    return f"Start studying {node.title}"


def _action_locked(
    unsatisfied: list[tuple[str, str]], titles: dict[str, str]
) -> str:
    if unsatisfied:
        first_id, _ = unsatisfied[0]
        first_title = titles.get(first_id, first_id)
        return f"Work on {first_title} first -- that's the unlock path"
    return "Run `skilltrace sync` to refresh readiness"


def _action_active(
    node: SkillNode,
    specs: list[ArtifactSpec],
    has_gate: bool,
    records,
) -> str:
    elig = compute_eligibility(
        node.id,
        [s for s in specs if s.node_id == node.id],
        has_gate=has_gate,
        records=records,
        node_state="active",
    )
    if elig.eligible:
        return f"Mark {node.title} passed: `skilltrace pass {node.id}`"
    return f"Submit your next piece of evidence for {node.title}"


def _action_passed(node: SkillNode) -> str:
    return f"Schedule a review: `skilltrace review schedule {node.id} --date <YYYY-MM-DD>`"


def _action_mastered(node: SkillNode) -> str:
    return "Nothing further needed -- explore what this skill unlocks"


def _unlocks_context(
    node_id: str, edges: list[GraphEdge], titles: dict[str, str]
) -> str | None:
    """Trailing context: what passing this node opens."""
    unlocks = _unlocked_by(node_id, edges)
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


def derive_node_detail(joined, node_id: str) -> list[str] | None:
    """Assemble the Mentor-voice lines for one node from a loaded JoinedView.

    Returns ``None`` when the node is unknown. Both ``skilltrace node`` and the
    serve shell's ``/nodes/{id}`` page render exactly these lines, so the two
    surfaces cannot drift apart.
    """
    edges = joined.edges
    store = joined.store
    specs = joined.specs
    gates = joined.gates
    records = joined.records

    # Verify node exists.
    node_map = joined.node_map
    if node_id not in node_map:
        return None
    node = node_map[node_id]

    has_gate = node_id in joined.has_gate
    node_resources = joined.resources_by_node.get(node_id, [])

    current_session = open_session(joined.sessions)
    has_open_session = current_session is not None

    node_blockers = _open_blockers_for_node(node_id, joined.blockers)

    # Derive context.
    titles = joined.titles
    state = store.state_of(node_id)
    state_label = _state_label(state)
    unsatisfied = _unsatisfied_prereqs(node_id, edges, store)

    # Build the Mentor voice output.
    lines: list[str] = []
    lines.append(render.section_kicker("This skill"))
    lines.extend(render.section_title_state(node.title, state_label))

    # Conversational brief (state-dependent).
    if state == "locked":
        brief = _brief_locked(node, unsatisfied, titles)
    elif state == "available":
        brief = _brief_available(node, specs, has_gate, records, node_blockers)
    elif state == "active":
        brief = _brief_active(
            node, specs, has_gate, records, has_open_session, node_blockers
        )
    elif state == "passed":
        brief = _brief_passed(node)
    elif state == "mastered":
        brief = _brief_mastered(node)
    else:
        brief = f"{node.title} is in state {state}."
    lines.extend(render.section_brief(brief))

    # Where to learn.
    lines.extend(render.section_where_to_learn(_resource_lines(node_resources)))

    # How to proceed.
    proceed = _evidence_summary(node_id, specs, has_gate, records)
    if state == "locked":
        if unsatisfied:
            prereq_names = [
                titles.get(pid, pid) for pid, _ in unsatisfied
            ]
            proceed = (
                f"Pass {', '.join(prereq_names)} first."
                " Until then this skill stays closed"
                " -- no evidence can be submitted here."
            )
        else:
            proceed = (
                "Readiness data may be stale -- run `skilltrace sync`"
                " to refresh."
            )
    lines.extend(render.section_how_to_proceed(proceed))

    # Do this next.
    if state == "locked":
        action = _action_locked(unsatisfied, titles)
    elif state == "available":
        action = _action_available(node)
    elif state == "active":
        action = _action_active(node, specs, has_gate, records)
    elif state == "passed":
        action = _action_passed(node)
    elif state == "mastered":
        action = _action_mastered(node)
    else:
        action = f"Check the status of {node.title}"
    lines.extend(render.section_do_this_next(action))

    # Trailing context (what this unlocks).
    context = _unlocks_context(node_id, edges, titles)
    if context:
        lines.extend(render.section_context(context))

    return lines


def node_detail(ctx: Context) -> CommandResult:
    """Load all layers via the JoinedView lenient seam and render the Mentor view."""
    root = ctx.root
    node_id = ctx.args.node_id

    # One deep join — graph/state strict, rest lenient (matches pre-JoinedView try/except blocks).
    try:
        joined = load_context_lenient(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"node: FAILED -- {exc}")
        return CommandResult(exit_code=1)

    lines = derive_node_detail(joined, node_id)
    if lines is None:
        print(f"node: FAILED -- unknown node {node_id}.")
        return CommandResult(exit_code=1)

    # Print the assembled view.
    for line in lines:
        print(line)

    return CommandResult(exit_code=0)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="node",
            kind=Kind.READ_ONLY,
            handler=node_detail,
            help="Show the Mentor-voice detail view for one node.",
        )
    )
