"""
The deprecated part-to-HTML serializer (ADR 0009). Reachable only
through ``cards_html`` for out-of-scope line producers (health liveness,
report exports); a grep gate in ``tests/web/test_rich_seam.py`` pins it.

"""

from __future__ import annotations

from ...mentor.cards import (
    Sub,
    Title,
    Label,
    Banner,
    Lead,
    NextAction,
    Kicker,
    Pill,
    MentorCard,
    lines_to_cards,
)
from ._shared import (
    _esc,
    _normalize_pill_label,
    _sentence_case,
    _slug,
)


def _render_part(part) -> str:
    """One typed card part to HTML — the single card-type-to-CSS-class map."""
    if isinstance(part, Banner):
        return f'<p class="banner {_esc(part.kind)}">{_esc(part.text)}</p>'
    if isinstance(part, Pill):
        norm_label = _normalize_pill_label(part.label)
        return (
            f'<span class="pill {_esc(_slug(norm_label))}">{_esc(norm_label)}</span>'
        )
    if isinstance(part, Kicker):
        return f'<div class="kicker">{_esc(_sentence_case(part.text))}</div>'
    if isinstance(part, (Title, Lead)):
        return f'<p class="lead">{_esc(part.text)}</p>'
    if isinstance(part, Label):
        return f'<p class="label">{_esc(part.text)}</p>'
    if isinstance(part, Sub):
        return f'<div class="sub">{_esc(part.text)}</div>'
    if isinstance(part, NextAction):
        # The web affordance mapping (v2.4 S1): the fact's intent renders as
        # a human affordance — never its ``command`` string (that is the
        # CLI's presentation; P3.1 bans it from every page string).
        from ..interface import intent_label

        title = None
        if part.command and part.intent == "pass" and " passed" in part.command:
            title = part.command.split(" passed")[0].removeprefix("Mark ").strip()
        label = intent_label(part.intent, title=title)
        return (
            f'<p class="next-action" data-intent="{_esc(part.intent)}">'
            f"{_esc(label)}</p>"
        )
    return f"<p>{_esc(part.text)}</p>"  # Para (and any future plain part)


def _render_card_inner(card: MentorCard) -> str:
    return "\n".join(_render_part(part) for part in card.parts)


def render_cards(cards: list[MentorCard]) -> str:
    """Deprecated-compat serializer: typed parts as one ``<div class="card">``.

    The pre-§E part-to-HTML map. Reachable only through :func:`cards_html`
    for out-of-scope line producers (health liveness, report exports);
    route bodies compose Richer Cards and render via
    ``interface.render.render_rich_cards``. A grep gate in
    ``tests/web/test_rich_seam.py`` pins this to the two definitions.
    """
    return "".join(
        f'<div class="card">\n{_render_card_inner(card)}\n</div>\n' for card in cards
    )


def cards_html(lines: list[str]) -> str:
    """Deprecated compat: legacy lines as cards (health/reports/export only).

    Parses ``lines`` via ``mentor.cards.lines_to_cards`` and renders through
    the deprecated :func:`render_cards` part map so out-of-scope line
    producers keep their HTML without a route body composing MentorCards.
    """
    return render_cards(lines_to_cards(lines))

