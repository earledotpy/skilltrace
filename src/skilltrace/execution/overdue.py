"""Overdue reviews — one seam for the seven duplicated derivation sites.

The seven "is this review overdue?" call sites (`commands/today.py`,
`commands/report.py`, `commands/listings.py`, `commands/suggest.py`,
`analytics/derive.py`, `policy/advisory.py`, `web/views.py`) all answered
the same question with slightly different shapes (string compare vs
`date` compare) and slightly different sources of "today". This module
is the canonical concept: **a scheduled review is overdue when its
`scheduled_for` date is strictly before `today`**.

The module is pure. It owns no wall-clock call — `utc_today` accepts
an optional `clock` callable; the default uses `Context.clock` when
available and falls back to `datetime.now(timezone.utc).date()`. Tests
fix the wall clock by passing a frozen clock or by passing a `today`
argument directly.

Two adapters justify the seam (per T-TestArch D1):

* Production uses `datetime.now(timezone.utc).date()`; the CLI/web layer
  passes `Context.clock` so the dispatcher's clock override threads in.
* Tests pass a counter-clocked callable or a literal `date`.

Public surface:

* `parse_date(val) -> date | None` — shared ISO-date parser (mirrors the
  three duplicated `_parse_date` copies it replaces).
* `is_overdue(review, *, today) -> bool`
* `days_overdue(review, *, today) -> int`
* `overdue_reviews(reviews, *, today) -> list[Review]`
* `utc_today(*, clock=None) -> date`
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Callable

from .reviews import Review


def parse_date(val: object) -> date | None:
    """Safely parse a stored ISO date or timestamp string into a date."""
    if val is None:
        return None
    try:
        return date.fromisoformat(str(val)[:10])
    except (ValueError, TypeError):
        return None


def is_overdue(review: Review, *, today: date) -> bool:
    """A scheduled review is overdue when its `scheduled_for` is strictly before today."""
    if review.status != "scheduled":
        return False
    due = parse_date(review.scheduled_for)
    return due is not None and due < today


def days_overdue(review: Review, *, today: date) -> int:
    """Whole days past the scheduled date; 0 when not overdue or undatable."""
    if not is_overdue(review, today=today):
        return 0
    due = parse_date(review.scheduled_for)
    if due is None:
        return 0
    return (today - due).days


def overdue_reviews(reviews: list[Review], *, today: date) -> list[Review]:
    """The subset of reviews that are scheduled and past their date.

    Order is the caller's responsibility — membership is the only contract
    here. Returns a new list; the input is not mutated.
    """
    return [r for r in reviews if is_overdue(r, today=today)]


def utc_today(*, clock: Callable[[], datetime] | None = None) -> date:
    """Today's date in UTC.

    `clock` is called exactly once per invocation. When `None`, falls
    back to `datetime.now(timezone.utc).date()`. The CLI/web layer
    passes `Context.clock` so the dispatcher's clock override threads in.
    """
    if clock is not None:
        moment = clock()
    else:
        moment = datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).date()
