"""Unit tests for the pure `compute_impact` core (graph/impact.py, v2.2).

Hand-built nodes/edges plus a small in-memory progress store drive every
finding — flips, asserted-standing, recommendation diffs, no-op edges —
deterministically with no disk and no git. The wired `graph impact` command
(baseline fetch, exit codes, rendering) is covered in test_impact_command.py.
"""

from __future__ import annotations

import pytest

from skilltrace.graph.edges import GraphEdge
from skilltrace.graph.impact import compute_impact
from skilltrace.graph.nodes import SkillNode
from skilltrace.graph.state import ProgressEntry, ProgressStore


def _node(node_id: str) -> SkillNode:
    return SkillNode(id=node_id, title=node_id, summary="s", domain="d", track="t")


def _edge(edge_id: str, source: str, target: str, *, active: bool = True) -> GraphEdge:
    return GraphEdge(
        id=edge_id,
        source=source,
        target=target,
        edge_type="hard_prerequisite",
        reason="r",
        active=active,
    )


def _soft_edge(edge_id: str, source: str, target: str) -> GraphEdge:
    return GraphEdge(
        id=edge_id,
        source=source,
        target=target,
        edge_type="soft_prerequisite",
        reason="r",
        active=True,
    )


def _store(**states: str) -> ProgressStore:
    store = ProgressStore()
    for node_id, state in states.items():
        store.entries[node_id] = ProgressEntry(state=state)
    return store


A = "math.a_01"
B = "math.b_01"
C = "math.c_01"


def _run(baseline_edges, current_edges, store, **kwargs):
    return compute_impact(
        [_node(A), _node(B), _node(C)],
        baseline_edges,
        [_node(A), _node(B), _node(C)],
        current_edges,
        store,
        **kwargs,
    )


# --- Readiness flips ---------------------------------------------------------


def test_new_hard_prereq_flips_available_to_locked():
    store = _store(**{B: "available"})
    report = _run([], [_edge("e1", A, B)], store)
    assert [(f.node_id, f.baseline_state, f.current_state) for f in report.flips] == [
        (B, "available", "locked")
    ]


def test_removed_hard_prereq_flips_locked_to_available():
    store = _store(**{B: "locked"})
    report = _run([_edge("e1", A, B)], [], store)
    assert [(f.node_id, f.baseline_state, f.current_state) for f in report.flips] == [
        (B, "locked", "available")
    ]


def test_inactive_and_soft_edges_never_flip_readiness():
    store = _store(**{B: "available"})
    report = _run([], [_soft_edge("e2", A, B), _edge("e3", A, B, active=False)], store)
    assert report.flips == []


def test_asserted_node_never_flips_but_stands():
    store = _store(**{B: "passed"})
    report = _run([], [_edge("e1", A, B)], store)
    assert report.flips == []
    assert report.asserted_standing == [B]


def test_asserted_standing_needs_an_available_baseline():
    # Baseline already locks B (hard prereq present on both sides): the edit
    # takes nothing away, so there is nothing to "stand".
    store = _store(**{B: "passed"})
    report = _run([_edge("e1", A, B)], [_edge("e1", A, B)], store)
    assert report.flips == []
    assert report.asserted_standing == []


def test_new_node_without_baseline_state_is_not_a_flip():
    store = _store()
    report = compute_impact(
        [_node(A), _node(B)],
        [],
        [_node(A), _node(B), _node(C)],
        [_edge("e1", A, C)],
        store,
    )
    assert report.flips == []


def test_recommendation_changes_enter_and_move():
    # Leverage feeds scores: baseline gives B one outgoing edge (top rank);
    # current drops it, so B falls behind A — both moved. All three nodes
    # are `available` in the store (absent nodes are never candidates).
    store = _store(**{A: "available", B: "available", C: "available"})
    report = _run([_edge("e1", B, C)], [], store)
    ranks = {c.node_id: (c.baseline_rank, c.current_rank) for c in report.recommendation_changes}
    assert ranks[A] == (2, 1)
    assert ranks[B] == (1, 2)


def test_recommendation_enter_and_leave_at_limit_one():
    # At limit 1 only the top rank survives: loosening B's leverage swaps
    # the winner — the old top left, the new top entered.
    store = _store(**{A: "available", B: "available", C: "available"})
    report = _run([_edge("e1", B, C)], [], store, limit=1)
    ranks = {c.node_id: (c.baseline_rank, c.current_rank) for c in report.recommendation_changes}
    assert ranks[B] == (1, None)  # left
    assert ranks[A] == (None, 1)  # entered


def test_recommendation_diff_is_empty_on_identical_edges():
    store = _store()
    report = _run([_edge("e1", A, B)], [_edge("e1", A, B)], store)
    assert report.recommendation_changes == []


def test_no_op_edge_detected_and_reported():
    # Two parallel justifications for B would make one redundant; at seed
    # scale the simplest no-op is an edge whose target is asserted (readiness
    # derives only for non-asserted nodes, and asserted targets never rank).
    store = _store(**{A: "passed", B: "passed"})
    report = _run([], [_edge("e1", A, B)], store)
    assert [(e.edge_id, e.source, e.target) for e in report.no_op_edges] == [
        ("e1", A, B)
    ]


def test_live_edge_is_not_a_no_op():
    store = _store(**{B: "available"})
    report = _run([], [_edge("e1", A, B)], store)
    assert report.no_op_edges == []


def test_quiet_when_nothing_changes():
    store = _store()
    report = _run([], [], store)
    assert report.quiet is True
    assert report.flips == [] and report.no_op_edges == []
    assert report.dangling == []


def test_dangling_spec_gate_record_attempt_listed():
    store = _store()
    report = _run(
        [],
        [],
        store,
        dangling_specs=[("spec.math.gone_thing", "math.gone_01")],
        dangling_gates=[("gate.math.gone_thing", "math.gone_01")],
        dangling_records=[("ev.math.gone_01.001", "spec.math.gone_thing", None)],
        dangling_attempts=[("att.math.gone_01.001", "math.gone_01")],
    )
    assert [(d.node_id, list(d.referenced_by)) for d in report.dangling] == [
        (
            "math.gone_01",
            [
                "attempt:att.math.gone_01.001",
                "gate:gate.math.gone_thing",
                "record:ev.math.gone_01.001",
                "spec:spec.math.gone_thing",
            ],
        )
    ]
    assert report.quiet is False


def test_present_nodes_are_never_dangling():
    store = _store()
    report = _run(
        [],
        [],
        store,
        dangling_specs=[("spec.math.a_thing", A)],
        dangling_gates=[("gate.math.a_thing", A)],
        dangling_records=[("ev.math.a_01.001", "spec.math.a_thing", None)],
        dangling_attempts=[("att.math.a_01.001", A)],
    )
    assert report.dangling == []
