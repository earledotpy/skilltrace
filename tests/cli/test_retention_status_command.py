"""`skilltrace retention status` — CLI command-output tests (spec §6.4).

Asserts presence/section rather than exact text — the surface is the
command's own concern. Drives `cli.run(...)` against a disposable repo
seeded with the shipped `policy/retention_model.yaml`.
"""

from __future__ import annotations

import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from skilltrace import cli
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]
PASSED_NODE = "math.arithmetic.order_operations_01"
MASTERED_NODE = "math.algebra.variables_expressions_01"


def _seed_repo(tmp_path: Path) -> Path:
    """Copy the shipped policy + a minimal graph/state so the command has data."""
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "evidence", tmp_path / "evidence")
    shutil.copytree(REPO_ROOT / "execution", tmp_path / "execution")
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    return tmp_path


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


# --- Registration ----------------------------------------------------------


def test_retention_status_is_registered_read_only():
    command = cli.REGISTRY.get("retention status")
    assert command is not None
    assert command.kind.value == "read_only"


def test_retention_status_logs_no_audit_event(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    initial_events = len(load_events(root))
    rc = cli.run(["retention", "status"], root=root)
    assert rc == 0
    assert len(load_events(root)) == initial_events


# --- Output shape on seed (no passed/mastered nodes yet) ------------------


def test_retention_status_seed_data_is_a_clean_zero(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["retention", "status"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "no passed or mastered nodes yet" in out


# --- One passed / one mastered node, with the documented columns ----------


def _passed_mastered_state(pass_offset: int = -30) -> dict:
    return {
        "progress": {
            PASSED_NODE: {
                "state": "passed",
                "changed_at": "2026-07-15T10:00:00Z",
                "transitions": {"passed": (date.today() + timedelta(days=pass_offset)).isoformat() + "T10:00:00Z"},
            },
            MASTERED_NODE: {
                "state": "mastered",
                "changed_at": "2026-08-01T10:00:00Z",
                "transitions": {
                    "passed": (date.today() + timedelta(days=pass_offset - 5)).isoformat() + "T10:00:00Z",
                    "mastered": "2026-08-01T10:00:00Z",
                },
            },
        }
    }


def test_retention_status_renders_one_row_per_passed_mastered_node(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    _write_yaml(root, "graph/state.yaml", _passed_mastered_state())

    rc = cli.run(["retention", "status"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert PASSED_NODE in out
    assert MASTERED_NODE in out
    # Each row carries the documented columns (presence only).
    assert "anchor=pass@" in out
    assert "half_life=" in out
    assert "confidence=" in out
    assert "suggested_next=" in out


def test_retention_status_below_threshold_marks_row(tmp_path, capsys):
    """A pass 60 days ago lands below the default 7-day half-life threshold."""
    root = _seed_repo(tmp_path)
    _write_yaml(root, "graph/state.yaml", _passed_mastered_state(pass_offset=-60))

    rc = cli.run(["retention", "status"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "BELOW THRESHOLD" in out


# --- --node-id ------------------------------------------------------------


def test_retention_status_node_id_filter_renders_one_row(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    _write_yaml(root, "graph/state.yaml", _passed_mastered_state())

    rc = cli.run(["retention", "status", "--node-id", PASSED_NODE], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert PASSED_NODE in out
    assert MASTERED_NODE not in out


def test_retention_status_unknown_node_fails_cleanly(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["retention", "status", "--node-id", "does.not.exist"], root=root)
    assert rc == 1
    out = capsys.readouterr().out
    assert "unknown node does.not.exist" in out


def test_retention_status_node_id_for_unpassed_node_says_so(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    _write_yaml(
        root,
        "graph/state.yaml",
        {"progress": {PASSED_NODE: {"state": "available", "changed_at": "2026-07-15T10:00:00Z"}}},
    )
    rc = cli.run(["retention", "status", "--node-id", PASSED_NODE], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "not passed or mastered" in out
