"""`skilltrace today` — the Mentor-voice daily study view (issue #43).

Per the #30 resolution: a conversational brief of the study state plus guided
Where to learn / How to proceed / Do this next. Read-only: drives the real CLI
in-process through `cli.run(argv, root=...)`, asserting only exit codes,
stdout, and the event log.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from _builders import write_node as _write_node

from skilltrace import cli
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_yaml(root: Path, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


@pytest.fixture
def today_repo(tmp_path: Path) -> Path:
    """A disposable repo: shipped policy, empty evidence/resources, one available node."""
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    _write_yaml(tmp_path, "evidence/artifact_specs.yaml", {"artifact_specs": []})
    _write_yaml(tmp_path, "evidence/validation_gates.yaml", {"validation_gates": []})
    _write_yaml(tmp_path, "evidence/evidence_records.yaml", {"evidence_records": []})
    _write_yaml(tmp_path, "evidence/attempts.yaml", {"attempts": []})
    _write_yaml(tmp_path, "graph/resources.yaml", {"resources": []})
    _write_node(tmp_path, "testing.today.subject_01")
    _write_yaml(
        tmp_path,
        "graph/state.yaml",
        {"progress": {"testing.today.subject_01": {"state": "available"}}},
    )
    return tmp_path


# --- Registration and exit gate ----------------------------------------------


def test_today_is_registered_read_only():
    command = cli.REGISTRY.get("today")
    assert command is not None
    assert command.kind.value == "read_only"


def test_shipped_repo_today_exits_zero(capsys):
    # The exit-gate command: today on the shipped seed repo is exit 0.
    rc = cli.run(["today"], root=REPO_ROOT)
    out = capsys.readouterr().out
    assert rc == 0
    assert out.strip().splitlines()[0] == "TODAY"


def test_today_is_read_only_and_logs_nothing(today_repo, capsys):
    rc = cli.run(["today"], root=today_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert load_events(today_repo) == []
    assert "TODAY" in out
    assert "Where to learn (top focus)" in out
    assert "DO THIS NEXT" in out


# --- Study-day synthesis -----------------------------------------------------


def test_today_names_the_top_recommendation_when_no_session(today_repo, capsys):
    rc = cli.run(["today"], root=today_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "no session open" in out
    assert "Title for testing.today.subject_01" in out
    assert "Start studying testing.today.subject_01" in out


def test_today_picks_up_the_open_session_as_focus(today_repo, capsys):
    # Open a session with a work item on the available node.
    _write_yaml(
        today_repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": "sess.001",
                    "status": "open",
                    "started_at": "2020-01-01T00:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        today_repo,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": "work.001",
                    "session_id": "sess.001",
                    "node_id": "testing.today.subject_01",
                    "created_at": "2020-01-01T00:05:00+00:00",
                }
            ]
        },
    )
    rc = cli.run(["today"], root=today_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "session open" in out
    assert "Title for testing.today.subject_01" in out


def test_today_reports_overdue_review_pressure(today_repo, capsys):
    from datetime import date, datetime, timedelta, timezone

    due = (datetime.now(timezone.utc).date() - timedelta(days=3)).isoformat()
    _write_yaml(
        today_repo,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": "rev.testing.today.subject_01.001",
                    "node_id": "testing.today.subject_01",
                    "status": "scheduled",
                    "scheduled_for": due,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ]
        },
    )
    rc = cli.run(["today"], root=today_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "overdue review" in out.lower()


def test_today_reports_open_blocker_pressure(today_repo, capsys):
    _write_yaml(
        today_repo,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": "blk.testing.today.subject_01.001",
                    "node_id": "testing.today.subject_01",
                    "status": "open",
                    "description": "stuck on something",
                    "created_at": "2020-01-01T00:00:00+00:00",
                }
            ]
        },
    )
    rc = cli.run(["today"], root=today_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "open blocker" in out.lower()


def test_today_with_no_focus_suggests_next(today_repo, capsys):
    # Remove the progress store so the available node reverts to locked:
    # no candidates, no session -> nothing to focus on.
    (today_repo / "graph" / "state.yaml").unlink()
    rc = cli.run(["today"], root=today_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "nothing stands out" in out
    assert "skilltrace next" in out
