"""The colour-contrast half of the AX-11 gate (spec-v3-study-day §9 AX-1).

WCAG 2.2 AA is the normative baseline, and AX-1 spells out the two floors
this module enforces:

* **4.5:1** for text — every text step on every canvas step, every status
  ink on its own soft fill, the accent ink on the accent fill, the mastery
  ink on the mastery fill;
* **3:1** for meaningful boundaries — the focus ring, the status colours,
  the accent action boundary and the three border steps against the canvas
  they sit on.

Both themes are asserted. The dark palette is the default; the light
companion redeclares the *same* semantic roles, so a role must not change
meaning when the colour scheme does — which means the light values must
clear the same floors, not a softer set of their own.

The gate also enforces two structural rules the token system depends on:

* **Fully tokenised.** No hex literal may appear in the served stylesheet
  outside a ``:root`` block. A colour reached by any other route would
  drift from the table this module reads, and the table is what the floors
  are computed from.
* **One accent, five statuses.** The accent family encodes *action and
  focus only* — never rank, eligibility, mastery, health or severity — and
  the five semantic status roles are all declared.

Where the shipped palette does not yet clear a floor, the shortfall is
*named* in :data:`KNOWN_DEVIATIONS` and recorded in
``tests/web/A11Y_FINDINGS.md``: the gate then holds the measured value as
a ratchet (a palette change may not make it worse) instead of pretending
the floor is met. Nothing here weakens a floor silently.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from a11y_harness import (
    BOUNDARY_FLOOR,
    CANVAS_ROLES,
    DECORATIVE_FLOOR,
    TEXT_FLOOR,
    contrast_ratio,
    meaningful_pairs,
    relative_luminance,
)

from skilltrace.web import views
from skilltrace.web.tokens import DARK_TOKENS, LIGHT_TOKENS, SCALE_TOKENS

# The two themes, named as the palette names them.
THEMES = {"dark": DARK_TOKENS, "light": LIGHT_TOKENS}

# The five semantic status roles (VS-3): a status colour is never the only
# carrier of a meaning, so each one must exist and each carries a text ink.
STATUS_ROLES = (
    "status-info",
    "status-success",
    "status-warning",
    "status-failure",
    "status-focus",
)

# The accent family: exactly one action colour, with its ink and its soft
# fill. One accent, shared by both modes (VS-3).
ACCENT_FAMILY = frozenset({"accent", "accent-ink", "accent-soft"})

# The three severity families whose hue must stay distinguishable from the
# action hue (VS-3: the accent never encodes severity).
SEVERITY_ROLES = ("status-success", "status-warning", "status-failure")

# --- The named shortfalls ----------------------------------------------------
#
# There are none. Every meaningful pairing in both themes clears its floor:
# the text steps clear 4.5:1, the meaningful boundary steps (the borders
# that bound controls) clear 3:1 against every canvas they may sit on, and
# the decorative hairline clears the lower visibility floor that keeps it
# visible at all.
#
# The map stays because the gate that consumes it must fail loudly if a
# shortfall is ever introduced again — a deviation has to be *named* to
# exist, never merely tolerated.
KNOWN_DEVIATIONS: dict[tuple[str, str, str], float] = {}

# The findings file: the named debt this gate records rather than hides.
FINDINGS = Path(__file__).resolve().parent / "A11Y_FINDINGS.md"

_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _root_blocks(stylesheet: str) -> list[str]:
    """Every ``:root`` block in the stylesheet, including nested ones.

    The light companion lives inside ``@media (prefers-color-scheme: light)``
    but is still a ``:root`` block, so a naive "the first :root" read would
    miss it — and would then read the light hexes as if they were component
    literals.
    """
    blocks: list[str] = []
    for match in re.finditer(r":root\s*\{", stylesheet):
        start = match.end() - 1
        depth = 0
        for index in range(start, len(stylesheet)):
            if stylesheet[index] == "{":
                depth += 1
            elif stylesheet[index] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(stylesheet[start : index + 1])
                    break
    return blocks


def _stylesheet_without_roots(stylesheet: str) -> str:
    """The served stylesheet with every ``:root`` block removed."""
    without = stylesheet
    for block in _root_blocks(stylesheet):
        without = without.replace(block, "")
    return without


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize("pairing", meaningful_pairs(), ids=lambda p: p.label)
def test_meaningful_pairing_meets_its_floor(pairing, theme) -> None:
    """Every meaningful pairing clears the floor its kind demands.

    A pairing listed in :data:`KNOWN_DEVIATIONS` is a named shortfall: the
    test asserts the measured value has not regressed and points at the
    findings file, rather than silently accepting it.
    """
    tokens = THEMES[theme]
    foreground = tokens[pairing.foreground]
    background = tokens[pairing.background]
    ratio = contrast_ratio(foreground, background)
    key = (theme, pairing.foreground, pairing.background)
    deviation = KNOWN_DEVIATIONS.get(key)
    if deviation is None:
        assert ratio >= pairing.floor, (
            f"{theme}: {pairing.label} is {ratio:.2f}:1, below the "
            f"{pairing.floor}:1 floor ({pairing.note}) — "
            f"{pairing.foreground}={foreground}, {pairing.background}={background}"
        )
        return
    assert ratio >= deviation - 0.01, (
        f"{theme}: {pairing.label} regressed from {deviation}:1 to {ratio:.2f}:1 "
        f"— the recorded deviation in tests/web/A11Y_FINDINGS.md must be "
        f"updated, not the value lowered"
    )
    assert ratio < pairing.floor, (
        f"{theme}: {pairing.label} now clears {pairing.floor}:1 "
        f"({ratio:.2f}:1) — the recorded deviation is obsolete. Delete it from "
        f"KNOWN_DEVIATIONS and from tests/web/A11Y_FINDINGS.md so the ordinary "
        f"floor applies again."
    )


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_every_pairing_has_a_declared_role(theme) -> None:
    """The pairing list names roles the theme actually declares.

    A renamed or dropped token must fail loudly here rather than silently
    drop out of the contrast gate.
    """
    tokens = THEMES[theme]
    for pairing in meaningful_pairs():
        assert pairing.foreground in tokens, (
            f"{theme}: pairing names an undeclared role {pairing.foreground!r}"
        )
        assert pairing.background in tokens, (
            f"{theme}: pairing names an undeclared role {pairing.background!r}"
        )


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_the_decorative_hairline_stays_visible(theme) -> None:
    """``border-subtle`` is decoration, but decoration must be visible.

    It is a table's row rules and a section divider — not a boundary the
    learner needs to identify a control, so it is not held to the 3:1
    SC 1.4.11 floor. It must still be *distinguishable* from the canvas
    it sits on, or the structure it decorates disappears.
    """
    tokens = THEMES[theme]
    hairline = tokens["border-subtle"]
    for canvas in CANVAS_ROLES:
        ratio = contrast_ratio(hairline, tokens[canvas])
        assert ratio >= DECORATIVE_FLOOR, (
            f"{theme}: border-subtle on {canvas} is {ratio:.2f}:1, below the "
            f"{DECORATIVE_FLOOR}:1 visibility floor — the decorative hairline "
            f"has become invisible"
        )


def test_the_two_themes_declare_the_same_roles() -> None:
    """The light companion redeclares the dark table's roles, one for one.

    A role that exists in one theme only would change meaning when the
    colour scheme does — the failure VS-3 forbids.
    """
    assert set(LIGHT_TOKENS) == set(DARK_TOKENS)


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_the_five_semantic_status_roles_are_declared(theme) -> None:
    """All five status roles exist in the theme (VS-3)."""
    tokens = THEMES[theme]
    for role in STATUS_ROLES:
        assert role in tokens, f"{theme}: missing status role {role!r}"
    for family in ("info", "success", "warning", "failure"):
        assert f"status-{family}-soft" in tokens
        assert f"status-{family}-ink" in tokens


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_there_is_exactly_one_accent_colour(theme) -> None:
    """One accent, shared by both modes: action and focus, nothing else.

    The accent family is the action colour plus its ink and its soft fill.
    No second accent may appear, and the accent must not double as a
    *severity* colour (VS-3).
    """
    tokens = THEMES[theme]
    accent_family = {name for name in tokens if name.startswith("accent")}
    assert accent_family == set(ACCENT_FAMILY), (
        f"{theme}: the accent family is {sorted(accent_family)}, "
        f"expected {sorted(ACCENT_FAMILY)}"
    )
    for severity in SEVERITY_ROLES:
        assert tokens["accent"] != tokens[severity], (
            f"{theme}: the accent doubles as {severity}"
        )


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_the_severity_colours_stay_distinguishable(theme) -> None:
    """Success, warning and failure are three different hues (VS-3).

    If two severities shared a hue, the label would be the only thing
    telling them apart — and colour is exactly what VS-3 forbids relying
    on.
    """
    tokens = THEMES[theme]
    colours = {role: tokens[role] for role in SEVERITY_ROLES}
    assert len(set(colours.values())) == len(colours), (
        f"{theme}: two severities share a hue: {colours}"
    )


def test_no_hex_literal_outside_a_root_block() -> None:
    """The served stylesheet is fully tokenised.

    Every hex must live in a ``:root`` block — the dark table or its light
    companion. A hex at a component would drift from the table the
    contrast gate reads, which is exactly the drift this gate exists to
    stop.
    """
    outside = _stylesheet_without_roots(views._STYLE)
    literals = _HEX.findall(outside)
    assert literals == [], f"hex literals outside :root: {literals}"


def test_the_root_blocks_declare_the_token_tables() -> None:
    """The served :root blocks *are* the token tables.

    If the stylesheet's root drifts from ``DARK_TOKENS``/``LIGHT_TOKENS``,
    the contrast gate would be asserting on values the product does not
    serve.
    """
    blocks = _root_blocks(views._STYLE)
    assert len(blocks) == 2, (
        f"expected a dark and a light :root block, got {len(blocks)}"
    )
    dark_block, light_block = blocks
    for role, value in DARK_TOKENS.items():
        assert f"--{role}:{value};" in dark_block, f"--{role} missing from the dark :root"
    for role, value in LIGHT_TOKENS.items():
        assert f"--{role}:{value};" in light_block, (
            f"--{role} missing from the light :root"
        )


def test_the_accent_is_only_used_for_actions_and_focus() -> None:
    """``--accent`` appears only in action, focus and emphasis rules.

    The accent encodes an action or the focus ring — never rank,
    eligibility, mastery, health or severity (VS-3). A status, severity
    state or mastery rule that reached for the accent would break that, so
    the stylesheet is checked rule by rule.
    """
    stylesheet = views._STYLE
    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", stylesheet)
    forbidden = (
        ".status-label",
        ".pill",
        ".master",
        "mastery",
        ".state-limited",
        ".state-refusal",
        ".state-failure",
        ".banner",
        "status-",
    )
    offenders: list[str] = []
    for selector, body in rules:
        if "--accent)" not in body and "--accent;" not in body:
            continue
        lowered = selector.lower()
        if any(marker in lowered for marker in forbidden):
            offenders.append(f"{selector.strip()} {{ {body.strip()} }}")
    assert offenders == [], (
        "the accent reached a status, severity or mastery rule: "
        + " | ".join(offenders)
    )


def test_the_accent_is_never_text_on_the_selected_canvas() -> None:
    """No rule paints accent text on the selected canvas.

    ``canvas-selected`` is the hover fill of a button, whose text is
    text-primary. The accent on that step would be 4.26:1 (dark) and
    4.38:1 (light) — under the 4.5:1 text floor in both themes — so the
    design system keeps the accent away from it. This asserts that stays
    true, rather than leaving it to a pairing that never occurs.
    """
    stylesheet = views._STYLE
    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", stylesheet)
    offenders = [
        f"{selector.strip()} {{ {body.strip()} }}"
        for selector, body in rules
        if "canvas-selected" in body
        and ("color:var(--accent)" in body or "--accent)" in body)
    ]
    assert offenders == [], (
        "the accent is painted on the selected canvas, where it is under the "
        "4.5:1 text floor: " + " | ".join(offenders)
    )


def test_the_focus_ring_uses_the_focus_role() -> None:
    """The visible keyboard focus ring is the focus role (AX-1)."""
    assert ":focus-visible{outline:2px solid var(--status-focus)" in views._STYLE


def test_the_scale_tokens_are_shared_by_both_themes() -> None:
    """Only the colours change with the scheme; the scale does not.

    A role that changes meaning with the colour scheme is forbidden; so is
    a spacing or type step that changes with it.
    """
    dark_root, light_root = _root_blocks(views._STYLE)
    for name, value in SCALE_TOKENS.items():
        assert f"--{name}:{value};" in dark_root
        assert f"--{name}:{value};" in light_root


def test_the_colour_maths_matches_the_wcag_reference_values() -> None:
    """The harness computes WCAG's own numbers, not an approximation.

    The reference pairs are the ones the WCAG definition itself uses, so
    a wrong sRGB linearisation or a swapped ratio would be caught here
    rather than silently shifting every measurement in the gate.
    """
    assert relative_luminance("#ffffff") == pytest.approx(1.0, abs=1e-9)
    assert relative_luminance("#000000") == pytest.approx(0.0, abs=1e-9)
    # Black on white is the maximum ratio WCAG defines.
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0, abs=1e-9)
    # The ratio is symmetric.
    assert contrast_ratio("#4493f8", "#0d1117") == pytest.approx(
        contrast_ratio("#0d1117", "#4493f8")
    )


def test_the_floors_are_the_wcag_aa_ones() -> None:
    """The floors this module enforces are WCAG 2.2 AA's own numbers.

    SC 1.4.3 is 4.5:1 for normal text; SC 1.4.11 is 3:1 for the visual
    information required to identify components and states. A future edit
    that quietly lowered a floor would make the gate lie.
    """
    assert TEXT_FLOOR == 4.5
    assert BOUNDARY_FLOOR == 3.1


def test_every_deviation_is_recorded_in_the_findings_file() -> None:
    """Each named shortfall is written down, with its measured value.

    A deviation nobody can find is a hidden waiver.
    """
    assert FINDINGS.exists(), (
        "the contrast gate records named deviations, so the findings file "
        "must exist and name them"
    )
    text = FINDINGS.read_text(encoding="utf-8")
    for (theme, foreground, background), value in KNOWN_DEVIATIONS.items():
        assert foreground in text, f"{foreground} deviation is not recorded"
        assert background in text, f"{background} is not named in the record"
        assert f"{value}" in text, (
            f"the measured value {value} of {foreground} on {background} "
            f"({theme}) is not recorded"
        )
