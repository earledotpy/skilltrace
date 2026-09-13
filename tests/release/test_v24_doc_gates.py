"""Release gates pinning v2.4's documentation obligations (spec §J).

The rewritten v2.4 slot row (G-Slot #226), the §C locked JavaScript-budget
sentence in spec-tier1-serve, the glossary terms the direction map locked,
and the release notes entry land in the same change as the sublayer build.
The safety gates in test_v24_safety_gates.py cover the engine rules; this
file proves the docs moved with them.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CONTEXT_MD = (REPO_ROOT / "CONTEXT.md").read_text(encoding="utf-8")
ROADMAP_MD = (REPO_ROOT / "docs" / "POST_V2_ROADMAP.md").read_text(encoding="utf-8")
TIER1_SPEC = (REPO_ROOT / "docs" / "spec-tier1-serve.md").read_text(encoding="utf-8")
SPEC_V24 = (REPO_ROOT / "docs" / "spec-v2.4-interface-sublayer.md").read_text(
    encoding="utf-8"
)
RELEASE_NOTES = (REPO_ROOT / "docs" / "RELEASE_NOTES.md").read_text(encoding="utf-8")


def test_v24_slot_row_is_the_locked_preference_driven_row():
    assert "Preference-driven, de-CLI-flavoured Tier 1 interface direction" in ROADMAP_MD
    assert "import-time + request-time validated" in ROADMAP_MD


def test_tier1_spec_carries_the_locked_javascript_budget_answer():
    # §C sentence fix: the budget is decided (0), not open.
    assert "sets the JavaScript \nbudget to 0" in TIER1_SPEC.replace(
        "\nbudget", "\nbudget"
    ) or "budget to 0" in TIER1_SPEC
    assert "0008 stays reserved-and-unused" in TIER1_SPEC
    assert "remains open and unclaimed" not in TIER1_SPEC


def test_context_md_defines_interface_sublayer_terms():
    assert "**Days practiced**" in CONTEXT_MD
    assert "**Next-action fact**" in CONTEXT_MD
    assert "Interface sublayer" in CONTEXT_MD


def test_context_md_days_practiced_is_a_mirror_not_a_metronome():
    start = CONTEXT_MD.index("**Days practiced**")
    end = CONTEXT_MD.find("\n**", start + 1)
    if end == -1:
        end = len(CONTEXT_MD)
    body = CONTEXT_MD[start:end]
    assert "mirror, not a metronome" in body
    # The streak mechanic is refused by name (the definition negates it).
    assert "no streak mechanic" in body


def test_v24_spec_exists_and_is_the_handoff_artifact():
    assert SPEC_V24.lstrip().startswith("# Spec — v2.4")
    assert "locked hand-off" in SPEC_V24


def test_release_notes_gain_the_v2_4_entry():
    assert "## v2.4.0" in RELEASE_NOTES
