"""Whole-layer validation for the execution files (`validate execution`).

Checks structure, referential integrity, and per-status required fields —
and deliberately nothing about node *state*: state gates live in commands,
and history may legitimately outlive the state that permitted it (a blocker
created on an available node whose readiness later flipped to locked is
valid history, not a defect).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..graph.nodes import NodeLoadError, load_nodes
from ._store import ExecutionLoadError
from .blockers import load_blockers
from .remediation import load_remediation_actions
from .reviews import OUTCOMES, load_reviews
from .sessions import load_sessions
from .work import load_session_work


@dataclass
class ExecutionValidationResult:
    session_count: int = 0
    work_count: int = 0
    blocker_count: int = 0
    remediation_count: int = 0
    review_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _duplicates(ids: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for record_id in ids:
        if record_id in seen and record_id not in dupes:
            dupes.append(record_id)
        seen.add(record_id)
    return dupes


def _parseable(timestamp: str) -> datetime | None:
    try:
        return datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return None


def load_and_validate_execution(root: Path | str) -> ExecutionValidationResult:
    result = ExecutionValidationResult()
    errors = result.errors

    def safe(loader):
        try:
            return loader(root)
        except ExecutionLoadError as exc:
            errors.append(str(exc))
            return []

    sessions = safe(load_sessions)
    work_items = safe(load_session_work)
    blockers = safe(load_blockers)
    actions = safe(load_remediation_actions)
    reviews = safe(load_reviews)

    result.session_count = len(sessions)
    result.work_count = len(work_items)
    result.blocker_count = len(blockers)
    result.remediation_count = len(actions)
    result.review_count = len(reviews)

    # Known graph node ids, for reference checks. A broken graph is its own
    # layer's failure; here it only means node refs cannot be checked.
    try:
        known_nodes = {node.id for node in load_nodes(root)}
    except NodeLoadError as exc:
        errors.append(f"cannot check node references — graph failed to load: {exc}")
        known_nodes = None

    for collection, kind in (
        (sessions, "session"),
        (work_items, "work item"),
        (blockers, "blocker"),
        (actions, "remediation action"),
        (reviews, "review"),
    ):
        for dupe in _duplicates([r.id for r in collection]):
            errors.append(f"duplicate {kind} id {dupe!r}.")

    # --- Sessions: one open at most; completed needs an end after the start.
    open_ids = [s.id for s in sessions if s.status == "open"]
    if len(open_ids) > 1:
        errors.append(f"more than one open session: {', '.join(open_ids)}.")
    for session in sessions:
        if session.status == "open" and session.ended_at is not None:
            errors.append(f"session {session.id}: open but has ended_at.")
        if session.status == "completed":
            if not session.ended_at:
                errors.append(f"session {session.id}: completed without ended_at.")
            else:
                started = _parseable(session.started_at)
                ended = _parseable(session.ended_at)
                if started is None or ended is None:
                    errors.append(f"session {session.id}: unparseable timestamp(s).")
                elif ended < started:
                    errors.append(
                        f"session {session.id}: ended_at is before started_at."
                    )

    session_ids = {s.id for s in sessions}
    blocker_ids = {b.id for b in blockers}

    def check_node_ref(kind: str, record_id: str, node_id: str) -> None:
        if known_nodes is not None and node_id not in known_nodes:
            errors.append(f"{kind} {record_id}: unknown node {node_id!r}.")

    # --- Work items: real session, real node, blocked needs notes.
    for item in work_items:
        if item.session_id not in session_ids:
            errors.append(f"work item {item.id}: unknown session {item.session_id!r}.")
        check_node_ref("work item", item.id, item.node_id)
        if item.blocked and not item.notes:
            errors.append(f"work item {item.id}: blocked without notes.")

    # --- Blockers: real node; resolved needs its summary.
    for blocker in blockers:
        check_node_ref("blocker", blocker.id, blocker.node_id)
        if blocker.status == "resolved" and not blocker.resolution_summary:
            errors.append(f"blocker {blocker.id}: resolved without resolution_summary.")

    # --- Remediation actions: real node, real blocker link, completed needs result.
    for action in actions:
        check_node_ref("remediation action", action.id, action.node_id)
        if action.blocker_id is not None and action.blocker_id not in blocker_ids:
            errors.append(
                f"remediation action {action.id}: unknown blocker {action.blocker_id!r}."
            )
        if action.status == "completed" and not action.result_summary:
            errors.append(
                f"remediation action {action.id}: completed without result_summary."
            )

    # --- Reviews: real node; completed needs valid outcome + summary;
    #     cancelled needs its reason.
    for review in reviews:
        check_node_ref("review", review.id, review.node_id)
        if review.status == "completed":
            if review.outcome not in OUTCOMES:
                errors.append(
                    f"review {review.id}: completed with invalid outcome {review.outcome!r}."
                )
            if not review.result_summary:
                errors.append(f"review {review.id}: completed without result_summary.")
        if review.status == "cancelled" and not review.cancel_reason:
            errors.append(f"review {review.id}: cancelled without cancel_reason.")

    return result
