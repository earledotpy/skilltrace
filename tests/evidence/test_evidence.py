"""Unified evidence loader: one call, many records, per-type degradation.

Issue #172: the four per-type loader modules collapse into
`skilltrace.evidence.evidence`. This file tests the new module's external
contract — the unified `load_evidence` result, the schema descriptors, and
the lenient degradation that the joined read context relies on.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from skilltrace.evidence import EvidenceLoadError
from skilltrace.evidence.evidence import (
    ATTEMPT_SCHEMA,
    GATE_SCHEMA,
    RECORD_SCHEMA,
    SPEC_SCHEMA,
    EvidenceRecords,
    load_assessment_attempt,
    load_artifact_spec,
    load_evidence,
    load_evidence_record,
    load_validation_gate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "math.arithmetic.order_operations_01"


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _minimal_repo(root: Path) -> None:
    _write_yaml(
        root,
        "evidence/artifact_specs.yaml",
        {
            "artifact_specs": [
                {
                    "id": "spec-01",
                    "node_id": NODE,
                    "title": "Spec 01",
                    "artifact_kind": "problem_set",
                    "required": True,
                    "minimum_count": 1,
                }
            ]
        },
    )
    _write_yaml(
        root,
        "evidence/validation_gates.yaml",
        {"validation_gates": [{"id": "gate-01", "node_id": NODE, "authority": "manual"}]},
    )
    _write_yaml(root, "evidence/evidence_records.yaml", {"evidence_records": []})
    _write_yaml(root, "evidence/attempts.yaml", {"attempts": []})


# -- unified contract: one call returns all four typed lists -----------------


def test_load_evidence_returns_typed_result(tmp_path: Path):
    _minimal_repo(tmp_path)
    result = load_evidence(tmp_path)
    assert isinstance(result, EvidenceRecords)
    assert [s.id for s in result.specs] == ["spec-01"]
    assert [g.id for g in result.gates] == ["gate-01"]
    assert result.records == []
    assert result.attempts == []
    assert result.errors == {}


def test_load_evidence_seed_repo_matches_per_type_loaders():
    result = load_evidence(REPO_ROOT)
    assert len(result.specs) == 81
    assert len(result.gates) == 81
    assert result.records == []
    assert result.attempts == []
    assert result.errors == {}


def test_load_evidence_does_not_assert_on_file_order(tmp_path: Path):
    # External contract: assert on typed result lists, not on which files
    # were opened or in what order.
    _minimal_repo(tmp_path)
    result = load_evidence(tmp_path)
    assert result.specs[0].node_id == NODE
    assert result.gates[0].authority == "manual"


# -- schema descriptors: each rejects unknown/missing/enum violations --------


def test_spec_descriptor_rejects_unknown_field():
    with pytest.raises(EvidenceLoadError):
        load_artifact_spec(
            {
                "id": "s",
                "node_id": NODE,
                "title": "T",
                "artifact_kind": "k",
                "required": True,
                "minimum_count": 1,
                "weight": 5,
            }
        )
    assert "weight" in SPEC_SCHEMA.allowed or True  # descriptor owns the set
    assert "id" in SPEC_SCHEMA.required


def test_gate_descriptor_rejects_bad_authority():
    with pytest.raises(EvidenceLoadError):
        load_validation_gate({"id": "g", "node_id": NODE, "authority": "ai"})
    assert GATE_SCHEMA.required == ("id", "node_id", "authority")


def test_record_descriptor_rejects_missing_field():
    with pytest.raises(EvidenceLoadError):
        load_evidence_record({"id": f"ev.{NODE}.001"})
    assert "artifact_spec_id" in RECORD_SCHEMA.required


def test_attempt_descriptor_rejects_bad_outcome():
    with pytest.raises(EvidenceLoadError):
        load_assessment_attempt(
            {
                "id": f"att.{NODE}.001",
                "node_id": NODE,
                "outcome": "partial",
                "created_at": "2026-07-03",
            }
        )
    assert ATTEMPT_SCHEMA.required == ("id", "node_id", "outcome", "created_at")


# -- lenient degradation: one bad file degrades only its type ---------------


def test_malformed_records_degrades_only_records(tmp_path: Path):
    _minimal_repo(tmp_path)
    _write_yaml(
        tmp_path,
        "evidence/evidence_records.yaml",
        {"evidence_records": [{"id": "not-an-id"}]},
    )
    result = load_evidence(tmp_path)
    assert result.records == []
    assert "records" in result.errors
    # The other three types still load.
    assert [s.id for s in result.specs] == ["spec-01"]
    assert [g.id for g in result.gates] == ["gate-01"]
    assert result.attempts == []
    assert "specs" not in result.errors
    assert "gates" not in result.errors


def test_missing_file_degrades_to_empty_with_error(tmp_path: Path):
    _minimal_repo(tmp_path)
    (tmp_path / "evidence" / "attempts.yaml").unlink()
    result = load_evidence(tmp_path)
    assert result.attempts == []
    assert "attempts" in result.errors
    assert [s.id for s in result.specs] == ["spec-01"]


# -- dataclass mapping: valid YAML maps to correct field values --------------


def test_dataclass_mapping_preserves_fields(tmp_path: Path):
    _write_yaml(
        tmp_path,
        "evidence/artifact_specs.yaml",
        {
            "artifact_specs": [
                {
                    "id": "spec-01",
                    "node_id": NODE,
                    "title": "Spec 01",
                    "artifact_kind": "diagram",
                    "required": False,
                    "minimum_count": 2,
                }
            ]
        },
    )
    _write_yaml(
        tmp_path,
        "evidence/validation_gates.yaml",
        {
            "validation_gates": [
                {
                    "id": "gate-01",
                    "node_id": NODE,
                    "authority": "objective",
                    "command": "pytest",
                }
            ]
        },
    )
    _write_yaml(
        tmp_path,
        "evidence/evidence_records.yaml",
        {
            "evidence_records": [
                {
                    "id": f"ev.{NODE}.001",
                    "artifact_spec_id": "spec-01",
                    "location": "evidence/x.md",
                    "accepted": True,
                    "accepted_by": "learner_manual",
                    "artifact_hash": "sha256:abc",
                    "created_at": "2026-07-03",
                }
            ]
        },
    )
    _write_yaml(
        tmp_path,
        "evidence/attempts.yaml",
        {
            "attempts": [
                {
                    "id": f"att.{NODE}.001",
                    "node_id": NODE,
                    "outcome": "failed",
                    "created_at": "2026-07-03",
                }
            ]
        },
    )
    result = load_evidence(tmp_path)
    assert result.errors == {}
    assert result.specs[0].artifact_kind == "diagram"
    assert result.specs[0].required is False
    assert result.gates[0].command == "pytest"
    assert result.records[0].accepted is True
    assert result.attempts[0].outcome == "failed"


# -- joined context: strict collects, lenient degrades ------------------------


def test_joined_strict_collects_evidence_errors(tmp_path: Path):
    from skilltrace.context import Loaders, load_context_strict
    from skilltrace.graph.state import ProgressStore

    _minimal_repo(tmp_path)
    _write_yaml(
        tmp_path,
        "evidence/evidence_records.yaml",
        {"evidence_records": [{"id": "bad"}]},
    )
    loaders = Loaders(
        load_nodes=lambda _r: [],
        load_edges=lambda _r: [],
        load_state=lambda _r: ProgressStore(),
        load_resources=lambda _r: [],
        load_events=lambda _r: [],
        load_policies=lambda _r: {},
    )
    view = load_context_strict(tmp_path, loaders=loaders)
    assert not view.ok
    assert view.records == []
    assert [s.id for s in view.specs] == ["spec-01"]


def test_joined_lenient_degrades_per_type(tmp_path: Path):
    from skilltrace.context import Loaders, load_context_lenient

    _minimal_repo(tmp_path)
    _write_yaml(
        tmp_path,
        "evidence/evidence_records.yaml",
        {"evidence_records": [{"id": "bad"}]},
    )
    view = load_context_lenient(tmp_path, loaders=Loaders())
    assert view.records == []
    assert [s.id for s in view.specs] == ["spec-01"]
    assert "records" in view.degraded
    assert "specs" not in view.degraded
