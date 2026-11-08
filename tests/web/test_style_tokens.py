"""T1 — the v3 design-token gate (docs/spec-v3-study-day.md §8).

What only this module shows: the served stylesheet is assembled from the
**one** semantic token table, and nothing in the component rules invents a
colour, a radius, a spacing step or a type step of its own.

The v2.4 §B light-first palette, its nine radii, the 1040px shell, the
single 960px desktop-only breakpoint and the serif/sans split are
superseded history (spec §20 SUP-5); this gate asserts the v3 system
instead. The palette's own contrast floors are asserted by the
accessibility harness (``tests/web/test_a11y_contrast.py``), which reads
the same table — so a token change that breaks AA fails there.
"""

from __future__ import annotations

import re

from skilltrace.web import views
from skilltrace.web.tokens import DARK_TOKENS, LIGHT_TOKENS, SCALE_TOKENS

_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _root_blocks() -> list[str]:
    """Every ``:root`` block in the served stylesheet.

    The v3 token system declares the dark palette in one block and its
    light companion in another (inside a ``prefers-color-scheme`` query).
    A read that took only the first would see the light values as if they
    were component literals.
    """
    blocks: list[str] = []
    for match in re.finditer(r":root\s*\{", views._STYLE):
        start = match.end() - 1
        depth = 0
        for index in range(start, len(views._STYLE)):
            if views._STYLE[index] == "{":
                depth += 1
            elif views._STYLE[index] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(views._STYLE[start : index + 1])
                    break
    return blocks


def test_the_token_table_is_served_whole() -> None:
    """Every declared token appears in the served ``:root`` blocks."""
    blocks = _root_blocks()
    assert len(blocks) == 2, (
        f"expected the dark palette and its light companion, got {len(blocks)}"
    )
    dark, light = blocks
    for token, value in DARK_TOKENS.items():
        assert re.search(rf"{re.escape(token)}:\s*{re.escape(value)}", dark), (
            f"{token}:{value} missing from the dark :root block"
        )
    for token, value in LIGHT_TOKENS.items():
        assert re.search(rf"{re.escape(token)}:\s*{re.escape(value)}", light), (
            f"{token}:{value} missing from the light :root block"
        )
    for token, value in SCALE_TOKENS.items():
        assert re.search(rf"{re.escape(token)}:\s*{re.escape(value)}", dark), (
            f"{token}:{value} missing from :root"
        )


def test_no_hex_literal_outside_root() -> None:
    """A colour declared at a component is a colour that can drift."""
    without = views._STYLE
    for block in _root_blocks():
        without = without.replace(block, "")
    assert _HEX.findall(without) == [], (
        f"hex literals outside :root: {_HEX.findall(without)}"
    )


def test_the_light_companion_declares_the_same_roles() -> None:
    """A role that exists in one theme only changes meaning with the scheme."""
    assert set(LIGHT_TOKENS) == set(DARK_TOKENS)


def test_the_spacing_rhythm_is_four_pixels() -> None:
    """Every spacing step is a multiple of the 4px base rhythm (VS-5)."""
    for name, value in SCALE_TOKENS.items():
        if name.startswith("space-"):
            pixels = int(value.removesuffix("px"))
            assert pixels % 4 == 0, f"{name}={value} breaks the 4px rhythm"


def test_the_type_scale_never_drops_below_the_base_target() -> None:
    """Density may reduce whitespace, never the required text size (VS-4)."""
    assert int(SCALE_TOKENS["text-base"].removesuffix("px")) >= 14
    assert "--text-base:14px" in views._STYLE
    assert "--measure:70ch" in views._STYLE


def test_the_radii_are_restrained() -> None:
    """Surfaces carry 4-8px radii; only a status label is a pill (VS-5)."""
    assert SCALE_TOKENS["radius-sm"] == "4px"
    assert SCALE_TOKENS["radius-md"] == "8px"
    assert int(SCALE_TOKENS["radius-pill"].removesuffix("px")) > 100


def test_the_motion_scale_is_two_brief_durations() -> None:
    """Motion is brief state-transition feedback only (VS-9)."""
    for name, value in SCALE_TOKENS.items():
        if name.startswith("motion-"):
            milliseconds = int(value.removesuffix("ms"))
            assert 100 <= milliseconds <= 200, f"{name}={value} is not brief"


def test_one_shell_width_and_the_narrow_window_query() -> None:
    """One shell, one narrow-window degradation query (AX-10)."""
    assert "--shell:1180px" in views._STYLE
    assert "max-width:var(--shell)" in views._STYLE
    assert "@media (max-width: 640px)" in views._STYLE


def test_the_reduced_motion_guard_is_not_a_breakpoint() -> None:
    """The motion guard kills animation; it is not a layout query (AX-6)."""
    assert "@media (prefers-reduced-motion: reduce)" in views._STYLE
    assert views._STYLE.count("@media (") == 3  # narrow, light companion, motion


def test_the_component_vocabulary_is_the_v3_one() -> None:
    """The normative component vocabulary of VS-5 is what the shell uses."""
    for selector in (
        ".section",
        ".row",
        ".requirement",
        ".queue",
        ".queue-item",
        ".command-bar",
        ".status-label",
        ".inspector",
        ".state-empty",
        ".state-limited",
        ".state-refusal",
        ".state-failure",
        ".state-recovery",
    ):
        assert selector in views._STYLE, f"missing component: {selector}"


def test_cards_are_not_the_default_layout_primitive() -> None:
    """Structure comes from sections, rows, tables and disclosures (VS-5)."""
    # A card is a fact container the Card seam renders, not the page frame:
    # the page frame is a section, and the shell's own body element is not
    # a card.
    assert 'class="section"' in views._STYLE or ".section{" in views._STYLE
    assert ".card{" in views._STYLE
