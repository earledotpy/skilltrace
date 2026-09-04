"""`skilltrace suggest remediation` / `suggest reviews` — advisory guidance.

Read-only answers to "what corrective or retention work is due?" — derived
remediation pressure with the policy suggestion defaults attached, and the
scheduled reviews at or past their date. Suggestions are words, not writes:
acting on one is always a separate learner command (`remediation create`,
`review complete`), so nothing here mutates records or appends an event.

`suggest reviews` (Tier 2) renders two sections: the existing calendar-due
list and a derived retention-suggestions block sourced from the retention
model. The two are visually distinct blocks; the calendar-due list is never
reordered by retention pressure (G-Authority / T-Exit §5). The retention
section appends a single count-based advisory line that downstream surfaces
(notably `next` and the Tier 1 home pressure strip) can pick up verbatim.
"""

from __future__ import annotations

from datetime import date, timedelta

from ..context import load_context_lenient
from ..dispatch import Command, CommandResult, Context, Kind, Registry
from ..execution.overdue import is_overdue, parse_date, utc_today
from ..graph.edges import EdgeLoadError
from ..graph.nodes import NodeLoadError
from ..graph.state import ProgressStoreError
from ..policy.remediation_edges import (
    active_remediations,
)
from ..policy.retention_model import derive_memory_states


def _today() -> date:
    return utc_today()


def _suggestion_defaults(view, today: date) -> tuple[int | None, str | None]:
    """(suggested minutes, ISO due date) from the remediation seed, or Nones.

    A missing or unreadable seed omits the sizing clause rather than inventing
    engine defaults — policy values live in seed data, not code.
    """
    minutes, due_in_days = view.policy.remediation_suggestion_defaults
    due = (
        (today + timedelta(days=due_in_days)).isoformat()
        if isinstance(due_in_days, int)
        else None
    )
    return (minutes if isinstance(minutes, int) else None), due


def _sizing_clause(minutes: int | None, due: str | None) -> str:
    parts = []
    if minutes is not None:
        parts.append(f"~{minutes} min")
    if due is not None:
        parts.append(f"due {due}")
    return f" ({', '.join(parts)})" if parts else ""


def suggest_remediation(ctx: Context) -> CommandResult:
    """Point at the remediation work the derived pressure asks for.

    Every active remediation edge suggests working its remediation node; every
    open blocker no active edge covers suggests logging an ad-hoc
    RemediationAction. Loader failures fail the command (exit 1, no event);
    files that simply don't exist yet read as empty histories.
    """
    root = ctx.root
    try:
        view = load_context_lenient(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"suggest remediation: FAILED — {exc}")
        return CommandResult(exit_code=1)

    active = active_remediations(
        view.edges,
        store=view.store,
        blockers=view.blockers,
        attempts=view.attempts,
        failed_attempt_threshold=view.policy.failed_attempt_threshold,
    )
    sizing = _sizing_clause(*_suggestion_defaults(view, _today()))

    lines: list[str] = []
    for remediation in active:
        lines.append(
            f"work {remediation.remediation_node} — it supports "
            f"{remediation.target} ({remediation.trigger}){sizing}."
        )
    covered = {remediation.target for remediation in active}
    for blocker in view.blockers:
        if blocker.status == "open" and blocker.node_id not in covered:
            lines.append(
                f"no remediation edge covers blocker {blocker.id} on "
                f"{blocker.node_id} — log an ad-hoc action: skilltrace "
                f"remediation create {blocker.node_id} --description "
                f"\"...\" --blocker {blocker.id}{sizing}."
            )

    if not lines:
        print(
            "suggest remediation: nothing to suggest — no active remediation "
            "edges or uncovered open blockers."
        )
    for line in lines:
        print(f"suggest remediation: {line}")
    return CommandResult()


def _grace_days(view) -> int | None:
    return view.policy.review_grace_days


def _retention_suggestions(view, today: date) -> list:
    """Derived retention suggestions for passed/mastered nodes.

    Returns the list sorted ascending by confidence (lowest first = most
    urgent), or an empty list when the seed is missing or the joined view
    cannot be loaded. Missing seed is a soft pass: the calendar section
    still renders; the retention section is omitted without an error.
    """
    seed = view.policy.retention
    if seed is None:
        return []
    below = [
        s for s in derive_memory_states(
            nodes=view.nodes, store=view.store, reviews=view.reviews,
            seed=seed, today=today,
        ) if s.below_threshold
    ]
    below.sort(key=lambda s: s.confidence)
    return below


def suggest_reviews(ctx: Context) -> CommandResult:
    """List the scheduled reviews at or past their date, oldest first,
    then the derived retention suggestions from the model.

    Two sections, in order:

    1. **Calendar-due** — existing behavior over real ``Review`` records.
       The header is present iff there is at least one such review.
    2. **Retention suggestions** — derived from the model, sorted by
       confidence (lowest first). The empty case renders a calm
       "nothing fading" line.

    The two blocks are visually distinct; the calendar-due list is never
    reordered by retention pressure (T-Exit safety gate #5). When the
    retention section is non-empty, a single count-based warning line is
    appended for downstream surfaces to surface verbatim.
    """
    root = ctx.root
    try:
        view = load_context_lenient(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"suggest reviews: FAILED — {exc}")
        return CommandResult(exit_code=1)
    reviews = view.reviews

    today = _today()
    due: list[tuple[date, str, str]] = []
    upcoming = 0
    for review in reviews:
        if review.status != "scheduled":
            continue
        scheduled = parse_date(review.scheduled_for)
        if scheduled is None:
            continue
        if scheduled <= today:
            due.append((scheduled, review.id, review.node_id))
        else:
            upcoming += 1

    calendar_header_printed = False
    if not due:
        print(f"suggest reviews: nothing due — {upcoming} scheduled ahead.")
    else:
        print("suggest reviews: Calendar-due reviews")
        print("suggest reviews: ---------------------")
        calendar_header_printed = True
        grace = _grace_days(view)
        for scheduled, review_id, node_id in sorted(due):
            overdue_days = (today - scheduled).days
            if overdue_days == 0:
                status = "due today"
            else:
                status = f"overdue by {overdue_days} day(s)"
                if grace is not None and overdue_days > grace:
                    status += f", past the {grace}-day grace"
            print(f"suggest reviews: {review_id} on {node_id} — {status}.")

    retention = _retention_suggestions(view, today)
    print()
    print("suggest reviews: Retention suggestions")
    print("suggest reviews: ----------------------")
    if not retention:
        print("suggest reviews: nothing fading — no retention suggestions right now.")
    else:
        for s in retention:
            print(
                f"suggest reviews: {s.node_id} — confidence {s.confidence:.4f}, "
                f"suggested {s.suggested_next_review.isoformat()} "
                f"(`review schedule` to make it real)."
            )
        print(
            f"suggest reviews: {len(retention)} retention suggestion(s) due — "
            "`review schedule <node> --date <YYYY-MM-DD>` to schedule a check."
        )

    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="suggest remediation",
            kind=Kind.READ_ONLY,
            handler=suggest_remediation,
            help="Suggest corrective work from derived remediation pressure.",
        )
    )
    registry.register(
        Command(
            name="suggest reviews",
            kind=Kind.READ_ONLY,
            handler=suggest_reviews,
            help="Suggest the scheduled reviews now due or overdue.",
        )
    )
