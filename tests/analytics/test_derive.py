"""Unit layer for analytics derivation (T-TestArch D2/D4 — exact values).

Calls derivation functions directly with a frozen ``today`` and hand-built
histories. Pins exact numbers computed from ``policy/analytics.yaml``
thresholds (T-TestArch D3 — no shared fixtures directory, no checked-in YAML).

Policy seed values used throughout (from policy/analytics.yaml):
  default_window_days      = 30
  default_group_by         = prefix
  min_sessions_for_full_data = 3
  advisory_thresholds.velocity_below_target_per_week = 2
  advisory_thresholds.review_completion_below_target = 0.80
  advisory_thresholds.evidence_coverage_below_target = 0.60
  advisory_thresholds.blockers_active_threshold = 3
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from skilltrace.analytics.derive import (
    derive_blockers,
    derive_evidence,
    derive_reviews,
    derive_velocity,
    _iso_week_label,
    _node_prefix,
)


# ---------------------------------------------------------------------------
# Minimal stubs
# ---------------------------------------------------------------------------

class _FakeStore:
    """Minimal ProgressStore stub for derive functions."""

    def __init__(self, state_map: dict[str, str] | None = None):
        self._map = state_map or {}

    def state_of(self, node_id: str) -> str:
        return self._map.get(node_id, "available")


def _session(id: str, started: str, status: str = "completed") -> SimpleNamespace:
    return SimpleNamespace(id=id, started_at=started, status=status, ended_at=None)


def _work(id: str, session_id: str, node_id: str, created: str, minutes: int | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=id, session_id=session_id, node_id=node_id,
        created_at=created, minutes=minutes, blocked=False, notes=None,
    )


def _blocker(id: str, node_id: str, status: str, created: str, resolved_at: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=id, node_id=node_id, status=status,
        description=f"Obstacle on {node_id}",
        created_at=created, resolved_at=resolved_at,
    )


def _review(id: str, node_id: str, status: str, scheduled_for: str,
            completed_at: str | None = None, outcome: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=id, node_id=node_id, status=status,
        scheduled_for=scheduled_for, created_at="2026-08-01",
        completed_at=completed_at, outcome=outcome,
    )


def _spec(id: str, node_id: str, required: bool = True) -> SimpleNamespace:
    return SimpleNamespace(id=id, node_id=node_id, required=required, minimum_count=1)


def _record(id: str, spec_id: str, accepted: bool, supersedes: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=id, artifact_spec_id=spec_id, accepted=accepted,
        supersedes=supersedes, location="path/to/artifact",
    )


def _node(id: str, track: str = "foundational") -> SimpleNamespace:
    return SimpleNamespace(id=id, track=track, title=id)


# Policy seed values matching policy/analytics.yaml
_MIN_SESSIONS = 3
_WINDOW_DAYS = 30
_TODAY = date(2026, 9, 1)


# ---------------------------------------------------------------------------
# Helper: _node_prefix
# ---------------------------------------------------------------------------


def test_node_prefix_two_segments():
    assert _node_prefix("math.arithmetic.order_operations_01") == "math.arithmetic"


def test_node_prefix_one_segment():
    assert _node_prefix("math") == "math"


def test_node_prefix_two_segment_id():
    assert _node_prefix("math.arithmetic") == "math.arithmetic"


# ---------------------------------------------------------------------------
# Helper: _iso_week_label
# ---------------------------------------------------------------------------


def test_iso_week_label_known_date():
    # 2026-09-01 is in ISO week 36 of 2026
    assert _iso_week_label(date(2026, 9, 1)) == "2026-W36"


# ---------------------------------------------------------------------------
# derive_velocity — is_limited threshold
# ---------------------------------------------------------------------------


def test_velocity_limited_below_threshold():
    """At 2 sessions (< 3 = min_sessions_for_full_data), is_limited is True."""
    sessions = [
        _session("s1", "2026-08-20"),
        _session("s2", "2026-08-25"),
    ]
    work = [
        _work("w1", "s1", "math.arithmetic.order_operations_01", "2026-08-20", minutes=30),
        _work("w2", "s2", "math.algebra.variables_01", "2026-08-25", minutes=45),
    ]
    result = derive_velocity(
        sessions, work,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        nodes=[],
        store=_FakeStore(),
        min_sessions_for_full_data=_MIN_SESSIONS,
    )
    assert result.is_limited is True
    assert result.sessions_in_window == 2


def test_velocity_not_limited_at_threshold():
    """At exactly 3 sessions (= min_sessions_for_full_data), is_limited is False."""
    sessions = [
        _session("s1", "2026-08-15"),
        _session("s2", "2026-08-20"),
        _session("s3", "2026-08-25"),
    ]
    work = []
    result = derive_velocity(
        sessions, work,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        nodes=[],
        store=_FakeStore(),
        min_sessions_for_full_data=_MIN_SESSIONS,
    )
    assert result.is_limited is False
    assert result.sessions_in_window == 3


def test_velocity_empty_state():
    """Zero sessions → empty shape, is_limited True."""
    result = derive_velocity(
        [], [],
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        nodes=[],
        store=_FakeStore(),
        min_sessions_for_full_data=_MIN_SESSIONS,
    )
    assert result.sessions_in_window == 0
    assert result.nodes_touched == 0
    assert result.total_minutes == 0
    assert result.group_rows == []
    assert result.is_limited is True


def test_velocity_counts_minutes():
    sessions = [
        _session("s1", "2026-08-20"),
        _session("s2", "2026-08-22"),
        _session("s3", "2026-08-24"),
    ]
    work = [
        _work("w1", "s1", "math.arithmetic.ops_01", "2026-08-20", minutes=30),
        _work("w2", "s2", "math.arithmetic.ops_01", "2026-08-22", minutes=45),
        _work("w3", "s3", "math.algebra.vars_01", "2026-08-24", minutes=60),
    ]
    result = derive_velocity(
        sessions, work,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        nodes=[],
        store=_FakeStore(),
        min_sessions_for_full_data=_MIN_SESSIONS,
    )
    assert result.total_minutes == 135
    assert result.nodes_touched == 2
    assert result.is_limited is False


def test_velocity_state_filter_applied_before_grouping():
    """State filter (OR semantics) excludes nodes not matching."""
    store = _FakeStore({"math.arithmetic.ops_01": "active", "math.algebra.vars_01": "locked"})
    sessions = [
        _session("s1", "2026-08-20"),
        _session("s2", "2026-08-22"),
        _session("s3", "2026-08-24"),
    ]
    work = [
        _work("w1", "s1", "math.arithmetic.ops_01", "2026-08-20", minutes=30),
        _work("w2", "s2", "math.algebra.vars_01", "2026-08-22", minutes=45),
        _work("w3", "s3", "math.arithmetic.ops_01", "2026-08-24", minutes=60),
    ]
    result = derive_velocity(
        sessions, work,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=["active"],  # only active nodes
        nodes=[],
        store=store,
        min_sessions_for_full_data=_MIN_SESSIONS,
    )
    # Only the math.arithmetic work items should be counted
    assert result.nodes_touched == 1
    assert result.total_minutes == 90


def test_velocity_sessions_outside_window_excluded():
    """Sessions starting before the window cutoff are not counted."""
    old_session = _session("s_old", "2026-07-01")  # > 30 days before 2026-09-01
    new_session = _session("s_new", "2026-08-20")
    work = [
        _work("w_old", "s_old", "math.arithmetic.ops_01", "2026-07-01", minutes=60),
        _work("w_new", "s_new", "math.arithmetic.ops_01", "2026-08-20", minutes=30),
    ]
    result = derive_velocity(
        [old_session, new_session], work,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        nodes=[],
        store=_FakeStore(),
        min_sessions_for_full_data=_MIN_SESSIONS,
    )
    assert result.sessions_in_window == 1
    assert result.total_minutes == 30


def test_velocity_group_by_prefix():
    sessions = [_session(f"s{i}", f"2026-08-{i + 10:02d}") for i in range(3)]
    work = [
        _work("w1", "s0", "math.arithmetic.ops_01", "2026-08-10"),
        _work("w2", "s1", "math.arithmetic.fractions_01", "2026-08-11"),
        _work("w3", "s2", "math.algebra.vars_01", "2026-08-12"),
    ]
    result = derive_velocity(
        sessions, work,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        nodes=[],
        store=_FakeStore(),
        min_sessions_for_full_data=_MIN_SESSIONS,
    )
    groups = {r[0] for r in result.group_rows}
    assert "math.arithmetic" in groups
    assert "math.algebra" in groups


# ---------------------------------------------------------------------------
# derive_blockers
# ---------------------------------------------------------------------------


def test_blockers_empty_state():
    result = derive_blockers(
        [],
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        nodes=[],
        store=_FakeStore(),
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=0,
    )
    assert result.open_count == 0
    assert result.resolved_in_window == 0
    assert result.rows == []
    assert result.is_limited is True


def test_blockers_counts_open():
    blockers = [
        _blocker("b1", "math.arithmetic.ops_01", "open", "2026-08-15"),
        _blocker("b2", "math.algebra.vars_01", "open", "2026-08-20"),
    ]
    result = derive_blockers(
        blockers,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        nodes=[],
        store=_FakeStore(),
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    assert result.open_count == 2
    assert result.is_limited is False


def test_blockers_resolved_in_window():
    blockers = [
        _blocker("b1", "math.arithmetic.ops_01", "resolved", "2026-08-01", resolved_at="2026-08-25"),
        _blocker("b2", "math.algebra.vars_01", "resolved", "2026-07-01", resolved_at="2026-07-15"),  # outside window
    ]
    result = derive_blockers(
        blockers,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        nodes=[],
        store=_FakeStore(),
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    assert result.resolved_in_window == 1


def test_blockers_sorted_by_days_open_descending():
    blockers = [
        _blocker("b1", "math.arithmetic.ops_01", "open", "2026-08-25"),   # 7 days
        _blocker("b2", "math.algebra.vars_01", "open", "2026-08-10"),     # 22 days
        _blocker("b3", "prog.python.env_01", "open", "2026-08-20"),       # 12 days
    ]
    result = derive_blockers(
        blockers,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        nodes=[],
        store=_FakeStore(),
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    days = [r.days_open for r in result.rows]
    assert days == sorted(days, reverse=True)


def test_blockers_state_filter():
    store = _FakeStore({
        "math.arithmetic.ops_01": "active",
        "math.algebra.vars_01": "locked",
    })
    blockers = [
        _blocker("b1", "math.arithmetic.ops_01", "open", "2026-08-20"),
        _blocker("b2", "math.algebra.vars_01", "open", "2026-08-22"),
    ]
    result = derive_blockers(
        blockers,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=["active"],
        nodes=[],
        store=store,
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    assert result.open_count == 1
    assert result.rows[0].node_id == "math.arithmetic.ops_01"


def test_blockers_limited_flag():
    """is_limited derived from sessions_in_window vs min_sessions_for_full_data."""
    result_limited = derive_blockers(
        [],
        today=_TODAY, window_days=_WINDOW_DAYS, group_by="prefix",
        state_filter=[], nodes=[], store=_FakeStore(),
        min_sessions_for_full_data=3, sessions_in_window=2,
    )
    result_ok = derive_blockers(
        [],
        today=_TODAY, window_days=_WINDOW_DAYS, group_by="prefix",
        state_filter=[], nodes=[], store=_FakeStore(),
        min_sessions_for_full_data=3, sessions_in_window=3,
    )
    assert result_limited.is_limited is True
    assert result_ok.is_limited is False


# ---------------------------------------------------------------------------
# derive_reviews
# ---------------------------------------------------------------------------


def test_reviews_empty_state():
    result = derive_reviews(
        [], [],
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=0,
        store=_FakeStore(),
    )
    assert result.scheduled_count == 0
    assert result.overdue_count == 0
    assert result.completed_in_window == 0
    assert result.completion_rate == 0.0
    assert result.is_limited is True


def test_reviews_overdue_detection():
    reviews = [
        _review("r1", "math.arithmetic.ops_01", "scheduled", "2026-08-01"),  # overdue
        _review("r2", "math.algebra.vars_01", "scheduled", "2026-09-15"),    # future
    ]
    result = derive_reviews(
        reviews, [],
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
        store=_FakeStore(),
    )
    assert result.overdue_count == 1
    assert result.scheduled_count == 2
    assert result.rows[0].days_overdue == 31   # 2026-09-01 - 2026-08-01


def test_reviews_completion_rate_exact():
    """2 completed in window, 1 still scheduled → rate = 2/3 ≈ 0.667."""
    reviews = [
        _review("r1", "math.arithmetic.ops_01", "completed", "2026-08-01",
                completed_at="2026-08-20", outcome="satisfactory"),
        _review("r2", "math.algebra.vars_01", "completed", "2026-08-05",
                completed_at="2026-08-25", outcome="satisfactory"),
        _review("r3", "prog.python.env_01", "scheduled", "2026-09-10"),
    ]
    result = derive_reviews(
        reviews, [],
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
        store=_FakeStore(),
    )
    assert result.completed_in_window == 2
    assert result.scheduled_count == 1
    assert pytest.approx(result.completion_rate, abs=0.01) == 2 / 3


def test_reviews_completed_outside_window_not_counted():
    reviews = [
        _review("r1", "math.arithmetic.ops_01", "completed", "2026-07-01",
                completed_at="2026-07-10", outcome="satisfactory"),  # outside window
    ]
    result = derive_reviews(
        reviews, [],
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
        store=_FakeStore(),
    )
    assert result.completed_in_window == 0


def test_reviews_overdue_first_in_rows():
    """Overdue rows come first, sorted most-overdue first."""
    reviews = [
        _review("r1", "n.a.01", "scheduled", "2026-09-10"),   # future
        _review("r2", "n.b.01", "scheduled", "2026-08-01"),   # 31 days overdue
        _review("r3", "n.c.01", "scheduled", "2026-08-20"),   # 12 days overdue
    ]
    result = derive_reviews(
        reviews, [],
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
        store=_FakeStore(),
    )
    assert result.rows[0].days_overdue == 31
    assert result.rows[1].days_overdue == 12
    assert result.rows[2].days_overdue == 0


# ---------------------------------------------------------------------------
# derive_evidence
# ---------------------------------------------------------------------------


def test_evidence_empty_state():
    result = derive_evidence(
        [], [], [], _FakeStore(),
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=0,
    )
    assert result.nodes_with_specs == 0
    assert result.nodes_with_gaps == 0
    assert result.coverage_rate == 0.0
    assert result.rows == []
    assert result.is_limited is True


def test_evidence_gap_detection():
    """Node with required spec and no accepted record is a gap."""
    nodes = [_node("math.arithmetic.ops_01")]
    specs = [_spec("spec.math.ops", "math.arithmetic.ops_01", required=True)]
    records = []  # no accepted record
    result = derive_evidence(
        specs, records, nodes, _FakeStore(),
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    assert result.nodes_with_gaps == 1
    assert result.rows[0].gap is True
    assert result.coverage_rate == 0.0


def test_evidence_no_gap_when_accepted():
    """Node with accepted evidence record has no gap."""
    nodes = [_node("math.arithmetic.ops_01")]
    specs = [_spec("spec.math.ops", "math.arithmetic.ops_01", required=True)]
    records = [_record("ev.001", "spec.math.ops", accepted=True)]
    result = derive_evidence(
        specs, records, nodes, _FakeStore(),
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    assert result.nodes_with_gaps == 0
    assert result.rows[0].gap is False
    assert result.coverage_rate == 1.0


def test_evidence_superseded_record_not_counted():
    """A superseded accepted record should not count toward coverage."""
    nodes = [_node("math.arithmetic.ops_01")]
    specs = [_spec("spec.math.ops", "math.arithmetic.ops_01", required=True)]
    records = [
        _record("ev.001", "spec.math.ops", accepted=True, supersedes=None),
        _record("ev.002", "spec.math.ops", accepted=True, supersedes="ev.001"),
    ]
    # ev.001 is superseded by ev.002; only ev.002 is live
    result = derive_evidence(
        specs, records, nodes, _FakeStore(),
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    assert result.nodes_with_gaps == 0
    assert result.rows[0].accepted_count == 1


def test_evidence_optional_spec_gap_not_counted():
    """Optional spec with no record does NOT create a gap."""
    nodes = [_node("math.arithmetic.ops_01")]
    specs = [_spec("spec.math.ops", "math.arithmetic.ops_01", required=False)]
    records = []
    result = derive_evidence(
        specs, records, nodes, _FakeStore(),
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    assert result.nodes_with_gaps == 0
    assert result.coverage_rate == 1.0


def test_evidence_coverage_rate_exact():
    """2 of 3 nodes have gaps → coverage_rate = 1/3."""
    nodes = [_node("math.arithmetic.a_01"), _node("math.arithmetic.b_01"), _node("math.algebra.c_01")]
    specs = [
        _spec("spec.a", "math.arithmetic.a_01", required=True),
        _spec("spec.b", "math.arithmetic.b_01", required=True),
        _spec("spec.c", "math.algebra.c_01", required=True),
    ]
    records = [_record("ev.001", "spec.a", accepted=True)]  # only one node covered
    result = derive_evidence(
        specs, records, nodes, _FakeStore(),
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    assert result.nodes_with_specs == 3
    assert result.nodes_with_gaps == 2
    assert pytest.approx(result.coverage_rate, abs=0.01) == 1 / 3


def test_evidence_state_filter():
    """State filter excludes nodes not matching."""
    store = _FakeStore({"math.arithmetic.ops_01": "locked", "math.algebra.vars_01": "active"})
    nodes = [_node("math.arithmetic.ops_01"), _node("math.algebra.vars_01")]
    specs = [
        _spec("spec.ops", "math.arithmetic.ops_01", required=True),
        _spec("spec.vars", "math.algebra.vars_01", required=True),
    ]
    records = []
    result = derive_evidence(
        specs, records, nodes, store,
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=["active"],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    assert result.nodes_with_specs == 1
    assert result.rows[0].node_id == "math.algebra.vars_01"


def test_evidence_gaps_first_in_rows():
    """Rows with gaps sort before rows without."""
    nodes = [_node("math.arithmetic.a_01"), _node("math.arithmetic.b_01")]
    specs = [
        _spec("spec.a", "math.arithmetic.a_01", required=True),
        _spec("spec.b", "math.arithmetic.b_01", required=True),
    ]
    records = [_record("ev.001", "spec.b", accepted=True)]
    result = derive_evidence(
        specs, records, nodes, _FakeStore(),
        today=_TODAY,
        window_days=_WINDOW_DAYS,
        group_by="prefix",
        state_filter=[],
        min_sessions_for_full_data=_MIN_SESSIONS,
        sessions_in_window=3,
    )
    assert result.rows[0].gap is True
    assert result.rows[1].gap is False
