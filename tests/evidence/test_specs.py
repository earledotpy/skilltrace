"""ArtifactSpec loader: closed schema, required bool, minimum_count >= 1.

Issue #10: `minimum_count: 0` fails; unknown fields fail; `artifact_kind` is
free curriculum vocabulary and is *not* enum-constrained.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skilltrace.evidence import EvidenceLoadError
from skilltrace.evidence.specs import ArtifactSpec, load_artifact_spec, load_artifact_specs

REPO_ROOT = Path(__file__).resolve().parents[2]

_VALID_SPEC = {
    "id": "spec.math.arithmetic.order_operations",
    "node_id": "math.arithmetic.order_operations_01",
    "title": "Order of operations evidence",
    "artifact_kind": "problem_set",
    "description": "Some description.",
    "required": True,
    "minimum_count": 3,
    "expected_location_hint": "evidence/math/",
    "example_filename": "example.md",
    "acceptance_summary": "Shows correct work.",
    "created_at": "2026-06-28",
    "updated_at": "2026-06-28",
}


def _spec_with(**overrides):
    data = dict(_VALID_SPEC)
    data.update(overrides)
    return data


def test_valid_spec_loads_all_fields():
    spec = load_artifact_spec(dict(_VALID_SPEC))
    assert isinstance(spec, ArtifactSpec)
    assert spec.id == _VALID_SPEC["id"]
    assert spec.node_id == "math.arithmetic.order_operations_01"
    assert spec.required is True
    assert spec.minimum_count == 3
    assert spec.artifact_kind == "problem_set"


def test_descriptive_fields_are_optional():
    minimal = {
        "id": "spec.x",
        "node_id": "a.b.c_01",
        "title": "T",
        "artifact_kind": "problem_set",
        "required": False,
        "minimum_count": 1,
    }
    spec = load_artifact_spec(minimal)
    assert spec.description is None
    assert spec.acceptance_summary is None
    assert spec.required is False


def test_unknown_field_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_artifact_spec(_spec_with(weight=5))
    assert "weight" in str(excinfo.value)


@pytest.mark.parametrize(
    "field", ["id", "node_id", "title", "artifact_kind", "required", "minimum_count"]
)
def test_missing_required_field_fails(field):
    data = {k: v for k, v in _VALID_SPEC.items() if k != field}
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_artifact_spec(data)
    assert field in str(excinfo.value)


def test_minimum_count_zero_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_artifact_spec(_spec_with(minimum_count=0))
    assert "minimum_count" in str(excinfo.value)


def test_negative_minimum_count_fails():
    with pytest.raises(EvidenceLoadError):
        load_artifact_spec(_spec_with(minimum_count=-1))


def test_non_integer_minimum_count_fails():
    with pytest.raises(EvidenceLoadError):
        load_artifact_spec(_spec_with(minimum_count="3"))


def test_boolean_minimum_count_fails():
    # bool is a subclass of int; True must not sneak through as 1.
    with pytest.raises(EvidenceLoadError):
        load_artifact_spec(_spec_with(minimum_count=True))


def test_non_boolean_required_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_artifact_spec(_spec_with(required="yes"))
    assert "required" in str(excinfo.value)


def test_invalid_node_id_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_artifact_spec(_spec_with(node_id="not-a-node"))
    assert "node_id" in str(excinfo.value)


def test_artifact_kind_is_not_enum_constrained():
    # A curriculum introducing a novel kind must load — the engine attaches no
    # meaning to the kind (same status as a track label).
    spec = load_artifact_spec(_spec_with(artifact_kind="diagram"))
    assert spec.artifact_kind == "diagram"


def test_non_mapping_fails_naming_index():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_artifact_spec(["nope"], index=2)
    assert "2" in str(excinfo.value)


def test_all_seed_specs_load():
    specs = load_artifact_specs(REPO_ROOT)
    assert len(specs) == 81
    assert all(s.minimum_count >= 1 for s in specs)
    assert all(s.required for s in specs)
    assert all(s.node_id for s in specs)
