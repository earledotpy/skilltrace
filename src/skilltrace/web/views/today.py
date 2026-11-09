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
the top available SkillNode plus ordinary discovery alternatives.

Three non-success states are distinguished and never merged (SC-00a):

* **empty** — the queried population is genuinely empty: say why, and
  preserve discovery;
* **limited** — valid values exist but a policy threshold is not met:
  retain the values, state the threshold;
* **could not compute** — a required source failed to load: an operational
  failure with a precise recovery. It never renders zeros and never
  fabricates a health fact.
"""

from __future__ import annotations

from pathlib import Path

from ...commands.recommend import derive_next
from ...evidence.eligibility import compute_eligibility
from ...execution.overdue import is_overdue, utc_today
from ...execution.records import open_session
from ._shared import _esc, _session_node_id
from .sections import BARE, section
from .shell import _page_head


def _queue_item(title: str, why: str, actions: str, *, dominant: bool = False) -> str:
    """One queue item — the priority queue's unit (a list item, not a card)."""
    cls = "queue-item dominant" if dominant else "queue-item"
    return (
        f'<li class="{cls}">\n'
        f'<p class="queue-title">{_esc(title)}</p>\n'
        f'<p class="queue-why">{_esc(why)}</p>\n'
        f'<div class="queue-actions">{actions}</div>\n'
        "</li>\n"
    )


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


def _overdue_reviews(view, today) -> list:
    return [
        r
        for r in view.reviews
        if r.status == "scheduled" and is_overdue(r, today=today)
    ]


def _open_blocker_records(view) -> list:
    return [b for b in view.blockers if b.status == "open"]


def home_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/` — Today: one priority queue, one dominant action."""
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
    session = open_session(view.sessions)
    overdue = _overdue_reviews(view, today)
    blockers = _open_blocker_records(view)

    try:
        next_model = derive_next(view, Path(root), minutes=60, limit=6)
        recommendations = list(next_model.recommendations)
        recommendation_error = ""
    except Exception as exc:  # noqa: BLE001 — an advisory preview, never the page
        recommendations = []
        recommendation_error = str(exc)

    pass_eligible = _pass_eligible_node(view)

    items: list[str] = []
    dominant_used = False

    # 1 — resume the open Session.
    if session is not None:
        node_id = _session_node_id(view, session)
        title = view.titles.get(node_id) or node_id
        actions = (
            f'<a class="btn primary" href="/session">Resume your session</a>'
            f'<a class="btn secondary" href="/nodes/{_esc(node_id)}">'
            "Open this skill</a>"
        )
        items.append(
            _queue_item(
                f"Continue on {title}",
                "Your session is open. Resuming shows where you left off.",
                actions,
                dominant=not dominant_used,
            )
        )
        dominant_used = True

    # 2 — overdue Reviews and open Blockers affecting current work.
    for review in overdue:
        title = view.titles.get(review.node_id) or review.node_id
        items.append(
            _queue_item(
                f"A check on {title} is overdue",
                "A retention check you scheduled is past its date.",
                '<a class="btn secondary" href="/reviews">Open reviews</a>',
                dominant=not dominant_used,
            )
        )
        dominant_used = True
    for blocker in blockers:
        title = view.titles.get(blocker.node_id) or blocker.node_id
        items.append(
            _queue_item(
                f"Something is blocking {title}",
                blocker.description or "A blocker is recorded on this skill.",
                '<a class="btn secondary" href="/session">Open the session</a>',
                dominant=not dominant_used,
            )
        )
        dominant_used = True

    # 3 — a pass-eligible SkillNode.
    if pass_eligible is not None:
        title = view.titles.get(pass_eligible) or pass_eligible
        actions = (
            f'<a class="btn primary" href="/nodes/{_esc(pass_eligible)}/pass">'
            "Mark this skill passed</a>"
            f'<a class="btn secondary" href="/nodes/{_esc(pass_eligible)}/evidence">'
            "See the evidence</a>"
        )
        items.append(
            _queue_item(
                f"{title} is ready to pass",
                "Its evidence requirements are met.",
                actions,
                dominant=not dominant_used,
            )
        )
        dominant_used = True

    # 4 — the highest-ranked normal recommendation.
    if recommendations:
        rec = recommendations[0]
        title = view.titles.get(rec.node_id) or rec.node_id
        state = view.store.state_of(rec.node_id)
        actions = (
            f'<a class="btn primary" href="/nodes/{_esc(rec.node_id)}">'
            "Open this skill</a>"
        )
        if state == "available":
            actions += (
                f'<form method="post" action="/nodes/{_esc(rec.node_id)}/start">'
                f'<input type="hidden" name="next" value="/">'
                f'<button type="submit" class="btn primary">Start studying</button>'
                "</form>"
            )
        items.append(
            _queue_item(
                title,
                rec.reason or "A recommended next step.",
                actions,
                dominant=not dominant_used,
            )
        )
        dominant_used = True

    body = head + _queue_section(items, recommendations, recommendation_error)
    return "Today", body, 200


def _queue_section(
    items: list[str], recommendations: list, recommendation_error: str
) -> str:
    """The priority queue, plus the secondary discovery paths."""
    if items:
        queue = f'<ul class="queue">\n{"".join(items)}</ul>\n'
    else:
        queue = (
            '<div class="state state-empty">\n'
            '<p class="state-title">Nothing is ready right now</p>\n'
            '<p class="state-body">There is no open session, nothing overdue, '
            "and no skill ready to pass. Nothing here is a problem with you — "
            "it is a fact about what is available. Start with any skill below, "
            "or search the whole curriculum.</p>\n"
            "</div>\n"
        )

    secondary = ""
    if recommendation_error:
        secondary = (
            '<div class="state state-failure">\n'
            '<p class="state-title">Recommendations could not be worked out</p>\n'
            "<p class=\"state-body\">Something needed to suggest the next step "
            "did not load, so no recommendation is shown. Your progress is "
            "unaffected. Try again in a moment, or look through the whole "
            'curriculum.</p>\n'
            '<p><a href="/find">Find a skill</a></p>\n'
            "</div>\n"
        )
    else:
        secondary = section(
            "Keep going",
            "",
            '<div class="command-bar"><div class="actions">'
            '<a class="btn secondary" href="/next">See more options</a>'
            '<a class="btn secondary" href="/find">Find a skill</a>'
            "</div></div>\n",
            frame=BARE,
        )

    return (
        section(
            "Your next step",
            "One thing at a time, in priority order.",
            f"{queue}",
        )
        + f"{secondary}"
    )
