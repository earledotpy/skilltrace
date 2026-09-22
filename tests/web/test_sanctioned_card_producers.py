"""#317 — the renderer module names every legitimate HTML producer.

The analytics page's per-theme cards ended in a middle state: hand-rolled
``<div class="card">`` markup nobody owned. This suite pins the written
verdict — **bless, don't migrate** — recorded where the Card-to-HTML map is
defined (``web/interface/render.py``): the theme card embeds raw chart SVG
(exploration result surface) and the controls card is page chrome, both
outside the Richer-Card anatomy, so they stay sanctioned non-Card producers
listed in ``render.SANCTIONED_CARD_PRODUCERS``. The middle state ends because
every ``card``-div-emitting function in the analytics view module must be
named by the registry — enforced by the AST sweep below, not by prose.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

from skilltrace.web.interface import render


def _synthetic(function_body: str) -> str:
    """One-module source with a single function of the given body."""
    return f"def probe():\n{function_body}\n"

REPO_ROOT = Path(__file__).resolve().parents[2]
RENDER = REPO_ROOT / "src" / "skilltrace" / "web" / "interface" / "render.py"
ANALYTICS = REPO_ROOT / "src" / "skilltrace" / "web" / "views" / "analytics.py"


def test_verdict_is_recorded_where_the_card_map_is_defined():
    """The written verdict lives in the renderer module, not an issue comment."""
    text = RENDER.read_text(encoding="utf-8")
    assert "SANCTIONED_CARD_PRODUCERS" in text
    assert "blessed" in text and "#317" in text


def test_registry_exists_and_names_every_producer():
    entries = render.SANCTIONED_CARD_PRODUCERS
    assert isinstance(entries, dict) and entries


def test_every_registered_producer_resolves():
    """A registry name that drifts from the code fails here, not silently."""
    for name, entry in render.SANCTIONED_CARD_PRODUCERS.items():
        module_name, _, attr = name.rpartition(".")
        assert module_name.startswith("views."), name
        module = importlib.import_module(f"skilltrace.web.{module_name}")
        assert callable(getattr(module, attr, None)), name
        assert entry.surface and entry.reason, name


def test_analytics_card_and_controls_are_the_blessed_producers():
    entries = render.SANCTIONED_CARD_PRODUCERS
    assert "views.analytics._analytics_card" in entries
    assert "views.analytics._analytics_controls" in entries
    theme = entries["views.analytics._analytics_card"]
    controls = entries["views.analytics._analytics_controls"]
    assert "chart SVG" in theme.reason
    assert "page chrome" in controls.reason


def test_analytics_module_defers_to_the_registry():
    """The analytics module points at the registry that owns its cardness."""
    text = ANALYTICS.read_text(encoding="utf-8")
    assert "SANCTIONED_CARD_PRODUCERS" in text


def _card_producing_functions(source: str) -> set[str]:
    """Functions in the analytics module whose body emits a card div."""
    tree = ast.parse(source)
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and '<div class="card' in ast.get_source_segment(source, node)
    }


def test_sweep_every_hand_rolled_card_producer_is_registered():
    """Closed world enforced, not asserted: the AST sweep over the analytics
    module finds every function whose body emits a hand-rolled card div, and
    that set must equal the registered analytics producers — a new hand-rolled
    producer fails here until it is blessed (or composes Card instead)."""
    produced = _card_producing_functions(ANALYTICS.read_text(encoding="utf-8"))
    registered = {
        name.removeprefix("views.analytics.")
        for name in render.SANCTIONED_CARD_PRODUCERS
        if name.startswith("views.analytics.")
    }
    assert produced == registered, produced - registered


def test_registered_producers_are_scoped_to_the_analytics_surface():
    for name, entry in render.SANCTIONED_CARD_PRODUCERS.items():
        assert entry.surface == "/analytics", name


def test_sweep_helper_is_not_vacuous():
    """The sweep sees a hand-rolled card div and skips non-card functions."""
    assert _card_producing_functions(
        _synthetic("    return '<div class=\"card\">x</div>'")
    ) == {"probe"}
    assert _card_producing_functions(_synthetic("    return '<p>plain</p>'")) == set()

