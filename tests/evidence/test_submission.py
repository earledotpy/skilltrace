"""Unit tests for the pure `plan_submit` planner (evidence/submission.py).

These drive the decision core with injected gate-runner and hasher stubs, so
every branch — spec resolution, gateless refusal, manual/objective verdict
rules, unrunnable gate, supersede rules, hashing, and the two advisory warnings
— is deterministic with no disk or subprocess. The wired CLI path (real
subprocess, real hash, real append + audit event) is covered in
test_submit_command.py.
"""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path

import pytest

from skilltrace.evidence.evidence import EvidenceRecord, ArtifactSpec
from skilltrace.evidence.submission import (
    GateInfo,
    GateRunResult,
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


_FAKE_ROOT = Path("C:/fake/repo").resolve()

# The files the fake repo contains: the submitted artifact and one shipped
# checker script a gate command may name as an argv token.
_FAKE_REPO_FILES = frozenset(
    {"evidence/math/set_001.md", "evidence/math/check_set_001.py"}
)


def _fake_exists(path: Path) -> bool:
    """File-existence predicate over the fake repo (the injected `exists`).

    A path counts as existing iff it resolves under `_FAKE_ROOT` to one of the
    fake repo's files — mirroring what the handler binds (`p.is_file()` over
    the real root) without touching a filesystem.
    """
    try:
        rel = path.resolve().relative_to(_FAKE_ROOT)
    except ValueError:
        return False
    return rel.as_posix() in _FAKE_REPO_FILES


def _never_run(command: str) -> GateRunResult:  # gate runner that must not be called
    raise AssertionError(f"gate command should not run: {command!r}")


def _plan(**overrides):
    """Call plan_submit with sensible manual-accept defaults, overridable.

    `run_gate` defaults to a stub returning a passing `GateRunResult` (the
    manual path never invokes it); `root`/`exists` default to a fake repo the
    receipt builder treats as the gate's cwd — `_fake_exists` recognizes the
    submitted location and argv file tokens under it.
    """
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
        run_gate=lambda command: GateRunResult(
            exit_code=0, stdout="all checks passed\n", stderr=""
        ),
        hasher=_hash_stub,
        now=NOW,
        root=_FAKE_ROOT,
        exists=_fake_exists,
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
    # Receipts are objective-gate provenance only — a manual record never carries one.
    assert "gate_run" not in out.record


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
    out = _plan(
        gate=_objective("echo ok"),
        accept=False,
        reject=False,
        run_gate=lambda c: GateRunResult(exit_code=0, stdout="ok\n"),
    )
    assert out.exit_code == 0
    assert out.record["accepted"] is True
    assert out.record["accepted_by"] == "objective_gate"
    assert any("exit code: 0" in m for m in out.messages)


def test_objective_gate_nonzero_writes_rejected_record_and_exits_zero():
    # A failing gate is a rejection verdict, not a submit failure: the rejected
    # record is written and the submit exits 0 so the dispatcher logs its event.
    out = _plan(
        gate=_objective("false"),
        accept=False,
        reject=False,
        run_gate=lambda c: GateRunResult(exit_code=1, stderr="assertion failed\n"),
    )
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


# --- Gate-run receipts (v2.2, spec §1) ---------------------------------------


def _objective_run(**overrides) -> GateRunResult:
    defaults: dict = {"exit_code": 0, "stdout": "all checks passed\n", "stderr": ""}
    defaults.update(overrides)
    return GateRunResult(**defaults)


def test_objective_receipt_captures_command_identity_and_exit_class():
    out = _plan(
        gate=_objective("python evidence/math/check_set_001.py"),
        accept=False,
        reject=False,
        run_gate=lambda c: _objective_run(),
    )
    receipt = out.record["gate_run"]
    assert receipt["command_argv"] == ["python", "evidence/math/check_set_001.py"]
    assert receipt["exit_class"] == "passed"
    assert receipt["exit_code"] == 0


def test_objective_receipt_inputs_list_artifact_and_in_repo_argv_files():
    out = _plan(
        gate=_objective("python evidence/math/check_set_001.py --verbose"),
        accept=False,
        reject=False,
        run_gate=lambda c: _objective_run(),
    )
    # The artifact's location comes first; the argv token naming a real file in
    # the (fake) repo joins root-relative; flags name no file and are excluded.
    assert out.record["gate_run"]["inputs"] == [
        "evidence/math/set_001.md",
        "evidence/math/check_set_001.py",
    ]


def test_objective_receipt_inputs_exclude_out_of_repo_tokens():
    out = _plan(
        gate=_objective("python C:/tools/checker.py --flag"),
        accept=False,
        reject=False,
        run_gate=lambda c: _objective_run(),
    )
    # Only the artifact is an input: the absolute token lies outside the repo
    # and the flag names no file (D-Normalize: root-relative, in-repo only).
    assert out.record["gate_run"]["inputs"] == ["evidence/math/set_001.md"]


def test_objective_receipt_hashes_streams_and_never_stores_raw_output():
    stdout = "line one\nline two\n"
    stderr = "warning: deprecation\n"
    out = _plan(
        gate=_objective("python evidence/math/check_set_001.py"),
        accept=False,
        reject=False,
        run_gate=lambda c: _objective_run(stdout=stdout, stderr=stderr),
    )
    receipt = out.record["gate_run"]
    assert receipt["stdout_hash"] == (
        "sha256:" + hashlib.sha256(stdout.encode("utf-8")).hexdigest()
    )
    assert receipt["stderr_hash"] == (
        "sha256:" + hashlib.sha256(stderr.encode("utf-8")).hexdigest()
    )
    # Raw output is never frozen — only hashes cross the boundary (spec §1).
    assert "all checks passed" not in str(receipt)


def test_objective_receipt_silent_run_carries_no_hash_or_tool_keys():
    out = _plan(
        gate=_objective("python evidence/math/check_set_001.py"),
        accept=False,
        reject=False,
        run_gate=lambda c: GateRunResult(exit_code=0),
    )
    receipt = out.record["gate_run"]
    assert "stdout_hash" not in receipt
    assert "stderr_hash" not in receipt
    # tool/version are schema placeholders — never populated in v2.2 (D-Normalize).
    assert "tool" not in receipt and "version" not in receipt


def test_objective_gate_nonzero_receipt_exit_class_failed():
    out = _plan(
        gate=_objective("false"),
        accept=False,
        reject=False,
        run_gate=lambda c: GateRunResult(exit_code=1, stderr="boom\n"),
    )
    receipt = out.record["gate_run"]
    assert receipt["exit_class"] == "failed"
    assert receipt["exit_code"] == 1


def test_receipt_is_omitted_for_manual_records():
    out = _plan()
    assert out.record is not None
    assert "gate_run" not in out.record


def test_gate_unrunnable_writes_no_record_so_no_receipt():
    def _unrunnable(command: str) -> GateRunResult:
        raise GateUnrunnable("spawn failed")

    out = _plan(gate=_objective("no_such_exe"), run_gate=_unrunnable)
    assert out.record is None
    assert out.exit_code != 0


def test_receipt_never_touches_eligibility_warnings():
    # Two identical supersede targets — one carrying a receipt, one not — must
    # produce identical warnings: a receipt is provenance, never a verdict
    # input (spec §1's pinned "eligibility math ignores receipts" test).
    spec = _spec(minimum_count=1)
    with_receipt = dataclasses.replace(
        _record(f"ev.{NODE}.001", accepted=True),
        gate_run={
            "command_argv": ["python", "check.py"],
            "inputs": ["evidence/math/set_001.md"],
            "exit_class": "passed",
            "exit_code": 0,
        },
    )
    plain = _record(f"ev.{NODE}.001", accepted=True)
    out_with = _plan(
        specs_for_node=[spec],
        accept=False,
        reject=True,
        supersedes=f"ev.{NODE}.001",
        supersede_reason="correction",
        existing_records=[with_receipt],
    )
    out_plain = _plan(
        specs_for_node=[spec],
        accept=False,
        reject=True,
        supersedes=f"ev.{NODE}.001",
        supersede_reason="correction",
        existing_records=[plain],
    )
    assert out_with.warnings == out_plain.warnings
