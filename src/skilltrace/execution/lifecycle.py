"""Pure planners for the execution-layer commands.

Same seam as the evidence layer's `plan_attempt`: a planner takes plain facts
(node state, existing ids, the open session), decides, and returns a plan of
records to write plus messages. It never touches the filesystem — the command
handlers load facts, call the planner, and bind the writes — so every rule
here is unit-testable without a repo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .ids import (
    allocate_blocker_id,
    allocate_remediation_id,
    allocate_review_id,
    allocate_session_id,
    allocate_work_id,
)

# Work marks a node `active` only as a forward move (CONTEXT.md): available
# asserts active; active is a no-op; passed/mastered record history without
# demotion; locked refuses — what cannot be started cannot be worked.
_ACTIVATABLE = "available"
_LOCKED = "locked"


@dataclass
class ExecutionPlan:
    """What a planner decided: records to write, state effect, and messages."""

    messages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    session: dict | None = None
    work: dict | None = None
    # `{"session_id": ..., "ended_at": ...}` — completes the open session.
    close_session: dict | None = None
    blocker: dict | None = None
    # `{"blocker_id": ..., "resolution_summary": ..., "resolved_at": ...}`.
    resolve_blocker: dict | None = None
    remediation: dict | None = None
    # `{"action_id": ..., "result_summary": ..., "completed_at": ...}`.
    complete_remediation: dict | None = None
    review: dict | None = None
    # `{"review_id": ..., "outcome": ..., "result_summary": ..., "completed_at": ...}`.
    complete_review: dict | None = None
    # `{"review_id": ..., "cancel_reason": ..., "cancelled_at": ...}`.
    cancel_review: dict | None = None
    activate_node: str | None = None
    records_touched: list[str] = field(default_factory=list)
    exit_code: int = 0


def _refuse(reason: str) -> ExecutionPlan:
    return ExecutionPlan(errors=[reason], exit_code=2)


def _plan_work_item(
    plan: ExecutionPlan,
    node_id: str,
    *,
    node_state: str,
    session_id: str,
    existing_work_ids: list[str],
    now: str,
    blocked: bool = False,
    notes: str | None = None,
    minutes: int | None = None,
) -> ExecutionPlan:
    """Attach one work item for `node_id` to `session_id` onto `plan`."""
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
) -> ExecutionPlan:
    """Open a new session with its first work item on `node_id`."""
    if node_state == _LOCKED:
        return _refuse(f"{node_id} is locked — a locked node cannot be started.")
    if open_session_id is not None:
        return _refuse(
            f"session {open_session_id} is already open — use `work` to add to it "
            "or `session close` to end it."
        )

    session_id = allocate_session_id(now[:10], existing_session_ids)
    session: dict = {"id": session_id, "status": "open", "started_at": now}
    plan = ExecutionPlan(
        session=session,
        records_touched=[session_id],
        messages=[f"opened session {session_id}."],
    )
    if template is not None:
        # Opaque label, track-style: unmapped warns, never fails, means nothing.
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
) -> ExecutionPlan:
    """Add one work item to the open session."""
    if node_state == _LOCKED:
        return _refuse(f"{node_id} is locked — a locked node cannot be worked on.")
    if open_session_id is None:
        return _refuse("no session is open — use `start <node_id>` to open one.")
    if blocked and not notes:
        return _refuse("blocked work requires --notes describing where you got stuck.")

    return _plan_work_item(
        ExecutionPlan(),
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
) -> ExecutionPlan:
    """Complete the open session at `end` (default: now).

    A retroactive `end` records the honest end of a forgotten session; it must
    land after the start and not in the future — closing is a recording of
    what happened, never a prediction.
    """
    if open_session_id is None:
        return _refuse("no session is open — nothing to close.")

    ended_at = end or now
    try:
        ended = datetime.fromisoformat(ended_at)
        started = datetime.fromisoformat(started_at) if started_at else None
        current = datetime.fromisoformat(now)
    except ValueError as exc:
        return _refuse(f"unparseable timestamp: {exc}")

    # Strictly-before is a lie; same-second equality is an instant close.
    if started is not None and ended < started:
        return _refuse(
            f"end {ended_at} is before the session start {started_at} — refused."
        )
    if ended > current:
        return _refuse(f"end {ended_at} is in the future — refused.")

    return ExecutionPlan(
        close_session={"session_id": open_session_id, "ended_at": ended_at},
        records_touched=[open_session_id],
        messages=[f"completed session {open_session_id} ({started_at} -> {ended_at})."],
    )


def plan_blocker_create(
    node_id: str,
    *,
    node_state: str,
    description: str | None,
    existing_blocker_ids: list[str],
    open_blocker_node_ids: list[str],
    now: str,
) -> ExecutionPlan:
    """Record persistent stuckness on `node_id` — an explicit, deliberate act."""
    if node_state == _LOCKED:
        return _refuse(f"{node_id} is locked — what cannot be started cannot be stuck.")
    if not description:
        return _refuse("a blocker names its own obstacle — --description is required.")

    plan = ExecutionPlan()
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
) -> ExecutionPlan:
    """Resolve one open blocker; resolution requires a summary and is terminal."""
    if blocker_status is None:
        return _refuse(f"blocker {blocker_id} does not exist.")
    if blocker_status != "open":
        return _refuse(f"blocker {blocker_id} is already {blocker_status} — refused.")
    if not summary:
        return _refuse("resolving a blocker requires --summary describing the resolution.")

    return ExecutionPlan(
        resolve_blocker={
            "blocker_id": blocker_id,
            "resolution_summary": summary,
            "resolved_at": now,
        },
        records_touched=[blocker_id],
        messages=[f"resolved blocker {blocker_id}."],
    )


def plan_remediation_create(
    node_id: str,
    *,
    description: str | None,
    blocker_id: str | None,
    known_blocker_ids: list[str],
    existing_action_ids: list[str],
    now: str,
) -> ExecutionPlan:
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
    return ExecutionPlan(
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
) -> ExecutionPlan:
    """Complete one open action; the result summary is required.

    Completing has zero mechanical effect beyond this record — it never
    resolves a linked blocker and never touches node state.
    """
    if action_status is None:
        return _refuse(f"remediation action {action_id} does not exist.")
    if action_status != "open":
        return _refuse(f"remediation action {action_id} is already {action_status} — refused.")
    if not summary:
        return _refuse("completing a remediation action requires --summary of the result.")

    return ExecutionPlan(
        complete_remediation={
            "action_id": action_id,
            "result_summary": summary,
            "completed_at": now,
        },
        records_touched=[action_id],
        messages=[f"completed remediation action {action_id}."],
    )


# A retention check needs something to retain (CONTEXT.md): only these states
# accept `review schedule`. After mastery only the learner schedules by hand.
_REVIEWABLE = ("passed", "mastered")

_REVIEW_OUTCOMES = ("satisfactory", "unsatisfactory")


def plan_review_schedule(
    node_id: str,
    *,
    node_state: str,
    date: str | None,
    existing_review_ids: list[str],
    now: str,
) -> ExecutionPlan:
    """Schedule a retention check on a passed or mastered node."""
    if node_state not in _REVIEWABLE:
        return _refuse(
            f"{node_id} is {node_state} — a review needs something to retain "
            "(passed or mastered only)."
        )
    if not date:
        return _refuse("scheduling a review requires --date (YYYY-MM-DD).")

    review_id = allocate_review_id(node_id, existing_review_ids)
    return ExecutionPlan(
        review={
            "id": review_id,
            "node_id": node_id,
            "status": "scheduled",
            "scheduled_for": date,
            "created_at": now,
        },
        records_touched=[review_id],
        messages=[f"scheduled review {review_id} for {date}."],
    )


def _require_scheduled(review_id: str, review_status: str | None) -> ExecutionPlan | None:
    """The shared guard for completing/cancelling: the review must be scheduled."""
    if review_status is None:
        return _refuse(f"review {review_id} does not exist.")
    if review_status != "scheduled":
        return _refuse(f"review {review_id} is already {review_status} — refused.")
    return None


def plan_review_complete(
    review_id: str,
    *,
    review_status: str | None,
    outcome: str | None,
    summary: str | None,
    now: str,
) -> ExecutionPlan:
    """Complete one scheduled review; outcome and result summary are required."""
    refusal = _require_scheduled(review_id, review_status)
    if refusal is not None:
        return refusal
    if outcome not in _REVIEW_OUTCOMES:
        return _refuse(
            f"review outcome must be one of {', '.join(_REVIEW_OUTCOMES)}; got {outcome!r}."
        )
    if not summary:
        return _refuse("completing a review requires --summary of the result.")

    return ExecutionPlan(
        complete_review={
            "review_id": review_id,
            "outcome": outcome,
            "result_summary": summary,
            "completed_at": now,
        },
        records_touched=[review_id],
        messages=[f"completed review {review_id} ({outcome})."],
    )


def plan_review_cancel(
    review_id: str,
    *,
    review_status: str | None,
    reason: str | None,
    now: str,
) -> ExecutionPlan:
    """Cancel one scheduled review — learner-only, reason required, record kept."""
    refusal = _require_scheduled(review_id, review_status)
    if refusal is not None:
        return refusal
    if not reason:
        return _refuse("cancelling a review requires --reason (the record is kept).")

    return ExecutionPlan(
        cancel_review={
            "review_id": review_id,
            "cancel_reason": reason,
            "cancelled_at": now,
        },
        records_touched=[review_id],
        messages=[f"cancelled review {review_id}."],
    )
