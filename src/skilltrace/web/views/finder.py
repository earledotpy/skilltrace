"""
GET ``/nodes/jump`` — the title-first jump finder (ADR 0009).

"""

from __future__ import annotations

from ...context import JoinedView
from ..discovery import (
    DiscoveryCard,
    ENTRY_NODES,
    browse_cards,
    browse_subjects,
    discover,
    discovery_page_cards,
)
from ..interface.render import render_discovery_cards
from ._shared import (
    _esc,
    plural,
)
from .shell import _page_head


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


def _no_results_html(view: JoinedView, raw: str) -> str:
    """The no-results pattern — never an empty box (spec §C-bis)."""
    entries = "".join(
        f'<li><a href="/nodes/{_esc(node_id)}">'
        f"{_esc(view.titles.get(node_id) or node_id)}</a></li>"
        for node_id in ENTRY_NODES
        if node_id in view.node_map
    )
    return (
        '<div class="card">\n'
        f'<h2 class="result-count">No skills match “{_esc(raw)}”.</h2>\n'
        "<p>Try different words, or start from a foundations entry:</p>\n"
        f"<ul>{entries}</ul>\n"
        '<p><a href="#browse">Browse by subject</a></p>\n'
        "</div>\n"
    )


def _browse_html(view: JoinedView) -> str:
    """The browse-by-subject half: anchor index + grouped-count table +
    per-subject card lists (entry nodes first, then rest, locked greyed)."""
    subjects = browse_subjects(view)
    index_links = "".join(
        f'<li><a href="#subject-{_esc(subject)}">{_esc(label)}</a></li>'
        for subject, label, _count in subjects
    )
    count_rows = "".join(
        f"<tr><td>{_esc(label)}</td><td>{count}</td></tr>"
        for _subject, label, count in subjects
    )
    parts = [
        '<div class="card" id="browse">\n',
        '<div class="kicker">Browse by subject</div>\n',
        f"<ul>{index_links}</ul>\n",
        "<table>\n<thead><tr><th>Subject</th><th>Skills</th></tr></thead>\n"
        f"<tbody>{count_rows}</tbody>\n</table>\n",
        "</div>\n",
    ]
    for subject, label, _count in subjects:
        subject_cards = _render_results(browse_cards(view, subject))
        parts.append(
            f'<div class="card" id="subject-{_esc(subject)}">\n'
            f'<div class="kicker">{_esc(label)}</div>\n'
            f"{subject_cards}"
            "</div>\n"
        )
    return "".join(parts)


def finder_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/nodes/jump` — the discovery combination surface (§C-bis, #310).

    The v2.4 S4 title-first list, upgraded to the locked discovery contract:
    a text input plus server-rendered result cards on submit — subject/track
    labels + title words + curated synonyms are the primary matchers, node-ID
    exact/fragment matching secondary only; every match shows (no silent
    top-1), ranked available first and locked last; locked cards render
    greyed and name + link their blocking prerequisite; a no-results query
    yields the entry-links + browse-anchor pattern; and the browse-by-subject
    index (anchor links per subject + grouped-count table) stands alongside.
    Zero JavaScript — full function with script absent (tier 0, ADR 0008; no
    live-filter). Selection navigates only. Nothing is marked current here
    (header form only).
    """
    view, head, failure = _page_head(root, query, dismiss_path="/nodes/jump")
    if failure is not None:
        return failure

    raw = ""
    if query:
        source = query.get("q") or query.get("node_id") or [""]
        raw = (source[0] if source else "").strip()

    parts = [
        '<div class="card">\n',
        '<div class="kicker">Find a skill</div>\n',
        '<form class="finder" method="get" action="/nodes/jump">'
        f'<label>Search skills <input type="text" name="q" value="{_esc(raw)}" placeholder="Type a skill name" aria-label="search skills by title" size="32"></label>'
        '<button type="submit">Search</button>'
        "</form>\n",
        "</div>\n",
    ]
    if raw:
        cards = discover(view, raw)
        heading = (
            f'<h2 class="result-count">{len(cards)} '
            f"skill{plural(len(cards))} "
            f"match{plural(len(cards), 'es', '')} "
            f"“{_esc(raw)}”</h2>\n"
        )
        if cards:
            parts.append(heading)
            parts.append(_render_results(cards))
        else:
            parts.append(_no_results_html(view, raw))
    parts.append(_browse_html(view))
    return (
        "Find a skill",
        head + "".join(parts),
        200,
    )

