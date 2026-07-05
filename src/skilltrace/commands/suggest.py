"""`skilltrace suggest remediation` / `suggest reviews` — advisory guidance.

Read-only answers to "what corrective or retention work is due?" — derived
remediation pressure with the policy suggestion defaults attached, and the
scheduled reviews at or past their date. Suggestions are words, not writes:
acting on one is always a separate learner command (`remediation create`,
`review complete`), so nothing here mutates records or appends an event.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence._schema import EvidenceLoadError
from ..evidence.attempts import load_assessment_attempts
from ..execution._store import ExecutionLoadError
from ..execution.blockers import load_blockers
from ..execution.reviews import load_reviews
from ..graph.edges import EdgeLoadError, load_edges
from ..graph.state import ProgressStoreError, load_state
from ..policy.loading import PolicyLoadError, load_policy_doc
from ..policy.remediation_edges import (
    active_remediations,
    load_failed_attempt_threshold,
)

_EDGES_RELPATH = Path("graph") / "edges.yaml"
_ATTEMPTS_RELPATH = Path("evidence") / "attempts.yaml"


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _suggestion_defaults(root) -> tuple[int | None, str | None]:
    """(suggested minutes, ISO due date) from the remediation seed, or Nones.

    A missing or unreadable seed omits the sizing clause rather than inventing
    engine defaults — policy values live in seed data, not code.
    """
    try:
        doc = load_policy_doc(root, "remediation.yaml")
    except PolicyLoadError:
        return None, None
    defaults = doc.get("suggestion_defaults")
    if not isinstance(defaults, dict):
        return None, None
    minutes = defaults.get("suggested_minutes")
    due_in_days = defaults.get("due_in_days")
    due = (
        (_today() + timedelta(days=due_in_days)).isoformat()
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
        edges = load_edges(root) if (root / _EDGES_RELPATH).exists() else []
        store = load_state(root)
        blockers = load_blockers(root)
        attempts = (
            load_assessment_attempts(root)
            if (root / _ATTEMPTS_RELPATH).exists()
            else []
        )
    except (EdgeLoadError, ProgressStoreError, ExecutionLoadError, EvidenceLoadError) as exc:
        print(f"suggest remediation: FAILED — {exc}")
        return CommandResult(exit_code=1)

    active = active_remediations(
        edges,
        store=store,
        blockers=blockers,
        attempts=attempts,
        failed_attempt_threshold=load_failed_attempt_threshold(root),
    )
    sizing = _sizing_clause(*_suggestion_defaults(root))

    lines: list[str] = []
    for remediation in active:
        lines.append(
            f"work {remediation.remediation_node} — it supports "
            f"{remediation.target} ({remediation.trigger}){sizing}."
        )
    covered = {remediation.target for remediation in active}
    for blocker in blockers:
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


def _grace_days(root) -> int | None:
    try:
        doc = load_policy_doc(root, "review_cadence.yaml")
    except PolicyLoadError:
        return None
    value = doc.get("missed_review_grace_days")
    return value if isinstance(value, int) else None


def suggest_reviews(ctx: Context) -> CommandResult:
    """List the scheduled reviews at or past their date, oldest first.

    Overdue is derived, never stored; the cadence seed's grace window only
    sharpens the wording (advisory policies warn, they never block).
    """
    root = ctx.root
    try:
        reviews = load_reviews(root)
    except ExecutionLoadError as exc:
        print(f"suggest reviews: FAILED — {exc}")
        return CommandResult(exit_code=1)

    today = _today()
    due: list[tuple[date, str, str]] = []
    upcoming = 0
    for review in reviews:
        if review.status != "scheduled":
            continue
        try:
            scheduled = date.fromisoformat(review.scheduled_for)
        except ValueError:
            continue
        if scheduled <= today:
            due.append((scheduled, review.id, review.node_id))
        else:
            upcoming += 1

    if not due:
        print(f"suggest reviews: nothing due — {upcoming} scheduled ahead.")
        return CommandResult()

    grace = _grace_days(root)
    for scheduled, review_id, node_id in sorted(due):
        overdue_days = (today - scheduled).days
        if overdue_days == 0:
            status = "due today"
        else:
            status = f"overdue by {overdue_days} day(s)"
            if grace is not None and overdue_days > grace:
                status += f", past the {grace}-day grace"
        print(f"suggest reviews: {review_id} on {node_id} — {status}.")
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
