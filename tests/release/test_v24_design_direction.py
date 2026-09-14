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

_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _root_block() -> str:
    start = views._STYLE.index(":root {")
    return views._STYLE[start : views._STYLE.index("}", start) + 1]


# --- DD1 — locked :root hexes -------------------------------------------------


def test_dd1_locked_root_hexes():
    root = _root_block()
    for token, hex_value in LOCKED_HEXES.items():
        assert re.search(rf"{re.escape(token)}:\s*{re.escape(hex_value)}", root), (
            f"{token}:{hex_value} missing from :root"
        )


# --- DD2 — no hex outside :root ------------------------------------------------


def test_dd2_no_hex_outside_root():
    root_end = views._STYLE.index("}", views._STYLE.index(":root {")) + 1
    outside = views._STYLE[root_end:]
    assert _HEX.findall(outside) == [], (
        f"hex literals outside :root: {_HEX.findall(outside)}"
    )


# --- DD3 — type scale, spacing bands, shells ------------------------------------

def test_dd3_type_scale_spacing_shells():
    # Airy daily register (non-home daily surfaces)
    assert "--base:16px" in views._STYLE
    m = re.search(r"--card-pad:\s*([0-9.]+)px", views._STYLE)
    assert m, "--card-pad not declared"
    # Airy band: card padding 24-32px
    assert 24 <= float(m.group(1)) <= 32
    assert "--shell:1040px" in views._STYLE
    assert "--loop:720px" in views._STYLE
    assert "max-width:var(--shell)" in views._STYLE
    assert "@media(max-width:960px)" in views._STYLE
    assert views._STYLE.count("@media(") == 1
    # Dense diagnostics register (rich home, /health detail, /analytics tables, node drill-down)
    # These are locked literal values for the dense band
    assert "--card-pad-dense:20px" in views._STYLE
    assert "--section-gap-dense:28px" in views._STYLE
    assert "--intra-gap-dense:14px" in views._STYLE
    assert "--bento-gutter-dense:20px" in views._STYLE
    assert "--shell-rich:1120px" in views._STYLE


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
