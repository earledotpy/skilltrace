"""Graph validation: the Layer 1 cross-reference contract (issue #5).

The loaders validate *shape* one file at a time; validation is where the graph
is checked *as a whole* — unique node/edge IDs, edge endpoints that name real
nodes, no cycle among active hard prerequisites, and no progress entry pointing
at a missing node. Soft-prerequisite cycles are surfaced as warnings, never
errors, and warnings never change the exit result.

The pure `check_graph(nodes, edges, store)` seam takes already-loaded data so
these fixtures are hand-built lists; `load_and_validate` is exercised against the
real seed data at the bottom (the roadmap exit gate, pinned as a test).
"""

from __future__ import annotations

from pathlib import Path

from skilltrace.graph.edges import GraphEdge
from skilltrace.graph.nodes import SkillNode
from skilltrace.graph.state import ProgressStore
from skilltrace.graph.validation import ValidationResult, check_graph, load_and_validate

REPO_ROOT = Path(__file__).resolve().parents[2]


def _node(node_id: str) -> SkillNode:
    return SkillNode(
        id=node_id, title=node_id, summary=node_id, domain="d", track="t"
    )


def _edge(
    source: str, target: str, *, edge_type: str = "hard_prerequisite", edge_id: str | None = None, active: bool = True
) -> GraphEdge:
    return GraphEdge(
        id=edge_id or f"edge.{source}__{target}",
        source=source,
        target=target,
        edge_type=edge_type,
        reason="because",
        active=active,
    )


def _chain(*ids: str, edge_type: str = "hard_prerequisite") -> list[GraphEdge]:
    return [_edge(a, b, edge_type=edge_type) for a, b in zip(ids, ids[1:])]


# --- Happy path -------------------------------------------------------------

def test_valid_graph_passes():
    nodes = [_node("a.b.n_01"), _node("a.b.n_02"), _node("a.b.n_03")]
    edges = _chain("a.b.n_01", "a.b.n_02", "a.b.n_03")
    result = check_graph(nodes, edges, ProgressStore())
    assert isinstance(result, ValidationResult)
    assert result.ok
    assert result.errors == []
    assert result.node_count == 3
    assert result.edge_count == 2


# --- Duplicate detection ----------------------------------------------------

def test_duplicate_node_id_fails_naming_the_id():
    nodes = [_node("a.b.n_01"), _node("a.b.n_01")]
    result = check_graph(nodes, [], ProgressStore())
    assert not result.ok
    assert any("a.b.n_01" in e for e in result.errors)


def test_duplicate_edge_id_fails_naming_the_id():
    nodes = [_node("a.b.n_01"), _node("a.b.n_02")]
    edges = [
        _edge("a.b.n_01", "a.b.n_02", edge_id="edge.dup"),
        _edge("a.b.n_02", "a.b.n_01", edge_id="edge.dup"),
    ]
    result = check_graph(nodes, edges, ProgressStore())
    assert not result.ok
    assert any("edge.dup" in e for e in result.errors)


# --- Edge endpoints ---------------------------------------------------------

def test_missing_edge_source_fails():
    nodes = [_node("a.b.n_02")]
    edges = [_edge("a.b.ghost_01", "a.b.n_02")]
    result = check_graph(nodes, edges, ProgressStore())
    assert not result.ok
    assert any("a.b.ghost_01" in e for e in result.errors)


def test_missing_edge_target_fails():
    nodes = [_node("a.b.n_01")]
    edges = [_edge("a.b.n_01", "a.b.ghost_01")]
    result = check_graph(nodes, edges, ProgressStore())
    assert not result.ok
    assert any("a.b.ghost_01" in e for e in result.errors)


def test_endpoint_check_applies_to_inactive_edges_too():
    # A dangling endpoint is a data error even when the edge is parked; node IDs
    # are immutable and never reused, so it is always a typo.
    nodes = [_node("a.b.n_01")]
    edges = [_edge("a.b.n_01", "a.b.ghost_01", active=False)]
    result = check_graph(nodes, edges, ProgressStore())
    assert not result.ok
    assert any("a.b.ghost_01" in e for e in result.errors)


# --- Hard-prerequisite cycle detection --------------------------------------

def test_hard_prerequisite_three_node_cycle_fails_with_path():
    nodes = [_node("a.b.n_01"), _node("a.b.n_02"), _node("a.b.n_03")]
    edges = [
        _edge("a.b.n_01", "a.b.n_02"),
        _edge("a.b.n_02", "a.b.n_03"),
        _edge("a.b.n_03", "a.b.n_01"),
    ]
    result = check_graph(nodes, edges, ProgressStore())
    assert not result.ok
    cycle_errors = [e for e in result.errors if "cycle" in e.lower()]
    assert cycle_errors
    # The closure is shown: the entry node appears twice in the printed path.
    message = cycle_errors[0]
    assert message.count("a.b.n_01") == 2


def test_inactive_hard_edge_does_not_form_cycle():
    nodes = [_node("a.b.n_01"), _node("a.b.n_02")]
    edges = [
        _edge("a.b.n_01", "a.b.n_02"),
        _edge("a.b.n_02", "a.b.n_01", active=False),  # parked — not in force
    ]
    result = check_graph(nodes, edges, ProgressStore())
    assert result.ok


# --- Soft-prerequisite issues are warnings, not errors ----------------------

def test_soft_prerequisite_cycle_is_a_warning_not_an_error():
    nodes = [_node("a.b.n_01"), _node("a.b.n_02"), _node("a.b.n_03")]
    edges = [
        _edge("a.b.n_01", "a.b.n_02", edge_type="soft_prerequisite"),
        _edge("a.b.n_02", "a.b.n_03", edge_type="soft_prerequisite"),
        _edge("a.b.n_03", "a.b.n_01", edge_type="soft_prerequisite"),
    ]
    result = check_graph(nodes, edges, ProgressStore())
    assert result.ok  # warnings do not affect the result
    assert result.warnings
    assert any("a.b.n_01" in w for w in result.warnings)


# --- Dangling progress references -------------------------------------------

def test_dangling_state_reference_fails():
    nodes = [_node("a.b.n_01")]
    store = ProgressStore()
    store.write_readiness("a.b.n_01", "available")
    store.write_readiness("a.b.ghost_01", "available")
    result = check_graph(nodes, [], store)
    assert not result.ok
    assert any("a.b.ghost_01" in e for e in result.errors)


# --- Report all, not just the first -----------------------------------------

def test_reports_all_errors_not_just_the_first():
    nodes = [_node("a.b.n_01"), _node("a.b.n_01")]  # duplicate
    edges = [_edge("a.b.n_01", "a.b.ghost_01")]  # dangling target
    result = check_graph(nodes, edges, ProgressStore())
    joined = " ".join(result.errors)
    assert "a.b.n_01" in joined  # duplicate reported
    assert "a.b.ghost_01" in joined  # dangling endpoint reported


# --- Summary counts ---------------------------------------------------------

def test_summary_counts_states_and_edges():
    nodes = [_node("a.b.n_01"), _node("a.b.n_02")]
    store = ProgressStore()
    store.write_readiness("a.b.n_01", "available")
    store.write_asserted("a.b.n_02", "active")
    edges = [_edge("a.b.n_01", "a.b.n_02"), _edge("a.b.n_02", "a.b.n_01", active=False)]
    result = check_graph(nodes, edges, store)
    assert result.node_count == 2
    assert result.edge_count == 2
    assert result.active_edge_count == 1
    assert result.state_counts.get("available") == 1
    assert result.state_counts.get("active") == 1


# --- Integration against the real seed graph (roadmap exit gate) ------------

def test_seed_graph_validates_clean():
    result = load_and_validate(REPO_ROOT)
    assert result.ok, f"seed graph should validate; errors: {result.errors}"
    assert result.node_count == 47


def test_empty_repo_validates_clean(tmp_path):
    # A fresh repo with no edges.yaml / nodes is an empty (valid) graph, not an
    # error — mirrors load_state treating a missing state file as an empty store.
    result = load_and_validate(tmp_path)
    assert result.ok
    assert result.node_count == 0
    assert result.edge_count == 0
