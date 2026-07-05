"""Review cadence — fixed post-pass intervals from `policy/review_cadence.yaml`.

Pure planning plus a values loader. A missing or unreadable cadence file
yields no intervals — automation quietly does nothing rather than inventing
an engine-default schedule; manual `review schedule` always remains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from .loading import PolicyLoadError, load_policy_doc


@dataclass
class CadenceInterval:
    label: str
    days_after_pass: int
    expected_minutes: int | None = None


@dataclass
class Cadence:
    schedule_reviews_after_pass: bool = False
    intervals: list[CadenceInterval] = field(default_factory=list)


def load_cadence(root: Path | str) -> Cadence:
    """Read the cadence seed; anything unusable degrades to "schedule nothing"."""
    try:
        doc = load_policy_doc(root, "review_cadence.yaml")
    except PolicyLoadError:
        return Cadence()
    cadence = Cadence(
        schedule_reviews_after_pass=doc.get("schedule_reviews_after_pass") is True
    )
    for raw in doc.get("intervals") or []:
        if not isinstance(raw, dict) or not isinstance(raw.get("days_after_pass"), int):
            continue
        cadence.intervals.append(
            CadenceInterval(
                label=str(raw.get("label", f"day_{raw['days_after_pass']}")),
                days_after_pass=raw["days_after_pass"],
                expected_minutes=raw.get("expected_minutes"),
            )
        )
    return cadence


def review_dates(pass_day: date, cadence: Cadence) -> list[tuple[str, str]]:
    """The (label, ISO date) schedule a pass on `pass_day` implies."""
    return [
        (interval.label, (pass_day + timedelta(days=interval.days_after_pass)).isoformat())
        for interval in cadence.intervals
    ]
