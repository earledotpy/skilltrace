"""Unit tests for `plan_pass` — the pure `skilltrace pass` decision.

The wired command is exercised in test_pass_command.py; here we pin the decision
core in isolation: which stored state + eligibility verdict lead to a written
`passed`, and which refuse. No disk, no store — just the pure planner.
"""

from __future__ import annotations

from skilltrace.evidence.eligibility import EligibilityResult, SpecEligibility
from skilltrace.evidence.passing import plan_pass

NODE = "math.arithmetic.order_operations_01"


def _eligible(node_id: str = NODE) -> EligibilityResult:
    return EligibilityResult(
        node_id=node_id,
        eligible=True,
        has_gate=True,
        has_required_spec=True,
        specs=[SpecEligibility(spec_id="spec.x", minimum_count=3, accepted_count=3)],
    )


def _not_eligible(node_id: str = NODE) -> EligibilityResult:
    return EligibilityResult(
        node_id=node_id,
        eligible=False,
        has_gate=True,
        has_required_spec=True,
        specs=[SpecEligibility(spec_id="spec.x", minimum_count=3, accepted_count=1)],
        reasons=["spec spec.x: 1 of 3 required accepted records — below minimum."],
    )


# --- Proceed cases ----------------------------------------------------------


def test_available_and_eligible_proceeds():
    outcome = plan_pass(NODE, current_state="available", eligibility=_eligible())
    assert outcome.proceed is True
    assert outcome.exit_code == 0
    assert outcome.records_touched == [NODE]
    assert not outcome.errors


def test_active_and_eligible_proceeds_skipping_no_step():
    # `active -> passed` is a legal forward move; `active` is not a precondition
    # for passing, but it is also not a blocker.
    outcome = plan_pass(NODE, current_state="active", eligibility=_eligible())
    assert outcome.proceed is True
    assert outcome.exit_code == 0
    assert outcome.records_touched == [NODE]


# --- Refusals ---------------------------------------------------------------


def test_locked_refuses_even_when_eligible():
    outcome = plan_pass(NODE, current_state="locked", eligibility=_eligible())
    assert outcome.proceed is False
    assert outcome.exit_code == 2
    assert outcome.records_touched == []
    assert any("locked" in e for e in outcome.errors)


def test_not_eligible_refuses_and_surfaces_reasons():
    outcome = plan_pass(NODE, current_state="available", eligibility=_not_eligible())
    assert outcome.proceed is False
    assert outcome.exit_code == 2
    assert any("not pass-eligible" in e for e in outcome.errors)
    # The eligibility reasons are carried through so the learner sees why.
    assert any("below minimum" in e for e in outcome.errors)


def test_already_passed_refuses():
    outcome = plan_pass(NODE, current_state="passed", eligibility=_eligible())
    assert outcome.proceed is False
    assert outcome.exit_code == 2
    assert any("passed" in e for e in outcome.errors)


def test_already_mastered_refuses():
    outcome = plan_pass(NODE, current_state="mastered", eligibility=_eligible())
    assert outcome.proceed is False
    assert outcome.exit_code == 2
    assert any("mastered" in e for e in outcome.errors)
