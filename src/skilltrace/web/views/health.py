"""
GET ``/health`` — the study-guidance roll-up (ADR 0009).

"""

from __future__ import annotations

from ...execution.overdue import utc_today
from ..health import (
    derive_study_guidance,
    guidance_page_cards,
)
from ..interface.cards import Affordance, Card
from ..interface.render import render_guidance_cards
from ._shared import _esc
from .shell import _page_head


def health_body(root, query: dict | None = None) -> tuple[str, str, int]:
    """GET `/health` — the study-guidance roll-up (§C-ter, build #311).

    Five cards in the locked hierarchy (Stuck right now → Due for review →
    Evidence gaps → Study rhythm → Study resources), each carrying counts +
    one-line why + links — composed into interface ``Card`` objects by the
    pure derivation module and rendered through the one Card-to-HTML map
    (#318). Repository diagnostics are CLI-only with zero web-UI presence —
    the per-layer validator table and liveness lines live only in
    `skilltrace health`. Not a nav stop: health reaches only through the
    header pill strip + ``Health`` pointer.
    """
    view, head, failure = _page_head(root, query, dismiss_path="/health")
    if failure is not None:
        return failure
    guidance = derive_study_guidance(view, utc_today())
    cards, banner = guidance_page_cards(guidance)
    body = (
        head
        + render_guidance_cards([_ROLLUP_CARD], chromes={0: _ROLLUP_CHROME})
        + render_guidance_cards(
            cards,
            chromes={
                index: _card_chrome(derivation_card)
                for index, derivation_card in enumerate(guidance.cards)
            },
            banner=banner[1] if banner else None,
        )
    )
    return "Health", body, 200


# The page's intro card — the roll-up opener, page chrome (#318). The five
# study-guidance cards below it are the §C-ter derivation; this one is the
# page's own constant copy introducing them, in the same guidance anatomy.
_ROLLUP_CARD = Card(
    state="active",
    title="Health roll-up",
    why="Your study guidance for today.",
    resources=["The Health page is study guidance only."],
    affordances=(Affordance.from_intent("explore"),),
    kicker="Health roll-up",
)
_ROLLUP_CHROME = (
    '<p class="mut">Daily study guidance only — repository checks live '
    "on the command line, and nothing here blocks your next move.</p>\n"
)


def _card_chrome(card) -> str:
    """One guidance card's links and notes — the per-card attachment.

    The §C-ter guidance anatomy (links list, muted notes) rides the
    renderer's per-card raw-markup channel. Values escape through the one
    door here, exactly as every other attachment does.
    """
    parts: list[str] = []
    if card.links:
        parts.append('<ul class="guidance-links">\n')
        for label, href in card.links:
            parts.append(f'<li><a href="{_esc(href)}">{_esc(label)}</a></li>\n')
        parts.append("</ul>\n")
    for note in card.notes:
        parts.append(f'<p class="mut">{_esc(note)}</p>\n')
    return "".join(parts)

