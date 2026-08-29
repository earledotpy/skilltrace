"""JoinedView deep module — interface is the test surface (C1 T01)."""

from __future__ import annotations

from pathlib import Path

import pytest

from _builders import write_node as _shared_write_node

from skilltrace.context import JoinedView, Loaders, load_context_lenient, load_context_strict
from skilltrace.evidence._schema import EvidenceLoadError
from skilltrace.evidence.gates import ValidationGate
from skilltrace.evidence.specs import ArtifactSpec
from skilltrace.execution._store import ExecutionLoadError
from skilltrace.graph.nodes import NodeLoadError, SkillNode
from skilltrace.graph.state import ProgressStore, ProgressStoreError
from skilltrace.resources.registry import ResourceLoadError
from skilltrace.resources.status import DEFAULT_STALE_AFTER_DAYS


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


def test_lenient_propagates_unexpected_optional_loader_exception(tmp_path: Path):
    def boom(_root: Path):
        raise RuntimeError("optional boom")

    loaders = Loaders(load_specs=boom)
    with pytest.raises(RuntimeError, match="optional boom"):
        load_context_lenient(tmp_path, loaders=loaders)


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


def test_strict_propagates_unexpected_loader_exception(tmp_path: Path):
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
    with pytest.raises(RuntimeError, match="boom"):
        load_context_strict(tmp_path, loaders=loaders)


def test_policy_access_is_typed_and_snapshot_local(tmp_path: Path):
    loaders = Loaders(
        load_nodes=lambda _r: [],
        load_edges=lambda _r: [],
        load_state=lambda _r: ProgressStore(),
        load_policies=lambda _r: {
            "recommendation.yaml": {
                "track_weights": {"foundational": "2.5"},
                "factor_weights": {"leverage": 1},
            },
            "remediation.yaml": {
                "failed_attempt_threshold": 3,
                "suggestion_defaults": {
                    "suggested_minutes": 20,
                    "due_in_days": 4,
                },
            },
            "review_cadence.yaml": {"missed_review_grace_days": 2},
            "workload.yaml": {"session_templates": {"focused": {"expected_minutes": 30}}},
            "mastery_promotion.yaml": {
                "min_accepted_evidence": 2,
                "min_days_pass_to_review": 5,
            },
            "retention_model.yaml": {
                "default_half_life_days": 10,
                "satisfactory_growth_factor": 1.2,
                "unsatisfactory_reduction_factor": 0.5,
                "attention_threshold": 0.6,
            },
        },
    )
    view = load_context_lenient(tmp_path, loaders=loaders)
    assert view.policy.track_weights == {"foundational": 2.5}
    assert view.policy.factor_weights == {"leverage": 1.0}
    assert view.policy.failed_attempt_threshold == 3
    assert view.policy.remediation_suggestion_defaults == (20, 4)
    assert view.policy.review_grace_days == 2
    assert view.policy.session_templates == {"focused"}
    assert view.policy.cadence.schedule_reviews_after_pass is False
    assert view.policy.mastery.min_accepted_evidence == 2
    assert view.policy.mastery.min_days_pass_to_review == 5
    assert view.policy.retention is not None


def test_policy_access_ignores_boolean_malformed_values(tmp_path: Path):
    loaders = Loaders(
        load_nodes=lambda _r: [],
        load_edges=lambda _r: [],
        load_state=lambda _r: ProgressStore(),
        load_policies=lambda _r: {
            "recommendation.yaml": {
                "track_weights": {"core": True, "oops": "2.0"},
                "factor_weights": {"quality": False, "impact": 3.5},
            },
            "remediation.yaml": {
                "failed_attempt_threshold": True,
                "suggestion_defaults": {
                    "suggested_minutes": False,
                    "due_in_days": True,
                },
            },
            "review_cadence.yaml": {
                "missed_review_grace_days": True,
                "schedule_reviews_after_pass": True,
                "intervals": [{"days_after_pass": True, "label": "bad"}],
            },
            "workload.yaml": {"session_templates": {True: {"expected_minutes": 30}}},
            "mastery_promotion.yaml": {
                "min_accepted_evidence": False,
                "min_days_pass_to_review": True,
            },
            "resource_verification.yaml": {"stale_after_days": False},
        },
    )
    view = load_context_lenient(tmp_path, loaders=loaders)
    assert view.policy.track_weights == {"oops": 2.0}
    assert view.policy.factor_weights == {"impact": 3.5}
    assert view.policy.failed_attempt_threshold is None
    assert view.policy.remediation_suggestion_defaults == (None, None)
    assert view.policy.review_grace_days is None
    assert view.policy.session_templates == set()
    assert view.policy.cadence.schedule_reviews_after_pass is True
    assert view.policy.cadence.intervals == []
    assert view.policy.mastery.min_accepted_evidence == 1
    assert view.policy.mastery.min_days_pass_to_review == 3
    assert view.policy.resource_stale_after_days == DEFAULT_STALE_AFTER_DAYS


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


def _write_node_file(root: Path, node_id: str) -> None:
    _shared_write_node(root, node_id)


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    import yaml as yaml_mod

    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml_mod.safe_dump(doc, sort_keys=False), encoding="utf-8")


def test_filesystem_loaders_and_in_memory_doubles_agree(tmp_path: Path):
    # The seam's justification (T1 acceptance): the same logical repo loaded
    # through the real filesystem adapters and through hand-built in-memory
    # doubles yields the same joined view — derived indexes included.
    n1, n2 = _node("testing.alpha.subject_01"), _node("testing.alpha.subject_02")
    spec = ArtifactSpec(
        id="spec-01",
        node_id="testing.alpha.subject_01",
        title="Spec 01",
        artifact_kind="problem_set",
        required=True,
        minimum_count=3,
    )
    gate = ValidationGate(
        id="gate-01", node_id="testing.alpha.subject_01", authority="manual"
    )
    resource = _fake_resource("testing.alpha.subject_01")

    # The same logical repo, written as real files.
    for node in (n1, n2):
        _write_node_file(tmp_path, node.id)
    _write_yaml(
        tmp_path,
        "evidence/artifact_specs.yaml",
        {
            "artifact_specs": [
                {
                    "id": spec.id,
                    "node_id": spec.node_id,
                    "title": spec.title,
                    "artifact_kind": spec.artifact_kind,
                    "required": spec.required,
                    "minimum_count": spec.minimum_count,
                }
            ]
        },
    )
    _write_yaml(
        tmp_path,
        "evidence/validation_gates.yaml",
        {
            "validation_gates": [
                {"id": gate.id, "node_id": gate.node_id, "authority": gate.authority}
            ]
        },
    )
    _write_yaml(
        tmp_path,
        "graph/resources.yaml",
        {
            "resources": [
                {
                    "id": resource.id,
                    "cost": resource.cost,
                    "url": resource.url,
                    "supports": list(resource.supports),
                }
            ]
        },
    )
    _write_yaml(tmp_path, "graph/state.yaml", {"progress": {}})

    fs_view = load_context_lenient(tmp_path, loaders=Loaders())

    doubles = Loaders(
        load_nodes=lambda _r: [n1, n2],
        load_edges=lambda _r: [],
        load_state=lambda _r: ProgressStore(),
        load_specs=lambda _r: [spec],
        load_gates=lambda _r: [gate],
        load_records=lambda _r: [],
        load_attempts=lambda _r: [],
        load_sessions=lambda _r: [],
        load_work=lambda _r: [],
        load_blockers=lambda _r: [],
        load_remediations=lambda _r: [],
        load_reviews=lambda _r: [],
        load_resources=lambda _r: [resource],
        load_events=lambda _r: [],
        load_policies=lambda _r: {},
    )
    double_view = load_context_lenient(tmp_path, loaders=doubles)

    assert fs_view.errors == []
    assert list(fs_view.titles) == list(double_view.titles)
    assert set(fs_view.node_map) == set(double_view.node_map) == {"testing.alpha.subject_01", "testing.alpha.subject_02"}
    assert fs_view.has_gate == double_view.has_gate == {"testing.alpha.subject_01"}
    assert list(fs_view.specs_by_node) == list(double_view.specs_by_node) == ["testing.alpha.subject_01"]
    assert [r.id for r in fs_view.resources_by_node["testing.alpha.subject_01"]] == ["res-01"]
    assert fs_view.resources_by_node["testing.alpha.subject_02"] == []
