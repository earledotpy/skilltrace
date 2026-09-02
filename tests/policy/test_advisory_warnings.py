"""Advisory warnings on `start` — warn at the moment of taking on work.

Workload pressure (active-node count), overdue reviews, and a remediation
backlog over the advisory maximum each print a `[warning]` line, and none
of them ever blocks the start (advisory policies never block a
human-initiated action).
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.events import load_events

from .conftest import NODE, _write_yaml

BUSY_A = "testing.policy.busy_node_01"
BUSY_B = "testing.policy.busy_node_02"


def _pile_on_pressure(root) -> None:
    """Two nodes already active, one overdue review, six open remediations."""
    _write_yaml(
        root,
        "graph/state.yaml",
        {
            "progress": {
                NODE: {"state": "available", "changed_at": "2026-07-01T10:00:00+00:00"},
                BUSY_A: {"state": "active", "changed_at": "2026-07-01T10:00:00+00:00"},
                BUSY_B: {"state": "active", "changed_at": "2026-07-01T10:00:00+00:00"},
            }
        },
    )
    _write_yaml(
        root,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": f"rev.{BUSY_A}.001",
                    "node_id": BUSY_A,
                    "status": "scheduled",
                    "scheduled_for": "2026-01-01",
                    "created_at": "2025-12-31T10:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        root,
        "execution/remediation_actions.yaml",
        {
            "remediation_actions": [
                {
                    "id": f"rem.{BUSY_A}.{n:03d}",
                    "node_id": BUSY_A,
                    "status": "open",
                    "description": "redo the drills",
                    "created_at": "2026-07-01T10:00:00+00:00",
                }
                for n in range(1, 7)
            ]
        },
    )


def test_start_warns_on_every_advisory_pressure_but_proceeds(mastery_repo, capsys):
    root = mastery_repo(state="available", passed_at=None)
    _pile_on_pressure(root)

    rc = cli.run(["start", NODE], root=root)
    assert rc == 0  # advisory warnings never block a human-initiated action

    out = capsys.readouterr().out
    warnings = [line for line in out.splitlines() if line.startswith("[warning]")]
    assert any("active" in w for w in warnings)
    assert any("overdue" in w for w in warnings)
    assert any("remediation" in w for w in warnings)

    # The start itself went through untouched: session opened, one audit event.
    events = load_events(root)
    assert len(events) == 1
    assert events[0]["command"] == "start"


def test_start_without_pressure_prints_no_warnings(mastery_repo, capsys):
    root = mastery_repo(state="available", passed_at=None)

    rc = cli.run(["start", NODE], root=root)
    assert rc == 0
    assert "[warning]" not in capsys.readouterr().out


def test_missing_policy_seeds_degrade_to_silence(mastery_repo, capsys):
    root = mastery_repo(state="available", passed_at=None)
    _pile_on_pressure(root)
    (root / "policy" / "workload.yaml").unlink()
    (root / "policy" / "remediation.yaml").unlink()

    rc = cli.run(["start", NODE], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    warnings = [line for line in out.splitlines() if line.startswith("[warning]")]
    # The review backlog needs no policy file; the workload and remediation
    # advisories quietly stand down without their seeds.
    assert not any("active" in w for w in warnings)
    assert not any("remediation" in w for w in warnings)



# ---------------------------------------------------------------------------
# analytics_warnings() — threshold math, empty inputs, PolicyLoadError path
# (T-TestArch D2 + D5, issue #129)
# ---------------------------------------------------------------------------

from datetime import date

from skilltrace.analytics.models import (
    AnalyticsView,
    BlockersResult,
    EvidenceResult,
    ReviewsResult,
    VelocityResult,
    WeekBucket,
)
from skilltrace.policy.advisory import analytics_warnings


# --- Helpers -----------------------------------------------------------------

_ONE_WEEK = [WeekBucket(label="2026-W35", session_count=0, node_count=0, minutes=0)]
_THREE_WEEKS_ACTIVE = [
    WeekBucket(label="2026-W33", session_count=3, node_count=2, minutes=90),
    WeekBucket(label="2026-W34", session_count=3, node_count=2, minutes=90),
    WeekBucket(label="2026-W35", session_count=3, node_count=2, minutes=90),
]


def _make_view(
    *,
    weeks: list | None = None,
    open_blockers: int = 0,
    completion_rate: float = 1.0,
    coverage_rate: float = 1.0,
) -> AnalyticsView:
    """Build a minimal AnalyticsView with the given metric values."""
    wks = weeks if weeks is not None else _ONE_WEEK
    velocity = VelocityResult(
        sessions_in_window=sum(w.session_count for w in wks),
        nodes_touched=0,
        total_minutes=0,
        weeks=wks,
        group_rows=[],
        is_limited=False,
    )
    blockers = BlockersResult(
        open_count=open_blockers,
        resolved_in_window=0,
        rows=[],
        is_limited=False,
    )
    reviews = ReviewsResult(
        scheduled_count=0,
        overdue_count=0,
        completed_in_window=0,
        completion_rate=completion_rate,
        rows=[],
        is_limited=False,
    )
    evidence = EvidenceResult(
        nodes_with_specs=10,
        nodes_with_gaps=max(0, 10 - int(coverage_rate * 10)),
        coverage_rate=coverage_rate,
        rows=[],
        is_limited=False,
    )
    return AnalyticsView(
        window_days=30,
        group_by="prefix",
        state_filter=[],
        velocity=velocity,
        blockers=blockers,
        reviews=reviews,
        evidence=evidence,
        is_limited=False,
        sessions_in_window=velocity.sessions_in_window,
        min_sessions_for_full_data=3,
    )


# --- No warnings when all metrics are above threshold -----------------------


def test_analytics_warnings_no_warnings_when_all_healthy(policy_repo):
    view = _make_view(
        weeks=_THREE_WEEKS_ACTIVE,   # avg 3 sessions/week >= target 2
        open_blockers=0,             # < threshold 3
        completion_rate=1.0,         # >= 0.80
        coverage_rate=1.0,           # >= 0.60
    )
    assert analytics_warnings(policy_repo, view) == []


# --- Velocity threshold -------------------------------------------------------


def test_analytics_warnings_velocity_below_target(policy_repo):
    # avg sessions/week = 1.0 < target 2
    low_weeks = [
        WeekBucket(label="2026-W33", session_count=1, node_count=1, minutes=30),
        WeekBucket(label="2026-W34", session_count=1, node_count=1, minutes=30),
        WeekBucket(label="2026-W35", session_count=1, node_count=1, minutes=30),
    ]
    view = _make_view(weeks=low_weeks, completion_rate=1.0, coverage_rate=1.0)
    warnings = analytics_warnings(policy_repo, view)
    assert any("velocity" in w.lower() for w in warnings)
    assert any("below target" in w.lower() for w in warnings)


def test_analytics_warnings_velocity_exactly_at_target_no_warning(policy_repo):
    # avg = 2.0 — exactly at target, should NOT warn
    at_target_weeks = [
        WeekBucket(label="2026-W33", session_count=2, node_count=1, minutes=60),
        WeekBucket(label="2026-W34", session_count=2, node_count=1, minutes=60),
    ]
    view = _make_view(weeks=at_target_weeks, completion_rate=1.0, coverage_rate=1.0)
    warnings = analytics_warnings(policy_repo, view)
    assert not any("velocity" in w.lower() for w in warnings)


def test_analytics_warnings_empty_weeks_no_velocity_warning(policy_repo):
    # No weekly buckets at all → no avg to compare; no velocity warning
    view = _make_view(weeks=[], completion_rate=1.0, coverage_rate=1.0)
    warnings = analytics_warnings(policy_repo, view)
    assert not any("velocity" in w.lower() for w in warnings)


# --- Review completion threshold ----------------------------------------------


def test_analytics_warnings_review_completion_below_target(policy_repo):
    # 0.50 < target 0.80
    view = _make_view(weeks=_THREE_WEEKS_ACTIVE, completion_rate=0.50, coverage_rate=1.0)
    warnings = analytics_warnings(policy_repo, view)
    assert any("review" in w.lower() for w in warnings)
    assert any("below target" in w.lower() for w in warnings)


def test_analytics_warnings_review_completion_at_target_no_warning(policy_repo):
    # 0.80 == target — should NOT warn
    view = _make_view(weeks=_THREE_WEEKS_ACTIVE, completion_rate=0.80, coverage_rate=1.0)
    warnings = analytics_warnings(policy_repo, view)
    assert not any("review" in w.lower() for w in warnings)


# --- Evidence coverage threshold ----------------------------------------------


def test_analytics_warnings_evidence_coverage_below_target(policy_repo):
    # 0.40 < target 0.60
    view = _make_view(weeks=_THREE_WEEKS_ACTIVE, completion_rate=1.0, coverage_rate=0.40)
    warnings = analytics_warnings(policy_repo, view)
    assert any("evidence" in w.lower() for w in warnings)
    assert any("below target" in w.lower() for w in warnings)


def test_analytics_warnings_evidence_coverage_at_target_no_warning(policy_repo):
    # 0.60 == target — should NOT warn
    view = _make_view(weeks=_THREE_WEEKS_ACTIVE, completion_rate=1.0, coverage_rate=0.60)
    warnings = analytics_warnings(policy_repo, view)
    assert not any("evidence" in w.lower() for w in warnings)


# --- Blockers threshold -------------------------------------------------------


def test_analytics_warnings_blockers_at_threshold(policy_repo):
    # 3 >= threshold 3 → warn
    view = _make_view(weeks=_THREE_WEEKS_ACTIVE, open_blockers=3, completion_rate=1.0, coverage_rate=1.0)
    warnings = analytics_warnings(policy_repo, view)
    assert any("blocker" in w.lower() for w in warnings)


def test_analytics_warnings_blockers_above_threshold(policy_repo):
    view = _make_view(weeks=_THREE_WEEKS_ACTIVE, open_blockers=5, completion_rate=1.0, coverage_rate=1.0)
    warnings = analytics_warnings(policy_repo, view)
    assert any("blocker" in w.lower() for w in warnings)


def test_analytics_warnings_blockers_below_threshold_no_warning(policy_repo):
    # 2 < threshold 3 → no warning
    view = _make_view(weeks=_THREE_WEEKS_ACTIVE, open_blockers=2, completion_rate=1.0, coverage_rate=1.0)
    warnings = analytics_warnings(policy_repo, view)
    assert not any("blocker" in w.lower() for w in warnings)


# --- Multiple thresholds fire at once ----------------------------------------


def test_analytics_warnings_multiple_thresholds_all_fire(policy_repo):
    low_weeks = [WeekBucket(label="2026-W35", session_count=0, node_count=0, minutes=0)]
    view = _make_view(
        weeks=low_weeks,
        open_blockers=4,
        completion_rate=0.30,
        coverage_rate=0.20,
    )
    warnings = analytics_warnings(policy_repo, view)
    assert len(warnings) == 4  # velocity + reviews + evidence + blockers


# --- PolicyLoadError degrades to [] ------------------------------------------


def test_analytics_warnings_missing_policy_file_returns_empty(tmp_path):
    # No analytics.yaml in policy/ → PolicyLoadError → []
    (tmp_path / "policy").mkdir()
    view = _make_view(
        weeks=[WeekBucket(label="2026-W35", session_count=0, node_count=0, minutes=0)],
        open_blockers=5,
        completion_rate=0.0,
        coverage_rate=0.0,
    )
    assert analytics_warnings(tmp_path, view) == []
