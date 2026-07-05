"""Review commands: `skilltrace review schedule` / `complete` / `cancel`.

Manual scheduling only in v0.5 — auto-scheduling on `pass` attaches in v0.6
with the policy engine. Scheduling needs something to retain (passed or
mastered); completing needs an outcome and result summary; cancelling is
learner-only with a required reason, and the record stays as history.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ._common import now_iso as _now_iso, report_plan as _report
from ..execution._store import ExecutionLoadError
from ..execution.lifecycle import (
    ExecutionPlan,
    plan_review_cancel,
    plan_review_complete,
    plan_review_schedule,
)
from ..execution.reviews import (
    append_review,
    cancel_review,
    complete_review,
    load_reviews,
)
from ..graph.state import ProgressStoreError, load_state


def schedule(ctx: Context) -> CommandResult:
    root = ctx.root
    try:
        store = load_state(root)
        reviews = load_reviews(root)
    except (ExecutionLoadError, ProgressStoreError) as exc:
        print(f"review schedule: FAILED — {exc}")
        return CommandResult(exit_code=1)

    plan = plan_review_schedule(
        ctx.args.node_id,
        node_state=store.state_of(ctx.args.node_id),
        date=ctx.args.date,
        existing_review_ids=[r.id for r in reviews],
        now=_now_iso(),
    )
    _report(plan)
    if plan.exit_code != 0:
        return CommandResult(exit_code=plan.exit_code)
    append_review(root, plan.review)
    return CommandResult(records_touched=plan.records_touched)


def _find_status(reviews, review_id: str) -> str | None:
    target = next((r for r in reviews if r.id == review_id), None)
    return target.status if target is not None else None


def complete(ctx: Context) -> CommandResult:
    root = ctx.root
    try:
        reviews = load_reviews(root)
    except ExecutionLoadError as exc:
        print(f"review complete: FAILED — {exc}")
        return CommandResult(exit_code=1)

    plan = plan_review_complete(
        ctx.args.review_id,
        review_status=_find_status(reviews, ctx.args.review_id),
        outcome=ctx.args.outcome,
        summary=ctx.args.summary,
        now=_now_iso(),
    )
    _report(plan)
    if plan.exit_code != 0:
        return CommandResult(exit_code=plan.exit_code)
    complete_review(
        root,
        plan.complete_review["review_id"],
        outcome=plan.complete_review["outcome"],
        result_summary=plan.complete_review["result_summary"],
        completed_at=plan.complete_review["completed_at"],
    )
    return CommandResult(records_touched=plan.records_touched)


def cancel(ctx: Context) -> CommandResult:
    root = ctx.root
    try:
        reviews = load_reviews(root)
    except ExecutionLoadError as exc:
        print(f"review cancel: FAILED — {exc}")
        return CommandResult(exit_code=1)

    plan = plan_review_cancel(
        ctx.args.review_id,
        review_status=_find_status(reviews, ctx.args.review_id),
        reason=ctx.args.reason,
        now=_now_iso(),
    )
    _report(plan)
    if plan.exit_code != 0:
        return CommandResult(exit_code=plan.exit_code)
    cancel_review(
        root,
        plan.cancel_review["review_id"],
        cancel_reason=plan.cancel_review["cancel_reason"],
        cancelled_at=plan.cancel_review["cancelled_at"],
    )
    return CommandResult(records_touched=plan.records_touched)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="review schedule",
            kind=Kind.MUTATING,
            handler=schedule,
            help="Schedule a retention check on a passed or mastered node.",
        )
    )
    registry.register(
        Command(
            name="review complete",
            kind=Kind.MUTATING,
            handler=complete,
            help="Complete a scheduled review (outcome + result summary required).",
        )
    )
    registry.register(
        Command(
            name="review cancel",
            kind=Kind.MUTATING,
            handler=cancel,
            help="Cancel a scheduled review (reason required; the record is kept).",
        )
    )
