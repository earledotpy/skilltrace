"""T3 — Richer Card vocabulary as the render seam (§E) acceptance gates.

What only the enforced seam can show:

* a ``Card`` missing any minimum field (state / title / why / resources /
  the one next action) is refused at construction, never degraded;
* every rendered affordance traces to an intent — the label comes from the
  intent's affordance vocabulary, never from a ``binding.command`` string,
  and no raw command string reaches page HTML;
* the interface renderer is the only Card-to-HTML map (#320: the deprecated
  part-map serializer and its ``cards_html`` entry point are retired — no
  route body or helper composes ``MentorCard``s directly).
"""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path
from typing import get_args

import pytest

from skilltrace.mentor.cards import Intent, NextAction
from skilltrace.web import views
from skilltrace.web.interface import render_rich_cards
from skilltrace.web.interface.affordances import intent_label
from skilltrace.web.interface.cards import Affordance, Card
from skilltrace.web.interface.validate import SublayerError

REPO_ROOT = Path(__file__).resolve().parents[2]

_RESOURCE = ["Docs — https://example.test/"]


def _full_card(**overrides) -> Card:
    fields = dict(
        state="available",
        title="Apply X",
        why="It unlocks two skills and fits your morning.",
        resources=list(_RESOURCE),
        affordances=(Affordance.from_intent("start", title="Apply X"),),
    )
    fields.update(overrides)
    return Card(**fields)


# --- Minimum fields are enforced at construction (§E) -------------------------------


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"state": "Ready to start"}, "canonical"),
        ({"state": ""}, "canonical"),
        ({"title": ""}, "title"),
        ({"title": "   "}, "title"),
        ({"why": ""}, "why"),
        ({"why": "  "}, "why"),
        ({"resources": []}, "resources"),
        ({"resources": ["", "  "]}, "resources"),
        ({"affordances": ()}, "exactly one next action"),
        (
            {
                "affordances": (
                    Affordance.from_intent("start", title="Apply X"),
                    Affordance.from_intent("explore", title="Apply X"),
                )
            },
            "exactly one next action",
        ),
    ],
)
def test_card_refuses_each_missing_minimum_field(overrides, match):
    with pytest.raises(SublayerError, match=match):
        _full_card(**overrides)


def test_affordance_refuses_an_intent_outside_the_closed_set():
    with pytest.raises(SublayerError, match="closed"):
        Affordance(intent="deploy", label="Deploy it")


def test_affordance_label_is_refused_when_blank():
    with pytest.raises(SublayerError, match="no human label"):
        Affordance(intent="start", label="   ")


# --- Affordances render from the intent, never from a command string ----------------


def test_rendered_affordance_label_traces_to_the_intent_not_the_command():
    binding = NextAction(
        intent="pass",
        node_id="math.arithmetic.x_01",
        command="Mark Apply X passed: `skilltrace pass math.arithmetic.x_01`",
        eligible=True,
    )
    affordance = Affordance.from_intent(
        binding.intent, binding=binding, title="Apply X"
    )
    # The label is the intent's vocabulary — never the command string.
    assert affordance.label == intent_label("pass", title="Apply X")
    assert "skilltrace" not in affordance.label

    card = _full_card(
        state="active",
        title="Apply X",
        affordances=(affordance,),
    )
    html = render_rich_cards([card])
    assert 'data-intent="pass"' in html
    assert "skilltrace" not in html


# --- No raw command string in any page HTML ------------------------------------------


def _first_node_id(root: Path, *, state: str | None = None) -> str:
    from skilltrace.context import load_context_lenient

    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if state is None or view.store.state_of(node.id) == state:
            return node.id
    raise AssertionError(f"no node with state {state!r}")


def _all_route_bodies() -> list[tuple[str, str]]:
    repo = Path(tempfile.mkdtemp())
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, repo / dirname)
    node_id = _first_node_id(repo, state="available")
    return [
        ("home", views.home_body(repo)[1]),
        ("next", views.next_body(repo, {})[1]),
        ("next locked", views.next_body(repo, {"locked": ["1"]})[1]),
        ("node", views.node_body(repo, node_id)[1]),
        ("health", views.health_body(repo)[1]),
        ("analytics", views.analytics_body(repo, {})[1]),
        # #319: the discovery surface owes the same guarantees — its cards
        # compose through the Card seam, so the gates hold by construction.
        ("finder", views.finder_body(repo, {})[1]),
        ("finder query", views.finder_body(repo, {"q": ["order of operations"]})[1]),
    ]


def test_no_raw_command_string_in_any_page_html():
    pattern = re.compile(r"skilltrace\s+[a-z]|\b--node\b", re.IGNORECASE)
    for name, body in _all_route_bodies():
        assert not pattern.search(body), f"raw command string leaked into {name}"


def test_every_data_intent_is_in_the_closed_set():
    closed = set(get_args(Intent))
    for name, body in _all_route_bodies():
        for intent in re.findall(r'data-intent="([^"]+)"', body):
            assert intent in closed, f"{name}: unknown intent {intent!r}"


# --- The interface renderer is the only Card-to-HTML map (#320) ------------------


def test_the_deprecated_part_map_serializer_is_gone():
    from _web_source import web_source_text

    source = web_source_text()
    for token in (
        "render_cards",
        "_render_card_inner",
        "_render_part",
        "cards_html",
        "lines_to_cards",
        "views.compat",
    ):
        assert token not in source, f"deprecated compat survivor: {token}"
    assert (
        sorted(
            Path(__file__)
            .resolve()
            .parents[2]
            .glob("src/skilltrace/web/views/compat*")
        )
        == []
    )
