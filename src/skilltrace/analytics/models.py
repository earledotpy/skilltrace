"""Typed view shapes for the four analytics themes (v1.6).

These dataclasses are the shared contract between the derivation layer
(``derive.py``), the CLI handlers (``commands/analytics.py``), and the
web layer (``GET /analytics``). They carry only plain Python values so
they serialize cleanly to JSON and render trivially to a table.

No I/O, no wall-clock calls — this module is a pure data-shape
declaration.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Velocity
# ---------------------------------------------------------------------------


@dataclass
class WeekBucket:
    """One weekly bucket in the velocity sparkline."""

    label: str          # ISO week label, e.g. "2026-W35"
    session_count: int
    node_count: int     # distinct nodes touched
    minutes: int        # sum of logged minutes


@dataclass
class VelocityResult:
    """Study-velocity theme: session cadence and node-progress over the window.

    ``weeks`` is ordered oldest-first (sparkline order).
    ``sessions_in_window`` drives the soft-threshold check.
    ``is_limited`` is True when ``sessions_in_window < min_sessions_for_full_data``.
    ``group_rows`` is keyed by the chosen group dimension (prefix or track).
    """

    sessions_in_window: int
    nodes_touched: int          # distinct nodes with work items in window
    total_minutes: int          # sum of logged minutes in window
    weeks: list[WeekBucket]     # weekly buckets, oldest first
    group_rows: list[tuple[str, int, int]]  # (group, session_count, node_count)
    is_limited: bool


# ---------------------------------------------------------------------------
# Blockers
# ---------------------------------------------------------------------------


@dataclass
class BlockerRow:
    """One row in the blockers table."""

    node_id: str
    group: str          # prefix or track, depending on --group-by
    description: str
    days_open: int
    status: str         # "open" or "resolved"


@dataclass
class BlockersResult:
    """Blockers theme: active stuckness grouped and sorted by age."""

    open_count: int
    resolved_in_window: int
    rows: list[BlockerRow]      # open blockers sorted by days_open descending
    is_limited: bool


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------


@dataclass
class ReviewRow:
    """One row in the reviews table."""

    node_id: str
    status: str             # "scheduled", "completed", "cancelled"
    scheduled_for: str      # ISO date string
    days_overdue: int       # 0 when not overdue
    outcome: str | None     # "satisfactory" / "unsatisfactory" / None


@dataclass
class ReviewsResult:
    """Reviews theme: completion rate and overdue highlighting."""

    scheduled_count: int
    overdue_count: int
    completed_in_window: int
    completion_rate: float          # completed / (completed + scheduled), or 0.0
    rows: list[ReviewRow]           # scheduled reviews, overdue first
    is_limited: bool


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


@dataclass
class EvidenceRow:
    """One row in the evidence-coverage table."""

    node_id: str
    group: str              # prefix or track
    state: str              # node state from progress store
    spec_count: int         # number of artifact specs
    accepted_count: int     # accepted evidence records
    gap: bool               # True when a required spec has no accepted record


@dataclass
class EvidenceResult:
    """Evidence theme: coverage per node and gap analysis."""

    nodes_with_specs: int
    nodes_with_gaps: int
    coverage_rate: float    # nodes_without_gaps / nodes_with_specs, or 0.0
    rows: list[EvidenceRow]
    is_limited: bool


# ---------------------------------------------------------------------------
# Umbrella
# ---------------------------------------------------------------------------


@dataclass
class AnalyticsView:
    """The full analytics snapshot shared by the umbrella command and export."""

    window_days: int
    group_by: str
    state_filter: list[str]     # empty = all states
    velocity: VelocityResult
    blockers: BlockersResult
    reviews: ReviewsResult
    evidence: EvidenceResult
    is_limited: bool            # True when any theme is limited
    sessions_in_window: int     # convenience copy of velocity.sessions_in_window
    min_sessions_for_full_data: int
