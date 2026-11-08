"""The v3 dark-first token system (spec-v3-study-day §8 VS-2..VS-4).

One table, one stylesheet. Every colour, spacing step, type step, radius,
motion duration and elevation the shell uses is declared here by **semantic
role** — never by component — and the served stylesheet is assembled from
this table. The dark palette is the default; the light companion declares
the *same* semantic roles with different values, so a role never changes
meaning when the colour scheme does.

The nine light-first hexes of the v2.4 §B palette and its radius/spacing
token set are **replaced wholesale** by this table (the v2.4 token table is
superseded history — ``docs/spec-v3-study-day.md`` §20 SUP-5). Nothing is
extended: this is the whole palette.

Three rules the table itself encodes (VS-3):

* One accent (``--accent``) shared by both modes. It encodes an *action* or
  the focus ring — never rank, eligibility, mastery, health or severity.
* Five semantic status tokens (``--status-info``/``-success``/``-warning``/
  ``-failure``/``-focus``), each paired with a soft surface for fills and an
  ink for text on that fill. A status colour is never the only carrier of a
  meaning: every status renders with its text label.
* Purple (``--mastery-ink``) is reserved for mastery and retention context.
  It never celebrates.

Colour-contrast floors (AX-1) are not asserted here — they are asserted by
the accessibility harness in ``tests/web/test_a11y_contrast.py``, which
reads this same table, so a token change that breaks AA fails the build.
"""

from __future__ import annotations

__all__ = [
    "DARK_TOKENS",
    "LIGHT_TOKENS",
    "SCALE_TOKENS",
    "root_blocks",
    "token_table",
]


# --- the dark palette (the default) --------------------------------------------
#
# Canvas surfaces are the four elevation-free steps of the dark system; text
# is three steps (primary / secondary / muted, muted never below the AA
# floor on any canvas step); borders are three steps (subtle / default /
# strong). Each status carries a colour, a soft fill and an ink.
DARK_TOKENS: dict[str, str] = {
    # canvas
    "canvas-base": "#0d1117",
    "canvas-raised": "#161b22",
    "canvas-subtle": "#1c2129",
    "canvas-selected": "#26313d",
    # text
    "text-primary": "#e6edf3",
    "text-secondary": "#b7c0cb",
    "text-muted": "#9aa4b2",
    # borders — three steps of emphasis. ``border-subtle`` is a
    # decorative hairline (a table's row rules, a section divider): the
    # structure it decorates is carried by the table's own headers, so it
    # is not a "meaningful UI boundary" under WCAG 1.4.11 and stays
    # quiet. ``border-default`` and ``border-strong`` DO bound controls
    # and interactive regions, so they clear 3:1 against every canvas
    # step — the accessibility harness asserts that.
    "border-subtle": "#434c58",
    "border-default": "#7d8794",
    "border-strong": "#9aa4b2",
    # the one accent — actions and focus only
    "accent": "#4493f8",
    "accent-ink": "#06121f",
    "accent-soft": "#14243b",
    # semantic status
    "status-info": "#58a6ff",
    "status-info-soft": "#0d2338",
    "status-info-ink": "#9ecbff",
    "status-success": "#3fb950",
    "status-success-soft": "#0d2a18",
    "status-success-ink": "#8ee6a3",
    "status-warning": "#d29922",
    "status-warning-soft": "#33280d",
    "status-warning-ink": "#f0c674",
    "status-failure": "#f85149",
    "status-failure-soft": "#3a1512",
    "status-failure-ink": "#ffb3ad",
    "status-focus": "#4493f8",
    # mastery / retention context (purple, reserved)
    "mastery-ink": "#bc8cff",
    "mastery-soft": "#241b3a",
}

# --- the light companion -------------------------------------------------------
#
# Same semantic roles, different values. A role never changes meaning with
# the colour scheme: "warning" is an advisory attention amber in both.
LIGHT_TOKENS: dict[str, str] = {
    # canvas
    "canvas-base": "#f6f8fa",
    "canvas-raised": "#ffffff",
    "canvas-subtle": "#eef1f4",
    "canvas-selected": "#dbe4ee",
    # text
    "text-primary": "#111820",
    "text-secondary": "#3d4753",
    "text-muted": "#5a6472",
    # borders — the same three steps of emphasis as the dark theme, with
    # the same meaning: ``border-subtle`` decorates, ``border-default``
    # and ``border-strong`` bound controls and clear 3:1.
    "border-subtle": "#b6bfcb",
    "border-default": "#6f7683",
    "border-strong": "#464e5b",
    # the one accent
    "accent": "#0b62d6",
    "accent-ink": "#ffffff",
    "accent-soft": "#e3edfc",
    # semantic status
    "status-info": "#0b62d6",
    "status-info-soft": "#e3edfc",
    "status-info-ink": "#0b4fb8",
    "status-success": "#0f5c28",
    "status-success-soft": "#e2f5e8",
    "status-success-ink": "#0f5c28",
    "status-warning": "#7a5200",
    "status-warning-soft": "#fdf3d8",
    "status-warning-ink": "#7a5200",
    "status-failure": "#a3241f",
    "status-failure-soft": "#fbe9e9",
    "status-failure-ink": "#a3241f",
    "status-focus": "#0b62d6",
    # mastery / retention context
    "mastery-ink": "#6b3fa0",
    "mastery-soft": "#efe7f8",
}

# --- the non-colour scales -----------------------------------------------------
#
# A 4px base rhythm (VS-5), a type scale that never shrinks below the
# 14px desktop base target (VS-4), restrained 4–8px radii, the two motion
# durations VS-9 allows, and one elevation value for transient overlays.
SCALE_TOKENS: dict[str, str] = {
    # spacing — 4px rhythm
    "space-1": "4px",
    "space-2": "8px",
    "space-3": "12px",
    "space-4": "16px",
    "space-5": "24px",
    "space-6": "32px",
    "space-7": "40px",
    # type
    "text-xs": "12px",
    "text-sm": "13px",
    "text-base": "14px",
    "text-md": "16px",
    "text-lg": "20px",
    "text-xl": "24px",
    "text-display": "30px",
    "line-height": "1.55",
    "measure": "70ch",
    # radius
    "radius-sm": "4px",
    "radius-md": "8px",
    "radius-pill": "999px",
    # motion (brief state-transition feedback only)
    "motion-fast": "120ms",
    "motion-base": "180ms",
    # elevation — transient overlays only
    "elevation-overlay": "0 8px 24px rgba(1, 4, 9, 0.45)",
    # layout
    "shell": "1180px",
    "shell-narrow": "760px",
    # type roles — sans for titles, instructions, statuses and reading
    # content; mono for ids, paths, commands and timestamps (VS-4)
    "font-sans": "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    "font-mono": "ui-monospace, 'Cascadia Mono', 'SFMono-Regular', Menlo, Consolas, monospace",
}


def token_table() -> dict[str, str]:
    """Every declared token, dark values, as one flat ``name -> value`` map."""
    return {**SCALE_TOKENS, **DARK_TOKENS}


def _root_block(tokens: dict[str, str], scale: dict[str, str]) -> str:
    lines = [f"  --{name}:{value};" for name, value in tokens.items()]
    lines = [f"  --{name}:{value};" for name, value in scale.items()] + lines
    return ":root {\n" + "\n".join(lines) + "\n}"


def root_blocks() -> str:
    """The served stylesheet's token blocks: dark first, light companion.

    The dark block is the default. The light companion is a
    ``prefers-color-scheme`` override that redeclares the *same* semantic
    role names, so nothing in the page layer changes meaning with the
    scheme. Both blocks live in ``:root`` — the one place a hex literal may
    appear (the "no hex outside :root" release gate).
    """
    dark = _root_block(DARK_TOKENS, SCALE_TOKENS)
    light = _root_block(LIGHT_TOKENS, SCALE_TOKENS)
    return (
        "  /* v3 dark-first tokens (docs/spec-v3-study-day.md §8). Semantic roles\n"
        "     only: every colour lives here, never at a component. */\n"
        f"{dark}\n"
        "  /* the accessible light companion — the same roles, different values. */\n"
        "  @media (prefers-color-scheme: light) {\n"
        f"{light}\n"
        "  }\n"
    )
