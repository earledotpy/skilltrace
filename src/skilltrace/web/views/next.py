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
* **empty** — nothing is recommendable: an authoritative reason plus a
  recovery path that keeps discovery alive;
* **limited** — the values are real but the session window they need is
  not met: the values are retained and the threshold is stated;
* **could not compute** — the derivation failed: an operational failure
  with a precise recovery path, never zeros and never a fabricated fact.

A progress store whose readiness no longer matches the curriculum is
reported as a recovery prompt: the dependency is named, never hidden
behind silence.

**Why the helpers are nested.** The ``web.views`` facade freezes every
module-level name (ADR 0009); a new top-level helper here would have to be
re-exported by a facade this slice may not touch. The page-local helpers
therefore live inside the functions that use them, and the engine seams
they need are imported where they are used.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from ...commands.recommend import derive_next
from ._shared import (
    _esc,
    _normalize_pill_label,
    _parse_int,
    plural,
)
from .shell import _page_head

#: The bounded list: the number of options a learner may ask for is capped,
#: so one request can never turn the page into the whole curriculum.
MAX_OPTIONS = 20
#: How many locked skills the explanation section names before it counts the
#: rest — the explanation is bounded too, and the count stays truthful.
MAX_EXPLAINED = 8


def _why_details(reason: str, facts: list[str]) -> str:
    """The ``Why this?`` disclosure — the whole of this item's reasoning.

    The reason is the same honest sentence the queue shows; the facts are
    the contributing conditions behind it. Advisory wording rides along so
    the learner knows the ordering is advisory and never a gate (IC-8).
    """
    if facts:
        detail = "<ul>" + "".join(f"<li>{_esc(fact)}</li>" for fact in facts) + "</ul>"
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
    to the skill — and every item states why it sits where it does.
    """

    def downstream_count(node_id: str) -> int:
        """How many other skills are waiting on this one.

        The honest form of the ranker's leverage term: only the active hard
        prerequisites count, because only those make a skill wait. The
        relationship comes from the edge file alone (HB-8).
        """
        return sum(
            1
            for edge in view.edges
            if edge.active
            and edge.edge_type == "hard_prerequisite"
            and edge.source == node_id
        )

    def facts_for(rec) -> list[str]:
        """The contributing conditions behind one item's rank.

        Each fact is a derived condition the learner can check for
        themselves; nothing here is a score, a weight or a flag name.
        """
        facts: list[str] = []
        if rec.is_active:
            facts.append("You have already started this one, so it comes first.")
        if minutes <= 30:
            if rec.fits_session:
                facts.append(f"It fits a {minutes}-minute session.")
            else:
                facts.append(f"It does not fit a {minutes}-minute session.")
        if rec.prereq_reviews_due:
            facts.append(
                "A skill you have already passed is fading below retention, "
                "and this one builds on it."
            )
        if rec.open_blocked:
            facts.append("You have an open blocker recorded on it.")
        if rec.remediation_boosted:
            facts.append("It is a remediation step for a skill you are stuck on.")
        if rec.agent_boosted:
            facts.append("An advisory signal ranks it higher than the rest.")
        waiting = downstream_count(rec.node_id)
        if waiting:
            facts.append(
                f"{waiting} other skill{plural(waiting)} "
                f'{"is" if waiting == 1 else "are"} waiting on this one.'
            )
        return facts

    def reason_for(rec, facts: list[str]) -> str:
        """One honest sentence: why this skill sits where it does."""
        if not facts:
            if only_candidate:
                return "It is the only skill available to start right now."
            return "It is available now and nothing is holding it up."
        if len(facts) == 1:
            return facts[0]
        return f"{facts[0]} {facts[-1]}"

    items: list[str] = []
    for index, rec in enumerate(model.recommendations[:limit]):
        title = view.titles.get(rec.node_id) or "Another skill"
        state = view.store.state_of(rec.node_id)
        facts = facts_for(rec)
        reason = reason_for(rec, facts)
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
    return (
        '<section class="section">\n'
        '<div class="section-head">\n'
        '<h2 class="section-title">Not ready yet</h2>\n'
        '<p class="section-meta">These skills are waiting on another skill. '
        "They are not on your list, and they cannot be started yet.</p>\n"
        "</div>\n"
        f"{_not_ready_list(model, view)}\n"
        "</section>\n"
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

    def stale_readiness() -> list[str]:
        """The skills whose saved readiness no longer matches the curriculum.

        The readiness rule is the engine's, not the page's: the page asks
        the engine what each skill's readiness *would* be and compares it
        with what is saved. Asserted progress is never compared — a refresh
        never moves it.
        """
        from ...graph.readiness import derive_readiness
        from ...graph.state import ASSERTED_STATES

        sources: dict[str, list[str]] = {}
        for edge in view.edges:
            if edge.active and edge.edge_type == "hard_prerequisite":
                sources.setdefault(edge.target, []).append(edge.source)
        stale: list[str] = []
        for node in view.nodes:
            current = view.store.state_of(node.id)
            if current in ASSERTED_STATES:
                continue
            if derive_readiness(node.id, sources, view.store) != current:
                stale.append(node.id)
        return stale

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
        results = (
            '<section class="section">\n'
            '<div class="state state-empty">\n'
            '<p class="state-title">Nothing is recommendable right now</p>\n'
            '<p class="state-body">No skill is available or active for a '
            f"{minutes}-minute session at the moment. The ones you have "
            "already finished are done, and the rest are waiting on a skill "
            "you have not finished yet. That is a fact about the curriculum, "
            "not a problem with you.</p>\n"
            '<p><a href="/find">Find a skill</a> — the whole curriculum is '
            'open to you, whatever this list says.</p>\n'
            "</div>\n"
            "</section>\n"
        )

    # --- the stale-readiness recovery prompt ---------------------------------
    stale = stale_readiness()
    recovery = ""
    if stale:
        recovery = (
            '<div class="state state-recovery">\n'
            '<p class="state-title">Your saved readiness is out of date</p>\n'
            f'<p class="state-body">The curriculum changed since your '
            f"readiness was last computed, so {len(stale)} skill"
            f"{plural(len(stale))} may be shown as locked or available "
            "incorrectly. Refreshing readiness happens on the command line — "
            "this page never changes your saved readiness, and a refresh never "
            "moves your recorded progress: active, passed and mastered stay "
            "exactly as they are.</p>\n"
            '<p class="state-body">Refresh your readiness, then '
            f'<a href="{_esc(next_url(minutes, limit))}">reload this list</a>.</p>\n'
            "</div>\n"
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
