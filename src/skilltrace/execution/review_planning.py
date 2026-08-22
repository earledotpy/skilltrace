"""Review planners — schedule / complete / cancel (C2)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base_plan import BasePlan
from .ids import allocate_review_id

_REVIEWABLE = ("passed", "mastered")
_REVIEW_OUTCOMES = ("satisfactory", "unsatisfactory")


@dataclass
class ReviewPlan(BasePlan):
    review: dict | None = None
    # {"review_id": ..., "outcome": ..., "result_summary": ..., "completed_at": ...}
    complete_review: dict | None = None
    # {"review_id": ..., "cancel_reason": ..., "cancelled_at": ...}
    cancel_review: dict | None = None


def _refuse(reason: str) -> ReviewPlan:
    return ReviewPlan(errors=[reason], exit_code=2)


def plan_review_schedule(
    node_id: str,
    *,
    node_state: str,
    date: str | None,
    existing_review_ids: list[str],
    now: str,
) -> ReviewPlan:
    """Schedule a retention check on a passed or mastered node."""
    if node_state not in _REVIEWABLE:
        return _refuse(
            f"{node_id} is {node_state} — a review needs something to retain "
            "(passed or mastered only)."
        )
    if not date:
        return _refuse("scheduling a review requires --date (YYYY-MM-DD).")

    review_id = allocate_review_id(node_id, existing_review_ids)
    return ReviewPlan(
        review={
            "id": review_id,
            "node_id": node_id,
            "status": "scheduled",
            "scheduled_for": date,
            "created_at": now,
        },
        records_touched=[review_id],
        messages=[f"scheduled review {review_id} for {date}."],
    )


def _require_scheduled(review_id: str, review_status: str | None) -> ReviewPlan | None:
    """The shared guard for completing/cancelling: the review must be scheduled."""
    if review_status is None:
        return _refuse(f"review {review_id} does not exist.")
    if review_status != "scheduled":
        return _refuse(f"review {review_id} is already {review_status} — refused.")
    return None


def plan_review_complete(
    review_id: str,
    *,
    review_status: str | None,
    outcome: str | None,
    summary: str | None,
    now: str,
) -> ReviewPlan:
    """Complete one scheduled review; outcome and result summary are required."""
    refusal = _require_scheduled(review_id, review_status)
    if refusal is not None:
        return refusal
    if outcome not in _REVIEW_OUTCOMES:
        return _refuse(
            f"review outcome must be one of {', '.join(_REVIEW_OUTCOMES)}; got {outcome!r}."
        )
    if not summary:
        return _refuse("completing a review requires --summary of the result.")

    return ReviewPlan(
        complete_review={
            "review_id": review_id,
            "outcome": outcome,
            "result_summary": summary,
            "completed_at": now,
        },
        records_touched=[review_id],
        messages=[f"completed review {review_id} ({outcome})."],
    )


def plan_review_cancel(
    review_id: str,
    *,
    review_status: str | None,
    reason: str | None,
    now: str,
) -> ReviewPlan:
    """Cancel one scheduled review — learner-only, reason required, record kept."""
    refusal = _require_scheduled(review_id, review_status)
    if refusal is not None:
        return refusal
    if not reason:
        return _refuse("cancelling a review requires --reason (the record is kept).")

    return ReviewPlan(
        cancel_review={
            "review_id": review_id,
            "cancel_reason": reason,
            "cancelled_at": now,
        },
        records_touched=[review_id],
        messages=[f"cancelled review {review_id}."],
    )
