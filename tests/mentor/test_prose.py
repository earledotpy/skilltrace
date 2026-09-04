"""Table-driven tests for `mentor.prose` (issue #144).

Per-state prose (the per-handler `_brief_*` ladders that previously
lived in `commands/node_detail.py`, `commands/today.py`,
`commands/recommend.py`) collapses to one state-keyed dispatch.
The test surface is the dispatch itself — small fixture, no joined
view required.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from skilltrace.evidence.specs import ArtifactSpec
from skilltrace.execution.blockers import Blocker
from skilltrace.graph.nodes import SkillNode
from skilltrace.mentor.prose import (
    MentorSection,
    NodeFacts,
    NodeState,
    brief_for,
    resource_lines,
    state_phrase,
)
from skilltrace.resources.registry import LearningResource


def _node(id: str = "math.arithmetic.x_01", title: str = "Apply X") -> SkillNode:
    return SkillNode(
        id=id,
        title=title,
        summary="A test skill.",
        domain="mathematics",
        track="foundational",
    )


def _spec(id: str, node_id: str, *, required: bool, minimum: int = 1) -> ArtifactSpec:
    return ArtifactSpec(
        id=id,
        node_id=node_id,
        title="Test Spec",
        artifact_kind="repo_file",
        required=required,
        minimum_count=minimum,
    )


def _blocker(description: str) -> Blocker:
    return Blocker(
        id="blk.001",
        node_id="math.arithmetic.x_01",
        status="open",
        description=description,
        created_at="2026-08-01T00:00:00Z",
    )


def _facts(
    state: NodeState,
    *,
    specs=None,
    records=None,
    has_gate: bool = True,
    resource_lines=None,
    unsatisfied=None,
    unlocked_by=None,
    blockers_for_node=None,
    has_open_session: bool = False,
    titles=None,
) -> NodeFacts:
    return NodeFacts(
        node=_node(),
        state=state,
        specs=specs or [],
        records=records or [],
        has_gate=has_gate,
        resource_lines=resource_lines or [],
        unsatisfied_prereqs=unsatisfied or [],
        unlocked_by=unlocked_by or [],
        blockers_for_node=blockers_for_node or [],
        has_open_session=has_open_session,
        titles=titles or {},
    )


# ---------------------------------------------------------------------------
# state_phrase — one canonical lookup
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "state,expected",
    [
        (NodeState.LOCKED, "Locked"),
        (NodeState.AVAILABLE, "Ready to start"),
        (NodeState.ACTIVE, "In progress"),
        (NodeState.PASSED, "Passed"),
        (NodeState.MASTERED, "Mastered"),
    ],
)
def test_state_phrase_canonical(state, expected):
    assert state_phrase(state) == expected


# ---------------------------------------------------------------------------
# brief_for — locked branch
# ---------------------------------------------------------------------------


def test_brief_locked_with_one_unsatisfied_prereq():
    facts = _facts(
        NodeState.LOCKED,
        unsatisfied=[("math.arithmetic.prereq_01", "available")],
        titles={"math.arithmetic.prereq_01": "Earlier Skill"},
    )
    sections = brief_for(NodeState.LOCKED, facts, "node")
    assert [s.heading for s in sections] == ["Brief", "How to proceed", "Do this next"]
    assert "locked" in sections[0].lines[0].lower()
    assert "Earlier Skill (ready to start)" in sections[0].lines[0]
    assert "Earlier Skill first -- that's the unlock path" in sections[2].lines[0]


def test_brief_locked_with_multiple_unsatisfied_prereqs():
    facts = _facts(
        NodeState.LOCKED,
        unsatisfied=[
            ("math.arithmetic.prereq_01", "active"),
            ("math.arithmetic.prereq_02", "locked"),
        ],
        titles={
            "math.arithmetic.prereq_01": "Prereq One",
            "math.arithmetic.prereq_02": "Prereq Two",
        },
    )
    sections = brief_for(NodeState.LOCKED, facts, "node")
    assert "locked behind 2 prerequisites" in sections[0].lines[0]


def test_brief_locked_with_no_unsatisfied_prereqs():
    facts = _facts(NodeState.LOCKED, unsatisfied=[])
    sections = brief_for(NodeState.LOCKED, facts, "node")
    assert "no unsatisfied hard prerequisites" in sections[0].lines[0]
    assert "Run `skilltrace sync` to refresh readiness" in sections[2].lines[0]


# ---------------------------------------------------------------------------
# brief_for — available branch
# ---------------------------------------------------------------------------


def test_brief_available_no_blockers_no_specs():
    facts = _facts(NodeState.AVAILABLE)
    sections = brief_for(NodeState.AVAILABLE, facts, "node")
    assert "clear to begin" in sections[0].lines[0]
    assert "Start studying Apply X" in sections[-1].lines[0]


def test_brief_available_with_required_specs():
    facts = _facts(
        NodeState.AVAILABLE,
        specs=[_spec("spec.001", "math.arithmetic.x_01", required=True, minimum=2)],
    )
    sections = brief_for(NodeState.AVAILABLE, facts, "node")
    assert "2 accepted submission(s)" in sections[0].lines[0]


def test_brief_available_with_blockers_mentions_them_advisory():
    facts = _facts(
        NodeState.AVAILABLE,
        blockers_for_node=[_blocker("Confused about precedence")],
    )
    sections = brief_for(NodeState.AVAILABLE, facts, "node")
    assert "1 open blocker(s)" in sections[0].lines[0]
    assert "advisory only" in sections[0].lines[0]


# ---------------------------------------------------------------------------
# brief_for — active branch
# ---------------------------------------------------------------------------


def test_brief_active_with_open_session_mentions_it():
    facts = _facts(NodeState.ACTIVE, has_open_session=True)
    sections = brief_for(NodeState.ACTIVE, facts, "node")
    assert "A study session is open." in sections[0].lines[0]


def test_brief_active_without_open_session_does_not_mention_it():
    facts = _facts(NodeState.ACTIVE, has_open_session=False)
    sections = brief_for(NodeState.ACTIVE, facts, "node")
    assert "A study session is open." not in sections[0].lines[0]


def test_brief_active_with_blocker_appended_to_brief():
    facts = _facts(
        NodeState.ACTIVE,
        blockers_for_node=[_blocker("Confused about precedence")],
    )
    sections = brief_for(NodeState.ACTIVE, facts, "node")
    assert "Blocker: Confused about precedence." in sections[0].lines[0]


# ---------------------------------------------------------------------------
# brief_for — passed/mastered branches
# ---------------------------------------------------------------------------


def test_brief_passed():
    facts = _facts(NodeState.PASSED)
    sections = brief_for(NodeState.PASSED, facts, "node")
    assert "is passed" in sections[0].lines[0]
    assert "Schedule a review" in sections[-1].lines[0]


def test_brief_mastered():
    facts = _facts(NodeState.MASTERED)
    sections = brief_for(NodeState.MASTERED, facts, "node")
    assert "is mastered" in sections[0].lines[0]
    assert "Nothing further needed" in sections[-1].lines[0]


# ---------------------------------------------------------------------------
# resource_lines — single canonical formatter
# ---------------------------------------------------------------------------


def test_resource_lines_empty_returns_placeholder():
    assert resource_lines([]) == ["(no resources linked to this skill)"]


def test_resource_lines_with_url():
    @dataclass
    class _Stub:
        id: str
        url: str | None = None
        local_path: str | None = None

    assert resource_lines([_Stub(id="khan-algebra", url="https://x")]) == [
        "Khan Algebra -- https://x"
    ]


def test_resource_lines_with_local_path():
    @dataclass
    class _Stub:
        id: str
        url: str | None = None
        local_path: str | None = None

    assert resource_lines([_Stub(id="local-notes", local_path="docs/x.md")]) == [
        "Local Notes -- docs/x.md"
    ]


def test_resource_lines_with_just_id():
    @dataclass
    class _Stub:
        id: str
        url: str | None = None
        local_path: str | None = None

    assert resource_lines([_Stub(id="solo-resource")]) == ["Solo Resource"]
