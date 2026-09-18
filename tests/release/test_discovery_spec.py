"""Doc gates pinning the discovery spec amendment (#304).

Handoff step 4 in G-DecisionHandoff #297: the discovery Q7 examples and
card anatomy plus behavior contract from G-SubjectDiscovery #293 land in
the discovery/serve spec surface (`docs/spec-tier1-serve.md`). Decision
only made normative — no build, no new route, no release-criterion
change. The build follows in #310 against this surface.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TIER1_SPEC = (REPO_ROOT / "docs" / "spec-tier1-serve.md").read_text(encoding="utf-8")


def test_discovery_amendment_names_its_sources():
    assert "G-SubjectDiscovery #293" in TIER1_SPEC
    assert "#297" in TIER1_SPEC
    assert "#304" in TIER1_SPEC


def test_discovery_card_anatomy_is_locked():
    assert "140 chars max" in TIER1_SPEC
    assert "node-body first sentence" in TIER1_SPEC
    assert "description pending" in TIER1_SPEC
    assert "Ready to start" in TIER1_SPEC
    assert "In progress" in TIER1_SPEC
    assert "small" in TIER1_SPEC and "secondary" in TIER1_SPEC


def test_discovery_matching_is_subject_title_synonym_with_id_fallback():
    assert "synonym" in TIER1_SPEC
    assert "programming.python.*" in TIER1_SPEC
    assert "seed data" in TIER1_SPEC
    assert "is secondary only, never the primary" in TIER1_SPEC


def test_discovery_q7_acceptance_examples_are_recorded():
    assert "order of operations" in TIER1_SPEC
    assert "math.arithmetic.order_operations_01" in TIER1_SPEC
    assert "sql select" in TIER1_SPEC
    assert "data.sql.select_basics_01" in TIER1_SPEC
    assert "python variables" in TIER1_SPEC
    assert "programming.python.variables_01" in TIER1_SPEC
    assert "variables_01" in TIER1_SPEC


def test_discovery_no_results_pattern_is_locked():
    assert "3 entry-node links" in TIER1_SPEC or "3 entry links" in TIER1_SPEC
    assert "browse" in TIER1_SPEC


def test_discovery_locked_cards_name_and_link_the_prerequisite():
    assert "greyed" in TIER1_SPEC
    assert "blocking prerequisite" in TIER1_SPEC


def test_discovery_selection_navigates_without_starting():
    assert "navigates" in TIER1_SPEC
    assert "never implicitly starts" in TIER1_SPEC


def test_discovery_ranking_and_ambiguity_rules_are_locked():
    assert "available first" in TIER1_SPEC
    assert "locked last" in TIER1_SPEC
    assert "no silent top-1" in TIER1_SPEC


def test_discovery_behavior_contract_is_tier0_server_rendered():
    assert "Server-rendered result page on submit" in TIER1_SPEC
    assert "full function with script absent" in TIER1_SPEC
    assert "result-count heading" in TIER1_SPEC
    assert "stacked cards" in TIER1_SPEC


def test_discovery_browse_contract_shares_card_anatomy():
    assert "anchor links per subject" in TIER1_SPEC
    assert "grouped-count table" in TIER1_SPEC


def test_discovery_adr0008_refusal_is_recorded():
    assert "ADR 0008" in TIER1_SPEC
    assert "No live-filter" in TIER1_SPEC
    assert "evidence packet" in TIER1_SPEC


def test_discovery_amendment_changes_no_release_criterion_or_route():
    assert "No release-criterion change" in TIER1_SPEC
    assert "no new top-level view" in TIER1_SPEC or "no new route" in TIER1_SPEC
