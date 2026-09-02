"""Advisory policy warnings — warn and reorder, never block (AGENTS.md).

The warning texts are pure functions of counts the caller supplies; the
loaders here read the workload and remediation seeds and, like cadence,
degrade to "no opinion" when a seed is missing or unreadable — an advisory
policy that cannot be read simply stands down.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from ..execution.reviews import Review
from .loading import PolicyLoadError, load_policy_doc

if TYPE_CHECKING:
    from ..analytics.models import AnalyticsView


@dataclass
class WorkloadLimit:
    limit_kind: str
    value: int
    warning_threshold: int


def load_workload_limits(root: Path | str) -> dict[str, WorkloadLimit]:
    """The workload seed's limits by kind; malformed rows are skipped."""
    try:
        doc = load_policy_doc(root, "workload.yaml")
    except PolicyLoadError:
        return {}
    limits: dict[str, WorkloadLimit] = {}
    for raw in doc.get("limits") or []:
        if not isinstance(raw, dict):
            continue
        kind, value, threshold = (
            raw.get("limit_kind"),
            raw.get("value"),
            raw.get("warning_threshold"),
        )
        if isinstance(kind, str) and isinstance(value, int) and isinstance(threshold, int):
            limits[kind] = WorkloadLimit(kind, value, threshold)
    return limits


def load_max_open_remediations(root: Path | str) -> int | None:
    try:
        doc = load_policy_doc(root, "remediation.yaml")
    except PolicyLoadError:
        return None
    value = doc.get("max_open_remediations")
    return value if isinstance(value, int) else None


def overdue_review_count(reviews: list[Review], *, today: date) -> int:
    """Overdue is derived, never stored: scheduled and past its date."""
    count = 0
    for review in reviews:
        if review.status != "scheduled":
            continue
        try:
            scheduled = date.fromisoformat(review.scheduled_for)
        except ValueError:
            continue
        if scheduled < today:
            count += 1
    return count


def start_warnings(
    *,
    prospective_active_count: int,
    limits: dict[str, WorkloadLimit],
    overdue_reviews: int,
    open_remediations: int,
    max_open_remediations: int | None,
) -> list[str]:
    """The advisory lines a `start` should print (without the [warning] tag)."""
    warnings: list[str] = []
    limit = limits.get("active_node_count")
    if limit is not None and prospective_active_count >= limit.warning_threshold:
        if prospective_active_count > limit.value:
            warnings.append(
                f"this start makes {prospective_active_count} active nodes — "
                f"over the workload limit of {limit.value}."
            )
        else:
            warnings.append(
                f"this start makes {prospective_active_count} active nodes — "
                f"at or past the workload warning threshold of {limit.warning_threshold}."
            )
    if overdue_reviews > 0:
        warnings.append(
            f"{overdue_reviews} scheduled review(s) overdue — retention work is waiting."
        )
    if max_open_remediations is not None and open_remediations > max_open_remediations:
        warnings.append(
            f"{open_remediations} open remediation actions exceed the advisory "
            f"maximum of {max_open_remediations}."
        )
    return warnings



def analytics_warnings(root: "Path | str", view: "AnalyticsView") -> list[str]:
    """Return advisory warning strings derived from an AnalyticsView.

    Reads the four thresholds locked by G3 from ``policy/analytics.yaml``
    (``advisory_thresholds`` sub-key).  Returns ``[]`` on ``PolicyLoadError``
    — an unreadable policy file simply stands down (same pattern as
    ``load_workload_limits``).

    Threshold semantics:
    - ``velocity_below_target_per_week``   — lower bound (warn when avg < value)
    - ``review_completion_below_target``   — lower bound (warn when rate < value)
    - ``evidence_coverage_below_target``   — lower bound (warn when rate < value)
    - ``blockers_active_threshold``        — upper bound (warn when count >= value)

    Threshold comparison lives here; derivations (``derive.py``) stay pure
    of policy (G6).  This function does not call ``start_warnings()`` or
    any other advisory function — the two coexist independently (G6: "two
    functions, no unifying facade yet").
    """
    try:
        doc = load_policy_doc(root, "analytics.yaml")
    except PolicyLoadError:
        return []

    thresholds = doc.get("advisory_thresholds") or {}
    warnings: list[str] = []

    # --- Velocity: average sessions per week across all weekly buckets -------
    velocity_target = thresholds.get("velocity_below_target_per_week", 2)
    weeks = view.velocity.weeks
    if weeks:
        avg_sessions = sum(w.session_count for w in weeks) / len(weeks)
        if avg_sessions < velocity_target:
            warnings.append(
                f"Study velocity is below target: "
                f"{avg_sessions:.1f} sessions/week average "
                f"(target: {velocity_target})."
            )

    # --- Review completion rate -----------------------------------------------
    review_target = thresholds.get("review_completion_below_target", 0.80)
    if view.reviews.completion_rate < review_target:
        pct_actual = int(view.reviews.completion_rate * 100)
        pct_target = int(review_target * 100)
        warnings.append(
            f"Review completion is below target: "
            f"{pct_actual}% (target: {pct_target}%)."
        )

    # --- Evidence coverage rate -----------------------------------------------
    evidence_target = thresholds.get("evidence_coverage_below_target", 0.60)
    if view.evidence.coverage_rate < evidence_target:
        pct_actual = int(view.evidence.coverage_rate * 100)
        pct_target = int(evidence_target * 100)
        warnings.append(
            f"Evidence coverage is below target: "
            f"{pct_actual}% (target: {pct_target}%)."
        )

    # --- Active blockers ------------------------------------------------------
    blockers_threshold = thresholds.get("blockers_active_threshold", 3)
    if view.blockers.open_count >= blockers_threshold:
        warnings.append(
            f"Active blocker spike: {view.blockers.open_count} open blockers "
            f"(threshold: {blockers_threshold})."
        )

    return warnings
