"""Structured Mentor cards — the deep seam between CLI derivations and surfaces.

Replaces the undocumented line-grammar contract (``[tag]`` prefixes, ``---``
separators, indentation, uppercase kickers) that coupled the CLI handlers to
the web layer through a flat ``list[str]``. Handlers in ``commands/`` now
produce ``list[MentorCard]`` — typed parts with explicit fields — and the two
surfaces consume the model directly:

- terminals via ``render.cards_to_lines`` (the sole owner of the legacy line
  shape; terminal output is byte-identical to before),
- browsers via the interface renderer (derived ``MentorCard`` lists cross
  into interface ``Card`` objects through ``interface.translate.rich_cards``;
  no regex, no line parsing).

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
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


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


# --- NextAction: the structured next-action fact (v2.4 spec §E) -----------------
#
# The Mentor seam emits this fact alongside its human copy. Each surface
# renders its own affordance from it — the CLI prints the command line (you
# type it), the web renders a button. The fact carries no prose: which action
# is possible is derived once; how it is presented is per-surface.
#
# ``command`` is the CLI-printed action line for this intent — the exact
# string ``cards_to_lines`` prints under the ``DO THIS NEXT`` kicker (so the
# terminal output stays byte-identical to the pre-fact Kicker+Sub pair). The
# web never renders this field: the intent's affordance label renders instead.

Intent = Literal[
    "start",
    "submit_evidence",
    "pass",
    "schedule_review",
    "explore",
]


@dataclass(frozen=True)
class NextAction:
    """The single next human action, as a structured fact (v2.4 spec §E).

    - ``intent`` — closed Literal set (``start | submit_evidence | pass |
      schedule_review | explore``); grows only by editing the contract,
      never by string-typing.
    - ``node_id`` — the node the action binds to (``None`` when the action
      has no node to bind).
    - ``command`` — the CLI command line; present only when the intent has
      one, **never rendered by the web**.
    - ``eligible`` — the pass-case eligibility judgment, the only
      affordance-selection input the renderer needs.
    """

    intent: Intent
    node_id: str | None = None
    command: str | None = None
    eligible: bool | None = None


CardPart = Banner | Pill | Kicker | Title | Lead | Label | Para | Sub | NextAction


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
