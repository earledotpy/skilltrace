"""Blockers (`execution/blockers.yaml`).

A Blocker is the canonical record of *persistent* stuckness on a node,
created only by an explicit learner command — never auto-created from
blocked work. Each names its own obstacle; resolving requires a resolution
summary (CONTEXT.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._store import ExecutionLoadError, append_record, read_records, write_records

_BLOCKERS_RELPATH = Path("execution") / "blockers.yaml"
_TOP_KEY = "blockers"
_KIND = "blocker"

STATUSES = ("open", "resolved")


@dataclass
class Blocker:
    id: str
    node_id: str
    status: str
    description: str
    created_at: str
    resolved_at: str | None = None
    resolution_summary: str | None = None


def load_blockers(root: Path | str) -> list[Blocker]:
    """Load and shape-check every blocker; missing file -> empty history."""
    blockers: list[Blocker] = []
    raw = read_records(root, _BLOCKERS_RELPATH, top_key=_TOP_KEY, kind=_KIND)
    path = Path(root) / _BLOCKERS_RELPATH
    for index, data in enumerate(raw):
        if not isinstance(data, dict):
            raise ExecutionLoadError(f"{path}: blocker #{index} is not a mapping.")
        for field in ("id", "node_id", "status", "description", "created_at"):
            if field not in data:
                raise ExecutionLoadError(
                    f"{path}: blocker #{index} is missing required field {field!r}."
                )
        if data["status"] not in STATUSES:
            raise ExecutionLoadError(
                f"{path}: blocker {data['id']!r} has invalid status {data['status']!r} "
                f"— expected one of {', '.join(STATUSES)}."
            )
        blockers.append(
            Blocker(
                id=str(data["id"]),
                node_id=str(data["node_id"]),
                status=str(data["status"]),
                description=str(data["description"]),
                created_at=str(data["created_at"]),
                resolved_at=data.get("resolved_at"),
                resolution_summary=data.get("resolution_summary"),
            )
        )
    return blockers


def append_blocker(root: Path | str, record: dict) -> None:
    append_record(root, _BLOCKERS_RELPATH, top_key=_TOP_KEY, kind=_KIND, record=record)


def resolve_blocker(
    root: Path | str, blocker_id: str, *, resolution_summary: str, resolved_at: str
) -> None:
    """Flip one blocker `open -> resolved` with its summary; other rows untouched."""
    records = read_records(root, _BLOCKERS_RELPATH, top_key=_TOP_KEY, kind=_KIND)
    for record in records:
        if isinstance(record, dict) and record.get("id") == blocker_id:
            record["status"] = "resolved"
            record["resolution_summary"] = resolution_summary
            record["resolved_at"] = resolved_at
            break
    else:
        raise ExecutionLoadError(f"blocker {blocker_id!r} not found — cannot resolve.")
    write_records(root, _BLOCKERS_RELPATH, top_key=_TOP_KEY, records=records)
