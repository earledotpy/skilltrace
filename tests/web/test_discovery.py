"""Discovery surfaces — Next and Find a skill (spec-v3-study-day §10.2, §10.3).

The v3 contract for the two discovery routes:

* **Next** renders a bounded, ranked list of study targets, every item
  carrying an honest, human-readable reason for its rank — no scores, no
  weights, no flags, no identifiers. Locked skills appear only as
  explanation, never as selectable targets. The empty, limited and
  could-not-compute states each say something true, and a stale readiness
  store is reported as a recovery prompt rather than hidden.
* **Find a skill** searches the whole curriculum through labelled GET
  controls whose result set has its own URL — reloadable, shareable and
  reachable with the back button. A query that matches nothing explains
  itself and keeps discovery alive instead of dead-ending.

The golden cases at the end pin the populated, empty and limited shapes of
Next and the no-results shape of Find, so a change of copy or structure
cannot slip through unnoticed.
"""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from skilltrace.context import load_context_lenient
from skilltrace.web import views

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


@pytest.fixture
def writable_repo(tmp_path: Path) -> Path:
    """A fresh seed copy a test may edit."""
    root = tmp_path / "repo"
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    return root


def _next(root: Path, **query: str) -> str:
    params = {key: [value] for key, value in query.items()}
    return views.next_body(root, params)[1]


def _find(root: Path, **query: str) -> str:
    params = {key: [value] for key, value in query.items()}
    return views.finder_body(root, params)[1]


def _queue_items(body: str) -> list[str]:
    """The ranked queue items, in rank order."""
    return re.findall(r'<li class="queue-item[^"]*">.*?</li>', body, re.S)


def _section(body: str, title: str) -> str:
    """The section whose heading carries ``title``."""
    start = body.index(f">{title}</h2>")
    end = body.index("</section>", start)
    return body[start:end]


def _titles(root: Path) -> dict[str, str]:
    view = load_context_lenient(root)
    return dict(view.titles)


# --- Next: a ranked list with an honest reason for every rank ------------------


def test_next_renders_a_ranked_list_of_study_targets(repo):
    body = _next(repo)
    items = _queue_items(body)
    assert items, "Next must render a ranked list"
    # The first item is the page's one dominant action.
    assert 'class="queue-item dominant"' in items[0]
    assert 'class="queue-item dominant"' not in "".join(items[1:])
    # Every item is a selectable target: a link to the skill.
    for item in items:
        assert re.search(r'<a href="/nodes/[^"]+">', item), item


def test_next_every_item_carries_a_human_readable_reason_for_its_rank(repo):
    body = _next(repo)
    items = _queue_items(body)
    assert items
    for item in items:
        why = re.search(r'<p class="queue-why">(.*?)</p>', item, re.S)
        assert why, item
        reason = why.group(1)
        assert reason.strip()
        # A sentence in the learner's language — no ranker internals.
        assert reason[0].isupper()
        for internals in ("weight", "score", "track ", "leverage", "policy boost"):
            assert internals not in reason.lower(), reason


def test_next_keeps_the_why_this_disclosure(repo):
    body = _next(repo)
    items = _queue_items(body)
    assert len(items) == body.count('<details class="disclosure">')
    for item in items:
        assert "Why this?" in item
        assert "never block a human-initiated action" in item


def test_next_never_shows_a_raw_identifier_in_the_reasons(repo):
    body = _next(repo)
    queue = body[body.index('<ul class="queue">'): body.index("</ul>")]
    assert "math.arithmetic" not in queue
    assert "data.sql" not in queue
    assert ".01" not in queue


def test_next_is_read_only_navigation(repo):
    body = _next(repo)
    assert 'method="post"' not in body
    assert 'action="/nodes/' not in body  # no write target on the route
    assert "Mark this skill passed" not in body
    assert "Mark this skill mastered" not in body


def test_next_controls_are_labelled_get_controls(repo):
    body = _next(repo)
    assert '<form class="filters" method="get" action="/next">' in body
    assert '<label for="next-minutes">' in body
    assert '<label for="next-limit">' in body
    assert 'name="minutes" value="60"' in body
    assert 'name="limit" value="5"' in body
    # No CLI flag name ever renders.
    assert "--minutes" not in body
    assert "--limit" not in body


def test_next_controls_are_url_addressable(repo):
    body = _next(repo, minutes="30", limit="2")
    assert 'name="minutes" value="30"' in body
    assert 'name="limit" value="2"' in body
    assert len(_queue_items(body)) <= 2


def test_next_list_is_bounded(repo):
    body = _next(repo, limit="500")
    assert "bounded at 20" in body
    assert len(_queue_items(body)) <= 20


# --- Next: the states that are not success -------------------------------------


def test_next_empty_state_is_authoritative_and_offers_recovery(writable_repo):
    _set_all_states(writable_repo, "passed")
    body = _next(writable_repo)
    assert 'class="state state-empty"' in body
    # The reason is authoritative: it says what is and is not recommendable.
    assert "Nothing is recommendable right now" in body
    assert "No skill is available or active" in body
    # The recovery path keeps discovery alive.
    assert '<a href="/find">Find a skill</a>' in body


def test_next_limited_state_retains_the_values_and_states_the_threshold(repo):
    body = _next(repo, minutes="15")
    assert 'class="state state-limited"' in body
    # The threshold is stated.
    assert "15-minute session" in body
    # The values are retained, not dropped.
    assert _queue_items(body)
    # And a longer window is one link away.
    assert "minutes=30" in body


def test_next_failure_state_is_operational_and_invents_nothing(
    writable_repo, monkeypatch
):
    from skilltrace.web.views import next as next_view

    def boom(*args, **kwargs):
        raise RuntimeError("the ranker could not read the policy")

    monkeypatch.setattr(next_view, "derive_next", boom)
    body = _next(writable_repo)
    assert 'class="state state-failure"' in body
    assert "could not be worked out" in body
    # No zeros, no fabricated health fact.
    assert "0 skill" not in body
    assert "0 options" not in body
    # A precise recovery path.
    assert '<a href="/next">Try again</a>' in body
    assert 'href="/find"' in body


def test_next_stale_readiness_prompts_a_safe_refresh(writable_repo):
    # A new hard prerequisite makes the saved readiness out of date.
    _add_hard_prerequisite(
        writable_repo,
        source=ORDER_OPERATIONS,
        target=SELECT_BASICS,
    )
    body = _next(writable_repo)
    assert 'class="state state-recovery"' in body
    assert "readiness is out of date" in body
    # The dependency is named, not hidden behind silence, and the refresh is
    # safe: it never moves recorded progress.
    assert "command line" in body
    assert "never moves your recorded progress" in body
    # The recovery link reloads the same addressable result.
    assert "reload this list" in body


# --- Next: locked skills are explanation, never targets -----------------------


def test_next_locked_skills_are_explanation_never_targets(repo):
    body = _next(repo)
    section = _section(body, "Not ready yet")
    assert "waiting on" in section
    titles = _titles(repo)
    for node_id, title in titles.items():
        if f'>{title}</span>' not in section:
            continue
        # A locked skill is never a link out of this section.
        assert f'href="/nodes/{node_id}"' not in section
    # No locked skill carries a start action.
    assert "Start studying" not in section
    assert 'method="post"' not in section


# --- Find a skill: labelled GET controls with their own URL -------------------


def test_find_search_controls_are_labelled_get_controls(repo):
    body = _find(repo)
    assert '<form class="filters" method="get" action="/find">' in body
    assert '<label for="find-q">' in body
    assert '<label for="find-subject">' in body
    assert '<label for="find-state">' in body
    assert 'name="q"' in body
    assert 'name="subject"' in body
    assert 'name="state"' in body


def test_find_results_have_their_own_url(repo):
    body = _find(repo, q="sql select")
    # The search text is carried in the form, so the result set is a URL.
    assert 'name="q" value="sql select"' in body
    # A subject is a filter with a URL of its own.
    assert 'href="/find?subject=data"' in body
    # A state is a filter with a URL of its own.
    assert 'value="available"' in body
    assert 'value="locked"' in body


def test_find_subject_filter_narrows_the_result_set(repo):
    everything = _find(repo)
    data_only = _find(repo, subject="data")
    assert 'id="subject-data"' in everything
    assert "17 skills" in data_only
    assert "33 skills" not in data_only


def test_find_state_filter_narrows_the_result_set_and_says_what_it_hid(repo):
    body = _find(repo, state="locked")
    assert 'class="state state-limited"' in body
    assert "The state filter is what hides them" in body
    assert "Locked" in body


def test_find_searches_the_whole_curriculum(repo):
    body = _find(repo, q="python")
    assert "python" in body.lower()
    # Matches come from more than one subject — the search is not one folder.
    subjects = set(re.findall(r'<p class="mut ref">([a-z_]+)\.', body))
    assert len(subjects) >= 2


def test_find_no_results_preserves_discovery(repo):
    body = _find(repo, q="xyzzyplugh")
    assert 'class="state state-empty"' in body
    assert "No skills match" in body
    # The foundations entries stay reachable.
    for entry in (ORDER_OPERATIONS, SELECT_BASICS, VARIABLES):
        assert f'href="/nodes/{entry}"' in body
    # And the browse index stays on the page.
    assert 'id="browse"' in body
    assert 'href="#browse"' in body


def test_find_locked_results_are_explanation_not_targets(repo):
    body = _find(repo, q="filter and sort query results")
    cards = re.findall(r'<div class="card result[^"]*">.*?</div>', body, re.S)
    locked = [card for card in cards if "card result locked" in card]
    assert locked, "the seed's locked query card must render as locked"
    card = locked[0]
    # The locked skill's own title is not a link into the node.
    assert f'href="/nodes/{FILTER_SORT}"' not in card
    # It names the blocking prerequisite and links it.
    assert "Blocked by" in card
    assert f'href="/nodes/{SELECT_BASICS}">' in card


def test_find_shows_the_readable_title_not_the_identifier(repo):
    body = _find(repo, q="order of operations")
    card = re.findall(r'<div class="card result[^"]*">.*?</div>', body, re.S)[0]
    titles = _titles(repo)
    assert titles[ORDER_OPERATIONS] in card
    # The raw identifier survives only as labelled secondary technical data.
    assert f'<p class="mut ref">{ORDER_OPERATIONS}</p>' in card
    assert "The skill identifier is shown in grey" in body


def test_find_selection_navigates_only(repo):
    body = _find(repo, q="python")
    assert "/start" not in body
    assert 'method="post"' not in body


def test_find_full_function_with_script_absent(repo):
    for query in ({}, {"q": "order of operations"}, {"q": "xyzzyplugh"}):
        assert "<script" not in _find(repo, **query)


# --- golden cases --------------------------------------------------------------


def test_golden_next_populated(repo):
    body = _next(repo)
    queue = body[body.index('<ul class="queue">') : body.index("</ul>")]
    first = queue[: queue.index("</li>")]
    assert re.search(
        r'<li class="queue-item dominant">\n'
        r'<p class="queue-title"><a href="/nodes/[^"]+">[^<]+</a> '
        r'<span class="status-label (?:neutral|info)">\w+</span></p>\n'
        r'<p class="queue-why">[^<]+</p>\n'
        r'<div class="queue-actions">'
        r'<a class="btn primary" href="/nodes/[^"]+">Open this skill</a>'
        r"</div>\n"
        r'<details class="disclosure">\n'
        r"<summary>Why this\?</summary>\n",
        first,
    )


def test_golden_next_empty(writable_repo):
    _set_all_states(writable_repo, "passed")
    body = _next(writable_repo)
    empty = body[body.index('<div class="state state-empty">') :]
    assert empty.startswith(
        '<div class="state state-empty">\n'
        '<p class="state-title">Nothing is recommendable right now</p>\n'
        '<p class="state-body">No skill is available or active for a '
    )
    assert '<a href="/find">Find a skill</a>' in empty


def test_golden_next_limited(repo):
    body = _next(repo, minutes="15")
    limited = body[body.index('<div class="state state-limited">') :]
    assert limited.startswith(
        '<div class="state state-limited">\n'
        '<p class="state-title">None of these fits a 15-minute session</p>\n'
    )
    # The values are retained below the panel.
    assert _queue_items(body)


def test_golden_find_no_results(repo):
    body = _find(repo, q="xyzzyplugh")
    empty = body[body.index('<div class="state state-empty">') :]
    assert empty.startswith(
        '<div class="state state-empty">\n'
        '<p class="state-title">No skills match</p>\n'
        '<p class="state-body">Nothing came back — nothing in the curriculum '
        'matches “xyzzyplugh”. That is a fact about the curriculum, not about '
        "you."
    )


# --- helpers that edit the fixture ---------------------------------------------


def _set_all_states(root: Path, state: str) -> None:
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {"progress": {}}
    for entry in doc.get("progress", {}).values():
        entry["state"] = state
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _add_hard_prerequisite(root: Path, *, source: str, target: str) -> None:
    path = root / "graph" / "edges.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["edges"].append(
        {
            "id": f"edge.test.{source}__{target}",
            "source": source,
            "target": target,
            "edge_type": "hard_prerequisite",
            "reason": "A test prerequisite, added to make the saved readiness "
            "out of date.",
            "active": True,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
    )
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
