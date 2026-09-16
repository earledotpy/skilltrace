"""S2 sublayer scaffold + chrome tests (amended spec §I, map #252).

Covers the S2 deliverables: the View / Card / Command / Active-view-state
objects over the live dispatcher registry (ADR 0007), import-time +
request-time validation (serve refuses to start on inconsistency), the §B
dense diagnostics register, and the per-route budget held so far (no
`<script>` on any served page until S5 grants the /analytics one, ADR 0008).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skilltrace.web import interface
from skilltrace.web.interface.cards import Affordance, Card, View, view_by_name
from skilltrace.web.interface.validate import SublayerError


# --- frozen route table (G-RouteSurface) ------------------------------------------


def test_every_declared_view_has_route_title_and_group():
    for view in interface.VIEWS.values():
        assert view.route.startswith("/")
        assert view.title
        assert view.group in ("daily", "periodic", None)


def test_no_new_top_level_view_beyond_the_frozen_table():
    # G-RouteSurface: downward-only restructure. The declared top-level set
    # is the Tier-1 surface minus retired entries plus the finder re-place
    # plus the master-confirm acceptance step (T4 §H).
    assert set(interface.VIEWS) == {
        "today",
        "next",
        "node",
        "finder",
        "health",
        "analytics",
        "node pass",
        "node master",
        "master-confirm",
    }


def test_view_by_name_raises_on_unknown_names():
    with pytest.raises(KeyError):
        view_by_name("no-such-view")


def test_frozen_routes_match_the_normative_table():
    from skilltrace.web.interface.validate import FROZEN_ROUTES

    assert FROZEN_ROUTES == {
        "today": "/",
        "next": "/next",
        "finder": "/nodes/jump",
        "node": "/nodes/{id}",
        "node pass": "/nodes/{id}/pass",
        "node master": "/nodes/{id}/master",
        "master-confirm": "/nodes/{id}/master/confirm",
        "health": "/health",
        "analytics": "/analytics",
    }
    for name, route in FROZEN_ROUTES.items():
        assert interface.VIEWS[name].route == route


def test_validate_interface_reports_route_drift(monkeypatch):
    from dataclasses import replace

    from skilltrace.cli import REGISTRY
    from skilltrace.web.interface import cards as cards_mod

    drifted = replace(cards_mod.VIEWS["today"], route="/today")
    monkeypatch.setitem(cards_mod.VIEWS, "today", drifted)
    problems = interface.validate_interface(REGISTRY)
    assert any("frozen" in problem for problem in problems)


def test_validate_interface_reports_a_missing_frozen_view(monkeypatch):
    from skilltrace.cli import REGISTRY
    from skilltrace.web.interface import cards as cards_mod

    monkeypatch.delitem(cards_mod.VIEWS, "master-confirm")
    problems = interface.validate_interface(REGISTRY)
    assert any("master-confirm" in problem for problem in problems)


# --- validation: import time + serve boot ----------------------------------------


def test_structure_validates_at_import():
    # Importing the package ran validate_structure; the objects are usable.
    assert interface.VIEWS["today"].route == "/"


def test_validate_interface_against_the_live_registry_is_clean():
    from skilltrace.cli import REGISTRY

    assert interface.validate_interface(REGISTRY) == []


def test_validate_interface_reports_dead_write_paths():
    class _EmptyRegistry:
        def names(self):
            return []

    problems = interface.validate_interface(_EmptyRegistry())
    assert problems
    assert any("pass" in problem for problem in problems)


def test_structure_rejects_an_unlabeled_affordance(monkeypatch):
    from skilltrace.web.interface import validate as validate_mod
    from skilltrace.web.interface.affordances import COMMAND_AFFORDANCE_LABELS

    monkeypatch.delitem(COMMAND_AFFORDANCE_LABELS, "start")
    with pytest.raises(SublayerError, match="no human label"):
        validate_mod.validate_structure()


def test_structure_rejects_an_unknown_nav_group(monkeypatch):
    from dataclasses import replace

    from skilltrace.web.interface import cards as cards_mod
    from skilltrace.web.interface.validate import validate_structure

    bogus = replace(cards_mod.VIEWS["today"], group="somewhere")
    monkeypatch.setitem(cards_mod.VIEWS, "today", bogus)
    with pytest.raises(SublayerError, match="unknown nav group"):
        validate_structure()


# --- the Richer Card (§E) ---------------------------------------------------------


def test_card_carries_the_richer_shape():
    card = Card(
        state="available",
        title="Apply X",
        why="It unlocks two skills and fits your morning.",
        resources=["Hf Course — https://example.test/"],
        affordances=(
            Affordance.from_intent("start", title="Apply X"),
        ),
    )
    assert card.why  # one human sentence, first-class
    assert card.disclosure is None  # optional facts stay absent by default


def test_card_disclosure_is_opt_in_not_a_details_default():
    card = Card(
        state="active",
        title="Apply X",
        why="You're mid-way through.",
        resources=["Hf Course — https://example.test/"],
        affordances=(Affordance.from_intent("submit_evidence", title="Apply X"),),
        disclosure="2 of 3 evidence pieces accepted.",
    )
    assert card.disclosure == "2 of 3 evidence pieces accepted."
    assert View(name="x", route="/x", title="X", group=None).affordances == ()


def test_card_refuses_a_non_canonical_state_synonym():
    # P3.4 at construction: a UI synonym is a refusal, not a normalization.
    with pytest.raises(SublayerError, match="canonical"):
        Card(
            state="Ready to start",
            title="Apply X",
            why="It fits.",
            resources=["Docs — https://example.test/"],
            affordances=(Affordance.from_intent("start", title="Apply X"),),
        )


# --- serve boot gate (S2) ----------------------------------------------------------


def test_cli_and_serve_boot_clean_against_the_wired_sublayer():
    """The whole surface builds and the sublayer check passes at boot."""
    from skilltrace.cli import REGISTRY, build_parser
    from skilltrace.web.server import serve as _serve_marker  # noqa: F401

    build_parser()  # every command's co-located builder still attaches
    assert interface.validate_interface(REGISTRY) == []


def test_serve_refuses_to_start_on_an_inconsistent_sublayer(monkeypatch, tmp_path):
    """A dead write path is a boot failure with named problems, exit 1."""
    from argparse import Namespace
    from pathlib import Path

    from skilltrace.dispatch import Context
    from skilltrace.web import server as server_mod
    from skilltrace.web.interface import cards as cards_mod

    broken = View(
        name="today",
        route="/",
        title="Today",
        group="daily",
        affordances=("no-such-command",),
    )
    monkeypatch.setitem(cards_mod.VIEWS, "today", broken)

    ctx = Context(root=Path(tmp_path), args=Namespace(port=8341, no_browser=True))
    result = server_mod.serve(ctx)
    assert result.exit_code == 1


# --- the per-route budget gate (amended G-JS, ADR 0008) --------------------------


def test_per_route_script_budget_analytics_velocity_only():
    """The per-route budget (ADR 0008, narrow tier 1): exactly one inline
    vanilla script, on the /analytics velocity chart only.

    S5 landed the granted chart hover/focus tooltip script, so the interim
    "no script anywhere" assertion graduates: home/next/health carry none,
    non-velocity themes carry none, and the velocity theme carries exactly
    one. Tier-0 degradation (static SVG with native titles) is asserted in
    tests/web/test_analytics_tooltip.py.
    """
    import re

    from skilltrace.web import views

    repo = Path(__file__).resolve().parents[2]
    plain_pages = [
        views.home_body(repo),
        views.next_body(repo, {}),
        views.health_body(repo),
    ]
    for title, body, _status in plain_pages:
        assert not re.search(r"<script\b", body, re.IGNORECASE), title
    _, velocity, _ = views.analytics_body(repo, {"theme": ["velocity"]})
    assert len(re.findall(r"<script\b", velocity, re.IGNORECASE)) == 1, (
        "velocity theme must carry exactly the granted tooltip script"
    )
    for theme in ("blockers", "reviews", "evidence"):
        _, body, _ = views.analytics_body(repo, {"theme": [theme]})
        assert not re.search(r"<script\b", body, re.IGNORECASE), theme

