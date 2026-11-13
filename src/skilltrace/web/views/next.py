"""
GET ``/next`` — the Next destination (spec-v3-study-day §10.2).

A **bounded, ranked list of study targets**. Every item carries an honest,
human-readable reason for its place: the one-line reason is visible in the
queue, and the ``Why this?`` disclosure keeps the whole reasoning. The
ranker's internals — scores, weights, leverage counts, flags and node
identifiers — never render (VS-4, R1).

The route is read-only navigation. It starts nothing, passes nothing,
masters nothing and writes nothing; a ranked item is a *link* to the skill,
and a locked skill is never a link at all (HB-1, HB-4).

Four states are distinguished and never merged (SC-00a):

* **populated** — the ranked queue, with the locked half as explanation;
* **empty** — nothing is recommendable: the reason is derived from the
  records (how many skills are finished, how many are waiting) plus a
  recovery path that keeps discovery alive;
* **limited** — the values are real but the session window they need is
  not met: the values are retained and the threshold is stated;
* **could not compute** — the derivation failed: an operational failure
  with a precise recovery path, never zeros and never a fabricated fact.

A progress store whose readiness no longer matches the curriculum is
reported as a recovery prompt: the dependency is named, never hidden
behind silence.

**Why some helpers are nested.** The page-local pieces (``controls``,
``waiting_on``) close over this request's ``view`` and query. The
cross-surface helpers — the human reasons and the stale-readiness
derivation — live in the shared ``_reasons`` / ``_readiness`` modules, so
``/next`` and Today can never drift apart on the facts they state.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from ...commands.recommend import derive_next
from . import _readiness, _reasons
from ._shared import (
    _esc,
    _normalize_pill_label,
    _parse_int,
    plural,
)
from .sections import section
from .shell import _page_head

#: The bounded list: the number of options a learner may ask for is capped,
#: so one request can never turn the page into the whole curriculum.
MAX_OPTIONS = 20
#: How many locked skills the explanation section names before it counts the
#: rest — the explanation is bounded too, and the count stays truthful.
MAX_EXPLAINED = 8


def _why_details(reason: str, facts: list) -> str:
    """The ``Why this?`` disclosure — the whole of this item's reasoning.

    The reason is the same honest sentence the queue shows; the facts are
    the contributing conditions behind it, each rendered in its standalone
    sentence form. Advisory wording rides along so the learner knows the
    ordering is advisory and never a gate (IC-8).
    """
    if facts:
        detail = (
            "<ul>"
            + "".join(f"<li>{_esc(fact.sentence)}</li>" for fact in facts)
            + "</ul>"
        )
    else:
        detail = (
            '<p class="state-body">Nothing about this skill is holding it up. '
            "It is available, and it is on the list because it can be started "
            "now.</p>"
        )
    return (
        '<details class="disclosure">\n'
        "<summary>Why this?</summary>\n"
        f'<p class="state-body">{_esc(reason)}</p>\n'
        f"{detail}\n"
        '<p class="mut">Advisory policies reorder recommendations; they never '
        "block a human-initiated action.</p>\n"
        "</details>\n"
    )


def _candidate_stack(
    view,
    model,
    *,
    minutes: int = 60,
    limit: int = 5,
    only_candidate: bool = False,
) -> str:
    """The ranked queue — one queue item per study target.

    The first item is the dominant action of the page (VS-6): one visually
    dominant action at a time, never two. Every item is a *target* — a link
    to the skill — and every item states why it sits where it does. The
    reasons come from the shared ``_reasons`` helpers, so ``/next`` and
    Today state the same facts about the same skill.
    """

    items: list[str] = []
    for index, rec in enumerate(model.recommendations[:limit]):
        title = view.titles.get(rec.node_id) or "Another skill"
        state = view.store.state_of(rec.node_id)
        facts = _reasons.facts_for(view, rec, minutes=minutes)
        reason = _reasons.reason_for(rec, facts, only_candidate=only_candidate)
        cls = "queue-item dominant" if index == 0 else "queue-item"
        tone = "info" if state == "active" else "neutral"
        action_class = "btn primary" if index == 0 else "btn secondary"
        items.append(
            f'<li class="{cls}">\n'
            f'<p class="queue-title">'
            f'<a href="/nodes/{_esc(rec.node_id)}">{_esc(title)}</a> '
            f'<span class="status-label {tone}">'
            f"{_esc(_normalize_pill_label(state))}</span></p>\n"
            f'<p class="queue-why">{_esc(reason)}</p>\n'
            '<div class="queue-actions">'
            f'<a class="{action_class}" href="/nodes/{_esc(rec.node_id)}">'
            "Open this skill</a></div>\n"
            f"{_why_details(reason, facts)}\n"
            "</li>\n"
        )
    return f'<ul class="queue">\n{"".join(items)}</ul>\n'


def _not_ready_card(model, view) -> str:
    """The locked half — explanation only, never a selectable target.

    A locked skill cannot be started (HB-4), so it never appears as a link
    here. The section names the readable title and what the skill is
    waiting on; the count of the rest stays truthful.
    """
    if not model.locked:
        return ""
    return section(
        "Not ready yet",
        "These skills are waiting on another skill. They are not on your "
        "list, and they cannot be started yet.",
        f"{_not_ready_list(model, view)}\n",
    )


def _not_ready_list(model, view) -> str:
    """The waiting rows: readable titles and what each one waits on.

    A prerequisite is linked only when it is itself startable — a locked
    skill stays an explanation, never a target.
    """

    def waiting_on(cand) -> str:
        if not cand.unsatisfied:
            return (
                "its readiness looks out of date — refresh your readiness and "
                "it will be placed correctly"
            )
        parts: list[str] = []
        for pid, state in cand.unsatisfied:
            title = view.titles.get(pid) or "an earlier skill"
            label = _normalize_pill_label(state)
            if state == "locked":
                parts.append(f"{_esc(title)} ({_esc(label)})")
            else:
                parts.append(
                    f'<a href="/nodes/{_esc(pid)}">{_esc(title)}</a> ({_esc(label)})'
                )
        return "waiting on " + ", ".join(parts)

    shown = model.locked[:MAX_EXPLAINED]
    rows = "".join(
        '<div class="row">'
        f'<span class="row-label">'
        f"{_esc(view.titles.get(cand.node_id) or 'Another skill')}</span>"
        f'<span class="row-value">{waiting_on(cand)}</span>'
        "</div>\n"
        for cand in shown
    )
    rest = len(model.locked) - len(shown)
    more = ""
    if rest > 0:
        more = (
            f'<p class="section-meta">{rest} more skill{plural(rest)} '
            f'{"is" if rest == 1 else "are"} waiting on another skill — '
            '<a href="/find">find them in the curriculum</a>.</p>\n'
        )
    return f'<div class="rows">\n{rows}</div>\n{more}'


def _empty_state(view) -> str:
    """The empty state — the reason derived from the records.

    Nothing is recommendable exactly when no skill is recorded as
    ``available`` or ``active``, so the sentence is built from the counts
    that make that true: how many skills are finished, how many are
    waiting on an unfinished one. The session window plays no part here —
    the limited state is the one that speaks for the window — so the
    reason never claims a constraint the records do not make. The
    recovery path keeps discovery alive.
    """
    states = [view.store.state_of(node.id) for node in view.nodes]
    total = len(states)
    finished = sum(1 for state in states if state in ("passed", "mastered"))
    waiting = sum(1 for state in states if state == "locked")
    if total == 0:
        reason = (
            "The curriculum holds no skills yet, so there is nothing to "
            "search, browse or start."
        )
    elif waiting == 0:
        reason = (
            f"You have finished every one of the {total} "
            f"skill{plural(total)} in the curriculum — nothing is left "
            "to start."
        )
    elif finished == 0:
        reason = (
            f"None of the {total} skill{plural(total)} in the curriculum "
            "can be started yet — every one of them is waiting on a skill "
            "you have not finished."
        )
    else:
        reason = (
            f"You have finished {finished} skill{plural(finished)}, and "
            f"the other {waiting} skill{plural(waiting)} "
            f'{"is" if waiting == 1 else "are"} waiting on a skill you '
            "have not finished."
        )
    return (
        '<section class="section">\n'
        '<div class="state state-empty">\n'
        '<p class="state-title">Nothing is recommendable right now</p>\n'
        f'<p class="state-body">{_esc(reason)} That is a fact about the '
        "curriculum, not about you.</p>\n"
        '<p><a href="/find">Find a skill</a> — the whole curriculum is '
        'open to you, whatever this list says.</p>\n'
        "</div>\n"
        "</section>\n"
    )


def next_body(root, query: dict) -> tuple[str, str, int]:
    """GET `/next` — the bounded, ranked list of study targets (§10.2).

    The session window and the option count are ordinary labelled GET
    controls: the result set has its own URL, so it survives a reload, can
    be shared and is reachable with the back button (IC-4, IA-5). No flag
    name ever renders.
    """
    query = query or {}
    minutes = _parse_int(query, "minutes", 60)
    limit = _parse_int(query, "limit", 5)
    mode = (query.get("mode") or [""])[0]

    view, head, failure = _page_head(
        root,
        query,
        dismiss_path="/next",
        current_view="next",
        path="/next",
    )
    if failure is not None:
        return failure

    def next_url(mins: int, count: int) -> str:
        """This destination with different controls — one addressable URL."""
        return "/next?" + urlencode({"minutes": mins, "limit": count})

    def controls(mins: int, count: int) -> str:
        """The two controls, as labelled GET inputs (IC-4)."""
        hidden = (
            f'<input type="hidden" name="mode" value="{_esc(mode)}">' if mode else ""
        )
        return (
            '<section class="section">\n'
            '<div class="section-head">\n'
            '<h2 class="section-title">Your next steps</h2>\n'
            '<p class="section-meta">A short, ranked list for the time you have. '
            "Change the time or the number of options and the list changes — "
            "the result is a link you can reload, share or come back to.</p>\n"
            "</div>\n"
            '<form class="filters" method="get" action="/next">\n'
            f"{hidden}"
            '<div class="form-row">'
            '<label for="next-minutes">How much time do you have (minutes)</label>'
            f'<input id="next-minutes" type="number" name="minutes" value="{mins}"'
            ' min="1" size="4">'
            "</div>\n"
            '<div class="form-row">'
            '<label for="next-limit">How many ideas do you want</label>'
            f'<input id="next-limit" type="number" name="limit" value="{count}"'
            ' min="1" size="3">'
            "</div>\n"
            '<div class="actions">'
            '<button class="btn secondary" type="submit">Update the list</button>'
            "</div>\n"
            "</form>\n"
            "</section>\n"
        )

    # --- the controls the learner set ---------------------------------------
    if minutes is None or limit is None or minutes < 1 or limit < 1:
        body = (
            head
            + '<section class="section">\n'
            '<div class="state state-refusal">\n'
            '<p class="state-title">That link asks for something odd</p>\n'
            '<p class="state-body">The time and the number of options in the '
            "link were not usable numbers, so no list was worked out. Nothing "
            "about your progress changed.</p>\n"
            '<p><a href="/next">Show the standard list</a></p>\n'
            "</div>\n"
            "</section>\n"
        )
        return "Next", body, 400

    notes: list[str] = []
    if limit > MAX_OPTIONS:
        notes.append(
            f'<p class="banner advisory">You asked for {limit} options. The list '
            f"is bounded at {MAX_OPTIONS}, so the first {MAX_OPTIONS} are "
            "shown.</p>\n"
        )
        limit = MAX_OPTIONS

    # --- the derivation ------------------------------------------------------
    try:
        model = derive_next(
            view, Path(root), minutes=minutes, limit=limit + 1, show_locked=True
        )
    except Exception:  # noqa: BLE001 — an operational failure, never a crash
        body = (
            head
            + "".join(notes)
            + '<section class="section">\n'
            '<div class="state state-failure">\n'
            '<p class="state-title">The list could not be worked out</p>\n'
            '<p class="state-body">Something needed to rank your next steps did '
            "not load, so no list is shown. Nothing about your progress "
            "changed, and no made-up numbers are reported in place of the "
            "real ones.</p>\n"
            '<p><a href="/next">Try again</a> — or '
            '<a href="/find">find a skill in the curriculum</a>.</p>\n'
            "</div>\n"
            "</section>\n"
        )
        return "Next", body, 200

    recommendations = list(model.recommendations)
    has_more = len(recommendations) > limit
    shown = recommendations[:limit]
    only_candidate = not has_more and len(shown) == 1

    # --- the ranked list, or the reason there is none ------------------------
    if shown:
        fits = [rec for rec in shown if rec.fits_session]
        queue = _candidate_stack(
            view,
            model,
            minutes=minutes,
            limit=limit,
            only_candidate=only_candidate,
        )
        if minutes <= 30 and not fits:
            results = (
                '<div class="state state-limited">\n'
                '<p class="state-title">None of these fits a '
                f"{minutes}-minute session</p>\n"
                '<p class="state-body">The skills below are the ones you could '
                "work on, and every one of them needs a longer block than the "
                f"{minutes} minutes you asked for. The list is kept as it is — "
                "widening the window is what changes it.</p>\n"
                '<p><a href="'
                f'{_esc(next_url(minutes * 2, limit))}">'
                f"Try a {minutes * 2}-minute session</a></p>\n"
                "</div>\n"
            )
        else:
            results = ""
        results += (
            '<section class="section">\n'
            '<div class="section-head">\n'
            '<h2 class="section-title">Study targets</h2>\n'
            '<p class="section-meta">Ranked for the time you have. Each one '
            "tells you why it is here.</p>\n"
            "</div>\n"
            f"{queue}"
        )
        if has_more:
            results += (
                f'<p class="section-meta">There are more options than shown. '
                f'<a href="{_esc(next_url(minutes, MAX_OPTIONS))}">'
                "Show more of them</a>.</p>\n"
            )
        results += "</section>\n"
    else:
        results = _empty_state(view)

    # --- the stale-readiness recovery prompt ---------------------------------
    # One shared panel, so /next and Today name the dependency identically:
    # refreshing readiness happens on the command line, and this page never
    # changes saved readiness.
    recovery = _readiness.stale_readiness_section(
        view,
        reload_href=next_url(minutes, limit),
        reload_label="reload this list",
    )

    body = (
        head
        + "".join(notes)
        + controls(minutes, limit)
        + recovery
        + results
        + _not_ready_card(model, view)
    )
    return "Next", body, 200
