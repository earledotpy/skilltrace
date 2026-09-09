"""Pure graph-impact core (v2.2): what a curriculum edit would change.

`compute_impact` is the TDD seam (spec §2): over already-loaded baseline and
current nodes/edges plus the *same* progress store, it reports readiness flips
on non-asserted nodes, asserted nodes a baseline-edge edit would "re-lock"
(reported as standing, never as flips), recommendation changes under both edge
sets with identical store/weights/boosts, and no-op edges. Reads relationships
only from the passed edge lists (plus the same derived-readiness code `sync`
uses) — never node frontmatter. Writes nothing, blocks nothing; the command
shell renders it. Mirrors `check_graph` / `recommend` / `plan_submit` in the
house pure-core style.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .edges import GraphEdge
from .nodes import SkillNode
from .readiness import _active_hard_prereqs_by_target, derive_readiness
from .recommendation import recommend
from .state import ASSERTED_STATES, ProgressStore


@dataclass(frozen=True)
class ReadinessFlip:
    """One non-asserted node whose derived readiness differs between sides."""

    node_id: str
    baseline_state: str
    current_state: str


@dataclass(frozen=True)
class RecommendationChange:
    """One node that entered, left, or moved in the ranked list."""

    node_id: str
    baseline_rank: int | None  # None = entered
    current_rank: int | None  # None = left


@dataclass(frozen=True)
class NoOpEdge:
    """An active hard-prerequisite edge whose removal changes nothing."""

    edge_id: str
    source: str
    target: str


@dataclass(frozen=True)
class DanglingReference:
    """A working-tree node deleted while an evidence file still names it.

    `referenced_by` names the referencing file(s) compactly (`spec:<id>`,
    `gate:<id>`, `record:<id>`, `attempt:<id>`); the diagnostic *lists*
    these where `validate graph`/`validate evidence` *error* on them
    (spec §2, D-Dangling) — release impact, never a block.
    """

    node_id: str
    referenced_by: tuple[str, ...]


@dataclass
class ImpactReport:
    """The advisory finding set for one baseline -> current comparison."""

    flips: list[ReadinessFlip] = field(default_factory=list)
    asserted_standing: list[str] = field(default_factory=list)
    recommendation_changes: list[RecommendationChange] = field(default_factory=list)
    dangling: list[DanglingReference] = field(default_factory=list)
    no_op_edges: list[NoOpEdge] = field(default_factory=list)

    @property
    def quiet(self) -> bool:
        """True when nothing would change — the happy 'no impact' report."""
        return not (
            self.flips
            or self.asserted_standing
            or self.recommendation_changes
            or self.dangling
            or self.no_op_edges
        )


def _readiness_map(
    node_ids: list[str], edges: list[GraphEdge], store: ProgressStore
) -> dict[str, str]:
    """Derived readiness per node under one edge set, against the shared store."""
    prereq_sources = _active_hard_prereqs_by_target(edges)
    return {
        node_id: derive_readiness(node_id, prereq_sources, store)
        for node_id in node_ids
    }


def _ranked_ids(
    nodes: list[SkillNode],
    edges: list[GraphEdge],
    store: ProgressStore,
    *,
    minutes: int,
    limit: int,
    factor_weights,
    track_weights,
    remediation_boosted: set[str],
    open_blocked: set[str],
    prereq_reviews_due,
    agent_boosted: set[str],
) -> list[str]:
    """One `recommend()` pass, flattened to its ranked candidate ids."""
    result = recommend(
        nodes,
        edges,
        store,
        track_weights or {},
        minutes=minutes,
        limit=limit,
        show_locked=False,
        factor_weights=factor_weights or {},
        remediation_boosted=remediation_boosted,
        open_blocked=open_blocked,
        prereq_reviews_due=prereq_reviews_due,
        agent_boosted=agent_boosted,
    )
    return [rec.node_id for rec in result.recommendations]


def _rec_changes(
    baseline_ranked: list[str], current_ranked: list[str]
) -> list[RecommendationChange]:
    """Entered/left/moved nodes between two ranked lists (1-based ranks)."""
    baseline_pos = {node_id: i + 1 for i, node_id in enumerate(baseline_ranked)}
    current_pos = {node_id: i + 1 for i, node_id in enumerate(current_ranked)}
    changes: list[RecommendationChange] = []
    for node_id, rank in baseline_pos.items():
        other = current_pos.get(node_id)
        if other != rank:
            changes.append(RecommendationChange(node_id, rank, other))
    for node_id, rank in current_pos.items():
        if node_id not in baseline_pos:
            changes.append(RecommendationChange(node_id, None, rank))
    changes.sort(key=lambda c: c.node_id)
    return changes


def compute_impact(
    baseline_nodes: list[SkillNode],
    baseline_edges: list[GraphEdge],
    current_nodes: list[SkillNode],
    current_edges: list[GraphEdge],
    store: ProgressStore,
    *,
    minutes: int = 60,
    limit: int = 5,
    factor_weights=None,
    track_weights=None,
    remediation_boosted: set[str] | None = None,
    open_blocked: set[str] | None = None,
    prereq_reviews_due=None,
    agent_boosted: set[str] | None = None,
    dangling_specs: list[tuple[str, str]] | None = None,
    dangling_gates: list[tuple[str, str]] | None = None,
    dangling_records: list[tuple[str, str, str | None]] | None = None,
    dangling_attempts: list[tuple[str, str]] | None = None,
) -> ImpactReport:
    """Compare two graph sides over one shared progress store. Pure of I/O.

    The command shell loads both sides (baseline via the git fetch seam or a
    second checkout) and calls this; nothing here touches disk. The dangling
    inputs are `(id, node_id)` pairs from the current working tree's
    evidence files (records additionally carry their spec id): any named
    node absent from the current node set is dangling (spec §2, D-Dangling).
    Nothing here writes, blocks, or revokes asserted progress.
    """
    current_ids = [node.id for node in current_nodes]

    report = ImpactReport()

    # --- Readiness flips (non-asserted nodes only) --------------------------
    baseline_ready = _readiness_map(
        [n.id for n in baseline_nodes], baseline_edges, store
    )
    current_ready = _readiness_map(current_ids, current_edges, store)
    for node_id in current_ids:
        if store.state_of(node_id) in ASSERTED_STATES:
            continue  # asserted progress stands; never reported as a flip
        before = baseline_ready.get(node_id)
        after = current_ready.get(node_id)
        if before is not None and before != after:
            report.flips.append(ReadinessFlip(node_id, before, after))
    report.flips.sort(key=lambda f: f.node_id)

    # --- Asserted nodes a current edge would re-lock (they stand) -------------
    # No baseline-edges guard: the headline case is a *new* prerequisite
    # (empty baseline) that would re-lock an asserted node — skipping it
    # would blind the diagnostic to exactly the edit it exists to review.
    for node_id in current_ids:
        if store.state_of(node_id) not in ASSERTED_STATES:
            continue
        if (
            baseline_ready.get(node_id) == "available"
            and current_ready.get(node_id) == "locked"
        ):
            report.asserted_standing.append(node_id)
    report.asserted_standing.sort()

    # --- Recommendation diff (identical inputs, two edge sets) --------------
    common_kwargs = dict(
        minutes=minutes,
        limit=limit,
        factor_weights=factor_weights,
        track_weights=track_weights,
        remediation_boosted=remediation_boosted or set(),
        open_blocked=open_blocked or set(),
        prereq_reviews_due=prereq_reviews_due or {},
        agent_boosted=agent_boosted or set(),
    )
    baseline_ranked = _ranked_ids(current_nodes, baseline_edges, store, **common_kwargs)
    current_ranked = _ranked_ids(current_nodes, current_edges, store, **common_kwargs)
    report.recommendation_changes = _rec_changes(baseline_ranked, current_ranked)

    # --- Dangling references: evidence names a node the tree deleted --------
    report.dangling = _dangling_refs(
        current_ids,
        specs=dangling_specs or [],
        gates=dangling_gates or [],
        records=dangling_records or [],
        attempts=dangling_attempts or [],
    )

    # --- No-op edges (counterfactual removal of active hard prereqs) --------
    report.no_op_edges = _no_op_edges(
        current_nodes, current_edges, store, current_ranked, **common_kwargs
    )

    return report


def _dangling_refs(
    current_ids: list[str],
    *,
    specs: list[tuple[str, str]],
    gates: list[tuple[str, str]],
    records: list[tuple[str, str, str | None]],
    attempts: list[tuple[str, str]],
) -> list[DanglingReference]:
    """Nodes the evidence trail still names but the working tree deleted.

    Records name a spec, not a node — resolve through the spec map built
    from the same `specs` input (an unknown spec resolves to its own id so
    it still surfaces rather than vanishing). Sorted by node id for a
    stable advisory report.
    """
    present = set(current_ids)
    spec_to_node = {spec_id: node_id for spec_id, node_id in specs}
    refs: dict[str, set[str]] = {}
    for spec_id, node_id in specs:
        if node_id not in present:
            refs.setdefault(node_id, set()).add(f"spec:{spec_id}")
    for gate_id, node_id in gates:
        if node_id not in present:
            refs.setdefault(node_id, set()).add(f"gate:{gate_id}")
    for record_id, spec_id, _location in records:
        node_id = spec_to_node.get(spec_id, spec_id)
        if node_id not in present:
            refs.setdefault(node_id, set()).add(f"record:{record_id}")
    for attempt_id, node_id in attempts:
        if node_id not in present:
            refs.setdefault(node_id, set()).add(f"attempt:{attempt_id}")
    return [
        DanglingReference(node_id, tuple(sorted(names)))
        for node_id, names in sorted(refs.items())
    ]


def _no_op_edges(
    nodes: list[SkillNode],
    edges: list[GraphEdge],
    store: ProgressStore,
    current_ranked: list[str],
    **common_kwargs,
) -> list[NoOpEdge]:
    """Active hard-prereq edges whose removal changes no readiness and no rec.

    Counterfactual per edge: recompute readiness (asserted nodes cannot flip by
    construction) and re-rank with that one edge gone; an unchanged readiness
    map and an unchanged ranked list make the edge a no-op. Cheap at seed
    scale (100 nodes / 157 edges).
    """
    noop: list[NoOpEdge] = []
    baseline_ready = _readiness_map([n.id for n in nodes], edges, store)
    for edge in edges:
        if not (edge.active and edge.edge_type == "hard_prerequisite"):
            continue
        reduced = [e for e in edges if e.id != edge.id]
        reduced_ready = _readiness_map([n.id for n in nodes], reduced, store)
        if any(baseline_ready[nid] != reduced_ready[nid] for nid in baseline_ready):
            continue
        reduced_ranked = _ranked_ids(nodes, reduced, store, **common_kwargs)
        if reduced_ranked != current_ranked:
            continue
        noop.append(NoOpEdge(edge.id, edge.source, edge.target))
    noop.sort(key=lambda e: e.edge_id)
    return noop


