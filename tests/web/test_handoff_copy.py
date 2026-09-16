"""T-HandoffCopy â€” locked CLI-handoff copy at daily-loop dead-ends (map #258).

Locked in G-StudyDayHandoffs #263: one slotted sentence, P3.1-clean, plain
muted copy, omittable, at targeted dead-ends only. No new route, no literal
command names, never the bare word CLI. pytest green, no <script>.
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
HANDOFF = "continues in your terminal"
TAIL = "ask there for the exact form"


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
    _write_yaml(root, "execution/reviews.yaml", {"reviews": [{
        "id": f"rev.{nid}.001", "node_id": nid, "status": "scheduled",
        "scheduled_for": "2020-01-01", "created_at": "2020-01-01T10:00:00+00:00",
    }]})
    return nid


def test_passed_do_this_next_carries_handoff(repo):
    nid = _first(repo, state="available")
    _set_state(repo, nid, "passed")
    view = load_context_lenient(repo)
    title = view.node_map[nid].title
    _, body, _ = views.node_body(repo, nid)
    assert 'data-intent="schedule_review"' in body
    assert HANDOFF in body and TAIL in body
    assert title in body[body.index(HANDOFF) - 300: body.index(HANDOFF) + 100]
    assert forbidden_matches(body[body.index(HANDOFF) - 300: body.index(HANDOFF) + 200]) == []


def test_pressure_overdue_carries_handoff_and_zero_stays_calm(repo):
    _, calm, _ = views.home_body(repo)
    assert "Nothing is waiting" in calm
    assert HANDOFF not in calm
    _overdue_repo(repo)
    _, body, _ = views.home_body(repo)
    assert "Waiting quietly" in body
    assert HANDOFF in body and TAIL in body


def test_drilldown_tables_carry_handoffs(repo):
    view = load_context_lenient(repo)
    specced = sorted(n.id for n in view.nodes if view.specs_by_node.get(n.id))
    nid = specced[0]
    _write_yaml(repo, "evidence/attempts.yaml", {"attempts": [{
        "id": f"att.{nid}.001", "node_id": nid, "outcome": "passed",
        "created_at": "2026-08-20T10:00:00+00:00"}]})
    _write_yaml(repo, "execution/remediation_actions.yaml", {"remediation_actions": [{
        "id": f"rem.{nid}.001", "node_id": nid, "status": "open",
        "description": "redo the drill", "created_at": "2026-08-20T10:00:00+00:00"}]})
    _write_yaml(repo, "execution/reviews.yaml", {"reviews": [{
        "id": f"rev.{nid}.001", "node_id": nid, "status": "scheduled",
        "scheduled_for": "2026-08-01", "created_at": "2026-08-01T10:00:00+00:00"}]})
    _, body, _ = views.node_body(repo, nid)
    assert body.count(HANDOFF) >= 3  # attempt + remediation + review (+ maybe resource)


def test_resource_broken_stale_carries_handoff(repo):
    view = load_context_lenient(repo)
    target = None
    for nid, res in view.resources_by_node.items():
        if res:
            target = nid
            break
    assert target
    # force stale by backdating every resource for the target node
    doc = yaml.safe_load((repo / "graph" / "resources.yaml").read_text(encoding="utf-8"))
    for r in doc["resources"]:
        if target in (r.get("supports") or []):
            r["last_verified"] = "2020-01-01"
            if "broken" in r:
                del r["broken"]
    _write_yaml(repo, "graph/resources.yaml", doc)
    _, body, _ = views.node_body(repo, target)
    assert "stale" in body
    assert HANDOFF in body


def test_handoff_never_uses_cli_word_commands_or_script(repo):
    _overdue_repo(repo)
    nid = _first(repo, state="available")
    _set_state(repo, nid, "passed")
    bodies = [views.home_body(repo)[1], views.node_body(repo, nid)[1],
              views.next_body(repo, {})[1]]
    for body in bodies:
        assert "<script" not in body.lower()
        assert re.search(r"\bCLI\b", body) is None
        assert "skilltrace " not in body
        for m in re.finditer(r".{0,120}continues in your terminal.{0,120}", body):
            assert forbidden_matches(m.group(0)) == []
