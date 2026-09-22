"""The Richer Card renderer — the one Card-to-HTML map (v2.4 §E).

Page bodies compose :class:`interface.cards.Card` objects and hand them
here; nothing else turns a Card into HTML. The affordance renders from
the intent only (:func:`interface.affordances.intent_label`) — a binding's
``command`` string is the write path and is never rendered. ``state``
carries the per-request :class:`interface.cards.ActiveViewState` whose
flash renders as the page's banner block.

Not every legitimate producer is a Card composition. The blessed hand-rolled
ones are named and justified in :data:`SANCTIONED_CARD_PRODUCERS` (#317) — the
middle state of unowned card markup ends there: in a blessed page module, a
``<div class="card">`` either composes :class:`interface.cards.Card` through
this map or appears in that registry, so "nobody owns it" is no longer a
reachable state for those pages.

Escaping is not this module's to define: every interpolated value goes
through the one door in :mod:`interface.text` (imported as ``_esc``), so the
renderer and every other web-side HTML producer share a single escaper
(#315). The Health guidance cards render here too (#318) — the §C-ter
anatomy is the map's guidance variant, not a page-side producer — and so
do the discovery result cards (#319): the §C-bis anatomy (title link,
state chip, description, secondary id) is the map's discovery variant,
which is why the finder surface owes no ad-hoc card producer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .cards import ActiveViewState, Card, CHIP_LABELS
from .handoff import handoff_html
from .text import esc as _esc

# One banner kind map: the CLI's banner kinds (warning / error / advisory /
# locked appendix) collapse onto the sublayer's semantic classes — the alias
# classes never reach a page (P5.4 alias collapse).
BANNER_CLASSES: dict[str, str] = {
    "error": "err",
    "warning": "warn",
    "advisory": "attention",
    "locked": "warn",
    "ok": "success",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def sentence_case(text: str) -> str:
    """ALL-CAPS kickers → sentence case (P3.6)."""
    text = text.strip()
    if not text:
        return ""
    if text.isupper():
        lowered = text.lower()
        return lowered[0].upper() + lowered[1:]
    return text


def _state_label(state: str) -> str:
    """The canonical state word's display form (P3.4 — no synonyms)."""
    return state.capitalize()


def banner_html(kind: str, text: str) -> str:
    """One banner paragraph with its semantic class (P5.4 alias collapse)."""
    css = BANNER_CLASSES.get(kind, "warn")
    return f'<p class="banner {_esc(css)}">{_esc(text)}</p>\n'


def render_rich_cards(
    cards: list[Card],
    banners: list[tuple[str, str]] | None = None,
    *,
    state: ActiveViewState | None = None,
    extras: dict[int, str] | None = None,
    affordance_html: dict[int, str] | None = None,
    affordance_mode: str = "copy",
    classes: dict[int, str] | None = None,
) -> str:
    """Cards + banners (+ the per-request flash) as page HTML.

    ``extras`` attaches page-level chrome (a per-card ``<details>`` facts
    block) *inside* the card div; ``affordance_html`` replaces the default
    affordance rendering for one card (the one live write path — a form
    whose POST target is the command binding, never a rendered command);
    ``affordance_mode="link"`` renders the default affordance as the
    primary action link instead of the copy-only paragraph; ``classes``
    adds a per-card CSS class (the focus card's ``focus``).
    """
    parts: list[str] = []
    if state is not None:
        for css, text in state.flash:
            parts.append(f'<p class="banner {_esc(css)}">{_esc(text)}</p>\n')
    for kind, text in banners or ():
        parts.append(banner_html(kind, text))
    for index, card in enumerate(cards):
        parts.append(
            _card_html(card, index, extras, affordance_html, affordance_mode, classes)
        )
    return "".join(parts)


@dataclass(frozen=True)
class SanctionedProducer:
    """A hand-rolled card producer the map blesses instead of absorbing (#317).

    ``name`` is the ``module.attribute`` path of the producer, ``surface`` the
    route it serves, ``reason`` the written verdict for why it is not a
    :class:`interface.cards.Card` composition — the justification a reader
    gets instead of a silent exception to the map.
    """

    name: str
    surface: str
    reason: str


# The sanctioned non-Card producers (#317) — the map names every card-class
# producer the analytics page module hand-rolls, so the middle state
# (hand-rolled card markup nobody owns) ends there: a page-side
# ``<div class="card">`` in ``views/analytics.py`` either composes an
# :class:`interface.cards.Card` through :func:`render_rich_cards` or is
# blessed below with its reason. Verdict for the analytics page's per-theme
# cards: **blessed, not migrated**.
#
# Scope: entries name page-layer producers (``views.*``) of one surface, and
# the gate in ``tests/web/test_sanctioned_card_producers.py`` keeps that a
# closed world — an unlisted producer of card markup in the analytics module
# fails there, and a listed producer that stops producing markup fails too.
# Deliberately outside this claim: shared shell chrome (the error and modal
# cards in ``views.shell``, which render on every route); the finder's page
# chrome — the search-form card, the no-results pattern, and the browse
# index/subject containers (#319 migrated the discovery *node* cards through
# :func:`render_discovery_cards`; the chrome has no node or state behind it,
# same verdict as the shell's); and the deprecated compat serializer
# (``views.compat.render_cards``), which is pinned by its own grep gate and
# retires whole-file in #320.
SANCTIONED_CARD_PRODUCERS: dict[str, SanctionedProducer] = {
    entry.name: entry
    for entry in (
        SanctionedProducer(
            name="views.analytics._analytics_card",
            surface="/analytics",
            reason=(
                "blessed, not migrated (#317): the theme card is a chart "
                "panel — the engine's chart SVG, one theme's derived numbers "
                "and an export form, with no node behind them. A Card's state "
                "is one of the five canonical node-state words, so composing "
                "one here would assert a node state (and one next action) "
                "that do not exist, and the seam's guarantees — closed "
                "intents, no command strings — are vacuous for a panel with "
                "no affordance."
            ),
        ),
        SanctionedProducer(
            name="views.analytics._analytics_controls",
            surface="/analytics",
            reason=(
                "blessed, not migrated (#317): the controls card is page "
                "chrome — one GET form plus plain theme-toggle links, not "
                "engine content. A Card affordance binds a dispatcher write "
                "command, so composing one here would invent a write intent "
                "the panel does not have."
            ),
        ),
    )
}


def _card_html(
    card: Card,
    index: int,
    extras: dict[int, str] | None,
    affordance_html: dict[int, str] | None,
    affordance_mode: str,
    classes: dict[int, str] | None,
) -> str:
    extra = (classes or {}).get(index, "")
    cls = "card" + (f" {extra}" if extra else "")
    lines: list[str] = [f'<div class="{_esc(cls)}">\n']
    if card.kicker:
        lines.append(f'<div class="kicker">{_esc(sentence_case(card.kicker))}</div>\n')
    title_html = _esc(card.title)
    if card.node_id:
        title_html = f'<a href="/nodes/{_esc(card.node_id)}">{title_html}</a>'
    lines.append(f'<p class="lead">{title_html}</p>\n')
    label = _state_label(card.state)
    lines.append(
        f'<p><span class="pill {_esc(_slug(label))}">{_esc(label)}</span></p>\n'
    )
    lines.append(f'<p class="big">{_esc(card.why)}</p>\n')
    lines.append('<p class="label">Where to learn</p>\n')
    for resource in card.resources:
        lines.append(f'<div class="sub">{_esc(resource)}</div>\n')
    if affordance_html and index in affordance_html:
        lines.append(affordance_html[index])
    else:
        affordance = card.affordances[0]
        if affordance_mode == "link" and card.node_id:
            lines.append(
                '<div class="actions">'
                f'<a class="btn primary" href="/nodes/{_esc(card.node_id)}" '
                f'data-intent="{_esc(affordance.intent)}">'
                f"{_esc(affordance.label)}</a></div>\n"
            )
        else:
            lines.append(
                f'<p class="next-action" data-intent="{_esc(affordance.intent)}">'
                f"{_esc(affordance.label)}</p>\n"
            )
            if affordance.intent == "schedule_review":
                lines.append(handoff_html("Scheduling a review", card.title))
    if card.disclosure:
        # The optional one-click facts render inline — the collapsible
        # budget stays with the page's own advisory details (P5.3).
        lines.append('<p class="label">Facts</p>\n')
        lines.append(f'<div class="sub">{_esc(card.disclosure)}</div>\n')
    if extras and index in extras:
        lines.append(extras[index])
    lines.append("</div>\n")
    return "".join(lines)


def render_guidance_cards(
    cards: list[Card],
    chromes: dict[int, str] | None = None,
    banner: str | None = None,
) -> str:
    """The Health study-guidance cards (§C-ter) as page HTML (#318).

    The guidance anatomy is its own locked shape — ``card guidance`` div,
    kicker, one-line why, links list, muted notes — and it renders here,
    inside the one Card-to-HTML map, so no page-side producer owns card
    markup. The §C-ter guidance card is a read-only mirror: it has no state
    pill, resources section, or next action of its own, so the Richer-Card
    minimum fields its composition carries (:func:`web.health.guidance_page_cards`
    turns the pure derivation into :class:`interface.cards.Card` objects)
    render nowhere. ``chromes`` is the per-card links/notes attachment the
    page composes (escaped through the one door at the page layer); the
    limited-data advisory banner, when present, renders ahead of the cards
    under the locked §C-ter class — ``banner advisory`` is the contract's
    own class, pinned by the guidance tests, not a P5.4 alias.
    """
    parts: list[str] = []
    if banner:
        parts.append(f'<p class="banner advisory">{_esc(banner)}</p>\n')
    for index, card in enumerate(cards):
        parts.append(_guidance_card_html(card, index, chromes))
    return "".join(parts)


def _guidance_card_html(card: Card, index: int, chromes: dict[int, str] | None) -> str:
    """One §C-ter guidance card: kicker + one-line why + the attachment."""
    lines: list[str] = ['<div class="card guidance">\n']
    if card.kicker:
        lines.append(f'<div class="kicker">{_esc(sentence_case(card.kicker))}</div>\n')
    lines.append(f'<p class="big">{_esc(card.why)}</p>\n')
    if chromes and index in chromes:
        lines.append(chromes[index])
    lines.append("</div>\n")
    return "".join(lines)


def render_discovery_cards(
    cards: list[Card],
    chromes: dict[int, str] | None = None,
) -> str:
    """The discovery result and browse cards as page HTML (#319).

    The §C-bis anatomy is the map's discovery variant — ``card result``
    frame (``locked`` for the wall), the title as a node link *unless the
    card is locked* (locked stays the only wall), the state chip from the
    shared :data:`interface.cards.CHIP_LABELS` pairing, the one-line
    description, the foundations-stub pending marker when the composition
    set ``disclosure``, the secondary node id, then the page's blocked-
    prerequisite tail — so the finder surface owes no ad-hoc card producer
    and the closed-intent / no-command guarantees cover its cards by
    construction. The composition (:func:`web.discovery.discovery_page_cards`)
    turns each derivation record into a ``Card``; ``chromes`` is the
    per-card blocked-tail attachment the page composes (escaped through the
    one door at the page layer), exactly as on the guidance variant. The
    neutral ``resources`` and single ``explore`` affordance the Card
    minimums require render nowhere here: selection navigates only.
    """
    return "".join(
        _result_card_html(card, index, chromes)
        for index, card in enumerate(cards)
    )


def _result_card_html(card: Card, index: int, chromes: dict[int, str] | None) -> str:
    """One §C-bis discovery card: lead + chip, description, id, tail."""
    locked = card.state == "locked"
    cls = "card result" + (" locked" if locked else "")
    title_html = _esc(card.title)
    if not locked and card.node_id:
        title_html = f'<a href="/nodes/{_esc(card.node_id)}">{title_html}</a>'
    chip = CHIP_LABELS.get(card.state, card.state.capitalize())
    lines = [f'<div class="{cls}">\n']
    lines.append(
        f'<p class="lead">{title_html} '
        f'<span class="pill {_esc(_slug(chip))}">{_esc(chip)}</span></p>\n'
    )
    lines.append(f'<p class="big">{_esc(card.why)}</p>\n')
    if card.disclosure:
        lines.append(f'<p class="mut">{_esc(card.disclosure)}</p>\n')
    if card.node_id:
        lines.append(f'<p class="mut ref">{_esc(card.node_id)}</p>\n')
    if chromes and index in chromes:
        lines.append(chromes[index])
    lines.append("</div>\n")
    return "".join(lines)