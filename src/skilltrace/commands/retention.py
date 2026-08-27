"""`skilltrace retention status [--node-id]` — read-only retention overlay.

Per ``docs/spec-tier2-retention-analytics.md`` §2.3: derives the full
memory-state picture across every passed/mastered node from the review
history and the policy seed, with no writes and no audit event. The
``today`` clock is read once at the top of the handler — the only
``date.today()`` call site in the retention code path (T-Clock D1).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from ..context import load_context_lenient
from ..dispatch import Command, CommandResult, Context, Kind, Registry
from ..graph.nodes import NodeLoadError
from ..graph.state import ProgressStoreError
from ..policy.loading import PolicyLoadError, load_policy_doc
from ..policy.retention_model import (
    derive_memory_states,
    retention_seed_from_doc,
)
from ._common import now_iso


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _state_for_all(root: Path, today: date):
    """Compute memory state for every passed/mastered node.

    Returns ``(states, view, error_message)``. ``view`` is the joined
    view so callers can reuse it for node-id validation without a
    second ``load_context_lenient`` round-trip. ``error_message`` is
    non-empty when the command cannot produce output; the caller
    renders it and exits 1.
    """
    try:
        view = load_context_lenient(root)
    except (NodeLoadError, ProgressStoreError) as exc:
        return None, None, f"retention status: FAILED -- {exc}"
    try:
        seed_doc = load_policy_doc(root, "retention_model.yaml")
    except PolicyLoadError as exc:
        return None, view, f"retention status: FAILED -- {exc}"
    seed = retention_seed_from_doc(seed_doc)
    states = derive_memory_states(
        nodes=view.nodes,
        store=view.store,
        reviews=view.reviews,
        seed=seed,
        today=today,
    )
    return states, view, ""


def retention_status(ctx: Context) -> CommandResult:
    root = ctx.root
    node_id = getattr(ctx.args, "node_id", None)
    today = _today()

    states, view, error = _state_for_all(root, today)
    if error:
        print(error)
        return CommandResult(exit_code=1)

    if node_id is not None:
        if node_id not in view.node_map:
            print(f"retention status: FAILED -- unknown node {node_id}.")
            return CommandResult(exit_code=1)
        states = [s for s in states if s.node_id == node_id]
        if not states:
            print(
                f"retention status: {node_id} is not passed or mastered — "
                "the retention model only derives memory state for those."
            )
            return CommandResult()

    if not states:
        print("retention status: no passed or mastered nodes yet — nothing to derive.")
        return CommandResult()

    print(
        f"retention status ({len(states)} node(s), computed {now_iso()}, today={today.isoformat()})"
    )
    print("-" * 72)
    for s in states:
        title = view.titles.get(s.node_id, "")
        marker = " BELOW THRESHOLD" if s.below_threshold else ""
        heading = f"{s.node_id}"
        if title:
            heading = f"{title} ({s.node_id})"
        print(
            f"{heading}  state={s.asserted_state}  "
            f"anchor={s.anchor_kind}@{s.anchored_at.isoformat()}"
        )
        print(
            f"  half_life={s.half_life_days:g}d  confidence={s.confidence:.4f}  "
            f"suggested_next={s.suggested_next_review.isoformat()}{marker}"
        )
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="retention status",
            kind=Kind.READ_ONLY,
            handler=retention_status,
            help="Derive the retention model's memory state for every passed/mastered node (or one node).",
        )
    )
