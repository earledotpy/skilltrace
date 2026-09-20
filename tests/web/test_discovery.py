"""The discovery combination surface — spec-tier1-serve §C-bis (build #310).

Pins the locked discovery contract on `/nodes/jump`: Q7 acceptance examples
top-1 their entries, an ID fragment still resolves, gibberish yields the
no-results pattern (3 entry links + browse anchor), locked cards are greyed
and name + link their blocking prerequisite, selection navigates only, the
result-count heading and labeled input exist, the browse index carries
anchor links per subject plus the grouped-count table, and the page is full
function with script absent (tier 0 per ADR 0008).
"""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

import pytest

from skilltrace.context import load_context_lenient
from skilltrace.web import views
from skilltrace.web.discovery import browse_cards, discover

REPO_ROOT = Path(__file__).resolve().parents[2]

ORDER_OPERATIONS = "math.arithmetic.order_operations_01"
SELECT_BASICS = "data.sql.select_basics_01"
VARIABLES = "programming.python.variables_01"
FILTER_SORT = "data.sql.filtering_sorting_01"


@pytest.fixture(scope="module")
def repo() -> Path:
    """One read-only seed copy shared by this module's sweeps."""
    root = Path(tempfile.mkdtemp(prefix="discovery-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    return root


def _finder(repo: Path, q: str = "") -> str:
    query = {"q": [q]} if q else {}
    return views.finder_body(repo, query)[1]


def _results(body: str) -> list[str]:
    """The result cards, in render order (before the browse index)."""
    body = body.split('id="browse"')[0]
    return re.findall(r'<div class="card result[ "].*?</div>\n', body, re.S)


def _first_result_href(body: str) -> str | None:
    cards = _results(body)
    if not cards:
        return None
    match = re.search(r'<a href="(/nodes/[^"]+)"', cards[0])
    return match.group(1) if match else None


# --- Q7 acceptance examples -----------------------------------------------------


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("order of operations", ORDER_OPERATIONS),
        ("sql select", SELECT_BASICS),
        ("python variables", VARIABLES),
    ],
)
def test_q7_queries_top_one_their_entry(repo, query, expected):
    assert _first_result_href(_finder(repo, query)) == f"/nodes/{expected}"


def test_id_fragment_still_resolves(repo):
    body = _finder(repo, "variables_01")
    assert _first_result_href(body) == f"/nodes/{VARIABLES}"


# --- Card anatomy ---------------------------------------------------------------


def test_result_count_heading_is_server_rendered(repo):
    body = _finder(repo, "sql select")
    heading = re.search(r'<h2 class="result-count">([^<]+)</h2>', body)
    assert heading and "match" in heading.group(1)


def test_cards_carry_title_chip_description_and_secondary_id(repo):
    card = _results(_finder(repo, "order of operations"))[0]
    assert '<span class="pill ready-to-start">Ready to start</span>' in card
    assert "Evaluate arithmetic expressions" in card  # node-body first sentence
    assert f'<p class="mut ref">{ORDER_OPERATIONS}</p>' in card


def test_search_input_is_labeled(repo):
    body = _finder(repo)
    assert 'aria-label="search skills by title"' in body


# --- Locked cards ---------------------------------------------------------------


def test_locked_card_is_greyed_names_and_links_the_prerequisite(repo):
    body = _finder(repo, "filter and sort query results")
    cards = _results(body)
    locked = [c for c in cards if 'class="card result locked"' in c]
    assert locked, "the seed's locked query card must render greyed"
    card = locked[0]
    # Greyed: the title is not a link into the node as available.
    assert f'href="/nodes/{FILTER_SORT}"' not in card
    # It names and links the blocking prerequisite.
    assert "Blocked by" in card
    assert f'href="/nodes/{SELECT_BASICS}">Query rows and columns with SELECT</a>' in card


def test_ranking_available_first_locked_last(repo):
    view = load_context_lenient(repo)
    cards = discover(view, "query")
    states = [c.state for c in cards]
    assert states == sorted(states, key=lambda s: 9 if s == "locked" else 0)


def test_ambiguity_shows_all_matches_no_silent_top_one(repo):
    view = load_context_lenient(repo)
    cards = discover(view, "sql")
    assert len(cards) > 1
    assert {c.node_id for c in cards} >= {SELECT_BASICS, "data.sql.aggregation_01"}


# --- No-results pattern ---------------------------------------------------------


def test_gibberish_yields_the_no_results_pattern(repo):
    body = _finder(repo, "xyzzyplugh")
    assert "No skills match" in body
    for entry in (ORDER_OPERATIONS, SELECT_BASICS, VARIABLES):
        assert f'href="/nodes/{entry}"' in body
    assert 'href="#browse"' in body


# --- Browse by subject ----------------------------------------------------------


def test_browse_index_has_anchor_links_per_subject_and_count_table(repo):
    body = _finder(repo)
    assert 'id="browse"' in body
    assert 'href="#subject-math"' in body
    assert 'href="#subject-data"' in body
    assert 'href="#subject-programming"' in body
    assert "<table>" in body and "<th>Skills</th>" in body
    assert 'id="subject-data"' in body


def test_browse_subject_list_starts_with_the_entry_node(repo):
    cards = browse_cards(load_context_lenient(repo), "math")
    assert cards[0].node_id == ORDER_OPERATIONS
    assert cards[0].entry is True


# --- Behavior contract ----------------------------------------------------------


def test_selection_navigates_only_no_implicit_start(repo):
    body = _finder(repo, "python")
    assert "/start" not in body
    assert 'method="post"' not in body


def test_full_function_with_script_absent(repo):
    for q in ("", "order of operations", "xyzzyplugh"):
        assert "<script" not in _finder(repo, q)
