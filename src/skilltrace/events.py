"""Audit event log (`execution/events.yaml`).

The event log is audit-only (invariant / roadmap decision 10): every mutating
command appends exactly one event, and events are never read back to compute
state. This module is the *only* writer; the dispatcher calls `append_event`
after a mutating command succeeds. Nothing here is used to derive learner state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_EVENTS_RELPATH = Path("execution") / "events.yaml"


def events_path(root: Path | str) -> Path:
    return Path(root) / _EVENTS_RELPATH


def load_events(root: Path | str) -> list[dict]:
    """Return the recorded events (audit/inspection only — never for state)."""
    path = events_path(root)
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    events = data.get("events") if isinstance(data, dict) else None
    return events if isinstance(events, list) else []


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append_event(
    root: Path | str,
    *,
    command: str,
    args: dict[str, Any] | None = None,
    records_touched: list[str] | None = None,
) -> dict:
    """Append one audit event and return it.

    An event records that a mutating command ran: its timestamp, the command
    name, the invocation arguments, and the ids of records it touched (possibly
    empty — a mutating command that changed nothing still records one event).
    The file is created if absent so a fresh repo can log its first command.
    """
    path = events_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)

    events = load_events(root)
    event = {
        "timestamp": _now_iso(),
        "command": command,
        "args": dict(args or {}),
        "records_touched": list(records_touched or []),
    }
    events.append(event)
    path.write_text(
        yaml.safe_dump({"events": events}, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return event
