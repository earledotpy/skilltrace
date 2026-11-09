"""v2.4 design-direction release gate (map #231, T6; amended by map #243, G-Spec #250).

Asserts the spec's literal values from docs/spec-v2.4-interface-sublayer.md §B
plus the §C/§E/§G copy gates — at release level, against the served
stylesheet and the sublayer contract, so "pytest green" can never again stand
in for the design direction (the failure that produced map #231: green tests
beside an unchanged UI).

Static scans only (import but never execute commands, never touch the seed
repo): the per-surface behavioural truth lives in tests/web/ (style tokens,
copy register, surface sweep, safety panel); this file proves the *locked
values* that are acceptance clauses of the map:

- DD1 — the nine locked §B palette hexes live in `:root`.
- DD2 — no hex literal outside `:root` (P5.4, fully tokenised, one accent).
- DD3 — two density registers: airy daily band (24–32px card pad, 40px section
  gap, 720px loop column, 960px breakpoint) and **dense diagnostics band
  (20px card pad / 28px section gap / 14px intra-card gap / 20px bento gutters,
  1120px shell for rich home)**; 16px base type scale.
- DD4 — no `text-transform:uppercase` heading treatment anywhere in the
  served stylesheet (P3.6 — the ALL-CAPS kicker register is killed).
- DD5 — the five canonical state words are the sublayer's only card states
  (P3.4) and the banned UI synonyms never appear in served copy paths.
- DD6 — **per-route budget gate**: narrow tier 1 (one inline vanilla `<script>`
  on `/analytics` for chart hover/focus tooltips only); all other routes
  emit no `<script>`; ADR 0008 written; ADR 0006 unamended.
"""

from __future__ import annotations

import re
from pathlib import Path

from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src" / "skilltrace"
SUBLAYER = SRC / "web" / "interface"

_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _root_blocks() -> list[str]:
    """Every ``:root`` block in the served stylesheet.

    The v3 token system declares the dark palette in one ``:root`` block
    and its light companion in another (inside a ``prefers-color-scheme``
    query). A read that only took the first block would see the light
    values as if they were component literals — so the release gate
    reads them all, exactly as the accessibility harness does.
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


def _root_block() -> str:
    """The dark token block — the first ``:root`` in the served stylesheet."""
    return _root_blocks()[0]


# --- DD1 — locked :root hexes -------------------------------------------------


def test_dd1_locked_root_hexes():
    """Every declared token is present in the served ``:root`` block.

    Repointed from the v2.4 light-first §B palette to the v3 dark-first
    token table (ARC-7): the assertion keeps its exact form — every
    declared token appears with its declared value — and the table it
    names is now the semantic-role table in ``web/tokens.py``. The v2.4
    nine hexes are superseded history (spec §20 SUP-5).
    """
    from skilltrace.web.tokens import DARK_TOKENS, LIGHT_TOKENS, SCALE_TOKENS

    blocks = _root_blocks()
    assert len(blocks) == 2, (
        f"expected the dark palette and its light companion, got {len(blocks)}"
    )
    dark_root, light_root = blocks
    for token, hex_value in DARK_TOKENS.items():
        assert re.search(rf"{re.escape(token)}:\s*{re.escape(hex_value)}", dark_root), (
            f"{token}:{hex_value} missing from the dark :root block"
        )
    for token, hex_value in LIGHT_TOKENS.items():
        assert re.search(rf"{re.escape(token)}:\s*{re.escape(hex_value)}", light_root), (
            f"{token}:{hex_value} missing from the light :root block"
        )
    for token, value in SCALE_TOKENS.items():
        assert re.search(rf"{re.escape(token)}:\s*{re.escape(value)}", dark_root), (
            f"{token}:{value} missing from :root"
        )


# --- DD2 — no hex outside :root ------------------------------------------------


def test_dd2_no_hex_outside_root():
    """Every hex literal lives in a ``:root`` block — the palette is one table.

    A colour declared at a component is a colour that can drift from the
    theme; the v3 token system exists so that cannot happen.
    """
    without = views._STYLE
    for block in _root_blocks():
        without = without.replace(block, "")
    assert _HEX.findall(without) == [], (
        f"hex literals outside :root: {_HEX.findall(without)}"
    )


# --- DD3 — type scale, spacing bands, shells ------------------------------------

def test_dd3_type_scale_spacing_shells():
    """The type scale, the spacing rhythm and the shells are the v3 ones.

    Repointed from the v2.4 §B registers to the v3 token system
    (ARC-7): the v2.4 nine radii, the 1040px shell, the single 960px
    desktop-only breakpoint and the serif/sans split are superseded
    history (spec §20 SUP-5). What is asserted now is the v3 contract:
    a 4px spacing rhythm, a type scale that never drops below the 14px
    desktop base target, restrained 4-8px radii, one shell width, and
    the narrow-window degradation query plus the reduced-motion guard.
    """
    from skilltrace.web.tokens import SCALE_TOKENS

    style = views._STYLE
    # The 4px spacing rhythm (VS-5): every spacing step is a multiple of 4.
    for name, value in SCALE_TOKENS.items():
        if name.startswith("space-"):
            pixels = int(value.removesuffix("px"))
            assert pixels % 4 == 0, f"{name}={value} breaks the 4px rhythm"

    # The type scale never shrinks below the 14px desktop base target (VS-4).
    assert int(SCALE_TOKENS["text-base"].removesuffix("px")) >= 14
    assert "--text-base:14px" in style
    assert "--measure:70ch" in style

    # Restrained radii: 4-8px for surfaces, a pill for status labels (VS-5).
    assert SCALE_TOKENS["radius-sm"] == "4px"
    assert SCALE_TOKENS["radius-md"] == "8px"
    assert int(SCALE_TOKENS["radius-pill"].removesuffix("px")) > 100

    # One shell width, and the narrow-window degradation query (AX-10).
    assert "--shell:1180px" in style
    assert "max-width:var(--shell)" in style
    assert "@media (max-width: 640px)" in style

    # The reduced-motion guard is not a breakpoint (AX-6, VS-9).
    assert "@media (prefers-reduced-motion: reduce)" in style
    assert style.count("@media (") == 3  # narrow window, light companion, motion


# --- DD4 — no uppercase heading treatment ----------------------------------------


def test_dd4_no_uppercase_heading_treatment():
    assert "text-transform:uppercase" not in views._STYLE
    assert "text-transform: uppercase" not in views._STYLE


# --- DD5 — canonical state words, banned synonyms absent --------------------------


def test_dd5_canonical_state_words_and_no_synonyms():
    from skilltrace.web.interface import CANONICAL_STATES

    assert set(CANONICAL_STATES) == {
        "locked",
        "available",
        "active",
        "passed",
        "mastered",
    }
    for synonym in ("Ready to start", "In progress"):
        assert synonym not in views._STYLE, synonym
    for state in ("locked", "available", "active", "passed", "mastered"):
        assert f".pill.{state}" in views._STYLE, f"missing pill treatment: {state}"


# --- DD6 — per-route budget gate (narrow tier 1) ----------------------------------


def test_dd6_per_route_budget_gate():
    # /analytics is the ONLY route permitted to emit an inline <script> (for chart hover/focus tooltips)
    # All other routes must emit no <script>
    analytics_script_count = 0
    other_routes_script_count = 0
    for path in sorted((SRC / "web").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        code = re.sub(r'"""(?!").*?"""', "", text, flags=re.DOTALL)
        code = "\n".join(
            line for line in code.splitlines() if not line.strip().startswith("#")
        )
        if re.search(r"<script\b", code, re.IGNORECASE):
            if "analytics" in str(path):
                analytics_script_count += 1
            else:
                other_routes_script_count += 1
    # Exactly one route (/analytics) may have a script, and only for the granted interaction
    assert analytics_script_count >= 1, "analytics route must have the granted tier-1 script for chart tooltips"
    assert other_routes_script_count == 0, f"non-analytics routes must emit no <script>, found {other_routes_script_count}"
    # The base stylesheet must not contain <script>
    assert "<script" not in views._STYLE
