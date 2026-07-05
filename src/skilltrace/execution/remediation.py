"""Remediation actions (`execution/remediation_actions.yaml`).

A RemediationAction is an execution record of one deliberate corrective
intervention: tied to exactly one node, optionally naming the Blocker it
addresses. It has no mechanical effect — completing one never resolves a
blocker, never touches state or eligibility (CONTEXT.md). It is the ad-hoc
counterpart to a curriculum-level remediation edge.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._store import ExecutionLoadError, append_record, read_records, write_records

_REMEDIATION_RELPATH = Path("execution") / "remediation_actions.yaml"
_TOP_KEY = "remediation_actions"
_KIND = "remediation action"

STATUSES = ("open", "completed")


@dataclass
class RemediationAction:
    id: str
    node_id: str
    status: str
    description: str
    created_at: str
    blocker_id: str | None = None
    completed_at: str | None = None
    result_summary: str | None = None


def load_remediation_actions(root: Path | str) -> list[RemediationAction]:
    """Load and shape-check every action; missing file -> empty history."""
    actions: list[RemediationAction] = []
    raw = read_records(root, _REMEDIATION_RELPATH, top_key=_TOP_KEY, kind=_KIND)
    path = Path(root) / _REMEDIATION_RELPATH
    for index, data in enumerate(raw):
        if not isinstance(data, dict):
            raise ExecutionLoadError(f"{path}: remediation action #{index} is not a mapping.")
        for field in ("id", "node_id", "status", "description", "created_at"):
            if field not in data:
                raise ExecutionLoadError(
                    f"{path}: remediation action #{index} is missing required field {field!r}."
                )
        if data["status"] not in STATUSES:
            raise ExecutionLoadError(
                f"{path}: remediation action {data['id']!r} has invalid status "
                f"{data['status']!r} — expected one of {', '.join(STATUSES)}."
            )
        actions.append(
            RemediationAction(
                id=str(data["id"]),
                node_id=str(data["node_id"]),
                status=str(data["status"]),
                description=str(data["description"]),
                created_at=str(data["created_at"]),
                blocker_id=data.get("blocker_id"),
                completed_at=data.get("completed_at"),
                result_summary=data.get("result_summary"),
            )
        )
    return actions


def append_remediation_action(root: Path | str, record: dict) -> None:
    append_record(root, _REMEDIATION_RELPATH, top_key=_TOP_KEY, kind=_KIND, record=record)


def complete_remediation_action(
    root: Path | str, action_id: str, *, result_summary: str, completed_at: str
) -> None:
    """Flip one action `open -> completed` with its result; other rows untouched."""
    records = read_records(root, _REMEDIATION_RELPATH, top_key=_TOP_KEY, kind=_KIND)
    for record in records:
        if isinstance(record, dict) and record.get("id") == action_id:
            record["status"] = "completed"
            record["result_summary"] = result_summary
            record["completed_at"] = completed_at
            break
    else:
        raise ExecutionLoadError(
            f"remediation action {action_id!r} not found — cannot complete."
        )
    write_records(root, _REMEDIATION_RELPATH, top_key=_TOP_KEY, records=records)
