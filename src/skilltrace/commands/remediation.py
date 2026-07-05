"""Remediation commands: `skilltrace remediation create` / `remediation complete`.

Logs deliberate corrective interventions with zero mechanical effect —
completing an action never resolves its linked blocker (that stays an
explicit `blocker resolve`) and never touches node state.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ._common import now_iso as _now_iso, report_plan as _report
from ..execution._store import ExecutionLoadError
from ..execution.blockers import load_blockers
from ..execution.lifecycle import (
    ExecutionPlan,
    plan_remediation_complete,
    plan_remediation_create,
)
from ..execution.remediation import (
    append_remediation_action,
    complete_remediation_action,
    load_remediation_actions,
)


def create(ctx: Context) -> CommandResult:
    root = ctx.root
    try:
        actions = load_remediation_actions(root)
        blockers = load_blockers(root)
    except ExecutionLoadError as exc:
        print(f"remediation create: FAILED — {exc}")
        return CommandResult(exit_code=1)

    plan = plan_remediation_create(
        ctx.args.node_id,
        description=ctx.args.description,
        blocker_id=ctx.args.blocker,
        known_blocker_ids=[b.id for b in blockers],
        existing_action_ids=[a.id for a in actions],
        now=_now_iso(),
    )
    _report(plan)
    if plan.exit_code != 0:
        return CommandResult(exit_code=plan.exit_code)
    append_remediation_action(root, plan.remediation)
    return CommandResult(records_touched=plan.records_touched)


def complete(ctx: Context) -> CommandResult:
    root = ctx.root
    try:
        actions = load_remediation_actions(root)
    except ExecutionLoadError as exc:
        print(f"remediation complete: FAILED — {exc}")
        return CommandResult(exit_code=1)

    target = next((a for a in actions if a.id == ctx.args.action_id), None)
    plan = plan_remediation_complete(
        ctx.args.action_id,
        action_status=target.status if target is not None else None,
        summary=ctx.args.summary,
        now=_now_iso(),
    )
    _report(plan)
    if plan.exit_code != 0:
        return CommandResult(exit_code=plan.exit_code)
    complete_remediation_action(
        root,
        plan.complete_remediation["action_id"],
        result_summary=plan.complete_remediation["result_summary"],
        completed_at=plan.complete_remediation["completed_at"],
    )
    return CommandResult(records_touched=plan.records_touched)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="remediation create",
            kind=Kind.MUTATING,
            handler=create,
            help="Log a deliberate corrective intervention for a node.",
        )
    )
    registry.register(
        Command(
            name="remediation complete",
            kind=Kind.MUTATING,
            handler=complete,
            help="Complete a remediation action with a required result summary.",
        )
    )
