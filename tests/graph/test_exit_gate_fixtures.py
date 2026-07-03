"""v0.3 exit gate — the invalid-fixture matrix, driven through the loader path.

`test_validation.py` proves the *logic* of every whole-graph check against the
pure `check_graph` seam. This module proves the same failures survive a round
trip through the real loaders on real files: `load_and_validate(root)` reads
`graph/nodes/*.md` + `graph/edges.yaml`, folds any loader error into
`result.errors`, and returns a non-ok result naming the offender.

Two of these cases can *only* be caught here — they are loader rejections the
pure seam never sees, because it takes already-validated objects:

- a node whose frontmatter carries `state` (`NodeLoadError`);
- an edge carrying a pruned `strength` field (`EdgeLoadError`).

The others (duplicate id, dangling endpoint, hard cycle) are re-proved end to end
so the fixture matrix mirrors the roadmap's v0.3 test list one-for-one.
"""

from __future__ import annotations

from skilltrace.graph.validation import load_and_validate


# --- Happy path: minimal valid graph loads and validates ---------------------

def test_minimal_valid_graph_validates_clean(graph_builder):
    graph_builder.node("a.b.n_01").node("a.b.n_02").edges(
        [graph_builder.edge("a.b.n_01", "a.b.n_02")]
    )
    result = load_and_validate(graph_builder.root)
    assert result.ok, result.errors
    assert result.node_count == 2
    assert result.edge_count == 1


# --- Loader-only rejections (invisible to the pure check_graph seam) ---------

def test_frontmatter_state_key_fails_through_the_loader(graph_builder):
    # A node file carrying `state` is rejected by load_nodes; load_and_validate
    # folds the NodeLoadError into errors rather than raising.
    graph_builder.node("a.b.n_01", overrides={"state": "active"})
    result = load_and_validate(graph_builder.root)
    assert not result.ok
    assert any("state" in e for e in result.errors)


def test_edge_strength_field_fails_through_the_loader(graph_builder):
    # `strength` is a pruned edge field; the closed edge schema rejects it and the
    # EdgeLoadError is folded into the validation result.
    graph_builder.node("a.b.n_01").node("a.b.n_02").edges(
        [graph_builder.edge("a.b.n_01", "a.b.n_02", extra={"strength": 0.5})]
    )
    result = load_and_validate(graph_builder.root)
    assert not result.ok
    assert any("strength" in e for e in result.errors)


# --- Whole-graph failures, re-proved end to end ------------------------------

def test_duplicate_node_id_fails_through_the_loader(graph_builder):
    # Two files, same id, distinct filenames — load_nodes returns both; validation
    # flags the collision.
    graph_builder.node("a.b.n_01", filename="first.md")
    graph_builder.node("a.b.n_01", filename="second.md")
    result = load_and_validate(graph_builder.root)
    assert not result.ok
    assert any("a.b.n_01" in e for e in result.errors)


def test_missing_edge_source_fails_through_the_loader(graph_builder):
    graph_builder.node("a.b.n_02").edges(
        [graph_builder.edge("a.b.ghost_01", "a.b.n_02")]
    )
    result = load_and_validate(graph_builder.root)
    assert not result.ok
    assert any("a.b.ghost_01" in e for e in result.errors)


def test_missing_edge_target_fails_through_the_loader(graph_builder):
    graph_builder.node("a.b.n_01").edges(
        [graph_builder.edge("a.b.n_01", "a.b.ghost_01")]
    )
    result = load_and_validate(graph_builder.root)
    assert not result.ok
    assert any("a.b.ghost_01" in e for e in result.errors)


def test_hard_prerequisite_cycle_fails_through_the_loader(graph_builder):
    graph_builder.node("a.b.n_01").node("a.b.n_02").edges(
        [
            graph_builder.edge("a.b.n_01", "a.b.n_02", edge_id="edge.one"),
            graph_builder.edge("a.b.n_02", "a.b.n_01", edge_id="edge.two"),
        ]
    )
    result = load_and_validate(graph_builder.root)
    assert not result.ok
    assert any("cycle" in e.lower() for e in result.errors)
