"""`skilltrace report <target>` — unified report subcommand family tests (issue #42).

Tests registration, read-only contract (no audit event written), exit-0 on valid
data, and Mentor voice output across all 5 report subcommands:
- `skilltrace report progress`
- `skilltrace report blockers`
- `skilltrace report reviews`
- `skilltrace report evidence [--node-id <id>]`
- `skilltrace report resources`
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


@pytest.mark.parametrize(
    "cmd_name",
    [
        "report progress",
        "report blockers",
        "report reviews",
        "report evidence",
        "report resources",
    ],
)
def test_report_subcommands_are_registered_read_only(cmd_name: str):
    command = cli.REGISTRY.get(cmd_name)
    assert command is not None
    assert command.kind.value == "read_only"


@pytest.mark.parametrize(
    "argv",
    [
        ["report", "progress"],
        ["report", "blockers"],
        ["report", "reviews"],
        ["report", "evidence"],
        ["report", "evidence", "--node-id", "math.arithmetic.order_operations_01"],
        ["report", "resources"],
    ],
)
def test_report_subcommands_log_no_audit_events(tmp_path, argv):
    root = _seed_repo(tmp_path)
    initial_events = len(load_events(root))
    rc = cli.run(argv, root=root)
    assert rc == 0
    events = load_events(root)
    assert len(events) == initial_events


# --- 1. Report: Progress -----------------------------------------------------


def test_report_progress_seed_data(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["report", "progress"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "Your Learning Journey" in out
    assert "You have completed 0 of 81 skills (0 mastered, 0 passed) across 0 study sessions (0.0 hours)." in out
    assert "Track Breakdown" in out
    assert "Math Foundations" in out
    assert "Programming & Tooling" in out
    assert "Data & Communication" in out
    assert "Cross-Cutting & Portfolio" in out
    assert "Mentor Note:" in out


def test_report_progress_with_completed_nodes_and_sessions(tmp_path, capsys):
    root = _seed_repo(tmp_path)

    # Mark some nodes as passed/mastered
    state_doc = {
        "progress": {
            "math.arithmetic.order_operations_01": {
                "state": "mastered",
                "changed_at": "2026-08-01T10:00:00Z",
                "transitions": {"passed": "2026-07-15T10:00:00Z", "mastered": "2026-08-01T10:00:00Z"},
            },
            "math.algebra.variables_expressions_01": {
                "state": "passed",
                "changed_at": "2026-08-10T10:00:00Z",
                "transitions": {"passed": "2026-08-10T10:00:00Z"},
            },
            "programming.python.environment_01": {
                "state": "active",
                "changed_at": "2026-08-15T10:00:00Z",
                "transitions": {"active": "2026-08-15T10:00:00Z"},
            },
        }
    }
    _write_yaml(root, "graph/state.yaml", state_doc)

    # Add sessions and work items
    sessions_doc = {
        "sessions": [
            {"id": "ses.2026-08-10.001", "status": "completed", "started_at": "2026-08-10T10:00:00Z", "ended_at": "2026-08-10T11:30:00Z"},
            {"id": "ses.2026-08-15.001", "status": "open", "started_at": "2026-08-15T10:00:00Z"},
        ]
    }
    _write_yaml(root, "execution/sessions.yaml", sessions_doc)

    work_doc = {
        "session_work": [
            {"id": "wrk.001", "session_id": "ses.2026-08-10.001", "node_id": "math.algebra.variables_expressions_01", "created_at": "2026-08-10T10:30:00Z", "minutes": 90},
            {"id": "wrk.002", "session_id": "ses.2026-08-15.001", "node_id": "programming.python.environment_01", "created_at": "2026-08-15T10:15:00Z", "minutes": 30},
        ]
    }
    _write_yaml(root, "execution/session_work.yaml", work_doc)

    rc = cli.run(["report", "progress"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "You have completed 2 of 81 skills (1 mastered, 1 passed) across 2 study sessions (2.0 hours)." in out
    assert "Currently working on Run Python locally. Next up: finish active evidence submissions." in out


# --- 2. Report: Blockers -----------------------------------------------------


def test_report_blockers_seed_data(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["report", "blockers"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "Where you are stuck" in out
    assert "You have no open blockers -- smooth sailing!" in out
    assert "No open obstacles logged." in out
    assert "No resolved blockers in history." in out


def test_report_blockers_with_active_obstacles_and_rescue_nodes(tmp_path, capsys):
    root = _seed_repo(tmp_path)

    # Blocker on a node that has a remediation edge (math.algebra.linear_equations_01)
    blockers_doc = {
        "blockers": [
            {
                "id": "blk.math.algebra.linear_equations_01.001",
                "node_id": "math.algebra.linear_equations_01",
                "status": "open",
                "description": "Fractions in linear equations causing calculation errors",
                "created_at": "2026-08-18T10:00:00Z",
            },
            {
                "id": "blk.math.arithmetic.order_operations_01.001",
                "node_id": "math.arithmetic.order_operations_01",
                "status": "resolved",
                "description": "Parenthesis nested evaluation confusion",
                "created_at": "2026-08-10T10:00:00Z",
                "resolved_at": "2026-08-12T10:00:00Z",
                "resolution_summary": "Completed 10 Khan Academy practice problems",
            },
        ]
    }
    _write_yaml(root, "execution/blockers.yaml", blockers_doc)

    actions_doc = {
        "remediation_actions": [
            {
                "id": "rem.math.algebra.linear_equations_01.001",
                "blocker_id": "blk.math.algebra.linear_equations_01.001",
                "node_id": "math.algebra.linear_equations_01",
                "status": "open",
                "description": "Practice 5 fraction clearing problems",
                "created_at": "2026-08-19T10:00:00Z",
            }
        ]
    }
    _write_yaml(root, "execution/remediation_actions.yaml", actions_doc)

    rc = cli.run(["report", "blockers"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "You have 1 open blocker(s) holding back your progress." in out
    assert "One has an active rescue node ready in your graph." in out
    assert "Solve one-variable linear equations" in out
    assert "Obstacle: Fractions in linear equations causing calculation errors" in out
    assert "Where to turn: Rescue node 'math.arithmetic.fractions_01' is now prioritized in `skilltrace next`." in out
    assert "Intervention: Practice 5 fraction clearing problems" in out
    assert "Do this next: `skilltrace blocker resolve blk.math.algebra.linear_equations_01.001 --summary \"...\"`" in out
    assert "Apply order of operations -- stuck 2 days; resolved via Completed 10 Khan Academy practice problems" in out


# --- 3. Report: Reviews ------------------------------------------------------


def test_report_reviews_seed_data(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["report", "reviews"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "Retention & Mastery Health" in out
    assert "No reviews currently scheduled." in out
    assert "No completed reviews in history." in out


def test_report_reviews_with_scheduled_and_completed(tmp_path, capsys):
    root = _seed_repo(tmp_path)

    state_doc = {
        "progress": {
            "math.arithmetic.order_operations_01": {
                "state": "passed",
                "changed_at": "2026-07-15T10:00:00Z",
                "transitions": {"passed": "2026-07-15T10:00:00Z"},
            }
        }
    }
    _write_yaml(root, "graph/state.yaml", state_doc)

    reviews_doc = {
        "reviews": [
            {
                "id": "rev.math.arithmetic.order_operations_01.001",
                "node_id": "math.arithmetic.order_operations_01",
                "status": "scheduled",
                "scheduled_for": "2026-08-01",
                "created_at": "2026-07-15T10:00:00Z",
            },
            {
                "id": "rev.math.algebra.variables_expressions_01.001",
                "node_id": "math.algebra.variables_expressions_01",
                "status": "completed",
                "scheduled_for": "2026-07-20",
                "completed_at": "2026-07-21T10:00:00Z",
                "created_at": "2026-07-10T10:00:00Z",
                "outcome": "satisfactory",
                "result_summary": "10/10 correct without hesitation.",
            },
            {
                "id": "rev.prog.python.local_environment_01.001",
                "node_id": "prog.python.local_environment_01",
                "status": "cancelled",
                "scheduled_for": "2026-07-25",
                "cancelled_at": "2026-07-24T10:00:00Z",
                "created_at": "2026-07-15T10:00:00Z",
                "cancel_reason": "Rescheduled for consolidation week",
            },
        ]
    }
    _write_yaml(root, "execution/reviews.yaml", reviews_doc)

    rc = cli.run(["report", "reviews"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "Retention & Mastery Health" in out
    assert "Apply order of operations" in out
    assert "Why this matters: Passed node awaiting retention verification." in out
    assert "Do this next: `skilltrace review complete rev.math.arithmetic.order_operations_01.001 --outcome satisfactory --summary \"...\"`" in out
    assert "[OK] Work with variables and algebraic expressions -- 10/10 correct without hesitation." in out
    assert "[-] rev.prog.python.local_environment_01.001 cancelled" in out
    assert "Rescheduled for consolidation week" in out


# --- 4. Report: Evidence -----------------------------------------------------


def test_report_evidence_seed_data(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["report", "evidence"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "Evidence & Proof Trail" in out
    assert "Apply order of operations (`math.arithmetic.order_operations_01`) / State: AVAILABLE" in out
    assert "Gate: Learner manual review against rubric" in out
    assert "Required Order of operations problem-set evidence: NOT YET SUBMITTED" in out


def test_report_evidence_single_node_filter(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    node_id = "math.arithmetic.order_operations_01"
    rc = cli.run(["report", "evidence", "--node-id", node_id], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert f"Apply order of operations (`{node_id}`)" in out
    assert "math.algebra" not in out


def test_report_evidence_unknown_node_fails_cleanly(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["report", "evidence", "--node-id", "nonexistent.node_01"], root=root)
    assert rc == 1
    out = capsys.readouterr().out
    assert "report evidence: FAILED -- unknown node nonexistent.node_01." in out


def test_report_evidence_with_superseded_and_accepted_records(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    node_id = "tooling.git.commit_workflow_01"
    spec_id = "spec.tooling.git.commit_workflow"

    # Objective gate node
    records_doc = {
        "evidence_records": [
            {
                "id": f"ev.{node_id}.001",
                "artifact_spec_id": spec_id,
                "location": "artifacts/repo_v1",
                "accepted": False,
                "accepted_by": "objective_gate",
                "artifact_hash": "abc1",
                "note": "Initial submission missing remote origin",
                "created_at": "2026-08-10T10:00:00Z",
            },
            {
                "id": f"ev.{node_id}.002",
                "artifact_spec_id": spec_id,
                "location": "artifacts/repo_v2",
                "accepted": True,
                "accepted_by": "objective_gate",
                "artifact_hash": "abc2",
                "note": "Configured origin and initial commit",
                "supersedes": f"ev.{node_id}.001",
                "supersede_reason": "Fixed origin URL",
                "created_at": "2026-08-11T10:00:00Z",
            },
        ]
    }
    _write_yaml(root, "evidence/evidence_records.yaml", records_doc)

    rc = cli.run(["report", "evidence", "--node-id", node_id], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "Objective verification command" in out
    assert f"ev.{node_id}.001 (superseded): Initial submission missing remote origin (superseded by ev.{node_id}.002)" in out
    assert f"ev.{node_id}.002 (accepted): Configured origin and initial commit (artifacts/repo_v2)" in out
    assert "Pass-eligible! Ready to mark passed" in out


# --- 5. Report: Resources ----------------------------------------------------


def test_report_resources_seed_data(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["report", "resources"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    assert "resource-report: 29 resource(s), 81 node(s)" in out
    assert "khan-arithmetic" in out
    assert "coverage: 81/81 node(s) have a linked resource." in out
