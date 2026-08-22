"""JoinedView deep module — interface is the test surface (C1 T01)."""

from __future__ import annotations

from pathlib import Path

import pytest

from skilltrace.context import JoinedView, Loaders, load_context_lenient, load_context_strict
from skilltrace.evidence._schema import EvidenceLoadError
from skilltrace.execution._store import ExecutionLoadError
from skilltrace.graph.nodes import NodeLoadError, SkillNode
from skilltrace.graph.state import ProgressStore, ProgressStoreError
from skilltrace.resources.registry import ResourceLoadError


# -- helpers --

def _node(node_id: str, title: str | None = None) -> SkillNode:
    return SkillNode(
        id=node_id,
        title=title or f"Title for {node_id}",
        summary="summary",
        domain="testing",
        track="foundational",
    )


def _fake_resource(node_id: str, rid: str = "res-01"):
    from skilltrace.resources.registry import LearningResource

    return LearningResource(
        id=rid,
        cost="free",
        url="https://example.com",
        supports=(node_id,),
    )


# -- lenient tier: graph/state strict, evidence/execution/resources degrade --


def test_lenient_raises_on_node_load_error(tmp_path: Path):
    def failing_nodes(_root: Path):
        raise NodeLoadError("nodes boom")

    loaders = Loaders(load_nodes=failing_nodes)
    with pytest.raises(NodeLoadError):
        load_context_lenient(tmp_path, loaders=loaders)


def test_lenient_raises_on_state_load_error(tmp_path: Path):
    def failing_state(_root: Path):
        raise ProgressStoreError("store boom")

    loaders = Loaders(load_state=failing_state)
    with pytest.raises(ProgressStoreError):
        load_context_lenient(tmp_path, loaders=loaders)


def test_lenient_degrades_evidence_to_empty_on_error(tmp_path: Path):
    def failing_specs(_root: Path):
        raise EvidenceLoadError("specs boom")

    loaders = Loaders(load_specs=failing_specs)
    view = load_context_lenient(tmp_path, loaders=loaders)
    assert view.specs == []
    assert view.errors == []  # lenient never collects


def test_lenient_degrades_execution_and_resources_to_empty(tmp_path: Path):
    def failing_sessions(_root: Path):
        raise ExecutionLoadError("sessions boom")

    def failing_resources(_root: Path):
        raise ResourceLoadError("resources boom")

    loaders = Loaders(load_sessions=failing_sessions, load_resources=failing_resources)
    view = load_context_lenient(tmp_path, loaders=loaders)
    assert view.sessions == []
    assert view.resources == []
    assert view.errors == []


# -- strict tier: collects every failure --


def test_strict_collects_graph_error_into_view_errors(tmp_path: Path):
    def failing_nodes(_root: Path):
        raise NodeLoadError("strict nodes boom")

    loaders = Loaders(load_nodes=failing_nodes)
    view = load_context_strict(tmp_path, loaders=loaders)
    assert not view.ok
    assert any("strict nodes boom" in e for e in view.errors)
    assert view.nodes == []


def test_strict_collects_evidence_and_execution_errors(tmp_path: Path):
    def failing_specs(_root: Path):
        raise EvidenceLoadError("specs boom")

    def failing_blockers(_root: Path):
        raise ExecutionLoadError("blockers boom")

    loaders = Loaders(
        load_nodes=lambda _r: [],
        load_edges=lambda _r: [],
        load_state=lambda _r: ProgressStore(),
        load_specs=failing_specs,
        load_gates=lambda _r: [],
        load_records=lambda _r: [],
        load_attempts=lambda _r: [],
        load_sessions=lambda _r: [],
        load_work=lambda _r: [],
        load_blockers=failing_blockers,
        load_remediations=lambda _r: [],
        load_reviews=lambda _r: [],
        load_resources=lambda _r: [],
        load_events=lambda _r: [],
        load_policies=lambda _r: {},
    )
    view = load_context_strict(tmp_path, loaders=loaders)
    assert len(view.errors) == 2
    assert view.specs == []
    assert view.blockers == []


def test_strict_produces_joined_view_even_when_all_fail(tmp_path: Path):
    def boom(_root: Path):
        raise RuntimeError("boom")

    loaders = Loaders(
        load_nodes=boom,
        load_edges=boom,
        load_state=boom,
        load_specs=boom,
        load_gates=boom,
        load_records=boom,
        load_attempts=boom,
        load_sessions=boom,
        load_work=boom,
        load_blockers=boom,
        load_remediations=boom,
        load_reviews=boom,
        load_resources=boom,
        load_events=boom,
        load_policies=boom,
    )
    view = load_context_strict(tmp_path, loaders=loaders)
    assert not view.ok
    assert len(view.errors) >= 10


# -- derived indexes --


def test_derived_titles_and_node_map_match_ground_truth(tmp_path: Path):
    n1 = _node("testing.alpha.subject_01", "Alpha")
    n2 = _node("testing.alpha.subject_02", "Beta")

    loaders = Loaders(
        load_nodes=lambda _r: [n1, n2],
        load_edges=lambda _r: [],
        load_state=lambda _r: ProgressStore(),
        load_specs=lambda _r: [],
        load_gates=lambda _r: [],
        load_records=lambda _r: [],
        load_attempts=lambda _r: [],
        load_sessions=lambda _r: [],
        load_work=lambda _r: [],
        load_blockers=lambda _r: [],
        load_remediations=lambda _r: [],
        load_reviews=lambda _r: [],
        load_resources=lambda _r: [],
        load_events=lambda _r: [],
        load_policies=lambda _r: {},
    )
    view = load_context_lenient(tmp_path, loaders=loaders)
    assert view.titles == {"testing.alpha.subject_01": "Alpha", "testing.alpha.subject_02": "Beta"}
    assert view.node_map["testing.alpha.subject_01"] is n1
    assert view.specs_by_node == {}
    assert view.has_gate == set()
    assert view.resources_by_node["testing.alpha.subject_01"] == []


def test_resources_by_node_uses_reverse_index(tmp_path: Path):
    n1 = _node("testing.alpha.subject_01")
    n2 = _node("testing.alpha.subject_02")
    r1 = _fake_resource("testing.alpha.subject_01", "res-01")
    r2 = _fake_resource("testing.alpha.subject_01", "res-02")

    loaders = Loaders(
        load_nodes=lambda _r: [n1, n2],
        load_edges=lambda _r: [],
        load_state=lambda _r: ProgressStore(),
        load_specs=lambda _r: [],
        load_gates=lambda _r: [],
        load_records=lambda _r: [],
        load_attempts=lambda _r: [],
        load_sessions=lambda _r: [],
        load_work=lambda _r: [],
        load_blockers=lambda _r: [],
        load_remediations=lambda _r: [],
        load_reviews=lambda _r: [],
        load_resources=lambda _r: [r1, r2],
        load_events=lambda _r: [],
        load_policies=lambda _r: {},
    )
    view = load_context_lenient(tmp_path, loaders=loaders)
    assert len(view.resources_by_node["testing.alpha.subject_01"]) == 2
    assert view.resources_by_node["testing.alpha.subject_02"] == []


def test_real_filesystem_wires_through(tmp_path: Path):
    # Uses the temp dir as root — lenient should degrade gracefully, strict should collect policy missing.
    # The shipped repo root is not tmp_path, so nodes will fail — but we just assert the seam is wired.
    view_lenient = load_context_strict(tmp_path, loaders=Loaders())
    # On a blank tmp dir, strict collects errors (nodes missing etc.)
    assert isinstance(view_lenient, JoinedView)
