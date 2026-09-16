"""The Richer Card renderer — the one Card-to-HTML map (v2.4 §E).

Page bodies compose :class:`interface.cards.Card` objects and hand them
here; nothing else turns a Card into HTML. The affordance renders from
the intent only (:func:`interface.affordances.intent_label`) — a binding's
``command`` string is the write path and is never rendered. ``state``
carries the per-request :class:`interface.cards.ActiveViewState` whose
flash renders as the page's banner block.
"""

from __future__ import annotations

import html
import re

from .cards import ActiveViewState, Card
from .handoff import handoff_html

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


def _esc(value: object) -> str:
    """Escape every interpolated value — the one door into page HTML."""
    return html.escape(str(value), quote=True)


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