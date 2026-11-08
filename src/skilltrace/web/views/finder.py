"""
GET ``/find`` — the Find a skill destination (spec-v3-study-day §10.3).

A dedicated discovery route across the whole curriculum. The search text,
the subject and the state are ordinary **labelled GET controls**, so a
result set has its own URL: it survives a reload, it can be shared, and the
back button reaches it (IC-4, IA-5). Nothing filters live — there is no
JavaScript anywhere (tier 0, ADR 0008).

A search that matches nothing explains itself and **keeps discovery
alive**: the foundations entries and the browse-by-subject index stay on
the page, so the route is never a dead end.

Locked skills appear as **explanation only** — never a selectable target
and never a start link (HB-4). Every learner-visible name is the readable
SkillNode title; a raw identifier survives only as labelled secondary
technical data (R1, VS-4).

**Why the page-local helpers are nested.** The ``web.views`` facade freezes
every module-level name (ADR 0009); a new top-level helper here would have
to be re-exported by a facade this slice may not touch. The helpers
therefore live inside the functions that use them.
"""

from __future__ import annotations

from urllib.parse import urlencode

from ...context import JoinedView
from ..discovery import (
    ENTRY_NODES,
    DiscoveryCard,
    browse_cards,
    browse_subjects,
    discover,
    discovery_page_cards,
)
from ..interface.render import render_discovery_cards
from ._shared import (
    _esc,
    _normalize_pill_label,
    _table,
    plural,
)
from .shell import _page_head

#: The five canonical node states, as filter choices. A locked skill is a
#: legitimate thing to look for — it is shown as explanation, never as a
#: target.
STATE_FILTERS: tuple[str, ...] = (
    "available",
    "active",
    "passed",
    "mastered",
    "locked",
)


def _discovery_chrome(card: DiscoveryCard) -> str:
    """One locked card's blocked-prerequisite tail — the page attachment (#319).

    The §C-bis anatomy's tail (the wall's name + link) travels with the
    page and rides the renderer's per-card attachment channel, exactly as
    the Health guidance links do (#318). Values escape through the one
    door here; locked stays the only wall — this names it, never overrides.
    """
    if not (card.locked and card.blocked_by_id):
        return ""
    return (
        f'<p class="sub">Blocked by <a href="/nodes/{_esc(card.blocked_by_id)}">'
        f"{_esc(card.blocked_by_title)}</a> — pass it first.</p>\n"
    )


def _render_results(cards: list[DiscoveryCard]) -> str:
    """Discovery records as page HTML: compose Cards, attach, render (#319).

    The §C-bis cards leave this page module as interface ``Card`` objects
    through the one Card-to-HTML map; this composer adds only the page's
    per-card tail attachment and owns no markup itself.
    """
    return render_discovery_cards(
        discovery_page_cards(cards),
        {index: _discovery_chrome(card) for index, card in enumerate(cards)},
    )


def _no_results_html(
    view: JoinedView,
    raw: str,
    subject: str = "",
    state: str = "",
) -> str:
    """The no-results state — an explanation that keeps discovery alive.

    A search that matches nothing is a fact about the curriculum, not about
    the learner. The panel names what was searched for and leaves the
    foundations entries and the browse index within reach, so the route
    never dead-ends.
    """
    entries = "".join(
        f'<li><a href="/nodes/{_esc(node_id)}">'
        f"{_esc(view.titles.get(node_id) or node_id)}</a></li>"
        for node_id in ENTRY_NODES
        if node_id in view.node_map
    )
    if raw:
        searched = f"nothing in the curriculum matches “{_esc(raw)}”"
    elif subject or state:
        searched = "no skill matches that combination of filters"
    else:
        searched = "there is nothing to show yet"
    return (
        '<div class="state state-empty">\n'
        '<p class="state-title">No skills match</p>\n'
        f'<p class="state-body">Nothing came back — {searched}. That is a fact '
        "about the curriculum, not about you. The whole curriculum is still "
        "open to you: start from a foundations entry, or browse by subject "
        "below.</p>\n"
        '<p class="state-body">Foundations entries:</p>\n'
        f"<ul>{entries}</ul>\n"
        '<p><a href="#browse">Browse by subject</a> — or '
        '<a href="/find">clear the search and start again</a>.</p>\n'
        "</div>\n"
    )


def _browse_html(view: JoinedView, *, sections: bool = True) -> str:
    """The browse-by-subject half: an index of subject links plus, when the
    page is in browse mode, one section per subject.

    Every subject link is a GET control, so a subject's skills have their
    own addressable URL rather than an in-page jump (IC-4).
    """
    subjects = browse_subjects(view)
    index_links = "".join(
        f'<li><a href="/find?subject={_esc(subject)}">{_esc(label)}</a></li>\n'
        for subject, label, _count in subjects
    )
    count_rows = [
        [_esc(label), str(count)] for _subject, label, count in subjects
    ]
    parts = [
        '<section class="section" id="browse">\n',
        '<div class="section-head">\n',
        '<h2 class="section-title">Browse by subject</h2>\n',
        '<p class="section-meta">Every subject in the curriculum. Each link '
        "is a filter of its own, so a subject has its own addressable "
        "URL.</p>\n",
        "</div>\n",
        f"<ul>{index_links}</ul>\n",
        _table(["Subject", "Skills"], count_rows),
        "\n</section>\n",
    ]
    if not sections:
        return "".join(parts)
    for subject, label, count in subjects:
        subject_cards = _render_results(browse_cards(view, subject))
        parts.append(
            f'<section class="section" id="subject-{_esc(subject)}">\n'
            '<div class="section-head">\n'
            f'<h2 class="section-title">{_esc(label)}</h2>\n'
            f'<p class="section-meta">{count} skill{plural(count)}</p>\n'
            "</div>\n"
            f"{subject_cards}"
            "</section>\n"
        )
    return "".join(parts)


def finder_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/find` — the Find a skill destination (spec-v3-study-day §10.3).

    The search text and the two filters are ordinary labelled GET
    controls, so the result set has its own URL: it survives a reload, it
    can be shared, and the back button reaches it. A query that matches
    nothing explains itself and keeps discovery alive; a locked skill is
    explanation, never a target; every learner-visible name is the
    readable SkillNode title.

    Selection navigates only — nothing here starts, passes or writes.
    """
    from ..discovery import subject_of

    query = query or {}
    view, head, failure = _page_head(
        root, query, dismiss_path="/find", current_view="find", path="/find"
    )
    if failure is not None:
        return failure

    raw = ""
    if query:
        source = query.get("q") or query.get("node_id") or [""]
        raw = (source[0] if source else "").strip()
    subject = ((query.get("subject") or [""])[0] or "").strip()
    state = ((query.get("state") or [""])[0] or "").strip()
    mode = (query.get("mode") or [""])[0]

    def find_url(**params: str) -> str:
        """The Find destination with these controls — one addressable URL."""
        clean = {key: value for key, value in params.items() if value}
        if not clean:
            return "/find"
        return "/find?" + urlencode(clean)

    def controls() -> str:
        """The search and the two filters — labelled GET controls (IC-4)."""
        subject_options = ['<option value="">Every subject</option>\n']
        for key, label, _count in browse_subjects(view):
            chosen = " selected" if key == subject else ""
            subject_options.append(
                f'<option value="{_esc(key)}"{chosen}>{_esc(label)}</option>\n'
            )
        state_options = ['<option value="">Any state</option>\n']
        for key in STATE_FILTERS:
            chosen = " selected" if key == state else ""
            state_options.append(
                f'<option value="{_esc(key)}"{chosen}>'
                f"{_esc(_normalize_pill_label(key))}</option>\n"
            )
        hidden = (
            f'<input type="hidden" name="mode" value="{_esc(mode)}">' if mode else ""
        )
        return (
            '<section class="section">\n'
            '<div class="section-head">\n'
            '<h2 class="section-title">Find a skill</h2>\n'
            '<p class="section-meta">Search the whole curriculum. Your search '
            "is a link — reload it, share it, or come back to it with the back "
            "button.</p>\n"
            "</div>\n"
            '<form class="filters" method="get" action="/find">\n'
            f"{hidden}"
            '<div class="form-row">'
            '<label for="find-q">Search skills</label>'
            f'<input id="find-q" type="search" name="q" value="{_esc(raw)}"'
            ' size="32">'
            "</div>\n"
            '<div class="form-row">'
            '<label for="find-subject">Subject</label>'
            f'<select id="find-subject" name="subject">'
            f'{"".join(subject_options)}</select>'
            "</div>\n"
            '<div class="form-row">'
            '<label for="find-state">State</label>'
            f'<select id="find-state" name="state">'
            f'{"".join(state_options)}</select>'
            "</div>\n"
            '<div class="actions">'
            '<button class="btn secondary" type="submit">Search</button></div>\n'
            "</form>\n"
            "</section>\n"
        )

    # --- the result set ------------------------------------------------------
    if raw:
        base = discover(view, raw)
    elif subject:
        base = browse_cards(view, subject)
    else:
        base = []
        for key, _label, _count in browse_subjects(view):
            base.extend(browse_cards(view, key))

    matched = base
    if subject and raw:
        matched = [card for card in matched if subject_of(card.node_id) == subject]
    hidden_by_subject = len(base) - len(matched)
    shown = [card for card in matched if not state or card.state == state]
    hidden_by_state = len(matched) - len(shown)

    parts = [controls()]

    if raw or subject or state:
        if shown:
            limits = ""
            scope = "that match" if raw else "in the curriculum"
            if hidden_by_subject:
                limits += (
                    '<div class="state state-limited">\n'
                    '<p class="state-title">Some matches are in other '
                    "subjects</p>\n"
                    f'<p class="state-body">{hidden_by_subject} other skill'
                    f"{plural(hidden_by_subject)} {scope} are in another "
                    "subject. The subject filter is what hides them.</p>\n"
                    '<p><a href="'
                    f'{_esc(find_url(q=raw, state=state))}">'
                    "Show every match</a></p>\n"
                    "</div>\n"
                )
            if hidden_by_state:
                limits += (
                    '<div class="state state-limited">\n'
                    '<p class="state-title">Some matches are in another '
                    "state</p>\n"
                    f'<p class="state-body">{hidden_by_state} other skill'
                    f"{plural(hidden_by_state)} {scope} are in another "
                    "state. The state filter is what hides them.</p>\n"
                    '<p><a href="'
                    f'{_esc(find_url(q=raw, subject=subject))}">'
                    "Show every match</a></p>\n"
                    "</div>\n"
                )
            if raw:
                count_text = (
                    f"{len(shown)} skill{plural(len(shown))} "
                    f"match{plural(len(shown), 'es', '')} “{_esc(raw)}”"
                )
            else:
                count_text = f"{len(shown)} skill{plural(len(shown))}"
            parts.append(
                '<section class="section">\n'
                '<div class="section-head">\n'
                '<h2 class="section-title">Results</h2>\n'
                f'<p class="section-meta">{count_text}. The skill identifier '
                "is shown in grey under each skill, for reference.</p>\n"
                "</div>\n"
                f"{limits}"
                f"{_render_results(shown)}"
                "</section>\n"
            )
        else:
            parts.append(
                '<section class="section">\n'
                f"{_no_results_html(view, raw, subject, state)}"
                "</section>\n"
            )

    parts.append(_browse_html(view, sections=not (raw or subject or state)))
    return (
        "Find a skill",
        head + "".join(parts),
        200,
    )
