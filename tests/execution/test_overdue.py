"""Table-driven tests for `execution.overdue` (issue #144).

The seam is the seven duplicated call sites that previously
reinvented "is this review overdue?". Every surface (today, report,
listings, suggest, analytics, web, advisory) collapses to one
import now; the public contract here is the only contract.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from skilltrace.execution.overdue import (
    days_overdue,
    is_overdue,
    overdue_reviews,
    parse_date,
    utc_today,
)
from skilltrace.execution.reviews import Review


def _review(*, status: str, scheduled_for: str, id: str = "rv.001") -> Review:
    return Review(
        id=id,
        node_id="n.01",
        status=status,
        scheduled_for=scheduled_for,
        created_at="2026-01-01T00:00:00Z",
    )


@pytest.mark.parametrize(
    "scheduled_for,status,today,expected",
    [
        # Not scheduled — never overdue regardless of date.
        ("2026-08-01", "completed", date(2026, 9, 1), False),
        ("2026-08-01", "cancelled", date(2026, 9, 1), False),
        # Scheduled-future — not overdue.
        ("2026-09-15", "scheduled", date(2026, 9, 1), False),
        # Scheduled-today — boundary; not strictly overdue.
        ("2026-09-01", "scheduled", date(2026, 9, 1), False),
        # Scheduled-past — overdue.
        ("2026-08-30", "scheduled", date(2026, 9, 1), True),
        # Malformed date — not overdue (parse fails).
        ("not-a-date", "scheduled", date(2026, 9, 1), False),
        ("", "scheduled", date(2026, 9, 1), False),
    ],
)
def test_is_overdue_table(scheduled_for, status, today, expected):
    review = _review(status=status, scheduled_for=scheduled_for)
    assert is_overdue(review, today=today) is expected


@pytest.mark.parametrize(
    "scheduled_for,status,today,expected",
    [
        # Not overdue — days = 0.
        ("2026-09-15", "scheduled", date(2026, 9, 1), 0),
        ("2026-09-01", "scheduled", date(2026, 9, 1), 0),
        # Overdue — full day delta.
        ("2026-08-30", "scheduled", date(2026, 9, 1), 2),
        # Malformed — 0.
        ("not-a-date", "scheduled", date(2026, 9, 1), 0),
    ],
)
def test_days_overdue_table(scheduled_for, status, today, expected):
    review = _review(status=status, scheduled_for=scheduled_for)
    assert days_overdue(review, today=today) == expected


def test_overdue_reviews_empty():
    assert overdue_reviews([], today=date(2026, 9, 1)) == []


def test_overdue_reviews_all_overdue():
    reviews = [
        _review(id="rv.a", status="scheduled", scheduled_for="2026-08-01"),
        _review(id="rv.b", status="scheduled", scheduled_for="2026-07-15"),
    ]
    result = overdue_reviews(reviews, today=date(2026, 9, 1))
    assert {r.id for r in result} == {"rv.a", "rv.b"}


def test_overdue_reviews_mixed():
    reviews = [
        _review(id="rv.overdue", status="scheduled", scheduled_for="2026-08-01"),
        _review(id="rv.future", status="scheduled", scheduled_for="2026-12-01"),
        _review(id="rv.completed", status="completed", scheduled_for="2026-08-01"),
        _review(id="rv.cancelled", status="cancelled", scheduled_for="2026-08-01"),
        _review(id="rv.today", status="scheduled", scheduled_for="2026-09-01"),
    ]
    result = overdue_reviews(reviews, today=date(2026, 9, 1))
    assert [r.id for r in result] == ["rv.overdue"]


def test_utc_today_default():
    """Default clock returns today in UTC."""
    today = utc_today()
    assert today == datetime.now(timezone.utc).date()


def test_utc_today_fixed_clock():
    """A frozen clock is honored exactly."""
    fixed = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert utc_today(clock=lambda: fixed) == date(2026, 9, 1)


def test_utc_today_naive_clock_is_normalized():
    """A naive datetime is treated as UTC before extracting the date."""
    naive = datetime(2026, 9, 1, 0, 0, 0)
    assert utc_today(clock=lambda: naive) == date(2026, 9, 1)


def test_utc_today_clock_called_exactly_once():
    """The clock callable is invoked exactly once per call."""
    calls = {"n": 0}

    def counting_clock() -> datetime:
        calls["n"] += 1
        return datetime(2026, 9, 1, tzinfo=timezone.utc)

    utc_today(clock=counting_clock)
    assert calls["n"] == 1


def test_parse_date_iso_date():
    assert parse_date("2026-09-01") == date(2026, 9, 1)


def test_parse_date_iso_timestamp_truncates_to_date():
    """A timestamp string is parsed as its date prefix."""
    assert parse_date("2026-09-01T12:34:56Z") == date(2026, 9, 1)


def test_parse_date_returns_none_for_malformed():
    assert parse_date(None) is None
    assert parse_date("not-a-date") is None
    assert parse_date(123) is None
