"""Next-node recommendation v1 — rank study candidates, each with a reason.

Issue #7 / PRD goal 1 ("What should I study next? Why that node?"). This module
owns the pure ranking rule; the `skilltrace next` command (commands/recommend.py)
loads nodes, edges, the progress store, and the policy track-weight map, calls
`recommend`, and formats the output — mirroring how sync wraps `sync_readiness`.

Candidates are the nodes the progress store records as `available` or `active`.
Readiness is the store's job (sync derives it, decision 2), so `next` *consumes*
recorded readiness rather than re-deriving it — which is exactly why a `locked`
node is never recommended as available. `--show-locked` appends locked nodes with
their unsatisfied hard prerequisites named, so "why is this blocked?" is answered
too.

Scoring v1 (decision 18 — the engine knows no track names; weights come from the
opaque policy map, an unmapped track scores 0 and warns):

    score = track_weight
          + LEVERAGE_WEIGHT * (# active outgoing edges)   # downstream leverage
          + FIT_WEIGHT     (if the node fits the session window)
          + ACTIVE_BONUS   (if the node is already active)

Full policy machinery (the factor-weight list, remediation/review/blocker terms)
is v0.6; v0.3 reads only the track-weight map and uses fixed coefficients for the
other three factors. Ties break by node id so ordering is deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .edges import GraphEdge
from .nodes import SkillNode
from .state import ProgressStore

# The two derived-readiness states a node may be recommended from. `locked` is
# excluded (never recommended as available); asserted `passed`/`mastered` are
# done, not candidates.
_CANDIDATE_STATES: frozenset[str] = frozenset({"available", "active"})

# A hard prerequisite is satisfied only once its source is asserted-complete
# (mirrors readiness._SATISFYING_STATES; kept local so this module stands alone).
_SATISFYING_STATES: frozenset[str] = frozenset({"passed", "mastered"})

# Fixed v0.3 coefficients for the non-track factors (the track weight itself
# comes from policy). Kept modest relative to the track weights so track priority
# leads, but large enough that leverage/fit/active break ties among same-track
# nodes.
LEVERAGE_WEIGHT: float = 0.5
FIT_WEIGHT: float = 1.0
ACTIVE_BONUS: float = 0.5


@dataclass(frozen=True)
class Recommendation:
    """One ranked study candidate, with the components behind its score.

    `reason` is the human-facing "why that node?" line; the numeric components are
    carried alongside so callers (and tests) can inspect the score without
    re-parsing prose.
    """

    node_id: str
    score: float
    track: str
    track_weight: float
    leverage: int
    fits_session: bool
    is_active: bool
    reason: str


@dataclass(frozen=True)
class LockedCandidate:
    """A locked node surfaced by `--show-locked`, with its blockers named.

    `unsatisfied` pairs each blocking hard-prerequisite source with its current
    state, so the report can say exactly what must be passed first.
    """

    node_id: str
    unsatisfied: tuple[tuple[str, str], ...]
    reason: str


@dataclass
class RecommendationResult:
    """The outcome of a recommendation run.

    `recommendations` is already ranked and truncated to the requested limit.
    `locked` is populated only when `show_locked` is set (and is not truncated —
    the limit bounds recommendations, not the locked appendix). `unmapped_tracks`
    lists every candidate track absent from the policy map, for a one-time warning.
    """

    recommendations: list[Recommendation]
    locked: list[LockedCandidate] = field(default_factory=list)
    unmapped_tracks: list[str] = field(default_factory=list)


def _outgoing_active_edge_counts(edges: list[GraphEdge]) -> dict[str, int]:
    """Count active outgoing edges per source node — the leverage proxy.

    The issue defines downstream leverage as the plain "outgoing edge count"; we
    scope it to `active` edges (a parked edge unlocks nothing) but deliberately
    count all edge types, matching the literal reading. Only hard edges truly
    unlock, but this is a v0.3 heuristic and the distinction moves no acceptance
    test.
    """
    counts: dict[str, int] = {}
    for edge in edges:
        if edge.active:
            counts[edge.source] = counts.get(edge.source, 0) + 1
    return counts


def _fits_session(micro_session_fit: dict, minutes: int) -> bool:
    """Whether a node fits a session of `minutes`, per its micro_session_fit block.

    A 15-minute window needs `can_fit_15_min`; a 16–30 window needs
    `can_fit_30_min`; anything longer is treated as a long block that fits every
    node. Missing flags read as falsey (the node does not fit the short window).
    """
    if minutes <= 15:
        return bool(micro_session_fit.get("can_fit_15_min"))
    if minutes <= 30:
        return bool(micro_session_fit.get("can_fit_30_min"))
    return True


def _reason(
    track: str, weight: float, mapped: bool, leverage: int, fits: bool,
    is_active: bool, minutes: int,
) -> str:
    if mapped:
        parts = [f"track {track!r} (weight {weight:g})"]
    else:
        parts = [f"track {track!r} (unmapped in policy, weight 0)"]
    if leverage:
        parts.append(f"unlocks {leverage} downstream edge(s)")
    if fits:
        parts.append(f"fits a {minutes}-min session")
    if is_active:
        parts.append("continues active work")
    return "; ".join(parts)


def _locked_candidates(
    nodes: list[SkillNode], edges: list[GraphEdge], store: ProgressStore
) -> list[LockedCandidate]:
    """List `locked` nodes with their unsatisfied active hard-prerequisite sources.

    Only active hard-prerequisite edges lock (soft/remediation never do), so only
    those appear as blockers. Sorted by node id for deterministic output.
    """
    hard_prereqs: dict[str, list[str]] = {}
    for edge in edges:
        if edge.active and edge.edge_type == "hard_prerequisite":
            hard_prereqs.setdefault(edge.target, []).append(edge.source)

    locked: list[LockedCandidate] = []
    for node in sorted(nodes, key=lambda n: n.id):
        if store.state_of(node.id) != "locked":
            continue
        unsatisfied = tuple(
            (source, store.state_of(source))
            for source in hard_prereqs.get(node.id, ())
            if store.state_of(source) not in _SATISFYING_STATES
        )
        if unsatisfied:
            reason = "blocked by: " + ", ".join(
                f"{source} ({state})" for source, state in unsatisfied
            )
        else:
            # Locked with no unsatisfied hard prereq means the store is stale
            # (prereqs now satisfied but sync hasn't run) — say so rather than
            # imply a phantom blocker.
            reason = "locked but no unsatisfied hard prerequisite — run 'skilltrace sync'"
        locked.append(LockedCandidate(node.id, unsatisfied, reason))
    return locked


def recommend(
    nodes: list[SkillNode],
    edges: list[GraphEdge],
    store: ProgressStore,
    track_weights: dict[str, float],
    *,
    minutes: int,
    limit: int,
    show_locked: bool = False,
) -> RecommendationResult:
    """Rank `available`/`active` nodes for a `minutes`-long session.

    Pure of I/O: the caller loads nodes, edges, the store, and the policy
    track-weight map. Returns the top `limit` recommendations (ranked by score,
    ties broken by node id), the locked appendix when `show_locked` is set, and
    the set of candidate tracks missing from `track_weights`.
    """
    leverage_counts = _outgoing_active_edge_counts(edges)
    recommendations: list[Recommendation] = []
    unmapped: set[str] = set()

    for node in nodes:
        state = store.state_of(node.id)
        if state not in _CANDIDATE_STATES:
            continue

        mapped = node.track in track_weights
        weight = float(track_weights[node.track]) if mapped else 0.0
        if not mapped:
            unmapped.add(node.track)

        leverage = leverage_counts.get(node.id, 0)
        fits = _fits_session(node.micro_session_fit, minutes)
        is_active = state == "active"

        score = (
            weight
            + LEVERAGE_WEIGHT * leverage
            + (FIT_WEIGHT if fits else 0.0)
            + (ACTIVE_BONUS if is_active else 0.0)
        )
        recommendations.append(
            Recommendation(
                node_id=node.id,
                score=score,
                track=node.track,
                track_weight=weight,
                leverage=leverage,
                fits_session=fits,
                is_active=is_active,
                reason=_reason(node.track, weight, mapped, leverage, fits, is_active, minutes),
            )
        )

    recommendations.sort(key=lambda rec: (-rec.score, rec.node_id))
    result = RecommendationResult(
        recommendations=recommendations[:limit],
        unmapped_tracks=sorted(unmapped),
    )
    if show_locked:
        result.locked = _locked_candidates(nodes, edges, store)
    return result
