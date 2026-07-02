"""Next-node recommendation v1: the pure ranking rule.

`recommend(nodes, edges, store, track_weights, ...)` ranks `available`/`active`
candidates and never surfaces a `locked` node as available. These are the
pure-seam tests over hand-built lists (mirroring test_readiness.py); the
command-level policy-read + report + read-only-audit path is covered in
test_next_command.py.
"""

from __future__ import annotations

from skilltrace.graph.edges import GraphEdge
from skilltrace.graph.nodes import SkillNode
from skilltrace.graph.recommendation import recommend
from skilltrace.graph.state import ProgressStore


def _node(
    node_id: str,
    *,
    track: str = "foundational",
    fit15: bool = True,
    fit30: bool = True,
) -> SkillNode:
    return SkillNode(
        id=node_id,
        title=node_id,
        summary=node_id,
        domain="d",
        track=track,
        micro_session_fit={"can_fit_15_min": fit15, "can_fit_30_min": fit30},
    )


def _edge(source: str, target: str, *, edge_type: str = "hard_prerequisite", active: bool = True) -> GraphEdge:
    return GraphEdge(
        id=f"edge.{source}__{target}",
        source=source,
        target=target,
        edge_type=edge_type,
        reason="because",
        active=active,
    )


def _store(**states: str) -> ProgressStore:
    store = ProgressStore()
    for node_id, state in states.items():
        if state in {"active", "passed", "mastered"}:
            store.write_asserted(node_id, state)
        else:
            store.write_readiness(node_id, state)
    return store


_WEIGHTS = {"foundational": 3.0, "core": 2.0, "portfolio": 1.0}


# --- Candidate selection ----------------------------------------------------

def test_only_available_and_active_nodes_are_recommended():
    nodes = [_node("a.b.avail_01"), _node("a.b.act_01"), _node("a.b.lock_01"),
             _node("a.b.pass_01"), _node("a.b.mast_01")]
    store = _store(**{
        "a.b.avail_01": "available",
        "a.b.act_01": "active",
        "a.b.lock_01": "locked",
        "a.b.pass_01": "passed",
        "a.b.mast_01": "mastered",
    })
    result = recommend(nodes, [], store, _WEIGHTS, minutes=60, limit=10)
    ids = {rec.node_id for rec in result.recommendations}
    assert ids == {"a.b.avail_01", "a.b.act_01"}


def test_locked_node_never_recommended_even_with_show_locked():
    nodes = [_node("a.b.lock_01"), _node("a.b.avail_01")]
    store = _store(**{"a.b.lock_01": "locked", "a.b.avail_01": "available"})
    result = recommend(nodes, [], store, _WEIGHTS, minutes=60, limit=10, show_locked=True)
    assert [r.node_id for r in result.recommendations] == ["a.b.avail_01"]
    assert [lc.node_id for lc in result.locked] == ["a.b.lock_01"]


# --- Every recommendation carries a reason ----------------------------------

def test_every_recommendation_has_a_nonempty_reason():
    nodes = [_node("a.b.one_01"), _node("a.b.two_01", track="core")]
    store = _store(**{"a.b.one_01": "available", "a.b.two_01": "active"})
    result = recommend(nodes, [], store, _WEIGHTS, minutes=60, limit=10)
    assert result.recommendations
    for rec in result.recommendations:
        assert rec.reason.strip()
        assert f"track {rec.track!r}" in rec.reason


# --- Track weights drive ordering (read from the policy map) -----------------

def test_track_weight_determines_order_between_otherwise_identical_nodes():
    # Two candidates identical but for track; the higher-weighted track wins.
    nodes = [_node("a.b.alpha_01", track="alpha"), _node("a.b.beta_01", track="beta")]
    store = _store(**{"a.b.alpha_01": "available", "a.b.beta_01": "available"})

    high_alpha = recommend(nodes, [], store, {"alpha": 5.0, "beta": 1.0}, minutes=60, limit=10)
    assert [r.node_id for r in high_alpha.recommendations] == ["a.b.alpha_01", "a.b.beta_01"]

    # Swap the weights in the map -> the ordering flips.
    high_beta = recommend(nodes, [], store, {"alpha": 1.0, "beta": 5.0}, minutes=60, limit=10)
    assert [r.node_id for r in high_beta.recommendations] == ["a.b.beta_01", "a.b.alpha_01"]


def test_unmapped_track_scores_zero_and_warns():
    nodes = [_node("a.b.known_01", track="core"), _node("a.b.mystery_01", track="mystery")]
    store = _store(**{"a.b.known_01": "available", "a.b.mystery_01": "available"})
    result = recommend(nodes, [], store, {"core": 2.0}, minutes=60, limit=10)

    assert result.unmapped_tracks == ["mystery"]
    mystery = next(r for r in result.recommendations if r.node_id == "a.b.mystery_01")
    assert mystery.track_weight == 0.0
    assert "unmapped" in mystery.reason
    # Mapped track outranks the unmapped one (2.0 vs 0.0, other factors equal).
    assert result.recommendations[0].node_id == "a.b.known_01"


# --- Session fit ------------------------------------------------------------

def test_minutes_15_prefers_15_minute_fit_nodes():
    nodes = [_node("a.b.fits_01", fit15=True), _node("a.b.big_01", fit15=False, fit30=False)]
    store = _store(**{"a.b.fits_01": "available", "a.b.big_01": "available"})

    short = recommend(nodes, [], store, _WEIGHTS, minutes=15, limit=10)
    assert [r.node_id for r in short.recommendations] == ["a.b.fits_01", "a.b.big_01"]
    assert short.recommendations[0].fits_session is True
    assert short.recommendations[1].fits_session is False

    # A long session fits both -> the fit factor no longer separates them.
    long = recommend(nodes, [], store, _WEIGHTS, minutes=60, limit=10)
    assert all(r.fits_session for r in long.recommendations)


# --- Active continuation and leverage bonuses -------------------------------

def test_active_node_outranks_identical_available_node():
    nodes = [_node("a.b.act_01"), _node("a.b.avail_01")]
    store = _store(**{"a.b.act_01": "active", "a.b.avail_01": "available"})
    result = recommend(nodes, [], store, _WEIGHTS, minutes=60, limit=10)
    assert result.recommendations[0].node_id == "a.b.act_01"
    assert result.recommendations[0].is_active is True


def test_downstream_leverage_boosts_score():
    nodes = [_node("a.b.hub_01"), _node("a.b.leaf_01"), _node("a.b.t1_01"), _node("a.b.t2_01")]
    # hub has two active outgoing edges; leaf has none.
    edges = [_edge("a.b.hub_01", "a.b.t1_01"), _edge("a.b.hub_01", "a.b.t2_01")]
    store = _store(**{"a.b.hub_01": "available", "a.b.leaf_01": "available"})
    result = recommend(nodes, edges, store, _WEIGHTS, minutes=60, limit=10)
    hub = next(r for r in result.recommendations if r.node_id == "a.b.hub_01")
    leaf = next(r for r in result.recommendations if r.node_id == "a.b.leaf_01")
    assert hub.leverage == 2 and leaf.leverage == 0
    assert hub.score > leaf.score


def test_inactive_outgoing_edges_do_not_count_as_leverage():
    nodes = [_node("a.b.hub_01"), _node("a.b.t1_01")]
    edges = [_edge("a.b.hub_01", "a.b.t1_01", active=False)]
    store = _store(**{"a.b.hub_01": "available"})
    result = recommend(nodes, edges, store, _WEIGHTS, minutes=60, limit=10)
    assert result.recommendations[0].leverage == 0


# --- Limit bounds recommendations, not the locked appendix -------------------

def test_limit_truncates_recommendations_only():
    nodes = [_node(f"a.b.n{i}_01") for i in range(5)]
    nodes += [_node("a.b.lock1_01"), _node("a.b.lock2_01")]
    store = ProgressStore()
    for i in range(5):
        store.write_readiness(f"a.b.n{i}_01", "available")
    store.write_readiness("a.b.lock1_01", "locked")
    store.write_readiness("a.b.lock2_01", "locked")

    result = recommend(nodes, [], store, _WEIGHTS, minutes=60, limit=2, show_locked=True)
    assert len(result.recommendations) == 2
    assert len(result.locked) == 2  # locked appendix is not truncated by limit


# --- Locked appendix names unsatisfied hard prerequisites -------------------

def test_locked_appendix_names_unsatisfied_hard_prereqs():
    nodes = [_node("a.b.src_01"), _node("a.b.dst_01")]
    edges = [_edge("a.b.src_01", "a.b.dst_01")]
    store = _store(**{"a.b.src_01": "available", "a.b.dst_01": "locked"})
    result = recommend(nodes, edges, store, _WEIGHTS, minutes=60, limit=10, show_locked=True)

    assert len(result.locked) == 1
    locked = result.locked[0]
    assert locked.node_id == "a.b.dst_01"
    assert locked.unsatisfied == (("a.b.src_01", "available"),)
    assert "a.b.src_01" in locked.reason


def test_soft_and_remediation_edges_are_not_named_as_blockers():
    nodes = [_node("a.b.src_01"), _node("a.b.dst_01")]
    edges = [_edge("a.b.src_01", "a.b.dst_01", edge_type="soft_prerequisite")]
    store = _store(**{"a.b.src_01": "available", "a.b.dst_01": "locked"})
    result = recommend(nodes, edges, store, _WEIGHTS, minutes=60, limit=10, show_locked=True)
    # dst is locked in the store but no *hard* prereq blocks it -> stale-store note.
    assert result.locked[0].unsatisfied == ()


def test_locked_omitted_without_show_locked():
    nodes = [_node("a.b.lock_01")]
    store = _store(**{"a.b.lock_01": "locked"})
    result = recommend(nodes, [], store, _WEIGHTS, minutes=60, limit=10, show_locked=False)
    assert result.locked == []
