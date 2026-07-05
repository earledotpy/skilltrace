"""Reviews (`execution/reviews.yaml`).

A Review is a scheduled retention check on a passed or mastered node.
Lifecycle: scheduled -> completed (outcome + result summary) or cancelled
(learner-only, reason required — the record stays as honest history).
Overdue is derived (scheduled and past its date), never stored (CONTEXT.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._store import ExecutionLoadError, append_record, read_records, write_records

_REVIEWS_RELPATH = Path("execution") / "reviews.yaml"
_TOP_KEY = "reviews"
_KIND = "review"

STATUSES = ("scheduled", "completed", "cancelled")
OUTCOMES = ("satisfactory", "unsatisfactory")


@dataclass
class Review:
    id: str
    node_id: str
    status: str
    scheduled_for: str
    created_at: str
    completed_at: str | None = None
    outcome: str | None = None
    result_summary: str | None = None
    cancelled_at: str | None = None
    cancel_reason: str | None = None


def load_reviews(root: Path | str) -> list[Review]:
    """Load and shape-check every review; missing file -> empty history."""
    reviews: list[Review] = []
    raw = read_records(root, _REVIEWS_RELPATH, top_key=_TOP_KEY, kind=_KIND)
    path = Path(root) / _REVIEWS_RELPATH
    for index, data in enumerate(raw):
        if not isinstance(data, dict):
            raise ExecutionLoadError(f"{path}: review #{index} is not a mapping.")
        for field in ("id", "node_id", "status", "scheduled_for", "created_at"):
            if field not in data:
                raise ExecutionLoadError(
                    f"{path}: review #{index} is missing required field {field!r}."
                )
        if data["status"] not in STATUSES:
            raise ExecutionLoadError(
                f"{path}: review {data['id']!r} has invalid status {data['status']!r} "
                f"— expected one of {', '.join(STATUSES)}."
            )
        reviews.append(
            Review(
                id=str(data["id"]),
                node_id=str(data["node_id"]),
                status=str(data["status"]),
                scheduled_for=str(data["scheduled_for"]),
                created_at=str(data["created_at"]),
                completed_at=data.get("completed_at"),
                outcome=data.get("outcome"),
                result_summary=data.get("result_summary"),
                cancelled_at=data.get("cancelled_at"),
                cancel_reason=data.get("cancel_reason"),
            )
        )
    return reviews


def append_review(root: Path | str, record: dict) -> None:
    append_record(root, _REVIEWS_RELPATH, top_key=_TOP_KEY, kind=_KIND, record=record)


def _update_review(root: Path | str, review_id: str, fields: dict) -> None:
    records = read_records(root, _REVIEWS_RELPATH, top_key=_TOP_KEY, kind=_KIND)
    for record in records:
        if isinstance(record, dict) and record.get("id") == review_id:
            record.update(fields)
            break
    else:
        raise ExecutionLoadError(f"review {review_id!r} not found.")
    write_records(root, _REVIEWS_RELPATH, top_key=_TOP_KEY, records=records)


def complete_review(
    root: Path | str, review_id: str, *, outcome: str, result_summary: str, completed_at: str
) -> None:
    """Flip one review `scheduled -> completed` with outcome and summary."""
    _update_review(
        root,
        review_id,
        {
            "status": "completed",
            "outcome": outcome,
            "result_summary": result_summary,
            "completed_at": completed_at,
        },
    )


def cancel_review(
    root: Path | str, review_id: str, *, cancel_reason: str, cancelled_at: str
) -> None:
    """Flip one review `scheduled -> cancelled`; the record stays as history."""
    _update_review(
        root,
        review_id,
        {"status": "cancelled", "cancel_reason": cancel_reason, "cancelled_at": cancelled_at},
    )
