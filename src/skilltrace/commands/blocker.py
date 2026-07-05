"""Blocker commands: `skilltrace blocker create` / `blocker resolve`.

A Blocker is the canonical record of persistent stuckness, created only by
this explicit command (blocked work never creates one) and refused on a
locked node. Resolution requires a summary and is terminal — a resolved
blocker stays resolved; being stuck again is a new blocker.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ._common import now_iso as _now_iso, report_plan as _report
from ..execution._store import ExecutionLoadError
from ..execution.blockers import append_blocker, load_blockers, resolve_blocker
from ..execution.lifecycle import (
    ExecutionPlan,
    plan_blocker_create,
    plan_blocker_resolve,
)
from ..graph.state import ProgressStoreError, load_state


def create(ctx: Context) -> CommandResult:
    root = ctx.root
    try:
        store = load_state(root)
        blockers = load_blockers(root)
    except (ExecutionLoadError, ProgressStoreError) as exc:
        print(f"blocker create: FAILED — {exc}")
        return CommandResult(exit_code=1)

    plan = plan_blocker_create(
        ctx.args.node_id,
        node_state=store.state_of(ctx.args.node_id),
        description=ctx.args.description,
        existing_blocker_ids=[b.id for b in blockers],
        open_blocker_node_ids=[b.node_id for b in blockers if b.status == "open"],
        now=_now_iso(),
    )
    _report(plan)
    if plan.exit_code != 0:
        return CommandResult(exit_code=plan.exit_code)
    append_blocker(root, plan.blocker)
    return CommandResult(records_touched=plan.records_touched)


def resolve(ctx: Context) -> CommandResult:
    root = ctx.root
    try:
        blockers = load_blockers(root)
    except ExecutionLoadError as exc:
        print(f"blocker resolve: FAILED — {exc}")
        return CommandResult(exit_code=1)

    target = next((b for b in blockers if b.id == ctx.args.blocker_id), None)
    plan = plan_blocker_resolve(
        ctx.args.blocker_id,
        blocker_status=target.status if target is not None else None,
        summary=ctx.args.summary,
        now=_now_iso(),
    )
    _report(plan)
    if plan.exit_code != 0:
        return CommandResult(exit_code=plan.exit_code)
    resolve_blocker(
        root,
        plan.resolve_blocker["blocker_id"],
        resolution_summary=plan.resolve_blocker["resolution_summary"],
        resolved_at=plan.resolve_blocker["resolved_at"],
    )
    return CommandResult(records_touched=plan.records_touched)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="blocker create",
            kind=Kind.MUTATING,
            handler=create,
            help="Record persistent stuckness on a node (explicit act; refused on locked).",
        )
    )
    registry.register(
        Command(
            name="blocker resolve",
            kind=Kind.MUTATING,
            handler=resolve,
            help="Resolve an open blocker with a required resolution summary.",
        )
    )
