"""Sessions (`execution/sessions.yaml`).

A session is a bounded block of study time in exactly one of two statuses:
`open` (started, not ended) or `completed` (both timestamps). There is no
planned session (CONTEXT.md). At most one session is open at a time — a rule
enforced by the commands and re-checked by `validate execution`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._store import ExecutionLoadError, append_record, read_records, write_records

_SESSIONS_RELPATH = Path("execution") / "sessions.yaml"
_TOP_KEY = "sessions"
_KIND = "session"

STATUSES = ("open", "completed")


@dataclass
class Session:
    id: str
    status: str
    started_at: str
    ended_at: str | None = None
    template: str | None = None


def load_sessions(root: Path | str) -> list[Session]:
    """Load and shape-check every session; missing file -> empty history."""
    sessions: list[Session] = []
    raw = read_records(root, _SESSIONS_RELPATH, top_key=_TOP_KEY, kind=_KIND)
    path = Path(root) / _SESSIONS_RELPATH
    for index, data in enumerate(raw):
        if not isinstance(data, dict):
            raise ExecutionLoadError(f"{path}: session #{index} is not a mapping.")
        for field in ("id", "status", "started_at"):
            if field not in data:
                raise ExecutionLoadError(
                    f"{path}: session #{index} is missing required field {field!r}."
                )
        if data["status"] not in STATUSES:
            raise ExecutionLoadError(
                f"{path}: session {data['id']!r} has invalid status {data['status']!r} "
                f"— expected one of {', '.join(STATUSES)} (there is no planned session)."
            )
        sessions.append(
            Session(
                id=str(data["id"]),
                status=str(data["status"]),
                started_at=str(data["started_at"]),
                ended_at=data.get("ended_at"),
                template=data.get("template"),
            )
        )
    return sessions


def open_session(sessions: list[Session]) -> Session | None:
    """The single open session, or None. (Multiple opens is a validation error.)"""
    for session in sessions:
        if session.status == "open":
            return session
    return None


def append_session(root: Path | str, record: dict) -> None:
    append_record(root, _SESSIONS_RELPATH, top_key=_TOP_KEY, kind=_KIND, record=record)


def complete_session(root: Path | str, session_id: str, *, ended_at: str) -> None:
    """Flip one session `open -> completed`, stamping its end.

    The only in-place mutation the session file ever sees; every other row is
    preserved untouched. A missing id is a programmer error upstream (the
    planner just found it), so it raises rather than silently no-ops.
    """
    records = read_records(root, _SESSIONS_RELPATH, top_key=_TOP_KEY, kind=_KIND)
    for record in records:
        if isinstance(record, dict) and record.get("id") == session_id:
            record["status"] = "completed"
            record["ended_at"] = ended_at
            break
    else:
        raise ExecutionLoadError(f"session {session_id!r} not found — cannot complete.")
    write_records(root, _SESSIONS_RELPATH, top_key=_TOP_KEY, records=records)
