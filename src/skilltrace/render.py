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
