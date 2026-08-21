"""`skilltrace node <node_id>` — Mentor voice node detail view (issue #41).

Tests the command registration, exit gate on seed data, read-only behavior
(no audit event written), and Mentor voice output across all states (available,
locked, active, passed, mastered), including evidence summaries, resources,
blockers, open sessions, and error handling.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from skilltrace import cli
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_repo(tmp_path: Path) -> Path:
    """Disposable copy of the seed repo."""
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "evidence", tmp_path / "evidence")
    shutil.copytree(REPO_ROOT / "execution", tmp_path / "execution")
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    return tmp_path


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


# --- Registration and read-only contract -------------------------------------


def test_node_is_registered_read_only():
    command = cli.REGISTRY.get("node")
    assert command is not None
    assert command.kind.value == "read_only"


def test_node_logs_no_audit_events(tmp_path):
    root = _seed_repo(tmp_path)
    initial_events = len(load_events(root))
    rc = cli.run(["node", "math.arithmetic.order_operations_01"], root=root)
    assert rc == 0
    events = load_events(root)
    assert len(events) == initial_events


# --- Exit gate on seed data --------------------------------------------------


def test_exit_gate_seed_node_order_operations(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["node", "math.arithmetic.order_operations_01"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    # Mentor voice sections
    assert "THIS SKILL" in out
    assert "Apply order of operations" in out
    assert "[Ready to start]" in out
    assert "You're clear to begin Apply order of operations" in out
    assert "Where to learn" in out
    assert "Khan Arithmetic -- https://www.khanacademy.org/math/arithmetic" in out
    assert "How to proceed" in out
    assert "0 of 3 Order of operations problem-set evidence." in out
    assert "DO THIS NEXT" in out
    assert "Start studying Apply order of operations" in out


def test_seed_locked_node_detail(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["node", "math.algebra.linear_equations_01"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "THIS SKILL" in out
    assert "Solve one-variable linear equations" in out
    assert "[Locked]" in out
    assert "still comes first" in out
    assert "Where to learn" in out
    assert "Khan Algebra -- https://www.khanacademy.org/math/algebra" in out
    assert "How to proceed" in out
    assert "DO THIS NEXT" in out
    assert "Work on Work with variables and algebraic expressions first" in out
    assert "Passing this opens the door to" in out


# --- Error conditions --------------------------------------------------------


def test_unknown_node_fails_with_exit_one(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["node", "nonexistent.node_01"], root=root)
    assert rc == 1
    out = capsys.readouterr().out
    assert "node: FAILED -- unknown node nonexistent.node_01." in out


def test_malformed_graph_fails_cleanly(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    # Corrupt a node file
    (root / "graph" / "nodes" / "math.arithmetic.order_operations_01.md").write_text(
        "no frontmatter", encoding="utf-8"
    )
    rc = cli.run(["node", "math.arithmetic.order_operations_01"], root=root)
    assert rc == 1
    out = capsys.readouterr().out
    assert "node: FAILED -- " in out


# --- State-specific rendering (Active, Passed, Mastered, Blockers) ------------


def test_active_node_with_open_session_and_blocker(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    node_id = "math.arithmetic.order_operations_01"

    # Set state to active in state.yaml
    state_doc = {
        "progress": {
            node_id: {
                "state": "active",
                "changed_at": "2026-08-20T10:00:00Z",
                "transitions": {"active": "2026-08-20T10:00:00Z"},
            }
        }
    }
    _write_yaml(root, "graph/state.yaml", state_doc)

    # Add an open session
    sessions_doc = {
        "sessions": [
            {
                "id": "ses.2026-08-20.001",
                "status": "open",
                "started_at": "2026-08-20T10:00:00Z",
            }
        ]
    }
    _write_yaml(root, "execution/sessions.yaml", sessions_doc)

    # Add an open blocker
    blockers_doc = {
        "blockers": [
            {
                "id": "blk.math.arithmetic.order_operations_01.001",
                "node_id": node_id,
                "status": "open",
                "description": "Confused about exponent precedence",
                "created_at": "2026-08-20T10:15:00Z",
            }
        ]
    }
    _write_yaml(root, "execution/blockers.yaml", blockers_doc)

    rc = cli.run(["node", node_id], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "[In progress]" in out
    assert "You're already working on Apply order of operations." in out
    assert "A study session is open." in out
    assert "Blocker: Confused about exponent precedence." in out
    assert "DO THIS NEXT" in out
    assert "Submit your next piece of evidence" in out


def test_passed_node_rendering(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    node_id = "math.arithmetic.order_operations_01"

    state_doc = {
        "progress": {
            node_id: {
                "state": "passed",
                "changed_at": "2026-08-20T12:00:00Z",
                "transitions": {
                    "active": "2026-08-20T10:00:00Z",
                    "passed": "2026-08-20T12:00:00Z",
                },
            }
        }
    }
    _write_yaml(root, "graph/state.yaml", state_doc)

    rc = cli.run(["node", node_id], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "[Passed]" in out
    assert "Apply order of operations is passed -- all evidence requirements are met." in out
    assert "DO THIS NEXT" in out
    assert f"Schedule a review: `skilltrace review schedule {node_id} --date <YYYY-MM-DD>`" in out


def test_mastered_node_rendering(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    node_id = "math.arithmetic.order_operations_01"

    state_doc = {
        "progress": {
            node_id: {
                "state": "mastered",
                "changed_at": "2026-08-20T15:00:00Z",
                "transitions": {
                    "active": "2026-08-20T10:00:00Z",
                    "passed": "2026-08-20T12:00:00Z",
                    "mastered": "2026-08-20T15:00:00Z",
                },
            }
        }
    }
    _write_yaml(root, "graph/state.yaml", state_doc)

    rc = cli.run(["node", node_id], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "[Mastered]" in out
    assert "Apply order of operations is mastered." in out
    assert "DO THIS NEXT" in out
    assert "Nothing further needed" in out


def test_node_without_linked_resources(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    # Empty out resources
    _write_yaml(root, "graph/resources.yaml", {"resources": []})

    rc = cli.run(["node", "math.arithmetic.order_operations_01"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Where to learn" in out
    assert "(no resources linked to this skill)" in out
