"""Stale-open-session detection.

A stale session is an open session older than a policy-configured window —
a derived status that warns and never blocks (CONTEXT.md). The mechanism
(staleness exists, warning fires) is engine; the threshold is seed data
(`workload_policy.stale_session_hours` in `policy/workload.yaml`), with an
engine fallback so a repo without the value still warns sensibly.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from .sessions import Session

DEFAULT_STALE_HOURS = 12.0

_WORKLOAD_RELPATH = Path("policy") / "workload.yaml"


def stale_session_hours(root: Path | str) -> float:
    """The staleness threshold: seed value if present and sane, else default."""
    path = Path(root) / _WORKLOAD_RELPATH
    if not path.exists():
        return DEFAULT_STALE_HOURS
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return DEFAULT_STALE_HOURS
    policy = doc.get("workload_policy") if isinstance(doc, dict) else None
    value = policy.get("stale_session_hours") if isinstance(policy, dict) else None
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    return DEFAULT_STALE_HOURS


def stale_warning(session: Session, *, now: str, threshold_hours: float) -> str | None:
    """A warning line if `session` has been open past the threshold, else None."""
    try:
        started = datetime.fromisoformat(session.started_at)
        current = datetime.fromisoformat(now)
    except ValueError:
        return None  # unparseable timestamps are validate's concern, not a crash
    open_hours = (current - started).total_seconds() / 3600
    if open_hours < threshold_hours:
        return None
    return (
        f"session {session.id} has been open {open_hours:.0f}h — stale "
        f"(threshold: {threshold_hours:g}h). Close it with `session close` "
        "(--end for an honest past end time)."
    )
