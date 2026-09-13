"""Days practiced (v2.4 P1.7) — the derived practice-day count.

A *practiced day* is a distinct calendar day on which the learner logged
study work: a day with at least one session started (``sessions.started_at``)
**or** at least one work item logged (``work.created_at``). Evidence
submissions alone do not count.

It is a mirror, not a metronome (``CONTEXT.md`` *Days practiced*): the count
carries no target, no countdown, no loss framing, and a day without work is
simply absent rather than shown as a break. It never affects eligibility,
ranking, recommendation order, or advisory pressure, and it never appears in
a refusal. Derived on demand from existing execution records — never stored,
never a new record type (no schema change). Calendar days are UTC, matching
the ``execution.overdue.utc_today`` wall-clock funnel.

The days-practiced **heatmap** is a recorded refusal (v2.4 spec §D2): a
density grid is a streak/loss mechanic — exactly what this term refuses to
be — and returns only as a fresh effort that re-opens the preference table.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Iterable


def _record_day(timestamp: str | None) -> date | None:
    """The UTC calendar day of one ISO timestamp, or ``None`` when unusable."""
    if not timestamp:
        return None
    try:
        moment = datetime.fromisoformat(str(timestamp))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).date()


def practiced_days(sessions: Iterable, work_items: Iterable) -> set[date]:
    """The distinct days with logged work across sessions and work items."""
    days: set[date] = set()
    for session in sessions:
        day = _record_day(getattr(session, "started_at", None))
        if day is not None:
            days.add(day)
    for item in work_items:
        day = _record_day(getattr(item, "created_at", None))
        if day is not None:
            days.add(day)
    return days


def days_practiced(sessions: Iterable, work_items: Iterable) -> int:
    """How many distinct days carry logged work (sessions ∪ work items)."""
    return len(practiced_days(sessions, work_items))
