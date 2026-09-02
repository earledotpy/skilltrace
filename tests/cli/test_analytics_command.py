"""`skilltrace analytics` command family tests (issue #128).

Tests registration, read-only contract (no audit event written), exit-0 on
valid data, and presence of the right sections in each subcommand's output
(T-TestArch D4 — presence/section only at the CLI layer, not exact text).

Pattern mirrors test_report_command.py: disposable repo via _seed_repo,
_write_yaml helper, in-process cli.run, load_events read-only assertion.
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
    """Disposable copy of the live seed repo (graph + evidence + execution + policy)."""
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "evidence", tmp_path / "evidence")
    shutil.copytree(REPO_ROOT / "execution", tmp_path / "execution")
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    return tmp_path


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _seed_with_sessions(tmp_path: Path) -> Path:
    """Seed repo with enough sessions to clear the min_sessions_for_full_data=3 threshold."""
    root = _seed_repo(tmp_path)
    sessions_doc = {
        "sessions": [
            {"id": "ses.2026-08-15.001", "status": "completed",
             "started_at": "2026-08-15T10:00:00Z", "ended_at": "2026-08-15T11:00:00Z"},
            {"id": "ses.2026-08-20.001", "status": "completed",
             "started_at": "2026-08-20T10:00:00Z", "ended_at": "2026-08-20T11:00:00Z"},
            {"id": "ses.2026-08-25.001", "status": "completed",
             "started_at": "2026-08-25T10:00:00Z", "ended_at": "2026-08-25T11:30:00Z"},
        ]
    }
    _write_yaml(root, "execution/sessions.yaml", sessions_doc)
    work_doc = {
        "session_work": [
            {"id": "wrk.001", "session_id": "ses.2026-08-15.001",
             "node_id": "math.arithmetic.order_operations_01",
             "created_at": "2026-08-15T10:30:00Z", "minutes": 30},
            {"id": "wrk.002", "session_id": "ses.2026-08-20.001",
             "node_id": "math.algebra.variables_expressions_01",
             "created_at": "2026-08-20T10:30:00Z", "minutes": 45},
            {"id": "wrk.003", "session_id": "ses.2026-08-25.001",
             "node_id": "programming.python.environment_01",
             "created_at": "2026-08-25T10:30:00Z", "minutes": 60},
        ]
    }
    _write_yaml(root, "execution/session_work.yaml", work_doc)
    return root


# ---------------------------------------------------------------------------
# Registration and kind
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cmd_name",
    [
        "analytics",
        "analytics velocity",
        "analytics blockers",
        "analytics reviews",
        "analytics evidence",
    ],
)
def test_analytics_commands_are_registered_read_only(cmd_name: str):
    command = cli.REGISTRY.get(cmd_name)
    assert command is not None
    assert command.kind.value == "read_only"


# ---------------------------------------------------------------------------
# Read-only contract: no audit events appended
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["analytics"],
        ["analytics", "velocity"],
        ["analytics", "blockers"],
        ["analytics", "reviews"],
        ["analytics", "evidence"],
    ],
)
def test_analytics_commands_log_no_audit_events(tmp_path, argv):
    root = _seed_repo(tmp_path)
    initial_events = len(load_events(root))
    rc = cli.run(argv, root=root)
    assert rc == 0
    assert len(load_events(root)) == initial_events


# ---------------------------------------------------------------------------
# Umbrella: all four theme sections present
# ---------------------------------------------------------------------------


def test_analytics_umbrella_contains_all_four_themes(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["analytics"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "ANALYTICS" in out
    assert "VELOCITY" in out
    assert "BLOCKERS" in out
    assert "REVIEWS" in out
    assert "EVIDENCE" in out


def test_analytics_umbrella_with_sessions_no_limited_advisory(tmp_path, capsys):
    root = _seed_with_sessions(tmp_path)
    rc = cli.run(["analytics"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    # 3 sessions in window >= min_sessions_for_full_data=3, so no "Limited data" advisory
    assert "Limited data" not in out


def test_analytics_umbrella_below_threshold_shows_advisory(tmp_path, capsys):
    """With 2 sessions (< 3 threshold), [advisory] Limited data line is printed."""
    root = _seed_repo(tmp_path)
    sessions_doc = {
        "sessions": [
            {"id": "ses.2026-08-20.001", "status": "completed",
             "started_at": "2026-08-20T10:00:00Z", "ended_at": "2026-08-20T11:00:00Z"},
            {"id": "ses.2026-08-25.001", "status": "completed",
             "started_at": "2026-08-25T10:00:00Z", "ended_at": "2026-08-25T11:00:00Z"},
        ]
    }
    _write_yaml(root, "execution/sessions.yaml", sessions_doc)
    rc = cli.run(["analytics"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "[advisory]" in out
    assert "Limited data" in out


# ---------------------------------------------------------------------------
# Per-theme subcommands: section header present, exit 0
# ---------------------------------------------------------------------------


def test_analytics_velocity_section_present(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["analytics", "velocity"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "VELOCITY" in out


def test_analytics_blockers_section_present(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["analytics", "blockers"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "BLOCKERS" in out


def test_analytics_reviews_section_present(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["analytics", "reviews"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "REVIEWS" in out


def test_analytics_evidence_section_present(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["analytics", "evidence"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "EVIDENCE" in out


# ---------------------------------------------------------------------------
# --days flag overrides the default window
# ---------------------------------------------------------------------------


def test_analytics_velocity_days_flag(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["analytics", "velocity", "--days", "7"], root=root)
    assert rc == 0


# ---------------------------------------------------------------------------
# --group-by flag accepted
# ---------------------------------------------------------------------------


def test_analytics_velocity_group_by_track(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["analytics", "velocity", "--group-by", "track"], root=root)
    assert rc == 0


# ---------------------------------------------------------------------------
# --state flag (repeatable, OR semantics)
# ---------------------------------------------------------------------------


def test_analytics_state_filter_flag(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    rc = cli.run(["analytics", "--state", "active", "--state", "passed"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "ANALYTICS" in out


# ---------------------------------------------------------------------------
# Velocity with sessions: counts surface in output
# ---------------------------------------------------------------------------


def test_analytics_velocity_with_sessions_shows_counts(tmp_path, capsys):
    root = _seed_with_sessions(tmp_path)
    rc = cli.run(["analytics", "velocity"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    # 3 sessions in window
    assert "3" in out


# ---------------------------------------------------------------------------
# Reviews: overdue banner surfaces when overdue reviews exist
# ---------------------------------------------------------------------------


def test_analytics_reviews_overdue_banner(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    reviews_doc = {
        "reviews": [
            {
                "id": "rev.math.arithmetic.order_operations_01.001",
                "node_id": "math.arithmetic.order_operations_01",
                "status": "scheduled",
                "scheduled_for": "2026-08-01",
                "created_at": "2026-07-15T10:00:00Z",
            }
        ]
    }
    _write_yaml(root, "execution/reviews.yaml", reviews_doc)
    rc = cli.run(["analytics", "reviews"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "REVIEWS" in out
    assert "overdue" in out.lower()


# ---------------------------------------------------------------------------
# Evidence: gap flagged in output
# ---------------------------------------------------------------------------


def test_analytics_evidence_gap_in_output(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    # evidence_records.yaml is already empty in the seed repo
    rc = cli.run(["analytics", "evidence"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "EVIDENCE" in out
    # All nodes with required specs have no accepted records → gaps expected
    assert "GAP" in out


# ---------------------------------------------------------------------------
# Blockers: open blocker surfaces in output
# ---------------------------------------------------------------------------


def test_analytics_blockers_with_open_blocker(tmp_path, capsys):
    root = _seed_repo(tmp_path)
    blockers_doc = {
        "blockers": [
            {
                "id": "blk.math.arithmetic.order_operations_01.001",
                "node_id": "math.arithmetic.order_operations_01",
                "status": "open",
                "description": "Cannot parse nested parentheses",
                "created_at": "2026-08-20T10:00:00Z",
            }
        ]
    }
    _write_yaml(root, "execution/blockers.yaml", blockers_doc)
    rc = cli.run(["analytics", "blockers"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "BLOCKERS" in out
    assert "1" in out  # open_count



# ---------------------------------------------------------------------------
# analytics_warnings() surface — warning block renders when threshold tripped
# (T-TestArch D5, issue #129)
# ---------------------------------------------------------------------------


def test_analytics_umbrella_warning_block_renders_when_blockers_spike(tmp_path, capsys):
    """analytics_warnings() block appears when open_count >= blockers_active_threshold (3)."""
    root = _seed_with_sessions(tmp_path)
    blockers_doc = {
        "blockers": [
            {
                "id": f"blk.math.arithmetic.order_operations_01.{n:03d}",
                "node_id": "math.arithmetic.order_operations_01",
                "status": "open",
                "description": f"stuck on step {n}",
                "created_at": "2026-08-01T10:00:00Z",
            }
            for n in range(1, 4)  # 3 open blockers >= threshold
        ]
    }
    _write_yaml(root, "execution/blockers.yaml", blockers_doc)
    rc = cli.run(["analytics"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    # At least one [advisory] line must mention blockers
    advisory_lines = [ln for ln in out.splitlines() if ln.startswith("[advisory]")]
    assert any("blocker" in ln.lower() for ln in advisory_lines), (
        f"Expected a blocker advisory line; got advisory lines: {advisory_lines}"
    )


def test_analytics_umbrella_no_warning_block_when_all_healthy(tmp_path, capsys):
    """analytics command exits 0 and no Limited-data advisory with sufficient sessions."""
    root = _seed_with_sessions(tmp_path)
    rc = cli.run(["analytics"], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    # The limited-data advisory is absent when sessions >= min_sessions threshold
    assert "Limited data" not in out
    # All four theme headers are still present regardless of any advisory warnings
    assert "VELOCITY" in out
    assert "BLOCKERS" in out
    assert "REVIEWS" in out
    assert "EVIDENCE" in out
