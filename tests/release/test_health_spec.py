"""Doc gates pinning the Health spec amendment (#305).

Handoff step 4 in G-DecisionHandoff #297: the Health hierarchy plus
empty/limited-data copy plus guardrails from G-LearnerHealth #294 land
in the Health/serve spec surface (`docs/spec-tier1-serve.md`).
Decision only made normative — no build, no new route, no
release-criterion change. The build follows in #311 against this
surface.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TIER1_SPEC = (REPO_ROOT / "docs" / "spec-tier1-serve.md").read_text(encoding="utf-8")


def test_health_amendment_names_its_sources():
    assert "G-LearnerHealth #294" in TIER1_SPEC
    assert "#297" in TIER1_SPEC
    assert "#305" in TIER1_SPEC


def test_health_hierarchy_order_is_locked():
    assert "Stuck right now" in TIER1_SPEC
    assert "Due for review" in TIER1_SPEC
    assert "Evidence gaps" in TIER1_SPEC
    assert "Study rhythm" in TIER1_SPEC
    assert "Study resources" in TIER1_SPEC
    order = [
        TIER1_SPEC.index("Stuck right now"),
        TIER1_SPEC.index("Due for review"),
        TIER1_SPEC.index("Evidence gaps"),
        TIER1_SPEC.index("Study rhythm"),
        TIER1_SPEC.index("Study resources"),
    ]
    assert order == sorted(order)


def test_health_cards_carry_counts_why_and_link():
    assert "counts + one-line why + link" in TIER1_SPEC
    assert "never repeats their recommendations" in TIER1_SPEC or "never repeats" in TIER1_SPEC


def test_health_diagnostics_have_zero_web_ui_presence():
    assert "zero web-UI presence" in TIER1_SPEC
    assert "not even a collapsed line-link" in TIER1_SPEC


def test_health_no_zero_denominator_percents():
    assert "No completion-ratio percent when the denominator is zero" in TIER1_SPEC


def test_health_reviews_card_counts_and_suggestion_label():
    assert "due-now / overdue / next-scheduled" in TIER1_SPEC
    assert "labeled as suggestions" in TIER1_SPEC
    assert "recomputed date" in TIER1_SPEC


def test_health_stuck_and_evidence_pointers_are_locked():
    assert "Blocked work never counts" in TIER1_SPEC
    assert "attempt counts never read as eligibility" in TIER1_SPEC


def test_health_resources_and_rhythm_rules_are_locked():
    assert "only resources supporting active/available nodes" in TIER1_SPEC
    assert "min_sessions_for_full_data" in TIER1_SPEC
    assert "mirror, never a metronome" in TIER1_SPEC


def test_health_empty_copy_is_locked():
    assert "No open blockers" in TIER1_SPEC
    assert "No reviews scheduled" in TIER1_SPEC
    assert "No gaps on active nodes" in TIER1_SPEC
    assert "one quiet line" in TIER1_SPEC


def test_health_limited_data_copy_suppresses_penalty():
    assert "Limited data (N sessions)" in TIER1_SPEC
    assert "suppresses the below-target advisory" in TIER1_SPEC


def test_health_guardrails_forbid_score_streak_blocking():
    assert "No composite health score" in TIER1_SPEC
    assert "no streak" in TIER1_SPEC
    assert "nothing in Health blocks or implies blocking" in TIER1_SPEC


def test_health_full_name_is_dropped():
    assert '"Full" name is dropped' in TIER1_SPEC
    assert "Full roll-up" in TIER1_SPEC


def test_health_amendment_changes_no_release_criterion_or_route():
    assert "No release-criterion change" in TIER1_SPEC
    assert "no new top-level view" in TIER1_SPEC
    assert "no new route" in TIER1_SPEC
    assert "#311" in TIER1_SPEC
