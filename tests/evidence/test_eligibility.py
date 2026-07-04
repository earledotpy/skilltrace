"""Unit tests for the pure `compute_eligibility` function (evidence/eligibility.py).

Pass eligibility is arithmetic over already-loaded evidence records: per required
spec, count accepted records with no successor; a node with no gate or no required
spec is never eligible. These tests drive the pure core directly — no disk, no
state store — so every rule (below-minimum, superseded drop, rejected drop,
optional specs ignored, gateless, spec-less, and the passed-but-not-backed
overlay) is deterministic. The wired CLI path (loaders, node existence, exit
codes, read-only audit) is covered in test_eligibility_command.py.

Note what the function deliberately never sees: assessment attempts. "Attempts
don't count" is enforced by construction — `compute_eligibility` has no attempts
parameter — not by filtering them out.
"""

from __future__ import annotations

from skilltrace.evidence.eligibility import compute_eligibility, live_accepted_count
from skilltrace.evidence.records import EvidenceRecord
from skilltrace.evidence.specs import ArtifactSpec

NODE = "math.arithmetic.order_operations_01"
SPEC_ID = "spec.math.arithmetic.order_operations"
OPTIONAL_SPEC_ID = "spec.math.arithmetic.reflection"


def _spec(
    spec_id: str = SPEC_ID, *, required: bool = True, minimum_count: int = 3
) -> ArtifactSpec:
    return ArtifactSpec(
        id=spec_id,
        node_id=NODE,
        title="Order of operations evidence",
        artifact_kind="problem_set",
        required=required,
        minimum_count=minimum_count,
    )


def _record(
    record_id: str,
    *,
    spec_id: str = SPEC_ID,
    accepted: bool = True,
    supersedes: str | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        id=record_id,
        artifact_spec_id=spec_id,
        location=f"evidence/{record_id}.md",
        accepted=accepted,
        accepted_by="learner_manual",
        artifact_hash="sha256:deadbeef",
        supersedes=supersedes,
        supersede_reason="correction" if supersedes else None,
    )


def _accepted(spec_id: str = SPEC_ID, n: int = 3) -> list[EvidenceRecord]:
    return [_record(f"ev.{NODE}.00{i}", spec_id=spec_id) for i in range(1, n + 1)]


# --- live_accepted_count primitive -----------------------------------------


def test_live_count_counts_accepted_non_superseded():
    records = _accepted(n=2)
    assert live_accepted_count(records, SPEC_ID) == 2


def test_live_count_ignores_other_specs():
    records = _accepted(n=2) + [_record("ev.x.001", spec_id=OPTIONAL_SPEC_ID)]
    assert live_accepted_count(records, SPEC_ID) == 2


# --- Eligible ---------------------------------------------------------------


def test_eligible_when_every_required_spec_meets_minimum():
    result = compute_eligibility(
        NODE, [_spec(minimum_count=3)], has_gate=True, records=_accepted(n=3),
        node_state="active",
    )
    assert result.eligible is True
    assert result.reasons == []
    assert result.specs[0].accepted_count == 3
    assert result.specs[0].met is True


# --- Below-minimum count ----------------------------------------------------


def test_below_minimum_count_not_eligible():
    result = compute_eligibility(
        NODE, [_spec(minimum_count=3)], has_gate=True, records=_accepted(n=2),
        node_state="active",
    )
    assert result.eligible is False
    assert result.specs[0].accepted_count == 2
    assert result.specs[0].met is False
    assert any("below" in r.lower() for r in result.reasons)


# --- Superseded records don't count ----------------------------------------


def test_superseded_records_do_not_count():
    # Three accepted records, but one is superseded by a correction → 3 live,
    # of which the superseded one drops out, leaving 2 accepted heads plus the
    # correction. Model it as: 2 originals + 1 that supersedes a would-be third.
    records = [
        _record(f"ev.{NODE}.001"),
        _record(f"ev.{NODE}.002"),
        _record(f"ev.{NODE}.003"),
        _record(f"ev.{NODE}.004", supersedes=f"ev.{NODE}.003"),
    ]
    # 001, 002, 004 are live accepted (003 superseded) → 3 meets minimum 3.
    assert live_accepted_count(records, SPEC_ID) == 3

    # Now supersede with a *rejected* correction: the accepted original drops and
    # nothing replaces its count.
    records = [
        _record(f"ev.{NODE}.001"),
        _record(f"ev.{NODE}.002"),
        _record(f"ev.{NODE}.003"),
        _record(f"ev.{NODE}.004", accepted=False, supersedes=f"ev.{NODE}.003"),
    ]
    result = compute_eligibility(
        NODE, [_spec(minimum_count=3)], has_gate=True, records=records,
        node_state="active",
    )
    assert result.specs[0].accepted_count == 2
    assert result.eligible is False


# --- Rejected records don't count ------------------------------------------


def test_rejected_records_do_not_count():
    records = _accepted(n=2) + [_record(f"ev.{NODE}.003", accepted=False)]
    result = compute_eligibility(
        NODE, [_spec(minimum_count=3)], has_gate=True, records=records,
        node_state="active",
    )
    assert result.specs[0].accepted_count == 2
    assert result.eligible is False


# --- Optional-spec records don't count -------------------------------------


def test_optional_spec_records_are_not_counted():
    # Required spec is unmet; an optional spec is fully satisfied. The optional
    # spec neither appears in the breakdown nor rescues eligibility.
    specs = [_spec(minimum_count=3), _spec(OPTIONAL_SPEC_ID, required=False, minimum_count=1)]
    records = _accepted(SPEC_ID, n=1) + _accepted(OPTIONAL_SPEC_ID, n=5)
    result = compute_eligibility(
        NODE, specs, has_gate=True, records=records, node_state="active",
    )
    assert [s.spec_id for s in result.specs] == [SPEC_ID]
    assert result.eligible is False


# --- Gateless node never eligible ------------------------------------------


def test_gateless_node_never_eligible_even_with_enough_records():
    result = compute_eligibility(
        NODE, [_spec(minimum_count=3)], has_gate=False, records=_accepted(n=3),
        node_state="active",
    )
    assert result.eligible is False
    assert any("gate" in r.lower() for r in result.reasons)


# --- Spec-less node never eligible -----------------------------------------


def test_node_with_no_required_spec_never_eligible():
    # Only an optional spec exists; no required spec to satisfy.
    result = compute_eligibility(
        NODE, [_spec(OPTIONAL_SPEC_ID, required=False)], has_gate=True,
        records=_accepted(OPTIONAL_SPEC_ID, n=9), node_state="active",
    )
    assert result.eligible is False
    assert result.specs == []
    assert any("required" in r.lower() for r in result.reasons)


def test_node_with_no_specs_at_all_never_eligible():
    result = compute_eligibility(
        NODE, [], has_gate=True, records=[], node_state="active",
    )
    assert result.eligible is False
    assert result.specs == []


# --- passed-but-not-backed discrepancy overlay -----------------------------


def test_passed_but_not_backed_flagged_when_state_passed_and_not_eligible():
    result = compute_eligibility(
        NODE, [_spec(minimum_count=3)], has_gate=True, records=_accepted(n=1),
        node_state="passed",
    )
    assert result.eligible is False
    assert result.passed_but_not_backed is True


def test_mastered_state_also_flags_discrepancy_when_not_eligible():
    result = compute_eligibility(
        NODE, [_spec(minimum_count=3)], has_gate=True, records=[],
        node_state="mastered",
    )
    assert result.passed_but_not_backed is True


def test_no_discrepancy_when_passed_and_still_eligible():
    result = compute_eligibility(
        NODE, [_spec(minimum_count=3)], has_gate=True, records=_accepted(n=3),
        node_state="passed",
    )
    assert result.eligible is True
    assert result.passed_but_not_backed is False


def test_no_discrepancy_when_not_passed_and_not_eligible():
    # An `active` node that isn't eligible yet is the normal in-progress case,
    # not a discrepancy.
    result = compute_eligibility(
        NODE, [_spec(minimum_count=3)], has_gate=True, records=_accepted(n=1),
        node_state="active",
    )
    assert result.eligible is False
    assert result.passed_but_not_backed is False
