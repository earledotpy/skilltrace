"""Session work items (`execution/session_work.yaml`).

One work item = one unit of what happened in a session, tied to exactly one
node. Interleaving is first-class: a session holds many items. Blocked work
is a session-scoped observation (notes required) — it never creates a
Blocker.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._store import ExecutionLoadError, append_record, read_records

_WORK_RELPATH = Path("execution") / "session_work.yaml"
_TOP_KEY = "session_work"
_KIND = "work item"


@dataclass
class SessionWork:
    id: str
    session_id: str
    node_id: str
    created_at: str
    blocked: bool = False
    notes: str | None = None
    minutes: int | None = None


def load_session_work(root: Path | str) -> list[SessionWork]:
    """Load and shape-check every work item; missing file -> empty history."""
    items: list[SessionWork] = []
    raw = read_records(root, _WORK_RELPATH, top_key=_TOP_KEY, kind=_KIND)
    path = Path(root) / _WORK_RELPATH
    for index, data in enumerate(raw):
        if not isinstance(data, dict):
            raise ExecutionLoadError(f"{path}: work item #{index} is not a mapping.")
        for field in ("id", "session_id", "node_id", "created_at"):
            if field not in data:
                raise ExecutionLoadError(
                    f"{path}: work item #{index} is missing required field {field!r}."
                )
        items.append(
            SessionWork(
                id=str(data["id"]),
                session_id=str(data["session_id"]),
                node_id=str(data["node_id"]),
                created_at=str(data["created_at"]),
                blocked=bool(data.get("blocked", False)),
                notes=data.get("notes"),
                minutes=data.get("minutes"),
            )
        )
    return items


def append_work(root: Path | str, record: dict) -> None:
    append_record(root, _WORK_RELPATH, top_key=_TOP_KEY, kind=_KIND, record=record)
