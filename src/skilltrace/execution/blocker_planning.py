"""Blocker planners — create / resolve (C2)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base_plan import BasePlan
from .ids import allocate_blocker_id

_LOCKED = "locked"


@dataclass
class BlockerPlan(BasePlan):
    blocker: dict | None = None
    # {"blocker_id": ..., "resolution_summary": ..., "resolved_at": ...}
    resolve_blocker: dict | None = None


def _refuse(reason: str) -> BlockerPlan:
    return BlockerPlan(errors=[reason], exit_code=2)


def plan_blocker_create(
    node_id: str,
    *,
    node_state: str,
    description: str | None,
    existing_blocker_ids: list[str],
    open_blocker_node_ids: list[str],
    now: str,
) -> BlockerPlan:
    """Record persistent stuckness on ``node_id`` — an explicit, deliberate act."""
    if node_state == _LOCKED:
        return _refuse(f"{node_id} is locked — what cannot be started cannot be stuck.")
    if not description:
        return _refuse("a blocker names its own obstacle — --description is required.")

    plan = BlockerPlan()
    if node_id in open_blocker_node_ids:
        plan.warnings.append(
            f"{node_id} already has an open blocker — a second one is legal but "
            "check it names a different obstacle."
        )
    blocker_id = allocate_blocker_id(node_id, existing_blocker_ids)
    plan.blocker = {
        "id": blocker_id,
        "node_id": node_id,
        "status": "open",
        "description": description,
        "created_at": now,
    }
    plan.records_touched.append(blocker_id)
    plan.messages.append(f"opened blocker {blocker_id}.")
    return plan


def plan_blocker_resolve(
    blocker_id: str,
    *,
    blocker_status: str | None,
    summary: str | None,
    now: str,
) -> BlockerPlan:
    """Resolve one open blocker; resolution requires a summary and is terminal."""
    if blocker_status is None:
        return _refuse(f"blocker {blocker_id} does not exist.")
    if blocker_status != "open":
        return _refuse(f"blocker {blocker_id} is already {blocker_status} — refused.")
    if not summary:
        return _refuse("resolving a blocker requires --summary describing the resolution.")

    return BlockerPlan(
        resolve_blocker={
            "blocker_id": blocker_id,
            "resolution_summary": summary,
            "resolved_at": now,
        },
        records_touched=[blocker_id],
        messages=[f"resolved blocker {blocker_id}."],
    )
