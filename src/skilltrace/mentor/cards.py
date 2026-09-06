"""Structured Mentor cards — the deep seam between CLI derivations and surfaces.

Replaces the undocumented line-grammar contract (``[tag]`` prefixes, ``---``
separators, indentation, uppercase kickers) that coupled the CLI handlers to
the web layer through a flat ``list[str]``. Handlers in ``commands/`` now
produce ``list[MentorCard]`` — typed parts with explicit fields — and the two
surfaces consume the model directly:

- terminals via ``render.cards_to_lines`` (the sole owner of the legacy line
  shape; terminal output is byte-identical to before),
- browsers via ``web.views.render_cards`` (a direct part-to-HTML map; no
  regex, no line parsing).

Pure data: no I/O, no HTML generation, no imports from ``views`` or
``render``. Tests construct cards without touching either surface.

A card is an ordered list of typed parts. The part vocabulary mirrors the
legacy grammar one-to-one so the serializer round-trips verbatim:

- ``Banner(kind, text)`` — the ``[warning]`` / ``[error]`` / ``[advisory]``
  callouts. ``kind`` is a field, not a string prefix.
- ``Pill(label)`` — the indented ``[State]`` chips. ``label`` is a field;
  the CSS slug is derived once at render time.
- ``Kicker(text)`` — the uppercase section openers (``TODAY``,
  ``OPTION 1 — …``, ``DO THIS NEXT``).
- ``Title(text)`` — the skill title directly under a kicker (renders lead).
- ``Lead(text)`` — the first prose under a kicker (renders lead).
- ``Label(text)`` — the short callout heading above indented lines.
- ``Para(text)`` — a plain paragraph.
- ``Sub(text)`` — an indented detail line.

``MentorCard.kind`` marks standalone banner/appendix cards (``"warning"``,
``"error"``, ``"advisory"``, ``"locked"``); content cards leave it ``None``.
The serializer uses it only to pick the inter-card separator (``---``
between content cards, a blank line before banner/appendix cards, nothing
after a leading banner) — the ``---`` convention no longer leaks into
handler code because card boundaries are already explicit.

``lines_to_cards`` is the deprecated-compat parser for out-of-scope surfaces
(health liveness, report exports) that still produce legacy lines. It owns
the only remaining copy of the line-grammar heuristics, moved out of the web
layer so ``views.py`` carries no regex. New code must construct cards
directly instead of parsing lines.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# --- Typed parts ------------------------------------------------------------


@dataclass(frozen=True)
class Banner:
    """An advisory callout. ``kind`` is a field, never a string prefix."""

    kind: str
    text: str


@dataclass(frozen=True)
class Pill:
    """A state chip. ``label`` is a field; the CSS slug derives at render."""

    label: str


@dataclass(frozen=True)
class Kicker:
    """An uppercase section opener (``TODAY``, ``OPTION 1 — …``)."""

    text: str


@dataclass(frozen=True)
class Title:
    """The skill title directly under a kicker (renders as lead)."""

    text: str


@dataclass(frozen=True)
class Lead:
    """The first prose paragraph under a kicker (renders as lead)."""

    text: str


@dataclass(frozen=True)
class Label:
    """A short callout heading above indented ``Sub`` lines."""

    text: str


@dataclass(frozen=True)
class Para:
    """A plain paragraph."""

    text: str


@dataclass(frozen=True)
class Sub:
    """An indented detail line (resource, action, locked entry)."""

    text: str


CardPart = Banner | Pill | Kicker | Title | Lead | Label | Para | Sub


@dataclass(frozen=True)
class MentorCard:
    """One browser card: an ordered list of typed parts.

    ``kind`` is ``None`` for content cards and ``"warning"`` / ``"error"`` /
    ``"advisory"`` / ``"locked"`` for standalone banner/appendix cards that
    previously started their own ``---``/banner block.
    """

    parts: tuple[CardPart, ...] = ()
    kind: str | None = None

    def __init__(
        self,
        parts: tuple[CardPart, ...] | list[CardPart] = (),
        kind: str | None = None,
    ) -> None:
        object.__setattr__(self, "parts", tuple(parts))
        object.__setattr__(self, "kind", kind)

    @classmethod
    def banner_card(cls, kind: str, text: str) -> "MentorCard":
        """A standalone banner card (previously its own ``[kind]`` block)."""
        return cls(parts=(Banner(kind=kind, text=text),), kind=kind)


# --- Compat parser: legacy lines -> cards (out-of-scope surfaces only) --------

_BANNER_PREFIXES = ("[warning] ", "[error] ", "[advisory] ")
_PILL_RE = re.compile(r"\[(.+)\]")


def _is_kicker(text: str) -> bool:
    stripped = text.strip()
    return (
        bool(stripped)
        and stripped == stripped.upper()
        and any(ch.isalpha() for ch in stripped)
        and len(stripped) <= 80
    )


def _split_blocks(lines: list[str]) -> list[list[str]]:
    """Split legacy lines at ``---`` separators and standalone banners."""
    blocks: list[list[str]] = [[]]
    for raw in lines:
        stripped = raw.strip()
        if stripped == "---":
            blocks.append([])
            continue
        if any(stripped.startswith(prefix) for prefix in _BANNER_PREFIXES):
            blocks.append([raw])
            continue
        blocks[-1].append(raw)
    return [block for block in blocks if any(line.strip() for line in block)]


def _parts_of_block(block: list[str]) -> tuple[CardPart, ...]:
    """Infer typed parts for one legacy block (mirrors the retired transform)."""
    substantive = [line for line in block if line.strip()]
    parts: list[CardPart] = []
    for index, raw in enumerate(substantive):
        stripped = raw.strip()

        banner = next(
            (p for p in _BANNER_PREFIXES if stripped.startswith(p)), None
        )
        if banner:
            kind = banner.strip("[] ")
            parts.append(Banner(kind=kind, text=stripped[len(banner):]))
            continue

        if raw.startswith("  "):
            match = _PILL_RE.fullmatch(stripped)
            if match:
                parts.append(Pill(label=match.group(1)))
            else:
                parts.append(Sub(text=stripped))
            continue

        if _is_kicker(stripped):
            parts.append(Kicker(text=stripped))
            continue

        if index:
            previous_is_sub = substantive[index - 1].startswith("  ")
            if not previous_is_sub and _is_kicker(substantive[index - 1].strip()):
                parts.append(Lead(text=stripped))
                continue
        if (
            index + 1 < len(substantive)
            and substantive[index + 1].startswith("  ")
            and len(stripped) <= 60
        ):
            parts.append(Label(text=stripped))
            continue
        # A title directly under a kicker renders as lead; the parser keeps
        # the explicit Title type only when the raw line follows a kicker and
        # the block opened with one — otherwise it is a plain paragraph.
        parts.append(Para(text=stripped))
    return tuple(parts)


def lines_to_cards(lines: list[str]) -> list[MentorCard]:
    """Parse legacy lines into cards (compat for health/report surfaces).

    Deprecated for new code — handlers must construct ``MentorCard``
    objects directly. Preserved so out-of-scope line producers (health
    liveness, report exports) render through the same ``render_cards``
    pipeline without duplicating the grammar in the web layer.
    """
    cards: list[MentorCard] = []
    for block in _split_blocks(lines):
        substantive = [line for line in block if line.strip()]
        if (
            len(substantive) == 1
            and substantive[0].strip() != "---"
            and any(
                substantive[0].strip().startswith(prefix)
                for prefix in _BANNER_PREFIXES
            )
        ):
            stripped = substantive[0].strip()
            prefix = next(
                p for p in _BANNER_PREFIXES if stripped.startswith(p)
            )
            kind = prefix.strip("[] ")
            cards.append(MentorCard.banner_card(kind, stripped[len(prefix):]))
            continue
        parts = _parts_of_block(block)
        kind: str | None = None
        if parts and all(isinstance(p, Banner) for p in parts):
            kind = parts[0].kind  # type: ignore[union-attr]
        cards.append(MentorCard(parts=parts, kind=kind))
    return cards
