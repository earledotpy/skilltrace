"""Ranking preparation seam — `prepare()` behind `recommend()` (issue #201).

`prepare()` consumes one loaded `JoinedView` (plus root/today as needed)
and produces the full `RecommendInputs` bundle `recommend()` expects.
`next`, `today`, and `graph impact` all call it once instead of
hand-assembling the recipe.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from skilltrace.context import JoinedView, PolicyAccess
from skilltrace.execution.records import Blocker
from skilltrace.graph.edges import GraphEdge
from skilltrace.graph.nodes import SkillNode
from skilltrace.graph.recommendation import recommend
from skilltrace.graph.recommendation_prep import RecommendInputs, prepare
from skilltrace.graph.state import ProgressEntry, ProgressStore

TARGET = "testing.prep.target_01"
REM = "testing.prep.remedial_01"


def _node(node_id: str, track: str = "foundational") -> SkillNode:
    return SkillNode(
        id=node_id,
        title=node_id,
        summary="summary",
        domain="testing",
        track=track,
    )


def _remediation_edge() -> GraphEdge:
    return GraphEdge(
        id="edge.remedial_rescues_target",
        source=REM,
        target=TARGET,
        edge_type="remediation",
        reason="rescues the target when it is stuck",
        active=True,
    )


def _open_blocker() -> Blocker:
    return Blocker(
        id="blk.target.001",
        node_id=TARGET,
        status="open",
        description="stuck on the core idea",
        created_at="2026-07-02T10:00:00+00:00",
    )


def _joined(*, blocker_open: bool = True) -> JoinedView:
    policies = {
        "recommendation.yaml": {
            "track_weights": {"foundational": 3.0, "core": 2.0},
            "factor_weights": {"remediation_priority": 4.0},
        },
    }
    return JoinedView(
        nodes=[_node(TARGET), _node(REM, track="core")],
        edges=[_remediation_edge()],
        store=ProgressStore(
            entries={
                TARGET: ProgressEntry(state="available"),
                REM: ProgressEntry(state="available"),
            }
        ),
        blockers=[_open_blocker()] if blocker_open else [],
        attempts=[],
        reviews=[],
        policies=policies,
        policy=PolicyAccess(dict(policies)),
    )


def test_prepare_assembles_all_boost_inputs():
    inputs = prepare(_joined(), root=None, today=date(2026, 7, 3))

    assert isinstance(inputs, RecommendInputs)
    # Open blocker on TARGET activates the REM -> TARGET remediation edge.
    assert inputs.open_blocked == frozenset({TARGET})
    assert inputs.remediation_boosted == frozenset({REM})
    assert inputs.active_remediations
    assert inputs.active_remediations[0].remediation_node == REM
    # No retention seed -> urgency stands down, never an error.
    assert inputs.prereq_reviews_due == {}
    # No root -> agent factor stands down quietly.
    assert inputs.agent_boosted == frozenset()
    assert inputs.agent_warnings == ()
    # Weight maps ride through from the joined policy.
    assert inputs.track_weights == {"foundational": 3.0, "core": 2.0}
    assert inputs.factor_weights == {"remediation_priority": 4.0}


def test_prepare_without_pressure_stands_boosts_down():
    inputs = prepare(_joined(blocker_open=False), root=None, today=date(2026, 7, 3))

    assert inputs.open_blocked == frozenset()
    assert inputs.remediation_boosted == frozenset()
    assert inputs.active_remediations == ()


def test_prepare_reads_agent_file_under_root(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "agent_recommendations.yaml").write_text(
        yaml.safe_dump(
            {"agent_recommendations": [{"node_id": TARGET, "priority": 0.8}]},
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    inputs = prepare(_joined(), root=tmp_path, today=date(2026, 7, 3))

    assert inputs.agent_boosted == frozenset({TARGET})
    assert inputs.agent_warnings == ()


def test_prepare_does_not_rejoin_from_disk(tmp_path: Path):
    """The join seam stays `JoinedView` — an empty root dir changes nothing."""
    joined = _joined()
    inputs = prepare(joined, root=tmp_path, today=date(2026, 7, 3))

    assert inputs.remediation_boosted == frozenset({REM})
    assert inputs.open_blocked == frozenset({TARGET})


def test_recommend_kwargs_feed_recommend_directly():
    """`recommend_kwargs()` is exactly the six `recommend()` inputs."""
    inputs = prepare(_joined(), root=None, today=date(2026, 7, 3))
    kwargs = inputs.recommend_kwargs()

    assert set(kwargs) == {
        "track_weights",
        "factor_weights",
        "remediation_boosted",
        "open_blocked",
        "prereq_reviews_due",
        "agent_boosted",
    }

    joined = _joined()
    result = recommend(
        joined.nodes,
        joined.edges,
        joined.store,
        kwargs["track_weights"],
        minutes=30,
        limit=5,
        factor_weights=kwargs["factor_weights"],
        remediation_boosted=kwargs["remediation_boosted"],
        open_blocked=kwargs["open_blocked"],
        prereq_reviews_due=kwargs["prereq_reviews_due"],
        agent_boosted=kwargs["agent_boosted"],
    )
    ranked = [rec.node_id for rec in result.recommendations]
    # REM carries track 2*3 + leverage + remediation boost; TARGET is dragged
    # down by the open blocker — the boost decides the order.
    assert ranked.index(REM) < ranked.index(TARGET)


def test_next_shares_prepare_inputs(monkeypatch):
    """`derive_next` ranks with exactly what `prepare` derives (same shape)."""
    from skilltrace.commands import recommend as next_cmd
    from skilltrace.graph import recommendation_prep as prep_mod

    joined = _joined()
    calls: list = []
    real_prepare = prep_mod.prepare

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        return real_prepare(*args, **kwargs)

    captured: dict = {}

    def fake_recommend(nodes, edges, store, track_weights, **kwargs):
        captured.update(kwargs)
        captured["track_weights"] = track_weights
        return recommend(nodes, edges, store, track_weights, **kwargs)

    monkeypatch.setattr(next_cmd, "prepare", spy)
    monkeypatch.setattr(next_cmd, "recommend", fake_recommend)
    next_cmd.derive_next(joined, None, minutes=30, limit=5)

    assert len(calls) == 1
    assert calls[0][0][0] is joined
    expected = real_prepare(joined, None).recommend_kwargs()
    assert {k: captured[k] for k in expected} == expected


def test_today_shares_prepare_inputs(monkeypatch):
    """`derive_today` ranks with exactly what `prepare` derives (same shape)."""
    from skilltrace.commands import today as today_cmd
    from skilltrace.graph import recommendation_prep as prep_mod

    joined = _joined()
    calls: list = []
    real_prepare = prep_mod.prepare

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        return real_prepare(*args, **kwargs)

    captured: dict = {}

    def fake_recommend(nodes, edges, store, track_weights, **kwargs):
        captured.update(kwargs)
        captured["track_weights"] = track_weights
        return recommend(nodes, edges, store, track_weights, **kwargs)

    monkeypatch.setattr(today_cmd, "prepare", spy)
    monkeypatch.setattr(today_cmd, "recommend", fake_recommend)
    today_cmd.derive_today(joined, None, minutes=30)

    assert len(calls) == 1
    assert calls[0][0][0] is joined
    expected = real_prepare(joined, None).recommend_kwargs()
    assert {k: captured[k] for k in expected} == expected
