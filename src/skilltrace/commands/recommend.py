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

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .. import render
from ..mentor.cards import (
    CardPart,
    Kicker,
    Label,
    Lead,
    MentorCard,
    Para,
    Pill,
    Sub,
    Title,
)
from ..context import load_context_lenient
from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..graph.edges import EdgeLoadError, GraphEdge
from ..graph.nodes import NodeLoadError, SkillNode
from ..graph.recommendation import (
    LockedCandidate,
    Recommendation,
    RecommendationResult,
    recommend,
)
from ..graph.state import ProgressStoreError
from ..mentor.prose import NodeState, resource_lines, state_phrase
from ..execution.overdue import utc_today
from ..policy.agent_input import load_agent_recommendations
from ..policy.remediation_edges import (
    ActiveRemediation,
    active_remediations,
)
from ..policy.sequencing import prereq_retention_urgency
from ..policy.weights import load_factor_weights, load_track_weights
from ..resources.registry import LearningResource


# --- Mentor-voice prose helpers -----------------------------------------------


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
    if rec.prereq_reviews_due:
        n = rec.prereq_reviews_due
        noun = "prerequisite is" if n == 1 else "prerequisites are"
        sentences.append(
            f"{n} of this node's {noun} below retention threshold — "
            "a quick review keeps the foundation solid (advisory)."
        )
    if rec.agent_boosted:
        sentences.append(
            "An agent signal flags this node as a suggested focus (advisory)."
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


# --- Report renderer ----------------------------------------------------------





def _mentor_cards(
    result: RecommendationResult,
    minutes: int,
    limit: int,
    node_map: dict[str, SkillNode],
    resources_by_node: dict[str, list[LearningResource]],
    store,
    active_remediations_list: list[ActiveRemediation],
) -> list[MentorCard]:
    """The enriched Mentor-voice next report as structured cards.

    One content card per ranked candidate: kicker + title + state pill,
    contrastive brief, Where to learn, How to proceed, Do this next.
    Track warnings and remediation advisories are standalone banner cards;
    the locked nodes ride as one appendix card. Both `next` and the serve
    shell's `/next` page render exactly these cards.
    """
    cards: list[MentorCard] = []
    for track in result.unmapped_tracks:
        cards.append(
            MentorCard.banner_card(
                "warning",
                f"track {track!r} is not in policy/recommendation.yaml "
                "track_weights (scored 0); add it there to prioritize its nodes.",
            )
        )

    if not result.recommendations:
        cards.append(
            MentorCard(
                parts=[
                    Kicker(text=render.section_kicker("What's next")),
                    Lead(
                        text=f"There's nothing available or active to recommend for a {minutes}-min session. "
                        "Run `skilltrace sync` if this looks wrong — readiness may be stale."
                    ),
                    Kicker(text="DO THIS NEXT"),
                    Sub(text="Refresh readiness: `skilltrace sync`"),
                ]
            )
        )
        return cards

    total = len(result.recommendations)
    session_label = f"{minutes}-min session"

    for rank, rec in enumerate(result.recommendations, start=1):
        node = node_map.get(rec.node_id)
        if node is None:
            # Should never happen (nodes and store are loaded together), but
            # degrade gracefully rather than crash.
            cards.append(MentorCard(parts=[Sub(text=f"{rank}. {rec.node_id}")]))
            continue

        state = store.state_of(rec.node_id)
        node_resources = resources_by_node.get(rec.node_id, [])

        parts: list[CardPart] = []
        parts.append(
            Kicker(text=render.section_kicker(f"Option {rank} — {session_label}"))
        )
        parts.append(Title(text=node.title))
        parts.append(Pill(label=state_phrase(NodeState(state))))
        parts.append(
            Para(text=_contrastive_brief(rec, rank, total, node, minutes))
        )
        parts.append(Label(text="Where to learn"))
        for resource_line in resource_lines(node_resources):
            parts.append(Sub(text=resource_line))
        parts.append(Label(text="How to proceed"))
        parts.append(Sub(text=_how_to_proceed(node, state, minutes)))
        parts.append(Kicker(text="DO THIS NEXT"))
        parts.append(Sub(text=_do_this_next(node, state)))

        cards.append(MentorCard(parts=parts))

    # Closing context: advisory remediation cards.
    for remediation in active_remediations_list:
        cards.append(
            MentorCard.banner_card(
                "advisory",
                f"remediation edge active: {remediation.remediation_node} "
                f"supports {remediation.target} — {remediation.trigger}.",
            )
        )

    # Locked appendix.
    if result.locked:
        appendix: list[CardPart] = [Label(text=f"Locked ({len(result.locked)}):")]
        for locked in result.locked:
            appendix.append(Sub(text=f"{locked.node_id} — {locked.reason}"))
        cards.append(MentorCard(parts=appendix, kind="locked"))

    return cards


@dataclass
class NextModel:
    """The recommendation derivation shared by `next` and the serve page.

    ``cards`` is the canonical Mentor output; ``lines`` is the legacy
    terminal serialization (``render.cards_to_lines(cards)``) kept so
    terminal output stays verbatim. The structured recommendations ride
    alongside so the web view can render its "Why this?" reasoning
    without re-running the ranker.
    """

    lines: list[str]
    recommendations: list[Recommendation]
    locked: list[LockedCandidate]
    cards: list[MentorCard]
    warnings: list[str] = field(default_factory=list)


def derive_next(
    joined,
    root: Path | None = None,
    *,
    minutes: int = 60,
    limit: int = 5,
    show_locked: bool = False,
) -> NextModel:
    """Load-free ranking over one loaded JoinedView. Pure of printing.

    Advisory inputs (prerequisite-retention urgency, agent recommendations)
    are derived fresh; a missing retention seed or agent file simply stands
    the relevant factor down.
    """
    active, blocked = _policy_pressure(joined)
    today = utc_today()
    urgency = prereq_retention_urgency(joined, today)
    agent_recs, agent_warns = (
        load_agent_recommendations(root) if root is not None else ({}, [])
    )
    result = recommend(
        joined.nodes,
        joined.edges,
        joined.store,
        joined.policy.track_weights,
        minutes=minutes,
        limit=limit,
        show_locked=show_locked,
        factor_weights=joined.policy.factor_weights,
        remediation_boosted={r.remediation_node for r in active},
        open_blocked=blocked,
        prereq_reviews_due=urgency,
        agent_boosted=set(agent_recs),
    )
    cards = _mentor_cards(
        result,
        minutes,
        limit,
        joined.node_map,
        joined.resources_by_node,
        joined.store,
        active,
    )
    return NextModel(
        lines=render.cards_to_lines(cards),
        recommendations=list(result.recommendations),
        locked=list(result.locked),
        cards=cards,
        warnings=list(agent_warns),
    )


def recommend_next(ctx: Context) -> CommandResult:
    """Load via the JoinedView lenient seam, rank candidates, and render."""
    root = ctx.root

    try:
        joined = load_context_lenient(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"next: FAILED — {exc}")
        return CommandResult(exit_code=1)

    model = derive_next(
        joined,
        root,
        minutes=ctx.args.minutes,
        limit=ctx.args.limit,
        show_locked=ctx.args.show_locked,
    )
    for line in model.lines:
        print(line)
    for warning in model.warnings:
        print(f"next: {warning}")
    return CommandResult()


def _policy_pressure(joined) -> tuple[list[ActiveRemediation], set[str]]:
    """Derive the active remediation edges and open-blocked nodes (advisory-only).

    Uses the already-joined blockers/attempts so no extra file reads are needed.
    """
    blockers = joined.blockers
    attempts = joined.attempts
    edges = joined.edges
    store = joined.store
    blocked = {b.node_id for b in blockers if b.status == "open"}
    active = active_remediations(
        edges,
        store=store,
        blockers=blockers,
        attempts=attempts,
        failed_attempt_threshold=joined.policy.failed_attempt_threshold,
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
