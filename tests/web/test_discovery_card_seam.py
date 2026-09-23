"""The discovery cards render through the Card seam (#319).

What only the enforced seam can show:

* the §C-bis result and browse cards are interface ``Card`` objects —
  composed by the pure discovery module (``web.discovery``) and rendered
  by the one Card-to-HTML map (``interface.render``); the page-side
  ``_discovery_card_html`` producer is gone, so the closed-intent and
  no-raw-command guarantees cover discovery cards by construction rather
  than by page sweep;
* the locked §C-bis anatomy — title link (greyed, never a link when
  locked), state chip from the plain-language pairing, description,
  secondary id, blocked-prerequisite tail — renders where every other
  Card renders, escaping through the shared door, byte for byte;
* the foundations-stub ``description pending`` marker rides the Card's
  disclosure slot and the subject-line fallback keeps the description
  line never bare (spec §C-bis ``Card anatomy``).
"""

from __future__ import annotations

import inspect
import re
import shutil
from pathlib import Path

import pytest

from skilltrace.context import load_context_lenient
from skilltrace.web import discovery as web_discovery
from skilltrace.web.discovery import (
    DiscoveryCard,
    browse_cards,
    discover,
    discovery_page_cards,
)
from skilltrace.web.interface.cards import CANONICAL_STATES, CHIP_LABELS, Card
from skilltrace.web.interface.render import render_discovery_cards
from skilltrace.web.views.finder import _discovery_chrome, _render_results

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB = REPO_ROOT / "src" / "skilltrace" / "web"

ENTRY = "programming.python.variables_01"  # a foundations entry node


def _web_sources() -> dict[Path, str]:
    """Web module code text (docstrings and comments stripped), by path."""
    sources = {}
    for path in sorted(WEB.rglob("*.py")):
        text = re.sub(r'"""(?!\").*?\"\"\"', "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        sources[path] = "\n".join(
            line for line in text.splitlines() if not line.strip().startswith("#")
        )
    return sources


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


# --- the derivation composes interface Cards ----------------------------------------


def test_discovery_page_cards_returns_interface_cards_with_the_derivation_copy():
    view = load_context_lenient(REPO_ROOT)
    records = discover(view, "order of operations")
    assert records, "the seed must answer the Q7 probe query"

    cards = discovery_page_cards(records)
    assert len(cards) == len(records)
    assert all(isinstance(card, Card) for card in cards)
    for record, card in zip(records, cards):
        assert card.state == record.state
        assert card.title == record.title
        assert card.node_id == record.node_id
        assert card.why == record.description
        assert card.disclosure is None  # no stub marker on a described node
    # The §C-bis anatomy renders no resources section or next action of its
    # own (selection navigates only), so the Richer-Card minimum fields ride
    # neutral values it never renders — the #318 precedent. Pinned exactly, so
    # the neutral choice is stated here rather than implied by the frame.
    assert all(card.resources == [web_discovery._DISCOVERY_RESOURCE] for card in cards)
    assert all(
        [affordance.intent for affordance in card.affordances]
        == [web_discovery._DISCOVERY_INTENT]
        for card in cards
    )


def test_the_neutral_affordance_stays_invisible_on_the_page():
    """The composition's Card minimum is a false next action — so it never renders.

    A discovery result navigates only; ``explore`` exists to satisfy the
    Card minimum. If the discovery anatomy ever rendered affordances, the
    finder would advertise a next action it does not have, so this pins the
    label out of the page.
    """
    records = discover(load_context_lenient(REPO_ROOT), "order of operations")
    [card] = discovery_page_cards(records[:1])
    label = card.affordances[0].label
    assert label  # real on the object…
    assert label not in _render_results(records[:1])  # …absent from the page


def test_browse_cards_compose_through_the_same_step():
    view = load_context_lenient(REPO_ROOT)
    records = browse_cards(view, "math")
    cards = discovery_page_cards(records)
    assert [card.node_id for card in cards] == [record.node_id for record in records]


def test_the_foundation_stub_fallback_is_never_bare():
    """Spec §C-bis: stub fallback = subject line + marker, never bare."""
    stub = DiscoveryCard(
        node_id=ENTRY,
        title="Variables",
        state="available",
        description="",
        description_pending=True,
        entry=True,
    )
    [card] = discovery_page_cards([stub])
    assert card.why == "Python foundations — beginner entry"
    assert card.disclosure == "description pending"
    assert card.why.strip()  # the Card minimum holds even for a stub


def test_the_derivation_stays_pure_composition_is_separate():
    for function in (
        web_discovery.discover,
        web_discovery.card_for,
        web_discovery.browse_cards,
    ):
        source = inspect.getsource(function)
        assert "Affordance(" not in source  # no interface objects in derivation
        assert "render_discovery" not in source  # rendering lives in the map


# --- the bespoke producer is gone ----------------------------------------------------


def test_the_ad_hoc_card_html_producer_is_gone():
    offenders = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path, source in _web_sources().items()
        if "_discovery_card_html" in source
    )
    assert offenders == []


def test_the_result_card_anatomy_lives_only_in_the_interface_renderer():
    # `card result` is the §C-bis frame — the one Card-to-HTML map owns it,
    # so discovery cards are covered by construction, not by page sweep.
    owners = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path, source in _web_sources().items()
        if "card result" in source
    )
    assert owners == ["src/skilltrace/web/interface/render.py"]


# --- the route renders through the seam ----------------------------------------------


def test_finder_body_renders_results_and_browse_through_the_renderer(
    repo, monkeypatch
):
    from skilltrace.web.views import finder as finder_view

    seen: list[list] = []
    real = finder_view.render_discovery_cards

    def spy(cards, chromes=None):
        seen.append(list(cards))
        return real(cards, chromes)

    monkeypatch.setattr(finder_view, "render_discovery_cards", spy)

    # the search-results path
    title, body, status = finder_view.finder_body(repo, {"q": ["order of operations"]})
    assert status == 200 and title == "Find a skill"
    assert seen, "the result cards never went through the interface renderer"
    assert all(isinstance(card, Card) for group in seen for card in group)

    # the browse path (no query still renders every subject's cards)
    seen.clear()
    finder_view.finder_body(repo, {})
    assert seen, "the browse cards never went through the interface renderer"
    assert all(isinstance(card, Card) for group in seen for card in group)


def test_the_page_composer_holds_no_markup():
    from skilltrace.web.views import finder as finder_view

    source = inspect.getsource(finder_view._render_results)
    assert "class=" not in source  # compose + attach + render, no hand-rolled HTML
    assert inspect.getsource(finder_view._discovery_chrome).count("<p") == 1


# --- the locked §C-bis anatomy, byte for byte -----------------------------------------


def _available_record() -> DiscoveryCard:
    return DiscoveryCard(
        node_id="math.arithmetic.order_operations_01",
        title="Order <ops> & more",
        state="available",
        description="1 < 2 & 3 'x'",
        description_pending=False,
        entry=True,
    )

def _locked_record() -> DiscoveryCard:
    return DiscoveryCard(
        node_id="data.sql.filtering_sorting_01",
        title="Filter & sort",
        state="locked",
        description="Sort rows",
        description_pending=False,
        entry=False,
        blocked_by_id="data.sql.select_basics_01",
        blocked_by_title="SELECT <basics> & 'more'",
    )


def test_the_discovery_anatomy_bytes_are_locked():
    records = [_available_record(), _locked_record()]
    html = render_discovery_cards(
        discovery_page_cards(records),
        {index: _discovery_chrome(record) for index, record in enumerate(records)},
    )
    assert html == (
        '<div class="card result">\n'
        '<p class="lead"><a href="/nodes/math.arithmetic.order_operations_01">'
        "Order &lt;ops&gt; &amp; more</a> "
        '<span class="pill ready-to-start">Ready to start</span></p>\n'
        "<p class=\"big\">1 &lt; 2 &amp; 3 &#x27;x&#x27;</p>\n"
        '<p class="mut ref">math.arithmetic.order_operations_01</p>\n'
        "</div>\n"
        '<div class="card result locked">\n'
        '<p class="lead">Filter &amp; sort '
        '<span class="pill locked">Locked</span></p>\n'
        '<p class="big">Sort rows</p>\n'
        '<p class="mut ref">data.sql.filtering_sorting_01</p>\n'
        '<p class="sub">Blocked by '
        '<a href="/nodes/data.sql.select_basics_01">'
        "SELECT &lt;basics&gt; &amp; &#x27;more&#x27;</a> — pass it first.</p>\n"
        "</div>\n"
    )


def test_the_locked_title_is_never_a_link_into_the_node():
    record = _locked_record()
    html = render_discovery_cards(
        discovery_page_cards([record]), {0: _discovery_chrome(record)}
    )
    assert f'href="/nodes/{record.node_id}"' not in html  # greyed stays the wall
    assert "Blocked by" in html


def test_the_pending_marker_rides_the_card_and_stays_ordered():
    stub = DiscoveryCard(
        node_id=ENTRY,
        title="Variables",
        state="available",
        description="",
        description_pending=True,
        entry=True,
    )
    html = render_discovery_cards(discovery_page_cards([stub]), {0: ""})
    assert '<p class="big">Python foundations — beginner entry</p>\n' in html
    assert '<p class="mut">description pending</p>\n' in html
    # marker between the description and the secondary id — the §C-bis order
    assert html.index("description pending") < html.index('class="mut ref"')


def test_the_chip_pairing_is_the_shared_state_vocabulary():
    """Every rendered chip label comes from the pairing, total over the words."""
    assert set(CHIP_LABELS) == set(CANONICAL_STATES)  # one home, no fork
    records = discover(load_context_lenient(REPO_ROOT), "sql select")
    html = _render_results(records)
    for record in records:
        label = CHIP_LABELS[record.state]
        slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        assert f'<span class="pill {slug}">{label}</span>' in html
