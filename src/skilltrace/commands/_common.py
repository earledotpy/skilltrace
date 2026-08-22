"""Shared plumbing for the execution-layer command handlers."""

from __future__ import annotations

from datetime import datetime, timezone

from ..execution.base_plan import BasePlan


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def report_plan(plan: BasePlan) -> None:
    """Print a plan's messages, warnings, and errors in the standard format."""
    for message in plan.messages:
        print(message)
    for warning in plan.warnings:
        print(f"[warning] {warning}")
    for error in plan.errors:
        print(f"[error] {error}")
