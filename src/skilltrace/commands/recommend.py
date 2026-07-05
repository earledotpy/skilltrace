"""`skilltrace next` — recommend prerequisite-safe nodes with a stated reason.

Loads nodes, edges, the progress store, and the policy weight maps, derives
the advisory pressure (active remediation edges, open blockers), ranks the
`available`/`active` candidates (`..graph.recommendation.recommend`), and
prints each with its "why that node?" reason — naming any policy effect on
the score. Read-only: the dispatcher appends no audit event, matching how
`validate graph` reports without mutating.

Readiness lives in the progress store (sync derives it); this command consumes
it, so a `locked` node is never recommended as available. `--show-locked` appends
the locked nodes with their unsatisfied hard prerequisites named.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence._schema import EvidenceLoadError
from ..evidence.attempts import load_assessment_attempts
from ..execution._store import ExecutionLoadError
from ..execution.blockers import load_blockers
from ..graph.edges import EdgeLoadError, GraphEdge, load_edges
from ..graph.nodes import NodeLoadError, load_nodes
from ..graph.recommendation import RecommendationResult, recommend
from ..graph.state import ProgressStoreError, load_state
from ..policy.remediation_edges import (
    ActiveRemediation,
    active_remediations,
    load_failed_attempt_threshold,
)

_EDGES_RELPATH = "graph/edges.yaml"
_POLICY_RELPATH = Path("policy") / "recommendation.yaml"


def _load_weight_map(root: Path, key: str) -> dict[str, float]:
    """Read one weight map from `policy/recommendation.yaml`.

    A missing file, missing key, or non-mapping value yields an empty map so
    `next` still runs and exits 0; individual non-numeric weights are skipped
    rather than aborting the whole read.
    """
    path = root / _POLICY_RELPATH
    if not path.exists():
        return {}
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    policy = doc.get("recommendation_policy") if isinstance(doc, dict) else None
    raw = policy.get(key) if isinstance(policy, dict) else None
    if not isinstance(raw, dict):
        return {}
    weights: dict[str, float] = {}
    for name, value in raw.items():
        try:
            weights[str(name)] = float(value)
        except (TypeError, ValueError):
            continue
    return weights


def load_track_weights(root: Path) -> dict[str, float]:
    """The opaque track-weight map (decision 18: the engine attaches no meaning
    to track names; an unmapped track scores 0 and warns)."""
    return _load_weight_map(root, "track_weights")


def load_factor_weights(root: Path) -> dict[str, float]:
    """The v0.6 factor-weight map; empty falls back to the ranking's built-in
    defaults."""
    return _load_weight_map(root, "factor_weights")


def _print_report(result: RecommendationResult, minutes: int, limit: int) -> None:
    for track in result.unmapped_tracks:
        print(
            f"[warning] track {track!r} is not in policy/recommendation.yaml "
            "track_weights (scored 0); add it there to prioritize its nodes."
        )

    if not result.recommendations:
        print(
            f"next: no available or active nodes to recommend for a {minutes}-min "
            "session — run 'skilltrace sync' if this is unexpected."
        )
    else:
        print(
            f"next: top {len(result.recommendations)} (of up to {limit}) for a "
            f"{minutes}-min session:"
        )
        for rank, rec in enumerate(result.recommendations, start=1):
            print(f"  {rank}. {rec.node_id}  (score {rec.score:g})")
            print(f"     {rec.reason}")

    if result.locked:
        print(f"\nlocked ({len(result.locked)}):")
        for locked in result.locked:
            print(f"  {locked.node_id} - {locked.reason}")


def recommend_next(ctx: Context) -> CommandResult:
    """Load the graph + store + policy, rank candidates, and print the report.

    Loader failures fail the command (non-zero exit, no event), matching sync and
    validate; a valid graph always exits 0 even when nothing is recommendable.
    """
    root = ctx.root

    try:
        nodes = load_nodes(root)
        edges: list[GraphEdge] = (
            load_edges(root) if (root / _EDGES_RELPATH).exists() else []
        )
        store = load_state(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"next: FAILED — {exc}")
        return CommandResult(exit_code=1)

    active, blocked = _policy_pressure(root, edges, store)
    result = recommend(
        nodes,
        edges,
        store,
        load_track_weights(root),
        minutes=ctx.args.minutes,
        limit=ctx.args.limit,
        show_locked=ctx.args.show_locked,
        factor_weights=load_factor_weights(root),
        remediation_boosted={r.remediation_node for r in active},
        open_blocked=blocked,
    )
    _print_report(result, ctx.args.minutes, ctx.args.limit)
    for remediation in active:
        print(
            f"[advisory] remediation edge active: {remediation.remediation_node} "
            f"supports {remediation.target} — {remediation.trigger}."
        )
    return CommandResult()


def _policy_pressure(
    root: Path, edges: list[GraphEdge], store
) -> tuple[list[ActiveRemediation], set[str]]:
    """Derive the active remediation edges and open-blocked nodes (advisory-only).

    Each history degrades independently: an unreadable (or, for attempts, not
    yet created) file reads as an empty history rather than failing `next` or
    dropping the pressure the other source still supports — the base ranking
    already has its facts.
    """
    try:
        blockers = load_blockers(root)
    except ExecutionLoadError:
        blockers = []
    try:
        attempts = load_assessment_attempts(root)
    except EvidenceLoadError:
        attempts = []
    blocked = {b.node_id for b in blockers if b.status == "open"}
    active = active_remediations(
        edges,
        store=store,
        blockers=blockers,
        attempts=attempts,
        failed_attempt_threshold=load_failed_attempt_threshold(root),
    )
    return active, blocked


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="next",
            kind=Kind.READ_ONLY,
            handler=recommend_next,
            help="Recommend prerequisite-safe nodes sized to available minutes.",
        )
    )
