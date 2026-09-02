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



# ---------------------------------------------------------------------------
# analytics_warnings() pressure paragraph extension — at most 2 bits
# (T-TestArch D5, issue #129)
# ---------------------------------------------------------------------------


def test_today_analytics_warning_appears_in_pressure_paragraph(today_repo, capsys):
    """When blockers spike (>= 3), an analytics bit surfaces in the today brief."""
    from datetime import datetime, timezone

    # Plant 3 open blockers to trip the blockers_active_threshold
    _write_yaml(
        today_repo,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": f"blk.testing.today.subject_01.{n:03d}",
                    "node_id": "testing.today.subject_01",
                    "status": "open",
                    "description": f"stuck on step {n}",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                for n in range(1, 4)  # 3 open blockers >= threshold 3
            ]
        },
    )
    # Seed enough sessions so velocity isn't the only warning (keeps the test
    # focused on the blocker spike path)
    _write_yaml(
        today_repo,
        "execution/sessions.yaml",
        {
            "sessions": [
                {
                    "id": f"ses.2026-08-{15 + n}.001",
                    "status": "completed",
                    "started_at": f"2026-08-{15 + n}T10:00:00Z",
                    "ended_at": f"2026-08-{15 + n}T11:00:00Z",
                }
                for n in range(3)
            ]
        },
    )
    _write_yaml(
        today_repo,
        "execution/session_work.yaml",
        {
            "session_work": [
                {
                    "id": f"wrk.{n:03d}",
                    "session_id": f"ses.2026-08-{15 + n}.001",
                    "node_id": "testing.today.subject_01",
                    "created_at": f"2026-08-{15 + n}T10:30:00Z",
                    "minutes": 30,
                }
                for n in range(3)
            ]
        },
    )
    rc = cli.run(["today"], root=today_repo)
    out = capsys.readouterr().out
    assert rc == 0
    assert "blocker" in out.lower()


def test_today_analytics_bits_capped_at_two(today_repo, capsys):
    """Even when all four analytics thresholds fire, at most 2 analytics bits
    appear in the today pressure paragraph (cap per G6 resolution)."""
    from datetime import datetime, timezone

    # Trip all four thresholds:
    # - velocity: no sessions → 0 avg/week < 2
    # - reviews: 0 completion rate (no completed reviews, 1 scheduled) < 0.80
    # - evidence: coverage 0% (no accepted records, specs exist) < 0.60
    # - blockers: 3 open >= 3
    _write_yaml(
        today_repo,
        "execution/blockers.yaml",
        {
            "blockers": [
                {
                    "id": f"blk.testing.today.subject_01.{n:03d}",
                    "node_id": "testing.today.subject_01",
                    "status": "open",
                    "description": f"stuck {n}",
                    "created_at": "2026-08-01T10:00:00Z",
                }
                for n in range(1, 4)
            ]
        },
    )
    from datetime import date, timedelta
    overdue_date = (date.today() - timedelta(days=5)).isoformat()
    _write_yaml(
        today_repo,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": "rev.testing.today.subject_01.001",
                    "node_id": "testing.today.subject_01",
                    "status": "scheduled",
                    "scheduled_for": overdue_date,
                    "created_at": "2026-07-01T10:00:00Z",
                }
            ]
        },
    )
    # Add a required spec so evidence coverage can be below target
    _write_yaml(
        today_repo,
        "evidence/artifact_specs.yaml",
        {
            "artifact_specs": [
                {
                    "id": "spec.testing.today.subject_01.main",
                    "node_id": "testing.today.subject_01",
                    "title": "Main artifact",
                    "artifact_kind": "problem_set",
                    "required": True,
                    "minimum_count": 1,
                }
            ]
        },
    )

    rc = cli.run(["today"], root=today_repo)
    out = capsys.readouterr().out
    assert rc == 0

    # Count the distinct analytics-warning phrases in the single pressure sentence.
    # The sentence is built from pressure_bits joined with " and "; analytics_bits
    # are sliced to [:2] before being appended. We verify the total advisory content
    # does not exceed the cap by counting known analytics warning keywords.
    analytics_keywords = ["velocity", "review completion", "evidence coverage", "blocker spike"]
    hits = sum(1 for kw in analytics_keywords if kw in out.lower())
    assert hits <= 2, f"Expected at most 2 analytics bits in today output, found {hits}: {out}"
