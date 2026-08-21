"""Shared render conventions for v0.9 output commands (issue #32 decision).

stdlib-pure: no `rich`, no hand-rolled ANSI. The `[warning]`/`[error]`/
`[advisory]` line prefixes and the closing verdict line, used by `health`
(its first consumer) and the `today`/`node` detail/report commands after it.
Existing commands migrate to this module only when touched for other
reasons — it is not a retrofit.
"""

from __future__ import annotations


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
