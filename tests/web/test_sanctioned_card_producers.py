"""#317 — the renderer module names every legitimate HTML producer.

The analytics page's per-theme cards ended in a middle state: hand-rolled
``<div class="card">`` markup nobody owned. This suite pins the written
verdict — **blessed, not migrated** — recorded where the Card-to-HTML map is
defined (``web/interface/render.py``): the theme card is a chart panel over
derived numbers with no node behind it, so a Card composition would have to
assert a node state and a next action that do not exist, and the controls card
is page chrome (a GET form plus plain theme-toggle links) whose affordance
would be a write path it does not have. Both stay sanctioned non-Card
producers listed in ``render.SANCTIONED_CARD_PRODUCERS``.

What the middle state's end means, mechanically:

* the AST sweep below is the closed world — every function in the analytics
  view module whose body emits card-class markup must be named by the
  registry, and every registry entry must still produce its markup (a new
  hand-rolled producer fails here until it is blessed or composed as a Card);
* every entry resolves to a live ``views.*`` producer on the analytics
  surface and carries the reason it cannot be a Card, so a registry name that
  drifts from the code fails here rather than rotting;
* the blessed producers still owe the page's discipline — total escaping, no
  intent vocabulary, no command string, no script (the velocity tooltip stays
  the route's one granted script, ADR 0008) — and the anatomy bytes the golden
  route-body snapshots (#312) hold are pinned here directly.
"""

from __future__ import annotations

import ast
import importlib
from dataclasses import dataclass
from pathlib import Path

from skilltrace.web.interface import forbidden_matches
from skilltrace.web.interface import render
from skilltrace.web.views import analytics as analytics_view

REPO_ROOT = Path(__file__).resolve().parents[2]
RENDER = REPO_ROOT / "src" / "skilltrace" / "web" / "interface" / "render.py"
ANALYTICS = REPO_ROOT / "src" / "skilltrace" / "web" / "views" / "analytics.py"

# The markup marker every producer of a card-class div emits.
CARD_FRAME = 'class="card'
SURFACE = "/analytics"
THEME_CARD = "views.analytics._analytics_card"
CONTROLS = "views.analytics._analytics_controls"


# --- the written verdict, where the Card-to-HTML map is defined --------------------


def test_verdict_is_recorded_where_the_card_map_is_defined():
    """The verdict lives in the renderer module, not an issue comment."""
    text = RENDER.read_text(encoding="utf-8")
    assert "SANCTIONED_CARD_PRODUCERS" in text
    assert "blessed, not migrated" in text and "#317" in text


def test_registry_names_every_producer_and_keeps_its_key():
    entries = render.SANCTIONED_CARD_PRODUCERS
    assert isinstance(entries, dict) and entries
    for key, entry in entries.items():
        assert entry.name == key, key


def test_the_analytics_card_and_controls_are_the_blessed_producers():
    """Both analytics producers are blessed, each with its own reason."""
    entries = render.SANCTIONED_CARD_PRODUCERS
    assert THEME_CARD in entries, entries
    assert CONTROLS in entries, entries
    assert entries[THEME_CARD].surface == SURFACE
    assert entries[CONTROLS].surface == SURFACE
    assert "chart panel" in entries[THEME_CARD].reason
    assert "node-state" in entries[THEME_CARD].reason
    assert "page chrome" in entries[CONTROLS].reason


def test_every_registered_producer_resolves_to_a_live_views_producer():
    """A registry name that drifts from the code fails here, not silently."""
    for key, entry in render.SANCTIONED_CARD_PRODUCERS.items():
        module_name, _, attr = key.rpartition(".")
        assert module_name.startswith("views."), key
        module = importlib.import_module(f"skilltrace.web.{module_name}")
        assert callable(getattr(module, attr, None)), key
        assert entry.surface and entry.reason, key


def test_registered_producers_are_scoped_to_the_analytics_surface():
    for key, entry in render.SANCTIONED_CARD_PRODUCERS.items():
        assert entry.surface == SURFACE, key


def test_analytics_module_defers_to_the_registry():
    """The analytics module points at the registry that owns its cardness."""
    text = ANALYTICS.read_text(encoding="utf-8")
    assert "SANCTIONED_CARD_PRODUCERS" in text
    assert "_analytics_controls" in text


# --- the closed world: the AST sweep -------------------------------------------------


def _synthetic(function_body: str) -> str:
    """One-module source with a single function of the given body."""
    return f"def probe():\n{function_body}\n"


def _docstring_constants(tree: ast.AST) -> set[int]:
    """Identity of the ``Constant`` nodes that are docstrings (prose, not markup)."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
            ):
                ids.add(id(body[0].value))
    return ids


def _card_producing_functions(source: str) -> set[str]:
    """Functions in ``source`` whose body emits card-class markup.

    Literal-based, so a function that only *mentions* ``<div class="card`` in
    prose (its own docstring) is not a producer.
    """
    tree = ast.parse(source)
    prose = _docstring_constants(tree)
    produced: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and id(child) not in prose:
                if isinstance(child.value, str) and CARD_FRAME in child.value:
                    produced.add(node.name)
                    break
    return produced


def test_sweep_helper_is_not_vacuous():
    """The sweep sees a hand-rolled card div and skips everything else."""
    assert _card_producing_functions(
        _synthetic("    return '<div class=\"card\">x</div>'")
    ) == {"probe"}
    assert _card_producing_functions(_synthetic("    return '<p>plain</p>'")) == set()
    # Prose is not production: a docstring naming the markup is not a producer.
    assert _card_producing_functions(
        'def probe():\n    """<div class="card">x</div>"""\n    return "<p>x</p>"\n'
    ) == set()


def test_sweep_every_hand_rolled_card_producer_is_registered():
    """Closed world, both directions: the analytics module's card-class
    producers and the registered analytics producers are the same set.

    A new hand-rolled producer fails here until it is blessed (or composes a
    Card instead); a blessed producer that stops producing its markup fails
    too, rather than lingering as a licence nobody needs."""
    produced = _card_producing_functions(ANALYTICS.read_text(encoding="utf-8"))
    registered = {
        key.rpartition(".")[2]
        for key in render.SANCTIONED_CARD_PRODUCERS
        if key.startswith("views.analytics.")
    }
    assert produced == registered, (
        f"unowned card producers: {sorted(produced - registered)}; "
        f"stale registry entries: {sorted(registered - produced)}"
    )


# --- the blessed producers still owe the page's discipline --------------------------


@dataclass(frozen=True)
class _Model:
    """The analytics model fields the theme card's export form reads."""

    window_days: int
    group_by: str


def test_the_blessed_producers_lock_the_anatomy_the_goldens_hold():
    """The bytes of both blessed producers, pinned where they are produced.

    The goldens (#312) hold the route; this holds the two producers directly,
    so a producer-side refactor is caught even before the route snapshot is.
    """
    card = analytics_view._analytics_card(
        "Velocity",
        "4 sessions, 140 minutes",
        "Sessions and work items started in the selected window.",
        "<svg>chart</svg>",
        "<p>detail</p>",
        _Model(window_days=30, group_by="prefix"),
        "velocity",
    )
    assert card == (
        '<div class="card analytics-card"><p class="lead">Velocity</p>'
        '<p class="big">4 sessions, 140 minutes</p>'
        '<p class="mut">Sessions and work items started in the selected window.</p>'
        "<svg>chart</svg>"
        "<details><summary>Details</summary><p>detail</p></details>"
        '<form method="post" action="/analytics/export" class="actions">'
        '<input type="hidden" name="theme" value="velocity">'
        '<input type="hidden" name="days" value="30">'
        '<input type="hidden" name="group_by" value="prefix">'
        '<button class="btn secondary" type="submit" name="format" value="md">Export MD</button>'
        '<button class="btn secondary" type="submit" name="format" value="html">Export HTML</button>'
        '<button class="btn secondary" type="submit" name="format" value="json">Export JSON</button>'
        "</form></div>"
    )

    controls = analytics_view._analytics_controls(30, "prefix", "velocity")
    assert controls == (
        '<div class="card analytics-controls"><form method="get" action="/analytics">'
        '<div class="form-row"><label>Date range</label>'
        '<select name="days">'
        '<option value="7" >Last 7 days</option>'
        '<option value="30" selected>Last 30 days</option>'
        '<option value="90" >Last 90 days</option>'
        '<option value="30" >Policy default (30d)</option>'
        "</select>"
        '<input type="hidden" name="group-by" value="prefix">'
        '<input type="hidden" name="theme" value="velocity">'
        '<p class="small mut">Which window the charts cover.</p>'
        '<button class="btn secondary" type="submit">Apply</button></div></form>'
        '<div class="form-row"><label>Group by</label>'
        '<p class="small mut">How sessions are bucketed in the charts.</p>'
        '<a class="btn " href="/analytics?days=30&amp;group-by=prefix&amp;theme=velocity">Prefix</a> '
        '<a class="btn secondary" href="/analytics?days=30&amp;group-by=track&amp;theme=velocity">Track</a>'
        "</div></div>"
    )


def test_the_blessed_producers_escape_and_stay_outside_the_script_budget():
    """Blessed is not a licence: no raw value, no intent, no script."""
    card = analytics_view._analytics_card(
        "Velocity <b>",
        "4 & 5 sessions",
        "derived from 'sessions'",
        "<svg>chart</svg>",
        "<p>detail</p>",
        _Model(window_days=30, group_by="prefix"),
        "velocity",
    )
    controls = analytics_view._analytics_controls(30, "pre<fix", "ve&locity")

    assert "&lt;b&gt;" in card and "&amp;" in card and "&#x27;" in card
    assert "<b>" not in card and "4 & 5" not in card
    # The controls panel escapes every value it interpolates — the hidden
    # inputs and the query strings of the two grouping links alike.
    assert "pre&lt;fix" in controls and "pre<fix" not in controls
    assert "ve&amp;locity" in controls and "ve&locity" not in controls
    for html in (card, controls):
        assert "<script" not in html.lower(), html
        assert 'data-intent="' not in html and 'data-tip="' not in html
        assert forbidden_matches(html) == [], html
