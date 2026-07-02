"""Readiness derivation — the `locked`/`available` half of the state model.

Decision 2: `locked` and `available` are *derived* readiness, recomputable from
the graph at any time; `active`/`passed`/`mastered` are *asserted* progress that
sync never touches. This module owns the derivation rule and nothing else — the
`skilltrace sync` command (commands/sync.py) loads the three sources, calls
`sync_readiness`, and persists the store, mirroring how `validate graph` wraps
the pure `check_graph`.

The rule (issue #6): a node is `available` iff every *active hard-prerequisite*
edge pointing at it has a source that is `passed` or `mastered`; otherwise it is
`locked`. Soft-prerequisite and remediation edges never affect readiness — only
in-force hard prerequisites lock.

**Single pass, order-independent.** Availability requires a prerequisite to be
`passed`/`mastered`, and sync writes *only* derived states — so the set of
passed/mastered nodes is fixed for the whole run. A node's readiness therefore
never depends on another node's *derived* readiness, only on the (immovable)
asserted set. There is no cascade to iterate to a fixpoint; recomputing every
node once against the store is exact regardless of iteration order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .edges import GraphEdge
from .nodes import SkillNode
from .state import ASSERTED_STATES, ProgressStore

# A prerequisite is satisfied only once its source is asserted-complete.
_SATISFYING_STATES: frozenset[str] = frozenset({"passed", "mastered"})


@dataclass(frozen=True)
class ReadinessChange:
    """One node whose derived readiness flipped during a sync run.

    Carries the before/after states for a human-readable report; the audit
    event records only the node id (see `SyncResult.changed_ids`).
    """

    node_id: str
    old_state: str
    new_state: str


@dataclass
class SyncResult:
    """The outcome of a readiness sync: what flipped and how much was scanned.

    `changes` lists only genuine readiness flips (a node whose recorded state
    differed from its recomputed one). `skipped_asserted` counts nodes left
    untouched because their state is asserted progress — the guarantee that sync
    never moves asserted progress, made visible in the report.
    """

    changes: list[ReadinessChange] = field(default_factory=list)
    node_count: int = 0
    skipped_asserted: int = 0

    @property
    def changed_ids(self) -> list[str]:
        """Sorted node ids for the audit event's `records_touched`."""
        return sorted(change.node_id for change in self.changes)


def _active_hard_prereqs_by_target(edges: Iterable[GraphEdge]) -> dict[str, list[str]]:
    """Map each node id to the sources of its active hard-prerequisite edges.

    Only `active` `hard_prerequisite` edges are indexed — soft and remediation
    edges, and parked (inactive) hard edges, never lock a node.
    """
    by_target: dict[str, list[str]] = {}
    for edge in edges:
        if edge.active and edge.edge_type == "hard_prerequisite":
            by_target.setdefault(edge.target, []).append(edge.source)
    return by_target


def derive_readiness(
    node_id: str, prereq_sources: dict[str, list[str]], store: ProgressStore
) -> str:
    """Return the derived readiness (`available`/`locked`) for one node.

    `available` iff every active hard-prerequisite source is `passed`/`mastered`
    (a node with no such prerequisites is trivially available); otherwise
    `locked`. An absent prerequisite source reads as its `locked` floor and so
    keeps the target locked.
    """
    for source in prereq_sources.get(node_id, ()):  # only active hard prereqs
        if store.state_of(source) not in _SATISFYING_STATES:
            return "locked"
    return "available"


def sync_readiness(
    nodes: list[SkillNode], edges: list[GraphEdge], store: ProgressStore
) -> SyncResult:
    """Recompute derived readiness for every non-asserted node, mutating `store`.

    Pure of I/O: the caller loads the store and persists it. Nodes in an asserted
    state are skipped outright (asserted progress is never revoked by sync); the
    write still goes through `store.write_readiness`, whose guard refuses asserted
    targets as defense in depth. Only genuine flips are written and reported, so a
    node already at its derived state is left untouched (no `changed_at` churn).
    """
    prereq_sources = _active_hard_prereqs_by_target(edges)
    result = SyncResult(node_count=len(nodes))

    for node in nodes:
        current = store.state_of(node.id)  # absent -> derived floor (locked)
        if current in ASSERTED_STATES:
            result.skipped_asserted += 1
            continue
        desired = derive_readiness(node.id, prereq_sources, store)
        if desired != current:
            store.write_readiness(node.id, desired)
            result.changes.append(ReadinessChange(node.id, current, desired))

    return result
