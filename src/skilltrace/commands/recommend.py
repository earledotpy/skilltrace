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

import argparse
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .. import render
from ..mentor.cards import (
    CardPart,
    Kicker,
    Label,
    Lead,
    MentorCard,
    NextAction,
    Para,
    Pill,
    Sub,
    Title,
)
from ..context import load_context_lenient
from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..execution.overdue import utc_today
from ..execution.records import open_session
from ..graph.edges import EdgeLoadError, GraphEdge
from ..graph.nodes import NodeLoadError, SkillNode
from ..graph.recommendation import (
    LockedCandidate,
    Recommendation,
    RecommendationResult,
    recommend,
)
from ..graph.recommendation_prep import prepare
from ..graph.state import ProgressStoreError
from ..mentor.prose import NodeState, resource_lines, state_phrase
from ..policy.remediation_edges import ActiveRemediation
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


def _do_this_next(node: SkillNode, state: str, *, has_open_session: bool) -> str:
    """The single concrete next action for this candidate.

    Honest handoff (issue #306, matching the discovery behavior contract
    from #304): every printed command is real, and never one the session
    planner would refuse — `start` is refused while a session is open
    (``use `work` to add to it``), `work` is refused with none open.
    """
    verb = "work" if has_open_session else "start"
    if state == "active":
        return f"Continue {node.id}: `skilltrace {verb} {node.id}`"
    return f"Start studying {node.id}: `skilltrace {verb} {node.id}`"


# --- Report renderer ----------------------------------------------------------





def _open_thread_banner(
    *,
    has_open_session: bool,
    open_thread_id: str | None,
    node_map: dict[str, SkillNode],
) -> MentorCard | None:
    """The lead banner naming the open thread, when a session is open.

    `next` accounts for active work consistently with `today` (issue #306):
    today picks the open session's node up as its focus; here the open
    thread leads the report instead of being ignored. Advisory only —
    ranking is untouched, nothing is started implicitly.
    """
    if not has_open_session:
        return None
    if open_thread_id is None:
        return MentorCard.banner_card(
            "advisory",
            "You've got a session open, but nothing's logged on it yet — "
            "add a work item with `skilltrace work <node_id>`.",
        )
    node = node_map.get(open_thread_id)
    title = node.title if node is not None else open_thread_id
    return MentorCard.banner_card(
        "advisory",
        f"You've still got a session open on {title} — that's the thread "
        f"to pick up. Add to it with `skilltrace work {open_thread_id}`.",
    )


def _mentor_cards(
    result: RecommendationResult,
    minutes: int,
    limit: int,
    node_map: dict[str, SkillNode],
    resources_by_node: dict[str, list[LearningResource]],
    store,
    active_remediations_list: list[ActiveRemediation],
    *,
    has_open_session: bool = False,
    open_thread_id: str | None = None,
) -> list[MentorCard]:
    """The enriched Mentor-voice next report as structured cards.

    One content card per ranked candidate: kicker + title + state pill,
    contrastive brief, Where to learn, How to proceed, Do this next.
    Track warnings and remediation advisories are standalone banner cards;
    the locked nodes ride as one appendix card. Both `next` and the serve
    shell's `/next` page render exactly these cards.
    """
    cards: list[MentorCard] = []
    banner = _open_thread_banner(
        has_open_session=has_open_session,
        open_thread_id=open_thread_id,
        node_map=node_map,
    )
    if banner is not None:
        cards.append(banner)
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
        # The next action as the structured fact (v2.4 §E): the CLI-printed
        # line rides in ``command`` so cards_to_lines stays byte-identical to
        # the pre-fact Kicker+Sub pair; the web renders the intent's
        # affordance and never this command string.
        parts.append(
            NextAction(
                intent="start",
                node_id=node.id,
                command=_do_this_next(node, state, has_open_session=has_open_session),
            )
        )

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
    today: date | None = None,
) -> NextModel:
    """Load-free ranking over one loaded JoinedView. Pure of printing.

    Advisory inputs (prerequisite-retention urgency, agent recommendations)
    are derived fresh by `prepare`; a missing retention seed or agent file
    simply stands the relevant factor down.

    ``today`` is the caller's clock date (``Context.clock`` under fixture
    runs so simulated-day runs rank against the simulation); ``None`` lets
    ``prepare`` read the wall clock.
    """
    inputs = prepare(joined, root, today)
    result = recommend(
        joined.nodes,
        joined.edges,
        joined.store,
        inputs.track_weights,
        minutes=minutes,
        limit=limit,
        show_locked=show_locked,
        factor_weights=inputs.factor_weights,
        remediation_boosted=inputs.remediation_boosted,
        open_blocked=inputs.open_blocked,
        prereq_reviews_due=inputs.prereq_reviews_due,
        agent_boosted=inputs.agent_boosted,
    )
    # Active work, the way `today` sees it (issue #306): the open session's
    # node is the thread to pick up — the last work item's node, or None
    # when nothing is logged on the open session yet.
    current_session = open_session(joined.sessions)
    open_thread_id: str | None = None
    if current_session is not None:
        session_items = [
            w for w in joined.work if w.session_id == current_session.id
        ]
        if session_items:
            open_thread_id = session_items[-1].node_id
    cards = _mentor_cards(
        result,
        minutes,
        limit,
        joined.node_map,
        joined.resources_by_node,
        joined.store,
        list(inputs.active_remediations),
        has_open_session=current_session is not None,
        open_thread_id=open_thread_id,
    )
    return NextModel(
        lines=render.cards_to_lines(cards),
        recommendations=list(result.recommendations),
        locked=list(result.locked),
        cards=cards,
        warnings=list(inputs.agent_warnings),
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
        today=utc_today(clock=ctx.clock),
    )
    for line in model.lines:
        print(line)
    for warning in model.warnings:
        print(f"next: {warning}")
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="next",
            kind=Kind.READ_ONLY,
            handler=recommend_next,
            help="Recommend prerequisite-safe nodes sized to available minutes.",
            add_parser=add_parser,
        )
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `next` parser to the top-level `subparsers` (issue #207 contract).

    Co-located owner of the `next` argparse surface (issue #207 contract: sole source of CLI flags and help text).
    """
    next_parser = subparsers.add_parser(
        "next", help="Recommend prerequisite-safe nodes sized to available minutes."
    )
    next_parser.add_argument(
        "--minutes", type=int, default=60, help="Minutes available this session."
    )
    next_parser.add_argument(
        "--limit", type=int, default=5, help="Maximum number of recommendations."
    )
    next_parser.add_argument(
        "--show-locked",
        action="store_true",
        help="Also show locked nodes (never recommended as available).",
    )
    next_parser.set_defaults(_command_name="next")
