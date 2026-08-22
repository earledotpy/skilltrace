"""Shared base for execution planners (C2 — split the god planner).

Every planner returns a narrow plan that shares this base: messages, warnings,
errors, records_touched and exit_code. The base owns the report contract so
``commands/_common.py:report_plan`` can stay typed against ``BasePlan``.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BasePlan:
    """Common fields every execution plan carries (interface is the test surface)."""

    messages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    records_touched: list[str] = field(default_factory=list)
    exit_code: int = 0
