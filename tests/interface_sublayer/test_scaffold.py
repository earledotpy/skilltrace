"""S2 sublayer scaffold + chrome tests (v2.4 spec §I).

Covers the S2 deliverables: the View / Card / Command / Active-view-state
objects over the live dispatcher registry (ADR 0007), import-time +
request-time validation (serve refuses to start on inconsistency), and the
grep-able no-``<script>`` gate over the served pages.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skilltrace.web import interface
from skilltrace.web.interface.cards import Card, View, view_by_name
from skilltrace.web.interface.validate import SublayerError


# --- frozen route table (G-RouteSurface) ------------------------------------------


def test_every_declared_view_has_route_title_and_group():
    for view in interface.VIEWS.values():
        assert view.route.startswith("/")
        assert view.title
        assert view.group in ("daily", "diagnostics", None)


def test_no_new_top_level_view_beyond_the_frozen_table():
    # G-RouteSurface: downward-only restructure. The declared top-level set
    # is the Tier-1 surface minus retired entries plus the finder re-place.
    assert set(interface.VIEWS) == {
        "today",
        "next",
        "node",
        "finder",
        "health",
        "analytics",
        "node pass",
        "node master",
    }


def test_view_by_name_raises_on_unknown_names():
    with pytest.raises(KeyError):
        view_by_name("no-such-view")


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
    )
    assert card.why  # one human sentence, first-class
    assert card.disclosure is None  # optional facts stay absent by default


def test_card_disclosure_is_opt_in_not_a_details_default():
    card = Card(
        state="active",
        title="Apply X",
        why="You're mid-way through.",
        disclosure="2 of 3 evidence pieces accepted.",
    )
    assert card.disclosure == "2 of 3 evidence pieces accepted."
    assert View(name="x", route="/x", title="X", group=None).affordances == ()


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


# --- the grep-able no-<script> gate (G-JS, D2) --------------------------------------


def test_served_pages_emit_no_script_tags():
    """The interaction posture is tier 0: no `<script>` in any served page."""
    import re

    from skilltrace.web import views

    repo = Path(__file__).resolve().parents[2]
    pages = [
        views.home_body(repo),
        views.next_body(repo, {}),
        views.health_body(repo),
        views.analytics_body(repo, {}),
    ]
    for title, body, _status in pages:
        assert not re.search(r"<script\b", body, re.IGNORECASE), title

