"""Dead-ends offer an in-web action, never a trip to the terminal.

What only this module shows: at every dead-end the learner meets, the
page offers the **action that continues the work inside the product**.

The v2.4 contract told the learner to "continue in your terminal" and
"ask there for the exact form". That is superseded (spec §20 SUP-4): the
web is the product, so a dead-end that sends the learner away to run a
command is a broken journey, not a courtesy. The v3 rule is that a
dead-end carries an actionable next step — a link or a form — and that no
learner-facing surface ever names a command or the word "terminal".
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
import yaml

from skilltrace.context import load_context_lenient
from skilltrace.web import views
from skilltrace.web.interface import forbidden_matches

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed(tmp_path: Path) -> Path:
    for dirname in ("graph", "evidence", "policy"):
        shutil.copytree(REPO_ROOT / dirname, tmp_path / dirname)
    return tmp_path


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return _seed(tmp_path)


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _set_state(root: Path, node_id: str, state: str) -> None:
    path = root / "graph" / "state.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {"progress": {}}
    doc.setdefault("progress", {})[node_id] = {"state": state}
    _write_yaml(root, "graph/state.yaml", doc)


def _first(root: Path, *, state: str | None = None) -> str:
    view = load_context_lenient(root)
    for node in sorted(view.nodes, key=lambda n: n.id):
        if state is None or view.store.state_of(node.id) == state:
            return node.id
    raise AssertionError("no node")


def _overdue_repo(root: Path) -> str:
    view = load_context_lenient(root)
    nid = sorted(n.id for n in view.nodes)[0]
    _write_yaml(
        root,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": f"rev.{nid}.001",
                    "node_id": nid,
                    "status": "scheduled",
                    "scheduled_for": "2020-01-01",
                    "created_at": "2020-01-01T10:00:00+00:00",
                }
            ]
        },
    )
    return nid


def _actions(body: str) -> list[str]:
    """The in-web actions a page offers."""
    return re.findall(r'href="(/[^"#]*)"', body) + re.findall(
        r'action="(/[^"#]*)"', body
    )


# --- a dead-end carries an action ------------------------------------------------


def test_a_passed_skill_offers_the_scheduling_action(repo):
    """The dead-end after passing offers the action that continues the work."""
    nid = _first(repo, state="available")
    _set_state(repo, nid, "passed")
    _, body, _ = views.node_body(repo, nid)
    assert "No reviews scheduled" in body
    # The action is here, in the product.
    assert "/reviews/schedule" in _actions(body)
    assert "Schedule this review" in body


def test_an_overdue_review_carries_an_action_and_a_calm_zero(repo):
    """Overdue is shown with the action; a calm page says so and does not nag."""
    _, calm, _ = views.home_body(repo)
    # A calm page never nags and never sends the learner away.
    assert "overdue" not in calm.lower()
    assert "terminal" not in calm.lower()

    _overdue_repo(repo)
    _, body, _ = views.home_body(repo)
    # The overdue check is now in the queue, and it carries an action.
    assert "is overdue" in body
    assert "/reviews" in _actions(body)


def test_the_drilldown_sections_carry_actions(repo):
    """Each record section that reports something incomplete carries an action."""
    view = load_context_lenient(repo)
    specced = sorted(n.id for n in view.nodes if view.specs_by_node.get(n.id))
    nid = specced[0]
    _write_yaml(
        repo,
        "evidence/attempts.yaml",
        {
            "attempts": [
                {
                    "id": f"att.{nid}.001",
                    "node_id": nid,
                    "outcome": "passed",
                    "created_at": "2026-08-20T10:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        repo,
        "execution/remediation_actions.yaml",
        {
            "remediation_actions": [
                {
                    "id": f"rem.{nid}.001",
                    "node_id": nid,
                    "status": "open",
                    "description": "redo the drill",
                    "created_at": "2026-08-20T10:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        repo,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": f"rev.{nid}.001",
                    "node_id": nid,
                    "status": "scheduled",
                    "scheduled_for": "2026-08-01",
                    "created_at": "2026-08-01T10:00:00+00:00",
                }
            ]
        },
    )
    _, body, _ = views.node_body(repo, nid)
    # The records are reported, and the learner can act on them here.
    assert "redo the drill" in body
    assert _actions(body)


def test_a_stale_resource_carries_an_action(repo):
    """A stale resource is reported and the learner can act on it."""
    view = load_context_lenient(repo)
    target = None
    for nid, res in view.resources_by_node.items():
        if res:
            target = nid
            break
    assert target
    doc = yaml.safe_load(
        (repo / "graph" / "resources.yaml").read_text(encoding="utf-8")
    )
    for r in doc["resources"]:
        if target in (r.get("supports") or []):
            r["last_verified"] = "2020-01-01"
            if "broken" in r:
                del r["broken"]
    _write_yaml(repo, "graph/resources.yaml", doc)
    _, body, _ = views.node_body(repo, target)
    assert "stale" in body
    assert _actions(body)


# --- no surface ever leaves the product -------------------------------------------


def test_no_surface_sends_the_learner_to_a_terminal(repo):
    """No learner-facing surface names a command or the word terminal."""
    _overdue_repo(repo)
    nid = _first(repo, state="available")
    _set_state(repo, nid, "passed")
    bodies = [
        views.home_body(repo)[1],
        views.node_body(repo, nid)[1],
        views.next_body(repo, {})[1],
        views.reviews_body(repo)[1],
        views.session_body(repo)[1],
    ]
    for body in bodies:
        assert "<script" not in body.lower()
        assert re.search(r"\bCLI\b", body) is None
        assert "terminal" not in body.lower()
        assert "skilltrace " not in body.lower()
        for m in re.finditer(r".{0,120}(?:ask there|over there|run the).{0,120}", body):
            assert forbidden_matches(m.group(0)) == []
