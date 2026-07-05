"""Remediation-edge activation — derived on demand, never stored (CONTEXT.md).

An in-force `remediation` edge activates when its target has an open Blocker
or has reached the policy failed-attempt threshold without a pass, and it
deactivates when the remediation node is passed or the trigger clears. While
active it raises the remediation node's recommendation priority only — it
never locks the target or alters progress, so nothing here writes anything.

An open blocker always activates; only the attempt threshold is tunable, so
a missing or unreadable remediation seed stands the attempt trigger down
without touching the blocker trigger.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..evidence.attempts import AssessmentAttempt
from ..execution.blockers import Blocker
from ..graph.edges import GraphEdge
from ..graph.state import ProgressStore
from .loading import PolicyLoadError, load_policy_doc

# A pass on either end quiets its side of the edge: a passed/mastered
# remediation node deactivates outright; a passed/mastered target clears the
# attempt trigger (an open blocker on it still activates).
_PASSED_STATES: frozenset[str] = frozenset({"passed", "mastered"})


@dataclass(frozen=True)
class ActiveRemediation:
    """One remediation edge currently applying pressure, with its trigger."""

    edge_id: str
    remediation_node: str
    target: str
    trigger: str


def load_failed_attempt_threshold(root: Path | str) -> int | None:
    try:
        doc = load_policy_doc(root, "remediation.yaml")
    except PolicyLoadError:
        return None
    value = doc.get("failed_attempt_threshold")
    return value if isinstance(value, int) and value > 0 else None


def active_remediations(
    edges: list[GraphEdge],
    *,
    store: ProgressStore,
    blockers: list[Blocker],
    attempts: list[AssessmentAttempt],
    failed_attempt_threshold: int | None,
) -> list[ActiveRemediation]:
    """The remediation edges active right now, in edge-file order."""
    open_blockers: dict[str, list[str]] = {}
    for blocker in blockers:
        if blocker.status == "open":
            open_blockers.setdefault(blocker.node_id, []).append(blocker.id)

    failed_counts: dict[str, int] = {}
    for attempt in attempts:
        if attempt.outcome == "failed":
            failed_counts[attempt.node_id] = failed_counts.get(attempt.node_id, 0) + 1

    active: list[ActiveRemediation] = []
    for edge in edges:
        if edge.edge_type != "remediation" or not edge.active:
            continue
        if store.state_of(edge.source) in _PASSED_STATES:
            continue

        trigger: str | None = None
        blocking = open_blockers.get(edge.target)
        if blocking:
            trigger = f"open blocker {', '.join(blocking)}"
        elif (
            failed_attempt_threshold is not None
            and store.state_of(edge.target) not in _PASSED_STATES
            and failed_counts.get(edge.target, 0) >= failed_attempt_threshold
        ):
            trigger = (
                f"{failed_counts[edge.target]} failed attempt(s) without a pass "
                f"(threshold {failed_attempt_threshold})"
            )
        if trigger is not None:
            active.append(
                ActiveRemediation(
                    edge_id=edge.id,
                    remediation_node=edge.source,
                    target=edge.target,
                    trigger=trigger,
                )
            )
    return active
