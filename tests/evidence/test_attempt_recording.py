"""Unit tests for the pure `plan_attempt` planner (evidence/attempt_recording.py).

These drive the decision core directly — no disk, no subprocess — so every
branch is deterministic: outcome validation (the only refusal), the gateless and
locked warnings (which never refuse), sequence allocation, and the note being
optional. The wired CLI path (real loaders, real append + audit event) is
covered in test_attempt_command.py.
"""

from __future__ import annotations

import pytest

from skilltrace.evidence.attempt_recording import plan_attempt

NODE = "math.arithmetic.order_operations_01"
NOW = "2026-07-03T12:00:00+00:00"


def _plan(**overrides):
    """Call plan_attempt with sensible passed/gated/available defaults."""
    kwargs = dict(
        node_id=NODE,
        outcome="passed",
        note=None,
        has_gate=True,
        existing_attempt_ids=[],
        node_state="available",
        now=NOW,
    )
    kwargs.update(overrides)
    return plan_attempt(kwargs.pop("node_id"), **kwargs)


# --- Outcome validation: the only refusal ----------------------------------


@pytest.mark.parametrize("outcome", ["passed", "failed"])
def test_both_outcomes_are_recorded(outcome):
    out = plan_attempt(
        NODE,
        outcome=outcome,
        note=None,
        has_gate=True,
        existing_attempt_ids=[],
        node_state="available",
        now=NOW,
    )
    assert out.exit_code == 0
    assert out.record is not None
    assert out.record["outcome"] == outcome
    assert out.records_touched == [out.record["id"]]


def test_unknown_outcome_refuses_writes_nothing():
    out = _plan(outcome="aced")
    assert out.exit_code == 2
    assert out.record is None
    assert out.records_touched == []
    assert out.errors


# --- Warnings never refuse -------------------------------------------------


def test_gateless_node_warns_but_records():
    out = _plan(has_gate=False)
    assert out.exit_code == 0
    assert out.record is not None
    assert any("no gate" in w for w in out.warnings)


def test_locked_node_warns_but_records():
    out = _plan(node_state="locked")
    assert out.exit_code == 0
    assert out.record is not None
    assert any("locked" in w for w in out.warnings)


def test_gated_available_node_has_no_warnings():
    out = _plan()
    assert out.warnings == []


# --- Record shape: id sequence, note, timestamp ----------------------------


def test_id_is_next_sequence_for_the_node():
    out = _plan(existing_attempt_ids=[f"att.{NODE}.001", f"att.{NODE}.002"])
    assert out.record["id"] == f"att.{NODE}.003"


def test_note_is_optional_and_omitted_when_absent():
    out = _plan(note=None)
    assert "note" not in out.record


def test_note_is_recorded_when_present_including_on_failure():
    out = _plan(outcome="failed", note="ran out of time on the last three")
    assert out.record["outcome"] == "failed"
    assert out.record["note"] == "ran out of time on the last three"
    assert out.record["created_at"] == NOW
