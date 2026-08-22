"""Session planners — start / work / close (C2).

One of four concern-split modules that replace the god ``lifecycle.py``.
Each planner is pure (takes plain facts, never touches the filesystem) so
every rule is unit-testable without a repo. State effect (available → active)
stays here per Q5a — the progress store's guard remains the mechanism, this
is the intent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .base_plan import BasePlan
from .ids import allocate_session_id, allocate_work_id

_ACTIVATABLE = "available"
_LOCKED = "locked"


@dataclass
class SessionPlan(BasePlan):
    """Result of a session planner — at most one of the three payloads is set."""

    session: dict | None = None
    work: dict | None = None
    # {"session_id": ..., "ended_at": ...}
    close_session: dict | None = None
    activate_node: str | None = None


def _refuse(reason: str) -> SessionPlan:
    return SessionPlan(errors=[reason], exit_code=2)


def _plan_work_item(
    plan: SessionPlan,
    node_id: str,
    *,
    node_state: str,
    session_id: str,
    existing_work_ids: list[str],
    now: str,
    blocked: bool = False,
    notes: str | None = None,
    minutes: int | None = None,
) -> SessionPlan:
    """Attach one work item for ``node_id`` to ``session_id`` onto ``plan``."""
    work_id = allocate_work_id(session_id, existing_work_ids)
    plan.work = {
        "id": work_id,
        "session_id": session_id,
        "node_id": node_id,
        "created_at": now,
    }
    if blocked:
        plan.work["blocked"] = True
    if notes is not None:
        plan.work["notes"] = notes
    if minutes is not None:
        plan.work["minutes"] = minutes
    plan.records_touched.append(work_id)

    if node_state == _ACTIVATABLE:
        plan.activate_node = node_id
        plan.records_touched.append(node_id)
        plan.messages.append(f"{node_id}: available -> active.")
    return plan


def plan_start(
    node_id: str,
    *,
    node_state: str,
    open_session_id: str | None,
    existing_session_ids: list[str],
    existing_work_ids: list[str],
    now: str,
    template: str | None = None,
    known_templates: set[str] | frozenset[str] = frozenset(),
) -> SessionPlan:
    """Open a new session with its first work item on ``node_id``."""
    if node_state == _LOCKED:
        return _refuse(f"{node_id} is locked — a locked node cannot be started.")
    if open_session_id is not None:
        return _refuse(
            f"session {open_session_id} is already open — use `work` to add to it "
            "or `session close` to end it."
        )

    session_id = allocate_session_id(now[:10], existing_session_ids)
    session: dict = {"id": session_id, "status": "open", "started_at": now}
    plan = SessionPlan(
        session=session,
        records_touched=[session_id],
        messages=[f"opened session {session_id}."],
    )
    if template is not None:
        session["template"] = template
        if template not in known_templates:
            plan.warnings.append(f"template {template!r} has no seed preset.")
    return _plan_work_item(
        plan,
        node_id,
        node_state=node_state,
        session_id=session_id,
        existing_work_ids=existing_work_ids,
        now=now,
    )


def plan_work(
    node_id: str,
    *,
    node_state: str,
    open_session_id: str | None,
    existing_work_ids: list[str],
    now: str,
    blocked: bool = False,
    notes: str | None = None,
    minutes: int | None = None,
) -> SessionPlan:
    """Add one work item to the open session."""
    if node_state == _LOCKED:
        return _refuse(f"{node_id} is locked — a locked node cannot be worked on.")
    if open_session_id is None:
        return _refuse("no session is open — use `start <node_id>` to open one.")
    if blocked and not notes:
        return _refuse("blocked work requires --notes describing where you got stuck.")

    return _plan_work_item(
        SessionPlan(),
        node_id,
        node_state=node_state,
        session_id=open_session_id,
        existing_work_ids=existing_work_ids,
        now=now,
        blocked=blocked,
        notes=notes,
        minutes=minutes,
    )


def plan_close(
    *,
    open_session_id: str | None,
    started_at: str | None,
    end: str | None,
    now: str,
) -> SessionPlan:
    """Complete the open session at ``end`` (default: now)."""
    if open_session_id is None:
        return _refuse("no session is open — nothing to close.")

    ended_at = end or now
    try:
        ended = datetime.fromisoformat(ended_at)
        started = datetime.fromisoformat(started_at) if started_at else None
        current = datetime.fromisoformat(now)
    except ValueError as exc:
        return _refuse(f"unparseable timestamp: {exc}")

    if started is not None and ended < started:
        return _refuse(
            f"end {ended_at} is before the session start {started_at} — refused."
        )
    if ended > current:
        return _refuse(f"end {ended_at} is in the future — refused.")

    return SessionPlan(
        close_session={"session_id": open_session_id, "ended_at": ended_at},
        records_touched=[open_session_id],
        messages=[f"completed session {open_session_id} ({started_at} -> {ended_at})."],
    )
