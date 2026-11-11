"""
GET ``/`` — Today, the Guided home of the study day (spec-v3-study-day
§10.1, SC-00a, R7).

One priority-ordered queue with **exactly one visually dominant action at
a time**, in this order:

1. resume the open Session (if one exists);
2. overdue Reviews and open Blockers affecting current work;
3. a pass-eligible SkillNode;
4. the highest-ranked normal recommendation;
5. Next and Find as secondary discovery paths.

A learner with no history gets one dominant **Start studying** action for
the top available SkillNode plus ordinary discovery alternatives. The
dominant item carries the page's one primary button; every other action
is secondary — one dominant action, never two (VS-6).

While a Session is open, **no second start is offered**: the engine
refuses it, so Today shows the open Session and its safe actions —
resume, log work on the skill it is bound to, close — instead of the
refusal alone (§10.5, R5).

Five non-success states are distinguished and never merged (SC-00a):

* **empty** — the queried population is genuinely empty: say why, and
  preserve discovery;
* **limited** — valid values exist but a policy threshold is not met:
  retain the values, state the threshold;
* **refusal** — every visible skill is locked: the reason is the
  curriculum, and unlocking is never offered — a skill opens when the
  skill before it is passed, never by an override;
* **could not compute** — a required source failed to load: an operational
  failure with a precise recovery. It never renders zeros and never
  fabricates a fact;
* **recovery** — saved readiness no longer matches the curriculum: a safe
  refresh is prompted, and the dependency is named rather than hidden.

The counts under the queue are the same figures the destination views
show — one derivation (``web.health.rhythm_facts``) serves Health and
Today, so the surfaces cannot disagree about a number (R7).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...analytics.policy import limited_data_sentence
from ...commands.recommend import derive_next
from ...evidence.eligibility import compute_eligibility
from ...execution.overdue import is_overdue, utc_today
from ...execution.records import open_session
from ..health import rhythm_facts
from ._readiness import every_skill_locked, stale_readiness_panel
from ._reasons import facts_for, reason_for
from ._shared import _esc, _session_node_id
from .sections import BARE, section
from .shell import _page_head

#: The minutes a Today recommendation is sized for — the same window
#: ``/next`` ranks by default, so the same skill never gets two different
#: reasons on the two surfaces.
MINUTES = 60


@dataclass(frozen=True)
class _Action:
    """One action inside a queue item — a link, or the explicit start form.

    A start is the one learner command §10.1 gives Today; everything else
    is navigation (HB-1, HB-6). The *dominant* item's first action is the
    page's one primary button.
    """

    label: str
    href: str | None = None
    start_node: str | None = None


@dataclass(frozen=True)
class _Item:
    """One queue item's content, before the dominant action is chosen."""

    title: str
    why: str
    actions: tuple[_Action, ...]


# --- the facts --------------------------------------------------------------- #


def _overdue_reviews(view, today) -> list:
    """The scheduled Reviews whose date has passed — the retention work due."""
    return [
        r
        for r in view.reviews
        if r.status == "scheduled" and is_overdue(r, today=today)
    ]


def _open_blocker_records(view) -> list:
    """The open Blockers — pressing work, ahead of ordinary recommendations."""
    return [b for b in view.blockers if b.status == "open"]


def _pass_eligible_node(view) -> str | None:
    """The first SkillNode whose derived eligibility says it can be passed."""
    for node in sorted(view.nodes, key=lambda n: n.id):
        node_id = node.id
        state = view.store.state_of(node_id)
        if state in ("passed", "mastered", "locked"):
            continue
        result = compute_eligibility(
            node_id,
            view.specs_by_node.get(node_id, []),
            has_gate=node_id in view.has_gate,
            records=view.records,
            node_state=state,
        )
        if result.eligible:
            return node_id
    return None


def _unavailable_parts(degraded: set[str]) -> list[str]:
    """The facts a degraded layer leaves unknown — named, never zeroed.

    Each entry is a fact the page would otherwise have stated; the failure
    state says exactly what is not being claimed (SC-00a).
    """
    parts: list[str] = []
    if {"sessions", "work"} & degraded:
        parts.append("whether a session is open")
    if "reviews" in degraded:
        parts.append("the checks you scheduled")
    if "blockers" in degraded:
        parts.append("the blockers you recorded")
    if {"records", "specs", "gates"} & degraded:
        parts.append("which skills are ready to pass")
    return parts


# --- the queue items, in priority order -------------------------------------- #


def _session_item(view, session) -> _Item:
    """Priority 1 — resume the open Session, with its safe actions (R5).

    A second start is refused while a Session is open, so the item states
    that and carries the safe actions instead: resume, log work on the
    skill the Session is bound to, close.
    """
    node_id = _session_node_id(view, session)
    title = view.titles.get(node_id) or "your open session"
    actions = [_Action(label="Resume your session", href="/session")]
    if node_id:
        actions.append(
            _Action(label="Log work on this skill", href=f"/nodes/{node_id}")
        )
    actions.append(_Action(label="Close this session", href="/session/close"))
    return _Item(
        title=f"Continue on {title}",
        why=(
            "Your session is open. A second session is refused while this "
            "one is open, and nothing here unlocks another one — resume "
            "this session, log work on the skill it is bound to, or close "
            "it first."
        ),
        actions=tuple(actions),
    )


def _review_item(view, review) -> _Item:
    """Priority 2 — an overdue Review: retention work that is due."""
    title = view.titles.get(review.node_id) or review.node_id
    return _Item(
        title=f"A check on {title} is overdue",
        why="A retention check you scheduled is past its date.",
        actions=(_Action(label="Open reviews", href="/reviews"),),
    )


def _blocker_item(view, blocker) -> _Item:
    """Priority 2 — an open Blocker: the record of persistent stuckness."""
    title = view.titles.get(blocker.node_id) or blocker.node_id
    return _Item(
        title=f"Something is blocking {title}",
        why=blocker.description or "A blocker is recorded on this skill.",
        actions=(_Action(label="Open this skill", href=f"/nodes/{blocker.node_id}"),),
    )


def _pass_item(view, node_id: str) -> _Item:
    """Priority 3 — a pass-eligible SkillNode, through its own safety panel."""
    title = view.titles.get(node_id) or node_id
    return _Item(
        title=f"{title} is ready to pass",
        why="Its evidence requirements are met.",
        actions=(
            _Action(label="Mark this skill passed", href=f"/nodes/{node_id}/pass"),
            _Action(label="See the evidence", href=f"/nodes/{node_id}/evidence"),
        ),
    )


def _recommendation_item(view, rec, *, start_allowed: bool) -> _Item:
    """Priority 4 — the highest-ranked normal recommendation.

    The reason is the one human sentence ``/next`` uses, built from the
    same facts — so the counts the two surfaces state agree (R7), and no
    engine voice (scores, weights, edge counts) ever reaches the page. The
    start form is offered only when no Session is open: a second start is
    refused by the engine, and Today never offers an action it knows will
    be refused.
    """
    title = view.titles.get(rec.node_id) or rec.node_id
    actions: list[_Action] = []
    if start_allowed and view.store.state_of(rec.node_id) == "available":
        actions.append(_Action(label="Start studying", start_node=rec.node_id))
    actions.append(_Action(label="Open this skill", href=f"/nodes/{rec.node_id}"))
    return _Item(
        title=title,
        why=reason_for(rec, facts_for(view, rec, minutes=MINUTES)),
        actions=tuple(actions),
    )


def _queue_items(
    view,
    *,
    session,
    overdue,
    blockers,
    pass_eligible,
    recommendations,
    start_allowed: bool,
) -> list[_Item]:
    """The priority queue's items, in the spec's exact order (§10.1)."""
    items: list[_Item] = []
    if session is not None:
        items.append(_session_item(view, session))
    for review in overdue:
        items.append(_review_item(view, review))
    for blocker in blockers:
        items.append(_blocker_item(view, blocker))
    if pass_eligible is not None:
        items.append(_pass_item(view, pass_eligible))
    if recommendations:
        items.append(
            _recommendation_item(view, recommendations[0], start_allowed=start_allowed)
        )
    return items
# --- the queue and its states ------------------------------------------------ #


def _queue_item(
    title: str,
    why: str,
    actions: tuple[_Action, ...],
    *,
    dominant: bool = False,
) -> str:
    """One queue item — the priority queue's unit (a list item, not a card).

    The **dominant** item carries the page's one primary action; every
    other action on the page is secondary, so exactly one action reads as
    the thing to do (VS-6).
    """
    parts: list[str] = []
    for index, action in enumerate(actions):
        cls = "btn primary" if dominant and index == 0 else "btn secondary"
        if action.start_node is not None:
            parts.append(
                f'<form method="post" action="/nodes/{_esc(action.start_node)}/start">'
                '<input type="hidden" name="next" value="/">'
                f'<button type="submit" class="{cls}">{_esc(action.label)}</button></form>'
            )
        else:
            parts.append(
                f'<a class="{cls}" href="{_esc(action.href or "")}">'
                f"{_esc(action.label)}</a>"
            )
    cls = "queue-item dominant" if dominant else "queue-item"
    return (
        f'<li class="{cls}">\n'
        f'<p class="queue-title">{_esc(title)}</p>\n'
        f'<p class="queue-why">{_esc(why)}</p>\n'
        f'<div class="queue-actions">{"".join(parts)}</div>\n'
        "</li>\n"
    )


def _unavailable_state(parts: list[str]) -> str:
    """Could-not-compute: the records behind part of the day did not load.

    Nothing is claimed about what could not be read — not even a count of
    zero — and the recovery path is precise (SC-00a).
    """
    joined = (
        ", ".join(parts[:-1]) + " and " + parts[-1] if len(parts) > 1 else parts[0]
    )
    return (
        '<div class="state state-failure">\n'
        '<p class="state-title">Your study day could not be read</p>\n'
        f'<p class="state-body">The records behind {joined} did not load, '
        "so nothing is claimed about them — not even a count. Your "
        "progress is unaffected.</p>\n"
        '<p class="state-body"><a href="/health">Open Health</a> for the '
        "detail, or try again in a moment.</p>\n"
        "</div>\n"
    )


def _derivation_state() -> str:
    """Could-not-compute for the ranked preview — recovery keeps discovery."""
    return (
        '<div class="state state-failure">\n'
        '<p class="state-title">Recommendations could not be worked out</p>\n'
        "<p class=\"state-body\">Something needed to suggest the next step "
        "did not load, so no recommendation is shown. Your progress is "
        "unaffected. Try again in a moment, or look through the whole "
        "curriculum.</p>\n"
        '<p><a href="/find">Find a skill</a></p>\n'
        "</div>\n"
    )


def _empty_day_state() -> str:
    """Empty: the population is genuinely empty — say why, keep discovery."""
    body = (
        "There is no open session, nothing is past its date, and no skill "
        "is ready to pass right now. That is a fact about what is "
        "available, not a problem with you. Everything you have already "
        "finished stays finished."
    )
    return (
        '<div class="state state-empty">\n'
        '<p class="state-title">Nothing is ready right now</p>\n'
        f'<p class="state-body">{_esc(body)}</p>\n'
        "</div>\n"
    )


def _refusal_state() -> str:
    """Refusal: every visible skill is locked, and unlock is never offered.

    The lock is the curriculum's, not the page's: the only way a skill
    opens is by passing what it waits on (HB-4), so the refusal states the
    reason, offers the next safe recovery path, and never frames the lock
    as learner failure.
    """
    return (
        '<div class="state state-refusal">\n'
        '<p class="state-title">Every skill is waiting on another skill</p>\n'
        '<p class="state-body">A locked skill opens only when the skill '
        "before it is passed, and nothing on this page unlocks one early — "
        "there is no override.</p>\n"
        '<p><a href="/next">See what each skill waits on</a> or '
        '<a href="/find">find a skill</a>.</p>\n'
        "</div>\n"
    )


def _queue_section(
    items: list[_Item],
    *,
    unavailable: list[str],
    derivation_error: str,
    view,
) -> str:
    """The priority queue, its states, and the recovery paths around them."""
    parts: list[str] = []
    if unavailable:
        parts.append(_unavailable_state(unavailable))
    if derivation_error:
        parts.append(_derivation_state())
    if items:
        parts.append(
            '<ul class="queue">\n'
            + "".join(
                _queue_item(item.title, item.why, item.actions, dominant=index == 0)
                for index, item in enumerate(items)
            )
            + "</ul>\n"
        )
    elif not unavailable and not derivation_error:
        parts.append(
            _refusal_state() if every_skill_locked(view) else _empty_day_state()
        )
    return section(
        "Your next step",
        "One thing at a time, in priority order.",
        "".join(parts),
    )


# --- the day's counts and the discovery paths -------------------------------- #


def _study_day_section(view, today) -> str:
    """The study-day counts — the same figures the destination views show.

    Days practiced is the lifetime mirror (CONTEXT.md); the window count
    feeds the soft-data threshold, and both come from the one derivation
    Health reads (``rhythm_facts``), so the surfaces cannot disagree (R7).
    Zero counts are dropped — a zero is not a fact worth the learner's
    attention (P1.3) — and when the threshold is not met the *limited*
    state retains the values and states the threshold (SC-00a).
    """
    rhythm = rhythm_facts(view, today)
    rows: list[tuple[str, str]] = []
    if rhythm.days_practiced > 0:
        rows.append(("Days practiced", str(rhythm.days_practiced)))
    if rhythm.sessions_in_window > 0:
        rows.append(
            (
                f"Sessions in the last {rhythm.window_days} days",
                str(rhythm.sessions_in_window),
            )
        )
    if not rows:
        return ""
    inner = (
        '<div class="rows">\n'
        + "".join(
            '<div class="row"><span class="row-label">'
            f"{_esc(label)}</span>"
            f'<span class="row-value">{_esc(value)}</span></div>\n'
            for label, value in rows
        )
        + "</div>\n"
    )
    if rhythm.limited:
        inner += (
            '<div class="state state-limited">\n'
            '<p class="state-title">Limited data</p>\n'
            "<p class=\"state-body\">"
            f"{_esc(limited_data_sentence(rhythm.min_sessions, rhythm.window_days))}"
            "</p>\n"
            "</div>\n"
        )
    return section("Your study day", "What your records actually show.", inner)


def _discovery_section() -> str:
    """Priority 5 — Next and Find, the secondary discovery paths."""
    return section(
        "Keep going",
        "",
        '<div class="command-bar"><div class="actions">'
        '<a class="btn secondary" href="/next">See more options</a>'
        '<a class="btn secondary" href="/find">Find a skill</a>'
        "</div></div>\n",
        frame=BARE,
    )


def home_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET ``/`` — Today: one priority queue, one dominant action."""
    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/",
        current_view="today",
        path="/",
    )
    if failure is not None:
        return failure

    today = utc_today()
    degraded = set(view.degraded)

    # A layer that did not load leaves its facts *unknown* — the item is
    # omitted and the failure state says so; nothing is claimed about it.
    session_known = not ({"sessions", "work"} & degraded)
    session = open_session(view.sessions) if session_known else None
    overdue = _overdue_reviews(view, today) if "reviews" not in degraded else []
    blockers = _open_blocker_records(view) if "blockers" not in degraded else []
    evidence_known = not ({"records", "specs", "gates"} & degraded)
    pass_eligible = _pass_eligible_node(view) if evidence_known else None

    try:
        next_model = derive_next(view, Path(root), minutes=MINUTES, limit=6)
        recommendations = list(next_model.recommendations)
        derivation_error = ""
    except Exception as exc:  # noqa: BLE001 — an advisory preview, never the page
        recommendations = []
        derivation_error = str(exc)

    items = _queue_items(
        view,
        session=session,
        overdue=overdue,
        blockers=blockers,
        pass_eligible=pass_eligible,
        recommendations=recommendations,
        # A second start is refused while a Session is open — and when the
        # session facts are unknown, Today offers no start at all rather
        # than one that may be refused.
        start_allowed=session_known and session is None,
    )

    body = (
        head
        + stale_readiness_panel(view, reload_href="/", reload_label="reload this page")
        + _queue_section(
            items,
            unavailable=_unavailable_parts(degraded),
            derivation_error=derivation_error,
            view=view,
        )
        + _study_day_section(view, today)
        + _discovery_section()
    )
    return "Today", body, 200

