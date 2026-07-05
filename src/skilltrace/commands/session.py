"""Session commands: `skilltrace start`, `work`, and `session close`.

`start` opens a new session and records its first work item on the given
node (refused while a session is already open); `work` appends items to the
open session; `session close` completes it, with `--end` for the honest
close of a forgotten session. The state effect — asserting `active` —
happens only as a forward move, through the guarded progress store; the
planners (`execution/lifecycle.py`) own every decision, these handlers just
load facts and bind the writes.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ._common import now_iso as _now_iso, report_plan as _report
from ..execution._store import ExecutionLoadError
from ..execution.lifecycle import ExecutionPlan, plan_close, plan_start, plan_work
from ..execution.sessions import (
    Session,
    append_session,
    complete_session,
    load_sessions,
    open_session,
)
from ..execution.staleness import stale_session_hours, stale_warning
from ..execution.templates import known_templates
from ..execution.work import append_work, load_session_work
from ..graph.state import ProgressStoreError, load_state, save_state


def _apply(root, plan: ExecutionPlan, store) -> CommandResult:
    """Bind a planner's decision to the filesystem (records, then state)."""
    if plan.exit_code != 0:
        return CommandResult(exit_code=plan.exit_code)
    if plan.session is not None:
        append_session(root, plan.session)
    if plan.work is not None:
        append_work(root, plan.work)
    if plan.close_session is not None:
        complete_session(
            root,
            plan.close_session["session_id"],
            ended_at=plan.close_session["ended_at"],
        )
    if plan.activate_node is not None:
        store.write_asserted(plan.activate_node, "active")
        save_state(store, root)
    return CommandResult(records_touched=plan.records_touched)


def _load_facts(root, command_name: str):
    """Load the store/session/work facts every session command needs.

    Returns (store, sessions, work_items) or None after printing the failure.
    """
    try:
        store = load_state(root)
        sessions = load_sessions(root)
        work_items = load_session_work(root)
    except (ExecutionLoadError, ProgressStoreError) as exc:
        print(f"{command_name}: FAILED — {exc}")
        return None
    return store, sessions, work_items


def start(ctx: Context) -> CommandResult:
    facts = _load_facts(ctx.root, "start")
    if facts is None:
        return CommandResult(exit_code=1)
    store, sessions, work_items = facts

    current = open_session(sessions)
    plan = plan_start(
        ctx.args.node_id,
        node_state=store.state_of(ctx.args.node_id),
        open_session_id=current.id if current is not None else None,
        existing_session_ids=[s.id for s in sessions],
        existing_work_ids=[w.id for w in work_items],
        now=_now_iso(),
        template=ctx.args.template,
        known_templates=known_templates(ctx.root),
    )
    _report(plan)
    return _apply(ctx.root, plan, store)


def _warn_if_stale(root, current: Session | None) -> None:
    """Print the stale-open-session warning (warn-only, never blocks)."""
    if current is None:
        return
    warning = stale_warning(
        current, now=_now_iso(), threshold_hours=stale_session_hours(root)
    )
    if warning is not None:
        print(f"[warning] {warning}")


def work(ctx: Context) -> CommandResult:
    facts = _load_facts(ctx.root, "work")
    if facts is None:
        return CommandResult(exit_code=1)
    store, sessions, work_items = facts

    current = open_session(sessions)
    _warn_if_stale(ctx.root, current)
    plan = plan_work(
        ctx.args.node_id,
        node_state=store.state_of(ctx.args.node_id),
        open_session_id=current.id if current is not None else None,
        existing_work_ids=[w.id for w in work_items],
        now=_now_iso(),
        blocked=ctx.args.blocked,
        notes=ctx.args.notes,
        minutes=ctx.args.minutes,
    )
    _report(plan)
    return _apply(ctx.root, plan, store)


def close(ctx: Context) -> CommandResult:
    facts = _load_facts(ctx.root, "session close")
    if facts is None:
        return CommandResult(exit_code=1)
    _store_unused, sessions, _work_unused = facts

    current = open_session(sessions)
    plan = plan_close(
        open_session_id=current.id if current is not None else None,
        started_at=current.started_at if current is not None else None,
        end=ctx.args.end,
        now=_now_iso(),
    )
    _report(plan)
    return _apply(ctx.root, plan, None)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="start",
            kind=Kind.MUTATING,
            handler=start,
            help="Open a new session with its first work item on a node.",
        )
    )
    registry.register(
        Command(
            name="work",
            kind=Kind.MUTATING,
            handler=work,
            help="Add a work item for a node to the open session.",
        )
    )
    registry.register(
        Command(
            name="session close",
            kind=Kind.MUTATING,
            handler=close,
            help="Complete the open session (--end records an honest past end time).",
        )
    )
