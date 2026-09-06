"""Shared render conventions for v0.9 output commands (issue #32 decision).

stdlib-pure: no `rich`, no hand-rolled ANSI. The `[warning]`/`[error]`/
`[advisory]` line prefixes and the closing verdict line, used by `health`
(its first consumer) and the `today`/`node` detail/report commands after it.
Existing commands migrate to this module only when touched for other
reasons — it is not a retrofit.
"""

from __future__ import annotations

from .mentor.cards import (
    Banner,
    Kicker,
    Label,
    Lead,
    MentorCard,
    Para,
    Pill,
    Sub,
    Title,
)


def warning(message: str) -> str:
    return f"[warning] {message}"


def error(message: str) -> str:
    return f"[error] {message}"


def advisory(message: str) -> str:
    return f"[advisory] {message}"


def verdict_line(name: str, *, error_count: int, warning_count: int) -> str:
    """The single closing line: `name: OK` / `OK (N warnings)` / `FAILED — N error(s)`."""
    if error_count:
        return f"{name}: FAILED — {error_count} error(s)."
    if warning_count:
        return f"{name}: OK ({warning_count} warning(s))."
    return f"{name}: OK."


# --- Mentor voice helpers (issue #30 / #41) ----------------------------------
# Shared shape for `node`, `today`, and enriched `next` as those build slices
# land. stdlib-pure per #32; each function returns a list of lines (caller
# joins and prints). The kicker + title + state + brief + Where to learn +
# How to proceed + Do this next + trailing context is the resolved shape from
# the #30 prototype.


def section_kicker(label: str) -> str:
    """The uppercase kicker line that opens a Mentor view (e.g. THIS SKILL)."""
    return label.upper()


def section_title_state(title: str, state: str) -> list[str]:
    """Title line followed by a state pill line."""
    return [title, f"  [{state}]"]


def section_brief(text: str) -> list[str]:
    """The conversational-brief paragraph."""
    return ["", text]


def section_where_to_learn(resource_lines: list[str], label: str = "Where to learn") -> list[str]:
    """The 'Where to learn' guided callout (label overridden by `today`)."""
    lines = ["", label]
    for line in resource_lines:
        lines.append(f"  {line}")
    return lines


def section_how_to_proceed(text: str) -> list[str]:
    """The 'How to proceed' guided callout."""
    return ["", "How to proceed", f"  {text}"]


def section_do_this_next(action: str) -> list[str]:
    """The single 'Do this next' action block."""
    return ["", "DO THIS NEXT", f"  {action}"]


def section_context(text: str) -> list[str]:
    """Trailing context line (what this unlocks, etc.)."""
    return ["", text]


# --- Structured cards -> legacy lines (issue #171) ---------------------------
# The sole owner of the legacy line shape. CLI handlers produce
# ``list[MentorCard]``; terminals print ``cards_to_lines(cards)`` verbatim,
# while the web layer consumes the same cards via ``views.render_cards``
# without serializing. Blank-line and ``---`` placement mirrors the retired
# per-handler line builders exactly so terminal output does not change.


def _part_to_line(part) -> str:
    """One typed part back to its legacy line (no blank separators)."""
    if isinstance(part, Banner):
        return f"[{part.kind}] {part.text}"
    if isinstance(part, Pill):
        return f"  [{part.label}]"
    if isinstance(part, Sub):
        return f"  {part.text}"
    if isinstance(part, (Kicker, Title, Lead, Label, Para)):
        return part.text
    raise TypeError(f"unknown card part: {part!r}")


def _needs_blank(previous, current) -> bool:
    """Whether legacy output puts a blank line between two adjacent parts."""
    if previous is None:
        return False
    if isinstance(previous, Kicker) and isinstance(current, Title):
        return False
    if isinstance(previous, Title) and isinstance(current, Pill):
        return False
    if isinstance(previous, Kicker) and isinstance(current, Sub):
        return False
    if isinstance(previous, Label) and isinstance(current, Sub):
        return False
    if isinstance(previous, Sub) and isinstance(current, Sub):
        return False
    return True


def cards_to_lines(cards: list[MentorCard]) -> list[str]:
    """Serialize structured cards back to the legacy terminal line format."""
    lines: list[str] = []
    seen_content = False
    for card in cards:
        if lines:
            if card.kind is None:
                if seen_content:
                    lines.extend(["", "---"])  # separator between content cards
                # else: first content card after leading banners stays attached
            elif seen_content:
                lines.append("")  # trailing banner/appendix card
            # else: consecutive leading banners stay back-to-back
        previous_part = None
        for part in card.parts:
            if _needs_blank(previous_part, part):
                lines.append("")
            lines.append(_part_to_line(part))
            previous_part = part
        if card.kind is None:
            seen_content = True
    return lines
