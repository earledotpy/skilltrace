"""The Graph capability (spec-v3-study-day §11.4, RT-14).

What only this module shows: the graph renders the relationship truth —
``graph/edges.yaml`` and nothing else — as a complete list equivalent whose
every node and edge is keyboard-reachable with a meaningful name, its current
state and its prerequisite context, and the same read and navigation actions
(AX-9). Selecting a node or an edge opens the contextual inspector inside the
graph route, with the selection carried on the route's URL so a shared or
reloaded link reproduces exactly what was seen. No fact exists only in a
picture, because there is no picture: the graph is server-rendered tables
and lists, with no pan, zoom, heatmap or client-side behaviour.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]

NODE = "data.pandas.dataframe_basics_01"
NODE_TITLE = "Use basic Pandas DataFrame operations"
PREREQ_NODE = "data.csv.clean_simple_dataset_01"
PREREQ_TITLE = "Clean a simple CSV dataset"


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A copy of the seed curriculum with an authored, pinned learner state.

    The learner store is authored (never derived from the live repo's own
    progress), so the assertions below hold no matter what the working
    repository's store says today.
    """
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    doc = {
        "progress": {
            NODE: {"state": "active", "changed_at": "2026-11-01T09:00:00+00:00"},
            PREREQ_NODE: {"state": "passed", "changed_at": "2026-11-01T09:00:00+00:00"},
        }
    }
    path = tmp_path / "graph" / "state.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return tmp_path


def _inspector(body: str) -> str:
    """The one inspector aside on the page, or a failing empty string."""
    parts = body.split('<aside class="inspector"')
    assert len(parts) == 2, "expected exactly one inspector aside on the page"
    return '<aside class="inspector"' + parts[1].split("</aside>")[0] + "</aside>"


# --- the contextual inspector: a selected skill ---------------------------------


def test_selecting_a_node_opens_the_inspector_on_the_graph_route(repo):
    """``?node=`` selects a skill; the inspector shows its canonical record."""
    title, body, status = views.graph_body(repo, {"node": [NODE]})
    assert (title, status) == ("Graph", 200)
    aside = _inspector(body)
    assert "Selected skill" in aside
    assert NODE_TITLE in aside
    assert f"<code>{NODE}</code>" in aside


def test_the_node_inspector_shows_state_and_prerequisite_context(repo):
    """The selected skill's state and its prerequisite context are canonical facts."""
    aside = _inspector(views.graph_body(repo, {"node": [NODE]})[1])
    assert "Active" in aside  # the authored state, as the canonical word
    assert PREREQ_TITLE in aside  # the prerequisite's readable title


def test_the_node_inspector_carries_event_provenance(repo):
    """Provenance renders as record detail behind a disclosure."""
    aside = _inspector(views.graph_body(repo, {"node": [NODE]})[1])
    assert "Event provenance" in aside


def test_the_selection_is_url_addressable_and_closeable(repo):
    """The route's own URL carries the selection; closing returns to the list."""
    body = views.graph_body(repo, {"node": [NODE]})[1]
    assert f'href="/graph?node={NODE}"' in body.replace("&", "&") or (
        f"node={NODE}" in body
    )
    aside = _inspector(body)
    assert 'href="/graph">Close inspector</a>' in aside


def test_a_selection_that_names_no_skill_is_a_refusal(repo):
    """An unknown selection refuses with the way back — never a silent fallback."""
    body = views.graph_body(repo, {"node": ["no.such.node_99"]})[1]
    assert "state-refusal" in body
    assert "no.such.node_99" in body
    assert 'href="/graph"' in body


def test_the_bare_graph_renders_no_inspector(repo):
    """No selection, no inspector — the list stands alone."""
    body = views.graph_body(repo, {})[1]
    assert '<aside class="inspector"' not in body


# --- the contextual inspector: a selected relationship --------------------------


def _edge_id(repo: Path, source: str, target: str) -> str:
    """One edge id read from the edge table — the sole relationship truth."""
    from skilltrace.graph.edges import load_edges

    edge = next(
        e for e in load_edges(repo) if e.source == source and e.target == target
    )
    return edge.id


def test_selecting_a_relationship_opens_the_inspector(repo):
    """``?edge=`` selects a relationship; the inspector shows its record."""
    edge_id = _edge_id(repo, PREREQ_NODE, NODE)
    title, body, status = views.graph_body(repo, {"edge": [edge_id]})
    assert (title, status) == ("Graph", 200)
    aside = _inspector(body)
    assert "Selected relationship" in aside
    assert f"<code>{edge_id}</code>" in aside
    assert NODE_TITLE in aside  # the source skill, readable
    assert PREREQ_TITLE in aside  # the target skill, readable
    assert "soft_prerequisite" in aside
    assert "In force" in aside


def test_an_unknown_relationship_is_a_refusal(repo):
    """An edge id that names nothing refuses with the way back."""
    body = views.graph_body(repo, {"edge": ["edge.nowhere.__nothing_99"]})[1]
    assert "state-refusal" in body
    assert "edge.nowhere.__nothing_99" in body
    assert 'href="/graph"' in body


# --- the list equivalent: the same actions on every node and edge ----------------


def test_every_node_row_carries_the_read_and_navigation_actions(repo):
    """A node row reads (detail) and navigates (neighborhood) — AX-9."""
    body = views.graph_body(repo, {})[1]
    assert f'href="/nodes/{NODE}">{NODE_TITLE}</a>' in body
    assert f'href="/graph/{NODE}"' in body


def test_every_relationship_row_carries_the_same_actions(repo):
    """An edge row reads (its endpoints) and inspects (the edge record)."""
    edge_id = _edge_id(repo, PREREQ_NODE, NODE)
    body = views.graph_body(repo, {})[1]
    assert f'href="/nodes/{PREREQ_NODE}"' in body
    assert f'href="/nodes/{NODE}"' in body
    assert f"edge={edge_id}" in body


# --- the learning-neighborhood view (/graph/{id}) -------------------------------


def test_the_neighborhood_shows_the_selected_skill_facts(repo):
    """The centred skill leads with its name, state and prerequisite context."""
    title, body, status = views.graph_body(repo, {}, node_id=NODE)
    assert (title, status) == (NODE_TITLE, 200)
    assert "Prerequisites" in body
    assert "Unlocks" in body
    assert f"<code>{NODE}</code>" in body
    assert "Active" in body


def test_the_ancestor_closure_is_an_expandable_disclosure(repo):
    """The full hard-prerequisite ancestry is expandable, not the default burden."""
    body = views.graph_body(repo, {}, node_id=NODE)[1]
    assert '<details class="disclosure">' in body
    assert "Full prerequisite ancestry" in body


def test_the_neighborhood_keeps_the_full_curriculum_explicit(repo):
    """The full list is one explicit link away, never the default burden."""
    body = views.graph_body(repo, {}, node_id=NODE)[1]
    assert 'href="/graph">The full curriculum</a>' in body


def test_an_unknown_neighborhood_centre_is_404(repo):
    """A centre that names no skill is a 404 — never a silent fallback."""
    title, body, status = views.graph_body(repo, {}, node_id="no.such.node_99")
    assert status == 404


def test_the_neighborhood_rows_carry_the_same_actions(repo):
    """Related skills read, inspect and navigate like every other row."""
    body = views.graph_body(repo, {}, node_id=NODE)[1]
    assert f'href="/nodes/{PREREQ_NODE}"' in body
    assert f'href="/graph/{PREREQ_NODE}"' in body
    edge_id = _edge_id(repo, PREREQ_NODE, NODE)
    assert f"edge={edge_id}" in body


# --- the state filter (IC-4, SUP-P7) ---------------------------------------------


def test_the_state_filter_narrows_the_skill_list(repo):
    """A labelled GET filter narrows the list and rides the URL."""
    title, body, status = views.graph_body(repo, {"state": ["passed"]})
    assert status == 200
    assert 'selected>Passed</option>' in body
    skills_table = body.split("Every relationship", 1)[0]
    assert f'href="/nodes/{PREREQ_NODE}"' in skills_table  # authored passed
    assert f'href="/nodes/{NODE}"' not in skills_table  # authored active — out


def test_an_unknown_state_filter_renders_the_unfiltered_list(repo):
    """A mistyped filter never dead-ends the route."""
    title, body, status = views.graph_body(repo, {"state": ["nonsense"]})
    assert status == 200
    assert f'href="/nodes/{NODE}"' in body


# --- the sole relationship truth -------------------------------------------------


@pytest.fixture()
def repo_with_dangling_edge(repo: Path) -> Path:
    """The same repo with one edge whose source names no real skill."""
    path = repo / "graph" / "edges.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["edges"].append(
        {
            "id": "edge.no.such.node_99__data.pandas.dataframe_basics_01",
            "source": "no.such.node_99",
            "target": NODE,
            "edge_type": "hard_prerequisite",
            "reason": "Authored fixture: a dangling reference.",
            "active": True,
        }
    )
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return repo


def test_a_dangling_relationship_renders_nowhere(repo_with_dangling_edge):
    """Normal rendering includes only valid relationships (§11.4)."""
    body = views.graph_body(repo_with_dangling_edge, {})[1]
    assert "no.such.node_99" not in body


def test_a_dangling_relationship_points_at_repository_diagnostics(
    repo_with_dangling_edge,
):
    """The fact is not hidden: Health's diagnostics carry the exact reference."""
    body = views.graph_body(repo_with_dangling_edge, {})[1]
    assert "Repository diagnostics" in body
    assert 'href="/health"' in body


def test_a_dangling_relationship_leaks_nowhere_else(repo_with_dangling_edge):
    """The neighbourhood and the inspector render only valid relationships."""
    neighbourhood = views.graph_body(
        repo_with_dangling_edge, {}, node_id=NODE
    )[1]
    assert "no.such.node_99" not in neighbourhood
    inspector = views.graph_body(
        repo_with_dangling_edge, {"node": [NODE]}
    )[1]
    assert "no.such.node_99" not in inspector
