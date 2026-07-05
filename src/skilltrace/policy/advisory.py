"""Advisory policy warnings — warn and reorder, never block (CLAUDE.md).

The warning texts are pure functions of counts the caller supplies; the
loaders here read the workload and remediation seeds and, like cadence,
degrade to "no opinion" when a seed is missing or unreadable — an advisory
policy that cannot be read simply stands down.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..execution.reviews import Review
from .loading import PolicyLoadError, load_policy_doc


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
