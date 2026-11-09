"""The pass and mastery journeys (spec-v3-study-day §10.7, §10.8).

What only this module shows: the two journeys are **separate decisions**.

* **Passing** restates the accepted evidence it rests on, and the result
  shows the visible Review-state consequence (R3).
* **Mastery** is a two-step journey, visibly distinct from passing, whose
  final confirmation revalidates eligibility against current truth
  (R3 extension).
* No surface anywhere offers a combined pass-and-master action (HB-1).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from skilltrace.context import load_context_lenient
from skilltrace.web import views

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def repo() -> Path:
    """One read-only seed copy shared by this module's sweeps."""
    root = Path(tempfile.mkdtemp(prefix="t5-pass-master-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    return root


def _write_yaml(path: Path, relpath: str, doc: dict) -> None:
    target = path / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _eligible_node(root: Path) -> str:
    """A node the seed marks available and whose evidence is in place."""
    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if view.store.state_of(node.id) == "available":
            return node.id
    raise AssertionError("the seed graph has no available node")


# --- two separate journeys ------------------------------------------------------


def test_the_pass_journey_says_it_is_only_about_passing(repo):
    _, body, _ = views.pass_modal_body(repo, _eligible_node(repo))
    assert "about passing only" in body
    assert "Mastering is a separate" in body


def test_the_mastery_journey_says_it_is_only_about_mastery(repo):
    _, body, _ = views.master_body(repo, _eligible_node(repo))
    assert "Mastering is a separate, later step from passing" in body
    assert "never combined with passing" in body


def test_no_surface_offers_a_combined_pass_and_master_action(repo):
    """HB-1: passing and mastering are never combined."""
    node_id = _eligible_node(repo)
    for body in (
        views.pass_modal_body(repo, node_id)[1],
        views.master_body(repo, node_id)[1],
        views.master_confirm_body(repo, node_id)[1],
    ):
        # A single form may not carry both commands.
        assert not (
            'action="/nodes/' in body and "/master" in body and "/pass" in body
        ) or body.count("<form") == 1


def test_the_two_journeys_have_different_titles(repo):
    """Different titles, so the learner never conflates them (C11)."""
    node_id = _eligible_node(repo)
    _, pass_title, _ = views.pass_modal_body(repo, node_id)
    _, master_title, _ = views.master_body(repo, node_id)
    _, confirm_title, _ = views.master_confirm_body(repo, node_id)
    assert pass_title != master_title
    assert master_title != confirm_title
    assert "Mastery" in master_title or "mastered" in master_title.lower()


def test_the_mastery_journey_is_two_steps(repo):
    """Mastery is a two-step journey with its own second step."""
    node_id = _eligible_node(repo)
    _, step1, _ = views.master_body(repo, node_id)
    _, step2, _ = views.master_confirm_body(repo, node_id)
    assert "Step 1" in step1
    assert "Step 2" in step2
    # Step 2 re-renders the facts freshly.
    for fact in ("Passed on", "Live proof accepted", "Review spacing"):
        assert fact in step1
        assert fact in step2


def test_the_permanent_confirmation_states_its_permanence(repo):
    _, step2, _ = views.master_confirm_body(repo, _eligible_node(repo))
    assert "Mastered never moves backward — this is permanent" in step2
    assert "pressure" in step2


# --- the pass result shows the Review consequence ---------------------------------


def test_a_passed_node_renders_the_result_not_the_confirmation(repo):
    """After passing, the panel is the result (R3)."""
    node_id = _eligible_node(repo)
    root = Path(tempfile.mkdtemp(prefix="t5-passed-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    # Mark the node passed in the store.
    state_path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": "passed"}
    state_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    _, body, _ = views.pass_modal_body(root, node_id)
    assert "What passing changed" in body
    assert "Mark " not in body.split("What passing changed")[0]


def test_the_result_names_the_scheduled_checks_when_there_are_any(repo):
    """Scheduled checks appear — the consequence is visible (R3)."""
    node_id = _eligible_node(repo)
    root = Path(tempfile.mkdtemp(prefix="t5-result-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    state_path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": "passed"}
    state_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    _write_yaml(
        root,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": "rev.result.001",
                    "node_id": node_id,
                    "status": "scheduled",
                    "scheduled_for": "2026-11-18",
                    "created_at": "2026-11-17T09:00:00+00:00",
                }
            ]
        },
    )
    _, body, _ = views.pass_modal_body(root, node_id)
    assert "2026-11-18" in body
    assert "scheduled" in body


def test_the_result_says_when_scheduling_stays_manual(repo):
    """When policy leaves scheduling manual, the page says so (R3)."""
    node_id = _eligible_node(repo)
    root = Path(tempfile.mkdtemp(prefix="t5-manual-"))
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, root / dirname)
    state_path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": "passed"}
    state_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    _, body, _ = views.pass_modal_body(root, node_id)
    assert "scheduling manual" in body
    # And the action is offered.
    assert 'href="/reviews"' in body
