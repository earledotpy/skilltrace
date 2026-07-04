"""AssessmentAttempt loader: two-value outcome, id/node_id agreement, immutable.

Issue #10: outcome outside `passed`/`failed` fails; id `att.<node_id>.NNN`; no
supersede mechanism.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from skilltrace.evidence import OUTCOMES, EvidenceLoadError
from skilltrace.evidence.attempts import (
    AssessmentAttempt,
    load_assessment_attempt,
    load_assessment_attempts,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "math.arithmetic.order_operations_01"

_VALID_ATTEMPT = {
    "id": f"att.{NODE}.001",
    "node_id": NODE,
    "outcome": "passed",
    "note": "Nailed it.",
    "created_at": "2026-07-03",
}


def _attempt_with(**overrides):
    data = dict(_VALID_ATTEMPT)
    data.update(overrides)
    return data


def test_valid_attempt_loads():
    att = load_assessment_attempt(dict(_VALID_ATTEMPT))
    assert isinstance(att, AssessmentAttempt)
    assert att.id == f"att.{NODE}.001"
    assert att.node_id == NODE
    assert att.outcome == "passed"


def test_attempt_is_frozen():
    att = load_assessment_attempt(dict(_VALID_ATTEMPT))
    with pytest.raises(dataclasses.FrozenInstanceError):
        att.outcome = "failed"  # type: ignore[misc]


def test_outcomes_are_exactly_two():
    assert OUTCOMES == {"passed", "failed"}


@pytest.mark.parametrize("outcome", sorted(OUTCOMES))
def test_each_outcome_loads(outcome):
    att = load_assessment_attempt(_attempt_with(outcome=outcome))
    assert att.outcome == outcome


@pytest.mark.parametrize("outcome", ["pass", "fail", "partial", "0.8", "passed_with_help", ""])
def test_outcome_outside_two_values_fails(outcome):
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_assessment_attempt(_attempt_with(outcome=outcome))
    assert "outcome" in str(excinfo.value)


def test_failed_attempt_needs_no_note():
    data = {k: v for k, v in _VALID_ATTEMPT.items() if k != "note"}
    data["outcome"] = "failed"
    att = load_assessment_attempt(data)
    assert att.note is None
    assert att.outcome == "failed"


def test_malformed_id_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_assessment_attempt(_attempt_with(id="att.badnode.001"))
    assert "id" in str(excinfo.value)


def test_evidence_style_id_fails_for_attempt():
    with pytest.raises(EvidenceLoadError):
        load_assessment_attempt(_attempt_with(id=f"ev.{NODE}.001"))


def test_id_node_mismatch_fails():
    # The id embeds one node; the node_id field declares another — intra-record
    # inconsistency the loader catches at #10, not cross-record #11.
    other = "programming.python.variables_01"
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_assessment_attempt(_attempt_with(id=f"att.{other}.001"))
    assert "node" in str(excinfo.value)


def test_invalid_node_id_field_fails():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_assessment_attempt(_attempt_with(node_id="nope", id="att.nope.001"))
    assert "node_id" in str(excinfo.value)


@pytest.mark.parametrize("field", ["id", "node_id", "outcome", "created_at"])
def test_missing_required_field_fails(field):
    data = {k: v for k, v in _VALID_ATTEMPT.items() if k != field}
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_assessment_attempt(data)
    assert field in str(excinfo.value)


def test_unknown_field_fails():
    # No supersede mechanism: a supersedes field is simply unknown here.
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_assessment_attempt(_attempt_with(supersedes=f"att.{NODE}.000"))
    assert "supersedes" in str(excinfo.value)


def test_non_mapping_fails_naming_index():
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_assessment_attempt("nope", index=7)
    assert "7" in str(excinfo.value)


def test_seed_attempts_load_empty():
    assert load_assessment_attempts(REPO_ROOT) == []
