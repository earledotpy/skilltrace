"""Roadmap anchors never control locking or recommendation (issue #8).

Decision (roadmap): roadmap anchors are `reference_only` metadata — they link a
node to an external curriculum for human context and nothing more. No engine
mechanic keys off them: they are not edges, so they cannot lock a node, and they
carry no weight, so they cannot reorder a recommendation.

These tests prove that behaviourally, end to end. A node whose only relationship
to the graph is a roadmap anchor pointing at a *different* phase — with an empty
`edges.yaml` — must be `available` after `sync` and must appear in `next`. If
anchors leaked into locking or scoring, one of those would break.
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.graph.state import load_state
from skilltrace.graph.validation import load_and_validate

_LATER_PHASE_ANCHOR = [
    {"phase": "phase_9", "roadmap_topic": "Much later material", "source_role": "reference_only"}
]


def _seed_two_anchored_nodes(graph_builder):
    """Two nodes, each anchored to a later phase, with no edges between them."""
    graph_builder.node("a.b.n_01", track="foundational", anchors=_LATER_PHASE_ANCHOR)
    graph_builder.node("a.b.n_02", track="foundational", anchors=_LATER_PHASE_ANCHOR)
    graph_builder.edges([])  # no relationships at all
    return graph_builder.root


def test_anchor_does_not_lock_a_node(graph_builder, capsys):
    root = _seed_two_anchored_nodes(graph_builder)
    assert cli.run(["sync"], root=root) == 0
    capsys.readouterr()  # discard sync output

    store = load_state(root)
    # An anchor to a later phase creates no hard prerequisite; both nodes are
    # available, never locked.
    assert store.state_of("a.b.n_01") == "available"
    assert store.state_of("a.b.n_02") == "available"


def test_anchor_does_not_remove_a_node_from_recommendations(graph_builder, capsys):
    root = _seed_two_anchored_nodes(graph_builder)
    cli.run(["sync"], root=root)
    capsys.readouterr()

    assert cli.run(["next", "--minutes", "60", "--limit", "5"], root=root) == 0
    out = capsys.readouterr().out
    # Both anchored nodes are recommended — the anchor neither locks them nor
    # reorders them out of range.
    assert "a.b.n_01" in out
    assert "a.b.n_02" in out


def test_anchored_graph_with_no_edges_has_zero_edges(graph_builder):
    # The structural half of the guarantee: a roadmap anchor is not an edge, so a
    # graph whose nodes are all anchored still validates with edge_count == 0.
    root = _seed_two_anchored_nodes(graph_builder)
    result = load_and_validate(root)
    assert result.ok, result.errors
    assert result.node_count == 2
    assert result.edge_count == 0
