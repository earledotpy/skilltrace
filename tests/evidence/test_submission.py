"""Unit tests for the pure `plan_submit` planner (evidence/submission.py).

These drive the decision core with injected gate-runner and hasher stubs, so
every branch — spec resolution, gateless refusal, manual/objective verdict
rules, unrunnable gate, supersede rules, hashing, and the two advisory warnings
— is deterministic with no disk or subprocess. The wired CLI path (real
subprocess, real hash, real append + audit event) is covered in
test_submit_command.py.
"""

from __future__ import annotations

import pytest

from skilltrace.evidence.records import EvidenceRecord
from skilltrace.evidence.specs import ArtifactSpec
from skilltrace.evidence.submission import (
    GateInfo,
    GateUnrunnable,
    plan_submit,
)

NODE = "math.arithmetic.order_operations_01"
SPEC_ID = "spec.math.arithmetic.order_operations"
OTHER_SPEC_ID = "spec.math.arithmetic.other"
NOW = "2026-07-03T12:00:00+00:00"


def _spec(spec_id: str = SPEC_ID, *, required: bool = True, minimum_count: int = 3) -> ArtifactSpec:
    return ArtifactSpec(
        id=spec_id,
        node_id=NODE,
        title="Order of operations evidence",
        artifact_kind="problem_set",
        required=required,
        minimum_count=minimum_count,
    )


def _manual() -> GateInfo:
    return GateInfo(authority="manual")


def _objective(command: str = "echo ok") -> GateInfo:
    return GateInfo(authority="objective", command=command)


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
        supersede_reason="fix" if supersedes else None,
    )


def _hash_stub(location: str) -> str:
    return "sha256:stubbed"


def _never_run(command: str) -> int:  # gate runner that must not be called
    raise AssertionError(f"gate command should not run: {command!r}")


def _plan(**overrides):
    """Call plan_submit with sensible manual-accept defaults, overridable."""
    kwargs = dict(
        node_id=NODE,
        specs_for_node=[_spec()],
        gate=_manual(),
        existing_records=[],
        node_state="available",
        spec_id=None,
        location="evidence/math/set_001.md",
        note=None,
        accept=True,
        reject=False,
        supersedes=None,
        supersede_reason=None,
        run_gate=_never_run,
        hasher=_hash_stub,
        now=NOW,
    )
    kwargs.update(overrides)
    return plan_submit(
        kwargs.pop("node_id"),
        kwargs.pop("specs_for_node"),
        kwargs.pop("gate"),
        kwargs.pop("existing_records"),
        kwargs.pop("node_state"),
        **kwargs,
    )


# --- Spec resolution -------------------------------------------------------


def test_single_spec_inferred_when_spec_omitted():
    out = _plan()
    assert out.exit_code == 0
    assert out.record["artifact_spec_id"] == SPEC_ID


def test_several_specs_without_spec_flag_refuses_and_lists():
    out = _plan(specs_for_node=[_spec(SPEC_ID), _spec(OTHER_SPEC_ID)])
    assert out.record is None
    assert out.exit_code == 2
    assert SPEC_ID in out.errors[0] and OTHER_SPEC_ID in out.errors[0]


def test_no_spec_on_node_refuses():
    out = _plan(specs_for_node=[])
    assert out.record is None
    assert out.exit_code == 2
    assert "nothing to submit" in out.errors[0]


def test_named_spec_not_on_node_refuses():
    out = _plan(spec_id="spec.not.here")
    assert out.record is None
    assert out.exit_code == 2
    assert "not an artifact spec" in out.errors[0]


# --- Gate presence ---------------------------------------------------------


def test_gateless_node_refuses():
    out = _plan(gate=None)
    assert out.record is None
    assert out.exit_code == 2
    assert "no gate" in out.errors[0]


# --- Manual authority ------------------------------------------------------


def test_manual_without_verdict_refuses():
    out = _plan(accept=False, reject=False)
    assert out.record is None
    assert out.exit_code == 2
    assert "explicit verdict" in out.errors[0]


def test_manual_reject_writes_rejected_record_and_exits_zero():
    out = _plan(accept=False, reject=True)
    assert out.exit_code == 0
    assert out.record["accepted"] is False
    assert out.record["accepted_by"] == "learner_manual"
    assert out.records_touched == [out.record["id"]]


def test_manual_accept_writes_accepted_record():
    out = _plan(accept=True, reject=False)
    assert out.record["accepted"] is True
    assert out.record["accepted_by"] == "learner_manual"


def test_manual_both_flags_refuses():
    out = _plan(accept=True, reject=True)
    assert out.record is None
    assert out.exit_code == 2


# --- Objective authority ---------------------------------------------------


def test_objective_with_verdict_flag_refuses_before_running():
    # _never_run guarantees the command is not executed on a refusal.
    out = _plan(gate=_objective(), accept=True, reject=False)
    assert out.record is None
    assert out.exit_code == 2
    assert "refused" in out.errors[0]


def test_objective_gate_exit_zero_accepts():
    out = _plan(gate=_objective("echo ok"), accept=False, reject=False, run_gate=lambda c: 0)
    assert out.exit_code == 0
    assert out.record["accepted"] is True
    assert out.record["accepted_by"] == "objective_gate"
    assert any("exit code: 0" in m for m in out.messages)


def test_objective_gate_nonzero_writes_rejected_record_and_exits_zero():
    # A failing gate is a rejection verdict, not a submit failure: the rejected
    # record is written and the submit exits 0 so the dispatcher logs its event.
    out = _plan(gate=_objective("false"), accept=False, reject=False, run_gate=lambda c: 1)
    assert out.exit_code == 0
    assert out.record is not None
    assert out.record["accepted"] is False
    assert out.record["accepted_by"] == "objective_gate"
    assert out.records_touched == [out.record["id"]]


def test_objective_gate_unrunnable_writes_nothing_and_exits_nonzero():
    def _unrunnable(command: str) -> int:
        raise GateUnrunnable("no such executable")

    out = _plan(gate=_objective("no_such_exe"), accept=False, reject=False, run_gate=_unrunnable)
    assert out.record is None
    assert out.exit_code == 1
    assert out.records_touched == []
    assert "not a judgment" in out.errors[0]


# --- Hash and id -----------------------------------------------------------


def test_record_carries_hash_and_allocated_id():
    existing = [_record(f"ev.{NODE}.001"), _record(f"ev.{NODE}.002")]
    out = _plan(existing_records=existing)
    assert out.record["artifact_hash"] == "sha256:stubbed"
    assert out.record["id"] == f"ev.{NODE}.003"  # max seen + 1


# --- Supersede rules -------------------------------------------------------


def test_supersede_without_reason_refuses():
    out = _plan(supersedes=f"ev.{NODE}.001", supersede_reason=None, existing_records=[_record(f"ev.{NODE}.001")])
    assert out.record is None
    assert "requires --reason" in out.errors[0]


def test_reason_without_supersedes_refuses():
    out = _plan(supersedes=None, supersede_reason="typo")
    assert out.record is None
    assert "without --supersedes" in out.errors[0]


def test_supersede_missing_target_refuses():
    out = _plan(supersedes=f"ev.{NODE}.099", supersede_reason="fix", existing_records=[])
    assert out.record is None
    assert "does not exist" in out.errors[0]


def test_supersede_cross_spec_refuses():
    target = _record(f"ev.{NODE}.001", spec_id=OTHER_SPEC_ID)
    out = _plan(
        specs_for_node=[_spec(SPEC_ID), _spec(OTHER_SPEC_ID)],
        spec_id=SPEC_ID,
        supersedes=f"ev.{NODE}.001",
        supersede_reason="fix",
        existing_records=[target],
    )
    assert out.record is None
    assert "one artifact spec" in out.errors[0]


def test_supersede_already_superseded_refuses():
    target = _record(f"ev.{NODE}.001")
    successor = _record(f"ev.{NODE}.002", supersedes=f"ev.{NODE}.001")
    out = _plan(
        supersedes=f"ev.{NODE}.001",
        supersede_reason="fix",
        existing_records=[target, successor],
    )
    assert out.record is None
    assert "one live head" in out.errors[0]


def test_valid_supersede_writes_record_with_pair():
    target = _record(f"ev.{NODE}.001")
    out = _plan(
        supersedes=f"ev.{NODE}.001",
        supersede_reason="clearer scan",
        existing_records=[target],
    )
    assert out.exit_code == 0
    assert out.record["supersedes"] == f"ev.{NODE}.001"
    assert out.record["supersede_reason"] == "clearer scan"


# --- Advisory warnings -----------------------------------------------------


def test_locked_node_warns_but_writes():
    out = _plan(node_state="locked")
    assert out.exit_code == 0
    assert out.record is not None
    assert any("locked" in w for w in out.warnings)


def test_supersede_dropping_eligibility_under_passed_warns():
    # Node needs 1 accepted record; one accepted record on file makes it eligible.
    # Superseding it with a *rejected* record drops eligibility; node is passed,
    # so the pass stands and only the drop is warned.
    spec = _spec(minimum_count=1)
    target = _record(f"ev.{NODE}.001", accepted=True)
    out = _plan(
        specs_for_node=[spec],
        node_state="passed",
        accept=False,
        reject=True,
        supersedes=f"ev.{NODE}.001",
        supersede_reason="was wrong",
        existing_records=[target],
    )
    assert out.exit_code == 0
    assert out.record is not None
    assert any("drops pass-eligibility" in w and "stands" in w for w in out.warnings)


def test_supersede_not_dropping_eligibility_does_not_warn():
    # Replace an accepted record with another accepted record: still eligible.
    spec = _spec(minimum_count=1)
    target = _record(f"ev.{NODE}.001", accepted=True)
    out = _plan(
        specs_for_node=[spec],
        node_state="passed",
        accept=True,
        reject=False,
        supersedes=f"ev.{NODE}.001",
        supersede_reason="clearer scan",
        existing_records=[target],
    )
    assert not any("drops pass-eligibility" in w for w in out.warnings)


def test_eligibility_drop_not_warned_when_node_active_not_passed():
    # `active` is asserted progress but not a *pass*: the "pass stands" warning
    # applies only to passed/mastered, so an active node's drop is not warned.
    spec = _spec(minimum_count=1)
    target = _record(f"ev.{NODE}.001", accepted=True)
    out = _plan(
        specs_for_node=[spec],
        node_state="active",
        accept=False,
        reject=True,
        supersedes=f"ev.{NODE}.001",
        supersede_reason="was wrong",
        existing_records=[target],
    )
    assert out.exit_code == 0
    assert not any("drops pass-eligibility" in w for w in out.warnings)


def test_eligibility_drop_warned_when_node_mastered():
    spec = _spec(minimum_count=1)
    target = _record(f"ev.{NODE}.001", accepted=True)
    out = _plan(
        specs_for_node=[spec],
        node_state="mastered",
        accept=False,
        reject=True,
        supersedes=f"ev.{NODE}.001",
        supersede_reason="was wrong",
        existing_records=[target],
    )
    assert any("drops pass-eligibility" in w for w in out.warnings)


def test_eligibility_drop_not_warned_when_node_not_asserted():
    # Same drop, but node is merely available (not an asserted pass): no warning,
    # because the warning is specifically about a pass that stands despite a drop.
    spec = _spec(minimum_count=1)
    target = _record(f"ev.{NODE}.001", accepted=True)
    out = _plan(
        specs_for_node=[spec],
        node_state="available",
        accept=False,
        reject=True,
        supersedes=f"ev.{NODE}.001",
        supersede_reason="was wrong",
        existing_records=[target],
    )
    assert not any("drops pass-eligibility" in w for w in out.warnings)
