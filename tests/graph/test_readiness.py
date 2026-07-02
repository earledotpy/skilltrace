"""Readiness derivation: the derived (`locked`/`available`) half of the model.

`sync_readiness(nodes, edges, store)` recomputes derived readiness for every
non-asserted node and never touches asserted progress. These are the pure-seam
tests over hand-built lists (mirroring test_validation.py); the command-level
save + audit-event path is covered in test_sync_command.py, and the real seed's
idempotency is pinned at the bottom.
"""

from __future__ import annotations

from pathlib import Path

from skilltrace.graph.edges import GraphEdge, load_edges
from skilltrace.graph.nodes import load_nodes
from skilltrace.graph.readiness import derive_readiness, sync_readiness
from skilltrace.graph.state import ProgressStore, load_state

REPO_ROOT = Path(__file__).resolve().parents[2]


def _node(node_id: str):
    from skilltrace.graph.nodes import SkillNode

    return SkillNode(id=node_id, title=node_id, summary=node_id, domain="d", track="t")


def _edge(
    source: str,
    target: str,
    *,
    edge_type: str = "hard_prerequisite",
    active: bool = True,
) -> GraphEdge:
    return GraphEdge(
        id=f"edge.{source}__{target}",
        source=source,
        target=target,
        edge_type=edge_type,
        reason="because",
        active=active,
    )


# --- The rule ---------------------------------------------------------------

def test_node_with_no_prerequisites_is_available():
    nodes = [_node("a.b.root_01")]
    result = sync_readiness(nodes, [], ProgressStore())
    assert [(c.node_id, c.new_state) for c in result.changes] == [("a.b.root_01", "available")]


def test_node_is_locked_until_hard_prereq_is_passed():
    nodes = [_node("a.b.src_01"), _node("a.b.dst_01")]
    edges = [_edge("a.b.src_01", "a.b.dst_01")]
    store = ProgressStore()

    # Source not yet passed -> target stays locked (absent == locked floor).
    result = sync_readiness(nodes, edges, store)
    assert store.state_of("a.b.dst_01") == "locked"
    assert store.state_of("a.b.src_01") == "available"  # src has no prereqs

    # Pass the source (asserted, as a fixture) and re-sync -> target available.
    store.write_asserted("a.b.src_01", "passed")
    result = sync_readiness(nodes, edges, store)
    assert store.state_of("a.b.dst_01") == "available"
    assert any(c.node_id == "a.b.dst_01" and c.new_state == "available" for c in result.changes)


def test_all_hard_prereqs_must_be_satisfied():
    nodes = [_node("a.b.p1_01"), _node("a.b.p2_01"), _node("a.b.dst_01")]
    edges = [_edge("a.b.p1_01", "a.b.dst_01"), _edge("a.b.p2_01", "a.b.dst_01")]
    store = ProgressStore()
    store.write_asserted("a.b.p1_01", "passed")  # only one of two passed
    sync_readiness(nodes, edges, store)
    assert store.state_of("a.b.dst_01") == "locked"

    store.write_asserted("a.b.p2_01", "mastered")  # mastered also satisfies
    sync_readiness(nodes, edges, store)
    assert store.state_of("a.b.dst_01") == "available"


def test_soft_and_remediation_edges_never_lock():
    nodes = [_node("a.b.src_01"), _node("a.b.soft_01"), _node("a.b.rem_01")]
    edges = [
        _edge("a.b.src_01", "a.b.soft_01", edge_type="soft_prerequisite"),
        _edge("a.b.src_01", "a.b.rem_01", edge_type="remediation"),
    ]
    store = ProgressStore()  # src never passed
    sync_readiness(nodes, edges, store)
    assert store.state_of("a.b.soft_01") == "available"
    assert store.state_of("a.b.rem_01") == "available"


def test_inactive_hard_edge_does_not_lock():
    nodes = [_node("a.b.src_01"), _node("a.b.dst_01")]
    edges = [_edge("a.b.src_01", "a.b.dst_01", active=False)]  # parked
    store = ProgressStore()
    sync_readiness(nodes, edges, store)
    assert store.state_of("a.b.dst_01") == "available"


# --- Curriculum edits re-lock un-started nodes only -------------------------

def test_adding_hard_prereq_relocks_an_unstarted_node():
    nodes = [_node("a.b.src_01"), _node("a.b.dst_01")]
    store = ProgressStore()
    store.write_readiness("a.b.dst_01", "available")  # un-started (derived)

    # A curriculum edit adds an unmet hard prerequisite.
    edges = [_edge("a.b.src_01", "a.b.dst_01")]
    result = sync_readiness(nodes, edges, store)

    assert store.state_of("a.b.dst_01") == "locked"
    assert any(
        c.node_id == "a.b.dst_01" and c.old_state == "available" and c.new_state == "locked"
        for c in result.changes
    )


def test_adding_hard_prereq_never_relocks_a_started_node():
    # Safety-critical: asserted progress is never moved backward by sync.
    nodes = [_node("a.b.src_01"), _node("a.b.dst_01")]
    store = ProgressStore()
    store.write_asserted("a.b.dst_01", "active")  # learner has started it

    edges = [_edge("a.b.src_01", "a.b.dst_01")]  # unmet hard prereq added
    result = sync_readiness(nodes, edges, store)

    assert store.state_of("a.b.dst_01") == "active"  # untouched
    assert result.skipped_asserted == 1
    assert all(c.node_id != "a.b.dst_01" for c in result.changes)


def test_sync_never_writes_asserted_progress():
    # Sync flips readiness of one node while three asserted nodes sit in the
    # store; their asserted states must be identical before and after.
    nodes = [_node(f"a.b.n{i}_01") for i in range(4)]
    store = ProgressStore()
    store.write_asserted("a.b.n0_01", "active")
    store.write_asserted("a.b.n1_01", "passed")
    store.write_asserted("a.b.n2_01", "mastered")
    # n3 has no prereqs -> will flip locked(floor) -> available.
    before = {nid: store.state_of(nid) for nid in ("a.b.n0_01", "a.b.n1_01", "a.b.n2_01")}

    result = sync_readiness(nodes, [], store)

    after = {nid: store.state_of(nid) for nid in ("a.b.n0_01", "a.b.n1_01", "a.b.n2_01")}
    assert before == after
    assert result.skipped_asserted == 3
    assert result.changed_ids == ["a.b.n3_01"]


# --- changed_ids shape ------------------------------------------------------

def test_changed_ids_is_sorted_node_ids_only():
    nodes = [_node("a.b.z_01"), _node("a.b.a_01")]
    result = sync_readiness(nodes, [], ProgressStore())
    assert result.changed_ids == ["a.b.a_01", "a.b.z_01"]
    assert all(isinstance(x, str) for x in result.changed_ids)


def test_idempotent_second_sync_reports_no_changes():
    nodes = [_node("a.b.src_01"), _node("a.b.dst_01")]
    edges = [_edge("a.b.src_01", "a.b.dst_01")]
    store = ProgressStore()
    sync_readiness(nodes, edges, store)  # first pass settles readiness
    result = sync_readiness(nodes, edges, store)  # second pass
    assert result.changes == []


# --- derive_readiness unit --------------------------------------------------

def test_derive_readiness_direct():
    store = ProgressStore()
    store.write_asserted("a.b.src_01", "passed")
    prereqs = {"a.b.dst_01": ["a.b.src_01"], "a.b.other_01": ["a.b.missing_01"]}
    assert derive_readiness("a.b.dst_01", prereqs, store) == "available"
    assert derive_readiness("a.b.other_01", prereqs, store) == "locked"
    assert derive_readiness("a.b.noprereq_01", prereqs, store) == "available"


# --- Integration: real seed is already in sync (idempotent) -----------------

def test_seed_graph_is_already_in_sync():
    # Verified empirically: no seed source is passed/mastered, so every node with
    # an active hard prerequisite is locked and all others available — a clean
    # sync produces zero changes. Pinned as a regression guard.
    nodes = load_nodes(REPO_ROOT)
    edges = load_edges(REPO_ROOT)
    store = load_state(REPO_ROOT)
    result = sync_readiness(nodes, edges, store)
    assert result.changes == [], (
        "seed state.yaml drifted from its derived readiness: "
        f"{[(c.node_id, c.old_state, c.new_state) for c in result.changes]}"
    )
