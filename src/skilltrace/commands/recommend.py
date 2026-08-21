"""`skilltrace next` — Mentor-voice ranked recommendations for the study session.

Loads nodes, edges, the progress store, and the policy weight maps, derives
the advisory pressure (active remediation edges, open blockers), ranks the
`available`/`active` candidates (`..graph.recommendation.recommend`), and
renders each with Mentor-voice contrastive rationale: why *this* skill over
the others, guided **Where to learn** and **How to proceed**, and one **Do
this next** per candidate.

Per the #30 resolution: learner language on the surface, CLI remains the v1
UI. The ranking engine (`..graph.recommendation`) is preserved as-is; all
enrichment is in the output layer. Read-only: the dispatcher appends no audit
event.

Readiness lives in the progress store (sync derives it); this command consumes
it, so a `locked` node is never recommended as available. `--show-locked` appends
the locked nodes with their unsatisfied hard prerequisites named.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .. import render
from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence._schema import EvidenceLoadError
from ..evidence.attempts import load_assessment_attempts
from ..execution._store import ExecutionLoadError
from ..execution.blockers import load_blockers
from ..graph.edges import EdgeLoadError, GraphEdge, load_edges
from ..graph.nodes import NodeLoadError, SkillNode, load_nodes
from ..graph.recommendation import Recommendation, RecommendationResult, recommend
from ..graph.state import ProgressStoreError, load_state
from ..policy.remediation_edges import (
    ActiveRemediation,
    active_remediations,
    load_failed_attempt_threshold,
)
from ..resources.registry import (
    LearningResource,
    ResourceLoadError,
    load_resources,
    resources_for_node,
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


# --- Mentor-voice prose helpers -----------------------------------------------


def _state_label(state: str) -> str:
    return {
        "available": "Ready to start",
        "active": "In progress",
    }.get(state, state.capitalize())


def _effort_phrase(node: SkillNode, minutes: int) -> str:
    """One phrase describing estimated effort, given the session window."""
    effort = node.estimated_effort
    min_m = effort.get("min_minutes")
    max_m = effort.get("max_minutes")
    if min_m is not None and max_m is not None:
        return f"Estimated effort: {min_m}–{max_m} min"
    if min_m is not None:
        return f"Estimated effort: {min_m}+ min"
    if max_m is not None:
        return f"Estimated effort: up to {max_m} min"
    # Fall back to session fit language when no effort data is recorded.
    msf = node.micro_session_fit
    if minutes <= 15 and msf.get("can_fit_15_min"):
        return "Fits a 15-min block"
    if minutes <= 30 and msf.get("can_fit_30_min"):
        return "Fits a 30-min block"
    if msf.get("requires_long_block"):
        return "Requires a longer block"
    return ""


def _contrastive_brief(
    rec: Recommendation,
    rank: int,
    total: int,
    node: SkillNode,
    minutes: int,
) -> str:
    """Conversational 'why this skill, not the others' rationale.

    The first candidate gets the strongest affirmative framing; lower-ranked
    ones get comparative framing that names why they score below the top pick.
    Pressure signals (remediation boost, open blocker) are surfaced naturally
    in-sentence, not as a label dump.
    """
    sentences: list[str] = []

    # Opening sentence: affirmative for #1, comparative for the rest.
    if rank == 1:
        if rec.is_active:
            sentences.append(
                f"Your best move right now is to keep going on {node.title} — "
                "you've already started this one."
            )
        elif rec.remediation_boosted:
            sentences.append(
                f"{node.title} rises to the top because an active remediation "
                "edge is flagging it — clearing this unblocks your progress."
            )
        else:
            sentences.append(
                f"{node.title} is the top pick for this session — "
                f"it's in the {rec.track!r} track and scores highest overall."
            )
    else:
        ordinal = {2: "second", 3: "third", 4: "fourth", 5: "fifth"}.get(rank, f"#{rank}")
        sentences.append(
            f"Also a strong option ({ordinal} of {total}): {node.title}."
        )

    # Leverage signal.
    if rec.leverage == 1:
        sentences.append("Passing this unlocks one downstream skill.")
    elif rec.leverage > 1:
        sentences.append(f"Passing this unlocks {rec.leverage} downstream skills.")

    # Session fit.
    if rec.fits_session:
        if minutes <= 15:
            sentences.append("It fits a 15-min micro-session.")
        elif minutes <= 30:
            sentences.append("It fits a 30-min session.")

    # Pressure signals.
    if rec.open_blocked:
        sentences.append(
            "There's an open blocker on this node — advisory only, not stopping you."
        )

    # Summary of the node itself.
    sentences.append(node.summary)

    return " ".join(sentences)


def _how_to_proceed(node: SkillNode, state: str, minutes: int) -> str:
    """Guided instruction for the candidate node."""
    effort = _effort_phrase(node, minutes)
    if state == "active":
        base = f"You're already working on {node.title} — bring the next piece of evidence back when it's ready."
    else:
        base = f"Start studying {node.title} and submit evidence when your work is ready."
    if effort:
        return f"{base} {effort}."
    return base


def _do_this_next(node: SkillNode, state: str) -> str:
    """The single concrete next action for this candidate."""
    if state == "active":
        return f"Continue {node.id}: `skilltrace session start --node {node.id}`"
    return f"Start studying {node.id}: `skilltrace session start --node {node.id}`"


def _resource_lines(resources: list[LearningResource]) -> list[str]:
    """Format resource lines for the Where to learn section."""
    if not resources:
        return ["(no resources linked to this skill)"]
    lines = []
    for r in resources:
        name = r.id.replace("-", " ").title()
        if r.url:
            lines.append(f"{name} -- {r.url}")
        elif r.local_path:
            lines.append(f"{name} -- {r.local_path}")
        else:
            lines.append(name)
    return lines


# --- Report renderer ----------------------------------------------------------


def _print_mentor_report(
    result: RecommendationResult,
    minutes: int,
    limit: int,
    node_map: dict[str, SkillNode],
    all_resources: list[LearningResource],
    store,
    active_remediations_list: list[ActiveRemediation],
) -> None:
    """Render the enriched Mentor-voice next report.

    One kicker block per ranked candidate: title + state, contrastive brief,
    Where to learn, How to proceed, Do this next. Warnings and locked appendix
    follow the same rules as before. Advisory remediation lines close the output.
    """
    for track in result.unmapped_tracks:
        print(
            render.warning(
                f"track {track!r} is not in policy/recommendation.yaml "
                "track_weights (scored 0); add it there to prioritize its nodes."
            )
        )

    if not result.recommendations:
        lines: list[str] = []
        lines.append(render.section_kicker("What's next"))
        lines.extend(
            render.section_brief(
                f"There's nothing available or active to recommend for a {minutes}-min session. "
                "Run `skilltrace sync` if this looks wrong — readiness may be stale."
            )
        )
        lines.extend(
            render.section_do_this_next("Refresh readiness: `skilltrace sync`")
        )
        for line in lines:
            print(line)
        return

    total = len(result.recommendations)
    session_label = f"{minutes}-min session"

    for rank, rec in enumerate(result.recommendations, start=1):
        node = node_map.get(rec.node_id)
        if node is None:
            # Should never happen (nodes and store are loaded together), but
            # degrade gracefully rather than crash.
            print(f"  {rank}. {rec.node_id}")
            continue

        state = store.state_of(rec.node_id)
        node_resources = resources_for_node(rec.node_id, all_resources)

        lines = []
        lines.append(render.section_kicker(f"Option {rank} — {session_label}"))
        lines.extend(render.section_title_state(node.title, _state_label(state)))
        lines.extend(
            render.section_brief(
                _contrastive_brief(rec, rank, total, node, minutes)
            )
        )
        lines.extend(render.section_where_to_learn(_resource_lines(node_resources)))
        lines.extend(render.section_how_to_proceed(_how_to_proceed(node, state, minutes)))
        lines.extend(render.section_do_this_next(_do_this_next(node, state)))

        for line in lines:
            print(line)

        # Separator between candidates (not after the last one).
        if rank < total:
            print()
            print("---")

    # Closing context: advisory remediation lines.
    for remediation in active_remediations_list:
        print()
        print(
            render.advisory(
                f"remediation edge active: {remediation.remediation_node} "
                f"supports {remediation.target} — {remediation.trigger}."
            )
        )

    # Locked appendix.
    if result.locked:
        print()
        print(f"Locked ({len(result.locked)}):")
        for locked in result.locked:
            print(f"  {locked.node_id} — {locked.reason}")


def recommend_next(ctx: Context) -> CommandResult:
    """Load the graph + store + policy + resources, rank candidates, and render.

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

    # Resources are loaded gracefully: a missing or broken registry never fails
    # `next`; it just renders "(no resources linked)" in each Where to learn block.
    try:
        all_resources = load_resources(root)
    except ResourceLoadError:
        all_resources = []

    node_map = {n.id: n for n in nodes}

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
    _print_mentor_report(
        result,
        ctx.args.minutes,
        ctx.args.limit,
        node_map,
        all_resources,
        store,
        active,
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
