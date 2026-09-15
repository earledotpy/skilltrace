"""Spec-value gates for T1 — the locked §B design tokens, type scale and shell.

Asserts the literal values from docs/spec-v2.4-interface-sublayer.md §B against
the live stylesheet (_STYLE), so "pytest green" can never again stand in for the
design direction. See map #231, ticket T1.
"""

from __future__ import annotations

import re

from skilltrace.web import views

# The nine locked §B palette hexes (spec §B table, lines 53-61).
LOCKED_HEXES = {
    "--bg": "#fbf7f0",
    "--fg": "#2b2622",
    "--muted": "#7a6f63",
    "--border": "#ece2d3",
    "--accent": "#b0562c",
    "--warn": "#faf0d7",
    "--err": "#f6ded4",
    "--ok": "#e7f3ec",
    "--advisory": "#e7eef5",
}

# T9: the private supporting set the palette needs (P5.4, one accent).
SUPPORTING_TOKENS = {
    "--card",
    "--pill",
    "--accent-ink",
    "--accent-soft",
    "--muted-ink",
    "--warn-ink",
    "--err-ink",
    "--ok-ink",
    "--advisory-ink",
    "--locked-ink",
    "--available-ink",
    "--active-ink",
    "--passed-ink",
    "--mastered-ink",
    "--space-section",
    "--space-intra",
    "--card-pad",
    "--card-pad-dense",
    "--section-gap-dense",
    "--intra-gap-dense",
    "--bento-gutter-dense",
    "--shell-rich",
    "--radius",
    "--radius-sm",
    "--radius-pill",
    "--shell",
    "--loop",
}

_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _root_block() -> str:
    """Extract the :root { ... } block from _STYLE."""
    start = views._STYLE.index(":root {")
    return views._STYLE[start : views._STYLE.index("}", start) + 1]


def test_every_locked_hex_is_present_in_root():
    root = _root_block()
    for token, hex_value in LOCKED_HEXES.items():
        assert re.search(rf"{re.escape(token)}:\s*{re.escape(hex_value)}", root), (
            f"{token}:{hex_value} missing from :root"
        )


def test_no_hex_literal_outside_root():
    root_end = views._STYLE.index("}", views._STYLE.index(":root {")) + 1
    outside = views._STYLE[root_end:]
    assert _HEX.findall(outside) == [], f"hex literals outside :root: {_HEX.findall(outside)}"
    # No legacy density tokens survive.
    assert "--density" not in views._STYLE


def test_supporting_token_set_is_declared():
    for token in SUPPORTING_TOKENS:
        assert f"{token}:" in views._STYLE, f"missing supporting token {token}"


def test_dense_register_literals_are_locked():
    # Amended §B dense diagnostics band (G-Spec #250): the literal values
    # DD3 asserts at release level, pinned here at the surface seam too.
    assert "--card-pad-dense:20px" in views._STYLE
    assert "--section-gap-dense:28px" in views._STYLE
    assert "--intra-gap-dense:14px" in views._STYLE
    assert "--bento-gutter-dense:20px" in views._STYLE
    assert "--shell-rich:1120px" in views._STYLE


def test_type_scale_tokens():
    assert "--base:16px" in views._STYLE
    assert "--lh:1.55" in views._STYLE
    assert "--step-display:32px" in views._STYLE
    # Base body font resolves to the locked base and line-height.
    assert "font:var(--base)/var(--lh)" in views._STYLE


def test_card_padding_is_inside_the_locked_band():
    m = re.search(r"--card-pad:\s*([0-9.]+)px", views._STYLE)
    assert m, "--card-pad not declared"
    value = float(m.group(1))
    assert 24 <= value <= 32, f"card padding {value}px outside the 24-32px band"


def test_shell_and_daily_loop_column():
    assert "--shell:1040px" in views._STYLE
    assert "--loop:720px" in views._STYLE
    assert "max-width:var(--shell)" in views._STYLE


def test_single_locked_breakpoint_and_no_legacy_css():
    assert "@media(max-width:960px){.analytics-grid{grid-template-columns:1fr}}" in views._STYLE
    assert views._STYLE.count("@media(") == 1
    assert ".sub {" not in views._STYLE
    # The legacy --mut token is gone; only the locked --muted remains.
    assert not re.search(r"--mut(?!ed)\b", views._STYLE)
    assert "density-pad" not in views._STYLE
    assert "density-gap" not in views._STYLE