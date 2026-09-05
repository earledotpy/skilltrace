"""Unit layer for the analytics policy seam (v1.6 G3, spec §3).

Pins the defensive-coercion defaults and the §3.2 value-range checks
owned by ``skilltrace.analytics.policy``. CLI-level refusal (non-zero
exit naming the field) is covered in
``tests/policy/test_validate_policy.py``; this file pins the pure
functions directly.
"""

from __future__ import annotations

import pytest

from skilltrace.analytics.policy import (
    DEFAULT_GROUP_BY,
    DEFAULT_MIN_SESSIONS_FOR_FULL_DATA,
    DEFAULT_WINDOW_DAYS,
    LIMITED_DATA_FOLLOWUP,
    limited_data_head,
    limited_data_sentence,
    resolve_analytics_defaults,
    validate_analytics_policy,
)


def _valid_doc() -> dict:
    return {
        "default_window_days": 30,
        "default_group_by": "prefix",
        "min_sessions_for_full_data": 3,
        "sparkline_bucket": "weekly",
        "advisory_thresholds": {
            "velocity_below_target_per_week": 2,
            "review_completion_below_target": 0.80,
            "evidence_coverage_below_target": 0.60,
            "blockers_active_threshold": 3,
        },
    }


# --- resolve_analytics_defaults: fail open ---------------------------------


def test_resolve_valid_doc_passes_through():
    assert resolve_analytics_defaults(_valid_doc()) == (30, "prefix", 3)


def test_resolve_empty_doc_falls_back_to_defaults():
    assert resolve_analytics_defaults({}) == (
        DEFAULT_WINDOW_DAYS,
        DEFAULT_GROUP_BY,
        DEFAULT_MIN_SESSIONS_FOR_FULL_DATA,
    )


@pytest.mark.parametrize("bad_window", [0, -1, "30", 30.5, True, None])
def test_resolve_bad_window_falls_back(bad_window):
    window, _, _ = resolve_analytics_defaults({**_valid_doc(), "default_window_days": bad_window})
    assert window == DEFAULT_WINDOW_DAYS


@pytest.mark.parametrize("bad_group", ["weekly", "", None, 0, True])
def test_resolve_bad_group_by_falls_back(bad_group):
    _, group_by, _ = resolve_analytics_defaults({**_valid_doc(), "default_group_by": bad_group})
    assert group_by == DEFAULT_GROUP_BY


@pytest.mark.parametrize("bad_min", [0, -2, "3", 2.5, True, None])
def test_resolve_bad_min_sessions_falls_back(bad_min):
    _, _, min_sessions = resolve_analytics_defaults(
        {**_valid_doc(), "min_sessions_for_full_data": bad_min}
    )
    assert min_sessions == DEFAULT_MIN_SESSIONS_FOR_FULL_DATA


# --- validate_analytics_policy: hard errors naming the field ---------------


def test_validate_shipped_seed_is_clean():
    assert validate_analytics_policy(_valid_doc(), "policy/analytics.yaml") == []


@pytest.mark.parametrize(
    "key,bad_value",
    [
        ("default_window_days", 0),
        ("default_window_days", -1),
        ("default_window_days", 366),
        ("default_window_days", "30"),
        ("default_window_days", True),
        ("min_sessions_for_full_data", 0),
        ("min_sessions_for_full_data", -1),
        ("min_sessions_for_full_data", "3"),
    ],
)
def test_validate_top_level_range_violation_names_field(key, bad_value):
    doc = _valid_doc()
    doc[key] = bad_value
    errors = validate_analytics_policy(doc, "policy/analytics.yaml")
    assert len(errors) == 1
    assert key in errors[0]


@pytest.mark.parametrize(
    "key,bad_value",
    [
        ("review_completion_below_target", 0),
        ("review_completion_below_target", 1),
        ("review_completion_below_target", 1.5),
        ("review_completion_below_target", "high"),
        ("evidence_coverage_below_target", 0),
        ("evidence_coverage_below_target", 1),
        ("evidence_coverage_below_target", -0.1),
        ("velocity_below_target_per_week", -1),
        ("velocity_below_target_per_week", "many"),
        ("blockers_active_threshold", -1),
        ("blockers_active_threshold", "few"),
    ],
)
def test_validate_threshold_range_violation_names_field(key, bad_value):
    doc = _valid_doc()
    doc["advisory_thresholds"][key] = bad_value
    errors = validate_analytics_policy(doc, "policy/analytics.yaml")
    assert len(errors) == 1
    assert key in errors[0]


def test_validate_missing_thresholds_mapping_is_an_error():
    doc = _valid_doc()
    del doc["advisory_thresholds"]
    errors = validate_analytics_policy(doc, "policy/analytics.yaml")
    assert len(errors) == 1
    assert "advisory_thresholds" in errors[0]


# --- canonical soft-data wording --------------------------------------------


def test_limited_data_head_matches_spec_section_4_3():
    head = limited_data_head(3, 30)
    assert head == "Limited data — fewer than 3 sessions in the last 30 days."
    assert LIMITED_DATA_FOLLOWUP == "Results may not reflect your full activity."
    assert limited_data_sentence(3, 30) == f"{head} {LIMITED_DATA_FOLLOWUP}"
