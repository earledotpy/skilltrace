"""`retention_model` — pure derivation unit tests (Tier 2 spec §6.3).

This file is the executable spec for the decay math and the policy seed
(``h = 7, ×2.0 / ÷0.5, attention_threshold = 0.5``). It calls the pure
function directly with a frozen ``today`` and hand-built review histories;
no CLI, no module-level clock, no fixtures directory.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from skilltrace.execution.reviews import Review
from skilltrace.policy.retention_model import (
    RetentionPolicySeed,
    compute_memory_state,
    retention_seed_from_doc,
)

NODE = "math.arithmetic.subject_node_01"
PASS_DATE = date(2026, 7, 1)

SEED = RetentionPolicySeed(
    default_half_life_days=7.0,
    satisfactory_growth_factor=2.0,
    unsatisfactory_reduction_factor=0.5,
    attention_threshold=0.5,
)


def _completed(
    review_id: str,
    completed_on: date,
    outcome: str,
) -> Review:
    return Review(
        id=review_id,
        node_id=NODE,
        status="completed",
        scheduled_for=completed_on.isoformat(),
        created_at=completed_on.isoformat() + "T10:00:00+00:00",
        completed_at=completed_on.isoformat() + "T10:00:00+00:00",
        outcome=outcome,
        result_summary="recall log",
    )


def _cancelled(review_id: str, scheduled_on: date) -> Review:
    return Review(
        id=review_id,
        node_id=NODE,
        status="cancelled",
        scheduled_for=scheduled_on.isoformat(),
        created_at=scheduled_on.isoformat() + "T10:00:00+00:00",
        cancelled_at=scheduled_on.isoformat() + "T10:00:00+00:00",
        cancel_reason="re-scheduled",
    )


# --- R(t) = 0.5^(t/h) at t = 0, h/2, h, 2h ----------------------------------


def test_t_zero_after_one_growth_yields_full_confidence():
    """Anchor day, one satisfactory growth: h=14, t=0, R=1.0, suggested=+14d."""
    review_on = PASS_DATE + timedelta(days=2)
    state = compute_memory_state(
        NODE,
        asserted_state="passed",
        pass_at=PASS_DATE,
        reviews=[_completed("rev.001", review_on, "satisfactory")],
        seed=SEED,
        today=review_on,
    )
    assert state.half_life_days == pytest.approx(14.0)
    assert state.confidence == pytest.approx(1.0)
    assert state.suggested_next_review == review_on + timedelta(days=14)
    assert state.anchor_kind == "last_completed_review"
    assert state.anchored_at == review_on


@pytest.mark.parametrize(
    "elapsed_days,expected_confidence",
    [
        (0, 1.0),  # R(0) = 1
        (3, 0.5 ** (3 / 14.0)),  # 3 days past 1-growth anchor (h=14)
        (7, 0.5),  # R(7) at default h=7
        (14, 0.25),  # R(2h) = 0.25
    ],
    ids=["t_zero", "t_three_of_h14", "t_h_at_h7", "t_2h"],
)
def test_r_at_known_t_over_h(elapsed_days, expected_confidence):
    """Sweep R(t) = 0.5^(t/h) at the textbook anchor points.

    All cases use the no-reviews path (anchor = pass date, h = 7) except `t=3
    of h=14`, which anchors on a one-growth completed review that doubled h to
    14 — the spec's headline example (issue #49 §6.3).
    """
    if elapsed_days == 3:
        review_on = PASS_DATE + timedelta(days=2)
        state = compute_memory_state(
            NODE,
            asserted_state="passed",
            pass_at=PASS_DATE,
            reviews=[_completed("rev.001", review_on, "satisfactory")],
            seed=SEED,
            today=review_on + timedelta(days=elapsed_days),
        )
    else:
        today = PASS_DATE + timedelta(days=elapsed_days)
        state = compute_memory_state(
            NODE,
            asserted_state="passed",
            pass_at=PASS_DATE,
            reviews=[],
            seed=SEED,
            today=today,
        )
    assert state.confidence == pytest.approx(expected_confidence, abs=1e-12)


# --- Unsatisfactory: multiplicative reduction, never reset, never demote ---


def test_unsatisfactory_multiplies_half_life_and_recomputes_confidence():
    """One unsatisfactory on a fresh node halves the default h=7 to 3.5."""
    review_on = PASS_DATE + timedelta(days=1)
    today = review_on  # t=0 from the completed review
    state = compute_memory_state(
        NODE,
        asserted_state="passed",
        pass_at=PASS_DATE,
        reviews=[_completed("rev.001", review_on, "unsatisfactory")],
        seed=SEED,
        today=today,
    )
    assert state.half_life_days == pytest.approx(3.5)
    assert state.confidence == pytest.approx(1.0)
    assert state.suggested_next_review == review_on + timedelta(days=3)  # floor


def test_unsatisfactory_followed_by_satisfactory_grows_back_without_reset():
    """Order matters: ×0.5 then ×2.0 → h = 7.0 (no reset; growth from the reduced value)."""
    unsat_on = PASS_DATE + timedelta(days=1)
    sat_on = unsat_on + timedelta(days=4)
    state = compute_memory_state(
        NODE,
        asserted_state="passed",
        pass_at=PASS_DATE,
        reviews=[
            _completed("rev.001", unsat_on, "unsatisfactory"),
            _completed("rev.002", sat_on, "satisfactory"),
        ],
        seed=SEED,
        today=sat_on,
    )
    assert state.anchor_kind == "last_completed_review"
    assert state.anchored_at == sat_on
    assert state.half_life_days == pytest.approx(7.0)  # 7 → 3.5 → 7
    assert state.confidence == pytest.approx(1.0)


# --- Cancelled-only fallback -----------------------------------------------


def test_cancelled_only_reviews_anchor_on_pass_date():
    """No completed reviews after pass → anchor on pass date at default h."""
    today = PASS_DATE + timedelta(days=4)
    state = compute_memory_state(
        NODE,
        asserted_state="passed",
        pass_at=PASS_DATE,
        reviews=[_cancelled("rev.001", PASS_DATE + timedelta(days=1))],
        seed=SEED,
        today=today,
    )
    assert state.anchor_kind == "pass"
    assert state.anchored_at == PASS_DATE
    assert state.half_life_days == pytest.approx(7.0)
    # 4 days from pass at h=7 → 0.5^(4/7)
    assert state.confidence == pytest.approx(0.5 ** (4 / 7.0), abs=1e-12)


# --- Empty case ------------------------------------------------------------


def test_passed_node_with_no_reviews_anchors_on_pass_date():
    today = PASS_DATE + timedelta(days=7)
    state = compute_memory_state(
        NODE,
        asserted_state="passed",
        pass_at=PASS_DATE,
        reviews=[],
        seed=SEED,
        today=today,
    )
    assert state.anchor_kind == "pass"
    assert state.anchored_at == PASS_DATE
    assert state.half_life_days == pytest.approx(7.0)
    assert state.confidence == pytest.approx(0.5)
    assert state.suggested_next_review == PASS_DATE + timedelta(days=7)


# --- Below threshold gating ------------------------------------------------


def test_below_threshold_flag_when_confidence_drops_below_0_5():
    today = PASS_DATE + timedelta(days=8)  # 0.5^(8/7) ≈ 0.45
    state = compute_memory_state(
        NODE,
        asserted_state="passed",
        pass_at=PASS_DATE,
        reviews=[],
        seed=SEED,
        today=today,
    )
    assert state.confidence < 0.5
    assert state.below_threshold is True


def test_above_threshold_when_just_anchored():
    today = PASS_DATE
    state = compute_memory_state(
        NODE,
        asserted_state="passed",
        pass_at=PASS_DATE,
        reviews=[],
        seed=SEED,
        today=today,
    )
    assert state.confidence == pytest.approx(1.0)
    assert state.below_threshold is False


def test_suggestion_date_arriving_triggers_below_threshold():
    """At the suggested date, the suggestion is due even if confidence is just at 0.5."""
    state = compute_memory_state(
        NODE,
        asserted_state="passed",
        pass_at=PASS_DATE,
        reviews=[],
        seed=SEED,
        today=PASS_DATE + timedelta(days=7),
    )
    assert state.suggested_next_review == PASS_DATE + timedelta(days=7)
    assert state.below_threshold is True


# --- Seed materialization --------------------------------------------------


def test_retention_seed_from_doc_constructs_typed_object():
    doc = {
        "default_half_life_days": 7,
        "satisfactory_growth_factor": 2.0,
        "unsatisfactory_reduction_factor": 0.5,
        "attention_threshold": 0.5,
    }
    seed = retention_seed_from_doc(doc)
    assert seed.default_half_life_days == 7.0
    assert seed.satisfactory_growth_factor == 2.0
    assert seed.unsatisfactory_reduction_factor == 0.5
    assert seed.attention_threshold == 0.5


# --- Determinism / clock-injection contract --------------------------------


def test_today_argument_is_the_only_clock():
    """The pure function must take ``today`` and not consult the wall clock."""
    fixed = date(2026, 8, 1)
    a = compute_memory_state(
        NODE, asserted_state="passed", pass_at=PASS_DATE, reviews=[],
        seed=SEED, today=fixed,
    )
    # Calling with the same frozen date twice is identical.
    b = compute_memory_state(
        NODE, asserted_state="passed", pass_at=PASS_DATE, reviews=[],
        seed=SEED, today=fixed,
    )
    assert a == b
    assert a.anchored_at == PASS_DATE
    assert a.confidence == pytest.approx(0.5 ** ((fixed - PASS_DATE).days / 7.0))
