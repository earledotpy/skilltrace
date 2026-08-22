"""Remediation planners — create / complete (C2)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base_plan import BasePlan
from .ids import allocate_remediation_id


@dataclass
class RemediationPlan(BasePlan):
    remediation: dict | None = None
    # {"action_id": ..., "result_summary": ..., "completed_at": ...}
    complete_remediation: dict | None = None


def _refuse(reason: str) -> RemediationPlan:
    return RemediationPlan(errors=[reason], exit_code=2)


def plan_remediation_create(
    node_id: str,
    *,
    description: str | None,
    blocker_id: str | None,
    known_blocker_ids: list[str],
    existing_action_ids: list[str],
    now: str,
) -> RemediationPlan:
    """Log one deliberate corrective intervention (any node state; zero effects)."""
    if not description:
        return _refuse("a remediation action needs --description of the intervention.")
    if blocker_id is not None and blocker_id not in known_blocker_ids:
        return _refuse(f"blocker {blocker_id} does not exist — cannot link to it.")

    action_id = allocate_remediation_id(node_id, existing_action_ids)
    record = {
        "id": action_id,
        "node_id": node_id,
        "status": "open",
        "description": description,
        "created_at": now,
    }
    if blocker_id is not None:
        record["blocker_id"] = blocker_id
    return RemediationPlan(
        remediation=record,
        records_touched=[action_id],
        messages=[f"opened remediation action {action_id}."],
    )


def plan_remediation_complete(
    action_id: str,
    *,
    action_status: str | None,
    summary: str | None,
    now: str,
) -> RemediationPlan:
    """Complete one open action; the result summary is required."""
    if action_status is None:
        return _refuse(f"remediation action {action_id} does not exist.")
    if action_status != "open":
        return _refuse(f"remediation action {action_id} is already {action_status} — refused.")
    if not summary:
        return _refuse("completing a remediation action requires --summary of the result.")

    return RemediationPlan(
        complete_remediation={
            "action_id": action_id,
            "result_summary": summary,
            "completed_at": now,
        },
        records_touched=[action_id],
        messages=[f"completed remediation action {action_id}."],
    )
