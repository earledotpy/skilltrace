"""Shared plumbing for the execution-layer command handlers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from ..execution.base_plan import BasePlan


def now_iso(*, clock: Callable[[], datetime] | None = None) -> str:
    """Current UTC timestamp as an ISO string.

    ``clock`` is the dispatcher's test/fixture override (``Context.clock``);
    when ``None`` the wall clock is read. Threading one ``now`` through
    every engine-written record lets fixture/simulated clocks date the
    records they write (issue #308, fortnight hazard H1).
    """
    if clock is not None:
        moment = clock()
    else:
        moment = datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.isoformat(timespec="seconds")


def report_plan(plan: BasePlan) -> None:
    """Print a plan's messages, warnings, and errors in the standard format."""
    for message in plan.messages:
        print(message)
    for warning in plan.warnings:
        print(f"[warning] {warning}")
    for error in plan.errors:
        print(f"[error] {error}")
