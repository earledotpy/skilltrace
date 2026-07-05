"""Read-only listings: `skilltrace blockers` and `skilltrace reviews`.

Both print current, actionable records and append no audit event. `reviews`
derives overdue on the fly — a scheduled review past its date — because
overdue is never stored (CONTEXT.md). Cancelled and completed reviews, like
resolved blockers, are history: visible in the files, not in the listing.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..execution._store import ExecutionLoadError
from ..execution.blockers import load_blockers
from ..execution.reviews import load_reviews


def blockers(ctx: Context) -> CommandResult:
    try:
        records = load_blockers(ctx.root)
    except ExecutionLoadError as exc:
        print(f"blockers: FAILED — {exc}")
        return CommandResult(exit_code=1)

    open_blockers = [b for b in records if b.status == "open"]
    if not open_blockers:
        print("no open blockers.")
        return CommandResult()
    print(f"{len(open_blockers)} open blocker(s):")
    for blocker in open_blockers:
        print(f"  {blocker.id}  {blocker.node_id}  — {blocker.description}")
    return CommandResult()


def reviews(ctx: Context) -> CommandResult:
    try:
        records = load_reviews(ctx.root)
    except ExecutionLoadError as exc:
        print(f"reviews: FAILED — {exc}")
        return CommandResult(exit_code=1)

    scheduled = [r for r in records if r.status == "scheduled"]
    if not scheduled:
        print("no scheduled reviews.")
        return CommandResult()

    today = datetime.now(timezone.utc).date().isoformat()
    print(f"{len(scheduled)} scheduled review(s):")
    for review in scheduled:
        marker = "  [OVERDUE]" if review.scheduled_for < today else ""
        print(f"  {review.id}  {review.node_id}  due {review.scheduled_for}{marker}")
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="blockers",
            kind=Kind.READ_ONLY,
            handler=blockers,
            help="List open blockers.",
        )
    )
    registry.register(
        Command(
            name="reviews",
            kind=Kind.READ_ONLY,
            handler=reviews,
            help="List scheduled reviews (overdue derived, never stored).",
        )
    )
