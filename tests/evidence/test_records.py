"""EvidenceRecord loader: frozen, closed schema, accepted_by enum, supersede pair.

Issue #10: id `ev.<node_id>.NNN`; sole node linkage is `artifact_spec_id` (a
stray `node_id` fails); `supersedes` without reason fails; record is immutable.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from skilltrace.evidence import ACCEPTED_BY_VALUES, EvidenceLoadError
from skilltrace.evidence.records import (
    EvidenceRecord,
    load_evidence_record,
    load_evidence_records,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "math.arithmetic.order_operations_01"

_VALID_RECORD = {
    "id": f"ev.{NODE}.001",
    "artifact_spec_id": "spec.math.arithmetic.order_operations",
    "location": "evidence/math/set_001.md",
    "note": "First set.",
    "accepted": True,
    "accepted_by": "learner_manual",
    "artifact_hash": "sha256:abc123",
    "created_at": "2026-07-03",
}


def _record_with(**overrides):
    data = dict(_VALID_RECORD)
    data.update(overrides)
    return data


def test_valid_record_loads():
    rec = load_evidence_record(dict(_VALID_RECORD))
    assert isinstance(rec, EvidenceRecord)
    assert rec.id == f"ev.{NODE}.001"
    assert rec.artifact_spec_id == "spec.math.arithmetic.order_operations"
    assert rec.accepted is True
    assert rec.accepted_by == "learner_manual"
    assert rec.supersedes is None
    assert rec.supersede_reason is None


def test_record_is_frozen():
    rec = load_evidence_record(dict(_VALID_RECORD))
    with pytest.raises(dataclasses.FrozenInstanceError):
        rec.accepted = False  # type: ignore[misc]


def test_stray_node_id_field_fails():
    # artifact_spec_id is the sole node linkage; a node_id field is unknown and
    # the closed schema rejects it — the structural enforcement of ADR 0003.
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_evidence_record(_record_with(node_id=NODE))
    assert "node_id" in str(excinfo.value)


def test_malformed_id_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_evidence_record(_record_with(id="ev.badnode.001"))
    assert "id" in str(excinfo.value)


def test_attempt_style_id_fails_for_record():
    with pytest.raises(EvidenceLoadError):
        load_evidence_record(_record_with(id=f"att.{NODE}.001"))


@pytest.mark.parametrize("value", sorted(ACCEPTED_BY_VALUES))
def test_each_accepted_by_value_loads(value):
    rec = load_evidence_record(_record_with(accepted_by=value))
    assert rec.accepted_by == value


def test_unknown_accepted_by_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_evidence_record(_record_with(accepted_by="ai_review"))
    assert "accepted_by" in str(excinfo.value)


def test_rejected_record_keeps_its_authority():
    # A rejected record (accepted: false) still names the authority that judged it.
    rec = load_evidence_record(_record_with(accepted=False, accepted_by="objective_gate"))
    assert rec.accepted is False
    assert rec.accepted_by == "objective_gate"


def test_non_boolean_accepted_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_evidence_record(_record_with(accepted="true"))
    assert "accepted" in str(excinfo.value)


def test_supersedes_without_reason_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_evidence_record(_record_with(supersedes=f"ev.{NODE}.001"))
    assert "supersede" in str(excinfo.value)


def test_reason_without_supersedes_fails():
    with pytest.raises(EvidenceLoadError):
        load_evidence_record(_record_with(supersede_reason="fixing an error"))


def test_valid_supersede_pair_loads():
    rec = load_evidence_record(
        _record_with(
            id=f"ev.{NODE}.002",
            supersedes=f"ev.{NODE}.001",
            supersede_reason="Corrected arithmetic.",
        )
    )
    assert rec.supersedes == f"ev.{NODE}.001"
    assert rec.supersede_reason == "Corrected arithmetic."


def test_malformed_supersedes_id_fails():
    with pytest.raises(EvidenceLoadError):
        load_evidence_record(
            _record_with(supersedes="not-an-id", supersede_reason="x")
        )


@pytest.mark.parametrize(
    "field",
    ["id", "artifact_spec_id", "location", "accepted", "accepted_by", "artifact_hash", "created_at"],
)
def test_missing_required_field_fails(field):
    data = {k: v for k, v in _VALID_RECORD.items() if k != field}
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_evidence_record(data)
    assert field in str(excinfo.value)


def test_unknown_field_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_evidence_record(_record_with(status="pending"))
    assert "status" in str(excinfo.value)


def test_seed_records_load_empty():
    assert load_evidence_records(REPO_ROOT) == []
