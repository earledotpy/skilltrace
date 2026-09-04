"""Mentor-voice prose layer — one seam for every read-only command and view.

The shallow prose layer (per-handler `_brief_locked` / `_brief_available`
ladders, divergent `_state_label` tables, three `_resource_lines`
duplicates) is the friction this module collapses. Pure of I/O and
pure of wall-clock calls: callers compute `NodeFacts` from the joined
view and pass them in.

The shape is a state-keyed dispatch (`brief_for(state, facts,
perspective)`), not a string-template engine. Each call returns a
typed `list[MentorSection]` value; future voice tuning is a per-state
edit, not a template rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from ..evidence.specs import ArtifactSpec
from ..evidence.records import EvidenceRecord
from ..execution.blockers import Blocker
from ..graph.nodes import SkillNode


class NodeState(str, Enum):
    """The five canonical node states (CONTEXT.md).

    Lives here so the prose dispatch and the web pill renderer share
    one canonical set; ``store.state_of(node_id)`` returns the raw
    string from disk and callers convert with ``NodeState(s)`` (the
    str-mixin keeps the existing string contract).
    """

    LOCKED = "locked"
    AVAILABLE = "available"
    ACTIVE = "active"
    PASSED = "passed"
    MASTERED = "mastered"


_STATE_PHRASES: dict[NodeState, str] = {
    NodeState.LOCKED: "Locked",
    NodeState.AVAILABLE: "Ready to start",
    NodeState.ACTIVE: "In progress",
    NodeState.PASSED: "Passed",
    NodeState.MASTERED: "Mastered",
}


def state_phrase(state: NodeState) -> str:
    """The canonical Mentor-voice phrase for a node state pill.

    One table; the two divergent `_state_label` ladders in
    `commands/node_detail.py` and `commands/recommend.py` both
    collapse to this lookup.
    """
    return _STATE_PHRASES[state]


@dataclass(frozen=True)
class MentorSection:
    """One rendered section: a heading plus its lines.

    The CLI's `render.py` line producers map each section to its
    canonical layout; the web layer's line-to-HTML transform consumes
    the same lines.
    """

    heading: str
    lines: list[str] = field(default_factory=list)


Perspective = Literal["node", "today", "next"]


@dataclass(frozen=True)
class NodeFacts:
    """The uniform tuple every Mentor section consumes.

    Constructing one is the caller's job — the prose module reads
    only these fields, never the joined view directly, so it stays
    pure of I/O and easy to test with a small fixture.
    """

    node: SkillNode
    state: NodeState
    specs: list[ArtifactSpec]
    records: list[EvidenceRecord]
    has_gate: bool
    resource_lines: list[str]
    unsatisfied_prereqs: list[tuple[str, str]]
    unlocked_by: list[str]
    blockers_for_node: list[Blocker]
    has_open_session: bool = False
    titles: dict[str, str] = field(default_factory=dict)


def brief_for(state: NodeState, facts: NodeFacts, perspective: Perspective) -> list[MentorSection]:
    """Return the Mentor-voice sections for one node.

    The dispatch is state-keyed (one branch per state) with a small
    perspective parameter for shared phrases. Per-state prose lives
    in ``_brief_*`` helpers below; this function is the single seam.

    Each branch returns the canonical shape ``[Brief, Do this next]``
    (plus optional extras like ``How to proceed`` when the prose
    itself owns it, e.g. locked). The caller adds state-aware
    sections (e.g. ``How to proceed`` for the eligibility-aware
    evidence line) on top of the prose output.
    """
    if state is NodeState.LOCKED:
        return _brief_locked(facts, perspective)
    if state is NodeState.AVAILABLE:
        return _brief_available(facts, perspective)
    if state is NodeState.ACTIVE:
        return _brief_active(facts, perspective)
    if state is NodeState.PASSED:
        return _brief_passed(facts, perspective)
    if state is NodeState.MASTERED:
        return _brief_mastered(facts, perspective)
    return [
        MentorSection(heading="Brief", lines=[f"{facts.node.title} is in state {state.value}."]),
        MentorSection(heading="Do this next", lines=[f"Check the status of {facts.node.title}"]),
    ]


def resource_lines(resources) -> list[str]:
    """The canonical resource-line formatter.

    Replaces the three duplicated `_resource_lines` copies in
    `commands/node_detail.py`, `commands/today.py`, and
    `commands/recommend.py`. Mirrors the prior output exactly:
    ``(no resources linked to this skill)`` placeholder when empty;
    URL or local-path trailing clause when present; just the title
    otherwise.
    """
    if not resources:
        return ["(no resources linked to this skill)"]
    lines: list[str] = []
    for r in resources:
        name = r.id.replace("-", " ").title()
        if r.url:
            lines.append(f"{name} -- {r.url}")
        elif r.local_path:
            lines.append(f"{name} -- {r.local_path}")
        else:
            lines.append(name)
    return lines


# ---------------------------------------------------------------------------
# Per-state prose
# ---------------------------------------------------------------------------


def _brief_locked(facts: NodeFacts, perspective: Perspective) -> list[MentorSection]:
    node = facts.node
    unsatisfied = facts.unsatisfied_prereqs
    if not unsatisfied:
        brief = (
            f"{node.title} is locked, but no unsatisfied hard prerequisites"
            " were found -- run `skilltrace sync` to refresh readiness."
        )
    else:
        parts = []
        for pid, pstate in unsatisfied:
            title = facts.titles.get(pid, pid)
            label = _STATE_PHRASES.get(NodeState(pstate), pstate.capitalize())
            parts.append(f"{title} ({label.lower()})")
        if len(parts) == 1:
            brief = (
                f"{node.title} is locked: {parts[0]} still comes first."
                " No evidence can be submitted here until that dependency is cleared."
            )
        else:
            listing = "; ".join(parts)
            brief = (
                f"{node.title} is locked behind {len(parts)} prerequisites:"
                f" {listing}. Those must be passed before this skill opens."
            )

    sections: list[MentorSection] = [MentorSection(heading="Brief", lines=[brief])]
    if unsatisfied:
        names = [pid for pid, _ in unsatisfied]
        proceed = (
            f"Pass {', '.join(names)} first."
            " Until then this skill stays closed"
            " -- no evidence can be submitted here."
        )
    else:
        proceed = (
            "Readiness data may be stale -- run `skilltrace sync`"
            " to refresh."
        )
    sections.append(MentorSection(heading="How to proceed", lines=[proceed]))

    if unsatisfied:
        first_id = unsatisfied[0][0]
        first_title = facts.titles.get(first_id, first_id)
        action = f"Work on {first_title} first -- that's the unlock path"
    else:
        action = "Run `skilltrace sync` to refresh readiness"
    sections.append(MentorSection(heading="Do this next", lines=[action]))
    return sections


def _brief_available(facts: NodeFacts, perspective: Perspective) -> list[MentorSection]:
    node = facts.node
    text = f"You're clear to begin {node.title} -- nothing is blocking you."
    node_specs = [s for s in facts.specs if s.node_id == node.id and s.required]
    if node_specs:
        total_needed = sum(s.minimum_count for s in node_specs)
        text += (
            f" It needs {total_needed} accepted submission(s) to pass."
            " You decide when the work is good enough, not an AI."
        )
    if facts.blockers_for_node:
        text += (
            f" (Note: you have {len(facts.blockers_for_node)} open blocker(s)"
            " -- advisory only, not blocking you from studying.)"
        )
    return [
        MentorSection(heading="Brief", lines=[text]),
        MentorSection(heading="Do this next", lines=[f"Start studying {node.title}"]),
    ]


def _brief_active(facts: NodeFacts, perspective: Perspective) -> list[MentorSection]:
    node = facts.node
    text = f"You're already working on {node.title}."
    if facts.has_open_session:
        text += " A study session is open."
    node_specs = [s for s in facts.specs if s.node_id == node.id and s.required]
    if node_specs:
        from ..evidence.eligibility import live_accepted_count

        for spec in node_specs:
            accepted = live_accepted_count(facts.records, spec.id)
            text += (
                f" You have {accepted} of {spec.minimum_count}"
                f" {spec.title}."
            )
    from ..evidence.eligibility import compute_eligibility

    elig = compute_eligibility(
        node.id,
        [s for s in facts.specs if s.node_id == node.id],
        has_gate=facts.has_gate,
        records=facts.records,
        node_state="active",
    )
    if elig.eligible:
        text += " You're pass-eligible -- you can mark this passed when ready."
    for b in facts.blockers_for_node:
        text += f" Blocker: {b.description}."
    if elig.eligible:
        action = f"Mark {node.title} passed: `skilltrace pass {node.id}`"
    else:
        action = f"Submit your next piece of evidence for {node.title}"
    return [
        MentorSection(heading="Brief", lines=[text]),
        MentorSection(heading="Do this next", lines=[action]),
    ]


def _brief_passed(facts: NodeFacts, perspective: Perspective) -> list[MentorSection]:
    node = facts.node
    return [
        MentorSection(
            heading="Brief",
            lines=[
                (
                    f"{node.title} is passed -- all evidence requirements are met."
                    " You can continue toward mastery with spaced reviews, or move"
                    " on to the skills this unlocks."
                )
            ],
        ),
        MentorSection(
            heading="Do this next",
            lines=[
                f"Schedule a review: `skilltrace review schedule {node.id} --date <YYYY-MM-DD>`"
            ],
        ),
    ]


def _brief_mastered(facts: NodeFacts, perspective: Perspective) -> list[MentorSection]:
    node = facts.node
    return [
        MentorSection(
            heading="Brief",
            lines=[
                (
                    f"{node.title} is mastered."
                    " You've demonstrated deep, retained understanding of this skill."
                )
            ],
        ),
        MentorSection(
            heading="Do this next",
            lines=["Nothing further needed -- explore what this skill unlocks"],
        ),
    ]
