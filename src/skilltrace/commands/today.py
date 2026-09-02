"""`skilltrace today` — the Mentor-voice daily study view (issue #43).

Per the #30 resolution: a conversational brief synthesizing the current study
state (open session, pressure from overdue reviews / open blockers, and the top
recommendation), then guided **Where to learn (top focus)** and **How to
proceed**, and one **Do this next**. The learner's language sits on the surface;
the CLI remains the v1 UI.

It joins execution (sessions, blockers, reviews) + graph (recommendations) +
resources for the study day. The focus skill is the open session's node when one
is open (the thread to pick up), otherwise the top recommendation. Read-only:
the dispatcher appends no audit event, and valid data always exits 0 — every
finding here is advisory, nothing mutates.

Reuses `src/skilltrace/render.py` (stdlib-pure, no rich/ANSI) as the shared
render helper per #32; this is the third of the remaining v0.9 output build
order from the friction-log resolution: **node -> today -> enrich next ->
reports**.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .. import render
from ..analytics.derive import derive_analytics
from ..context import load_context_lenient
from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence.eligibility import compute_eligibility, live_accepted_count
from ..evidence.specs import ArtifactSpec
from ..execution.blockers import Blocker
from ..execution.sessions import open_session
from ..graph.edges import EdgeLoadError
from ..graph.nodes import NodeLoadError, SkillNode
from ..graph.recommendation import recommend
from ..graph.state import ProgressStoreError
from ..policy.advisory import analytics_warnings
from ..policy.remediation_edges import active_remediations
from ..resources.registry import LearningResource


# --- Small loaders and helpers -------------------------------------------------


def _parse_date(val: Any) -> date | None:
    if val is None:
        return None
    try:
        return date.fromisoformat(str(val)[:10])
    except (ValueError, TypeError):
        return None


def _minutes_open(started_at: str | None) -> int | None:
    """Minutes the open session has been running, or None if unknown/stale."""
    if not started_at:
        return None
    try:
        started = datetime.fromisoformat(started_at)
    except ValueError:
        return None
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - started
    minutes = int(delta.total_seconds() // 60)
    return minutes if minutes >= 0 else None


def _resource_lines(resources: list[LearningResource]) -> list[str]:
    """Format resource lines for the Where to learn section (mirrors `node`)."""
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


def _node_title_map(nodes: list[SkillNode]) -> dict[str, str]:
    return {n.id: n.title for n in nodes}


# --- Study-day brief and focus prose (Mentor voice) ---------------------------


def _study_day_brief(
    *,
    has_open_session: bool,
    focus_title: str | None,
    minutes_open: int | None,
    overdue: list,  # list[Review]
    open_blockers: list[Blocker],
    titles: dict[str, str],
    analytics_bits: list[str] | None = None,
) -> str:
    """One conversational paragraph of the day's study state."""
    sentences: list[str] = []

    if has_open_session and focus_title:
        phrase = "You've still got a session open"
        if minutes_open is not None:
            phrase += f" (~{minutes_open} min)"
        phrase += f" on {focus_title} — that's the thread I'd pick up."
        sentences.append(phrase)
    elif has_open_session:
        sentences.append(
            "You've got a session open, but nothing's logged on it yet — "
            "add a work item with `skilltrace work <node_id>`."
        )
    elif focus_title:
        sentences.append(f"There's no session open — your best focus today is {focus_title}.")
    else:
        sentences.append("There's no session open and nothing stands out to start.")

    pressure_bits: list[str] = []
    if overdue:
        names = [titles.get(r.node_id, r.node_id) for r in overdue[:2]]
        extra = "" if len(overdue) <= 2 else f" (+{len(overdue) - 2} more)"
        noun = "review" if len(overdue) == 1 else "reviews"
        pressure_bits.append(f"{len(overdue)} overdue {noun} ({', '.join(names)}{extra})")
    if open_blockers:
        names = [titles.get(b.node_id, b.node_id) for b in open_blockers[:2]]
        extra = "" if len(open_blockers) <= 2 else f" (+{len(open_blockers) - 2} more)"
        noun = "blocker" if len(open_blockers) == 1 else "blockers"
        pressure_bits.append(f"{len(open_blockers)} open {noun} ({', '.join(names)}{extra})")

    # Analytics-derived pressure bits: at most 2, appended after the
    # execution-layer pressure (overdue reviews / open blockers).
    for bit in (analytics_bits or [])[:2]:
        pressure_bits.append(bit)

    if pressure_bits:
        sentences.append(
            "There's " + " and ".join(pressure_bits)
            + " needing attention — but finishing your open work matters more than "
            "starting something new."
        )
    elif has_open_session:
        sentences.append("Nothing's blocking you; stay with the open thread.")

    return " ".join(sentences)


def _focus_how_to_proceed(
    focus_node: SkillNode,
    focus_state: str,
    specs: list[ArtifactSpec],
    has_gate: bool,
    records,
) -> str:
    """Guided 'How to proceed' for the focus skill."""
    title = focus_node.title
    node_specs = [s for s in specs if s.node_id == focus_node.id and s.required]

    if focus_state == "active":
        if node_specs:
            parts = []
            for spec in node_specs:
                accepted = live_accepted_count(records, spec.id)
                parts.append(f"{accepted} of {spec.minimum_count} {spec.title}")
            summary = "; ".join(parts)
            return (
                f"You have {summary} accepted for {title}. "
                "Submit the next piece of evidence when it's ready."
            )
        return (
            f"You're already working on {title} — bring the next piece of "
            "evidence back when it's ready."
        )

    if focus_state == "available":
        if node_specs:
            total = sum(s.minimum_count for s in node_specs)
            return (
                f"Start studying {title}; it needs {total} accepted "
                "submission(s) to pass — you decide when the work is good "
                "enough, not an AI."
            )
        if has_gate:
            return f"Start studying {title}; it has an evidence gate to clear before you can pass."
        return f"Start studying {title}."

    return f"Keep moving on {title}."


def _focus_action(
    focus_node: SkillNode,
    focus_state: str,
    specs: list[ArtifactSpec],
    has_gate: bool,
    records,
) -> str:
    """The single 'Do this next' action for the focus skill."""
    node_id = focus_node.id
    if focus_state == "active":
        elig = compute_eligibility(
            node_id,
            [s for s in specs if s.node_id == node_id],
            has_gate=has_gate,
            records=records,
            node_state="active",
        )
        if elig.eligible:
            return f"Mark {node_id} passed: `skilltrace pass {node_id}`"
        return f"Submit your next piece of evidence for {node_id}"
    if focus_state == "available":
        return f"Start studying {node_id}: `skilltrace start {node_id}`"
    return f"Keep working on {node_id}"


# --- Command handler ----------------------------------------------------------


@dataclass
class TodayModel:
    """The study-day derivation shared by `today` and the serve home page.

    ``lines`` is the canonical Mentor output; the pressure facts and state
    counts ride alongside so the web view can excerpt them without
    re-deriving (one voice, no parallel vocabulary).
    """

    lines: list[str]
    focus_node_id: str | None
    overdue: list  # list[Review] — scheduled and past due
    open_blockers: list[Blocker]
    counts: dict[str, int]  # progress-store state -> node count


def derive_today(joined, root: Path, *, minutes: int = 30) -> TodayModel:
    """Synthesize the study day from one loaded JoinedView. Pure of printing."""
    nodes = joined.nodes
    edges = joined.edges
    store = joined.store
    sessions = joined.sessions
    session_work = joined.work
    blockers = joined.blockers
    reviews = joined.reviews
    attempts = joined.attempts
    specs = joined.specs
    gates = joined.gates
    records = joined.records

    node_map = joined.node_map
    titles = joined.titles

    # Top recommendations (same engine + advisory pressure as `next`).
    open_blocked = {b.node_id for b in blockers if b.status == "open"}
    active = active_remediations(
        edges,
        store=store,
        blockers=blockers,
        attempts=attempts,
        failed_attempt_threshold=joined.policy.failed_attempt_threshold,
    )
    result = recommend(
        nodes,
        edges,
        store,
        joined.policy.track_weights,
        minutes=minutes,
        limit=3,
        factor_weights=joined.policy.factor_weights,
        remediation_boosted={r.remediation_node for r in active},
        open_blocked=open_blocked,
    )

    # Focus skill: the open session's node if one is open, else the top pick.
    current_session = open_session(sessions)
    focus_node_id: str | None = None
    minutes_open: int | None = None
    if current_session is not None:
        session_items = [w for w in session_work if w.session_id == current_session.id]
        if session_items:
            focus_node_id = session_items[-1].node_id
        minutes_open = _minutes_open(current_session.started_at)

    top_rec = result.recommendations[0] if result.recommendations else None
    if focus_node_id is None and top_rec is not None:
        focus_node_id = top_rec.node_id

    focus_node = node_map.get(focus_node_id) if focus_node_id else None
    focus_state = store.state_of(focus_node_id) if focus_node_id else None
    focus_resources = (
        joined.resources_by_node.get(focus_node_id, [])
        if focus_node_id
        else []
    )
    has_gate = (focus_node_id in joined.has_gate) if focus_node_id else False

    # Pressure facts for the brief.
    today_dt = datetime.now(timezone.utc).date()
    overdue = [
        r
        for r in reviews
        if r.status == "scheduled"
        and (d := _parse_date(r.scheduled_for)) is not None
        and d < today_dt
    ]
    open_blocker_list = [b for b in blockers if b.status == "open"]

    # Analytics-derived pressure: derive the view with policy defaults, call
    # analytics_warnings(), cap at 2 bits so the brief doesn't become a nag screen.
    _analytics_policy = joined.policy.analytics if joined.policy.analytics else {}
    _window_days = _analytics_policy.get("default_window_days", 30)
    _min_sessions = _analytics_policy.get("min_sessions_for_full_data", 3)
    _group_by = _analytics_policy.get("default_group_by", "prefix")
    if _group_by not in ("prefix", "track"):
        _group_by = "prefix"
    try:
        _analytics_view = derive_analytics(
            joined,
            today=today_dt,
            window_days=int(_window_days) if isinstance(_window_days, (int, float)) else 30,
            group_by=_group_by,
            state_filter=[],
            min_sessions_for_full_data=int(_min_sessions) if isinstance(_min_sessions, (int, float)) else 3,
        )
        _raw_analytics_bits = analytics_warnings(root, _analytics_view)
    except Exception:  # noqa: BLE001 — advisory never raises to the surface
        _raw_analytics_bits = []
    analytics_bits = _raw_analytics_bits[:2]

    # Build the Mentor view.
    lines: list[str] = []
    lines.append(render.section_kicker("Today"))
    lines.extend(
        render.section_brief(
            _study_day_brief(
                has_open_session=current_session is not None,
                focus_title=focus_node.title if focus_node else None,
                minutes_open=minutes_open,
                overdue=overdue,
                open_blockers=open_blocker_list,
                titles=titles,
                analytics_bits=analytics_bits,
            )
        )
    )

    if focus_node is not None:
        lines.extend(
            render.section_where_to_learn(
                _resource_lines(focus_resources), label="Where to learn (top focus)"
            )
        )
        lines.extend(
            render.section_how_to_proceed(
                _focus_how_to_proceed(focus_node, focus_state, specs, has_gate, records)
            )
        )
        lines.extend(
            render.section_do_this_next(
                _focus_action(focus_node, focus_state, specs, has_gate, records)
            )
        )

        other_recs = [r for r in result.recommendations if r.node_id != focus_node.id]
        if other_recs:
            names = [titles.get(r.node_id, r.node_id) for r in other_recs[:3]]
            context = "Also in range: " + ", ".join(names) + "."
        elif open_blocker_list or overdue:
            bits = []
            if overdue:
                bits.append(
                    "clear your overdue review" + ("s" if len(overdue) != 1 else "")
                )
            if open_blocker_list:
                bits.append(
                    "resolve your open blocker"
                    + ("s" if len(open_blocker_list) != 1 else "")
                )
            context = "When this is done, " + " and ".join(bits) + "."
        else:
            context = None
        if context:
            lines.extend(render.section_context(context))
    else:
        lines.extend(
            render.section_how_to_proceed(
                "Run `skilltrace next` to see what to study, or `skilltrace sync` "
                "if your readiness looks stale.",
            )
        )
        lines.extend(
            render.section_do_this_next("Open your study options: `skilltrace next`")
        )

    counts: dict[str, int] = {}
    for entry in store.entries.values():
        counts[entry.state] = counts.get(entry.state, 0) + 1

    return TodayModel(
        lines=lines,
        focus_node_id=focus_node_id,
        overdue=overdue,
        open_blockers=open_blocker_list,
        counts=counts,
    )


def today(ctx: Context) -> CommandResult:
    """Load every layer, synthesize the study day, render the Mentor view."""
    root = ctx.root

    # One deep join — graph/state strict, rest lenient.
    try:
        joined = load_context_lenient(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"today: FAILED — {exc}")
        return CommandResult(exit_code=1)

    model = derive_today(joined, root, minutes=ctx.args.minutes)
    for line in model.lines:
        print(line)

    return CommandResult(exit_code=0)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="today",
            kind=Kind.READ_ONLY,
            handler=today,
            help="Show the Mentor-voice daily study view (read-only).",
        )
    )
