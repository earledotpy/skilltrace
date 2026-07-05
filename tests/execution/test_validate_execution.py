"""`skilltrace validate execution`: structure + refs + status fields — never
node-state preconditions.

The uniform rule from the design session: state gates live in commands,
structural truth lives in validate. History may legitimately outlive the
state that permitted it (a blocker created on an available node whose
readiness later flipped to locked), so validation never re-checks node-state
preconditions.
"""

from __future__ import annotations

import yaml

from skilltrace import cli
from skilltrace.events import load_events

NODE = "testing.execution.checked_node_01"


def _write_yaml(root, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _session(session_id="ses.2026-07-01.01", status="completed", **overrides):
    record = {
        "id": session_id,
        "status": status,
        "started_at": "2026-07-01T10:00:00+00:00",
        "ended_at": "2026-07-01T11:00:00+00:00",
    }
    if status == "open":
        record.pop("ended_at")
    record.update(overrides)
    return record


def test_real_command_history_validates_clean(exec_repo, capsys):
    root = exec_repo({NODE: "passed", "testing.execution.fresh_01": "available"})
    assert cli.run(["start", "testing.execution.fresh_01"], root=root) == 0
    assert cli.run(["work", NODE, "--blocked", "--notes", "hmm"], root=root) == 0
    assert cli.run(["blocker", "create", NODE, "--description", "stuck"], root=root) == 0
    assert cli.run(["remediation", "create", NODE, "--description", "drill"], root=root) == 0
    assert cli.run(["review", "schedule", NODE, "--date", "2026-07-10"], root=root) == 0
    events_before = len(load_events(root))

    rc = cli.run(["validate", "execution"], root=root)
    assert rc == 0
    assert "validate execution: OK" in capsys.readouterr().out
    # Read-only: no audit event.
    assert len(load_events(root)) == events_before


def test_planned_session_status_fails_validation(exec_repo, capsys):
    root = exec_repo({NODE: "available"})
    _write_yaml(root, "execution/sessions.yaml", {"sessions": [_session(status="planned")]})

    rc = cli.run(["validate", "execution"], root=root)
    assert rc != 0
    assert "planned" in capsys.readouterr().out


def test_two_open_sessions_fail_validation(exec_repo):
    root = exec_repo({NODE: "available"})
    _write_yaml(
        root,
        "execution/sessions.yaml",
        {
            "sessions": [
                _session("ses.2026-07-01.01", status="open"),
                _session("ses.2026-07-01.02", status="open"),
            ]
        },
    )
    assert cli.run(["validate", "execution"], root=root) != 0


def test_completed_session_requires_an_end_after_the_start(exec_repo):
    root = exec_repo({NODE: "available"})
    _write_yaml(
        root,
        "execution/sessions.yaml",
        {"sessions": [_session(ended_at="2026-07-01T09:00:00+00:00")]},
    )
    assert cli.run(["validate", "execution"], root=root) != 0

    _write_yaml(root, "execution/sessions.yaml", {"sessions": [_session(ended_at=None)]})
    assert cli.run(["validate", "execution"], root=root) != 0


def test_work_item_referencing_unknown_session_or_node_fails(exec_repo):
    root = exec_repo({NODE: "available"})
    _write_yaml(root, "execution/sessions.yaml", {"sessions": [_session()]})
    work = {
        "id": "wk.ses.2026-07-01.01.01",
        "session_id": "ses.2026-07-99.01",  # no such session
        "node_id": NODE,
        "created_at": "2026-07-01T10:10:00+00:00",
    }
    _write_yaml(root, "execution/session_work.yaml", {"session_work": [work]})
    assert cli.run(["validate", "execution"], root=root) != 0

    work["session_id"] = "ses.2026-07-01.01"
    work["node_id"] = "testing.execution.ghost_01"  # no such node
    _write_yaml(root, "execution/session_work.yaml", {"session_work": [work]})
    assert cli.run(["validate", "execution"], root=root) != 0


def test_blocked_work_without_notes_fails_validation(exec_repo):
    root = exec_repo({NODE: "available"})
    _write_yaml(root, "execution/sessions.yaml", {"sessions": [_session()]})
    work = {
        "id": "wk.ses.2026-07-01.01.01",
        "session_id": "ses.2026-07-01.01",
        "node_id": NODE,
        "created_at": "2026-07-01T10:10:00+00:00",
        "blocked": True,
    }
    _write_yaml(root, "execution/session_work.yaml", {"session_work": [work]})
    assert cli.run(["validate", "execution"], root=root) != 0


def test_resolved_blocker_requires_a_resolution_summary(exec_repo):
    root = exec_repo({NODE: "active"})
    blocker = {
        "id": f"blk.{NODE}.001",
        "node_id": NODE,
        "status": "resolved",
        "description": "stuck",
        "created_at": "2026-07-01",
        "resolved_at": "2026-07-02",
    }
    _write_yaml(root, "execution/blockers.yaml", {"blockers": [blocker]})
    assert cli.run(["validate", "execution"], root=root) != 0


def test_completed_and_cancelled_reviews_require_their_fields(exec_repo):
    root = exec_repo({NODE: "passed"})
    review = {
        "id": f"rev.{NODE}.001",
        "node_id": NODE,
        "status": "completed",
        "scheduled_for": "2026-07-10",
        "created_at": "2026-07-01",
        "completed_at": "2026-07-10",
        "result_summary": "fine",
        # missing outcome
    }
    _write_yaml(root, "execution/reviews.yaml", {"reviews": [review]})
    assert cli.run(["validate", "execution"], root=root) != 0

    review = {
        "id": f"rev.{NODE}.001",
        "node_id": NODE,
        "status": "cancelled",
        "scheduled_for": "2026-07-10",
        "created_at": "2026-07-01",
        # missing cancel_reason
    }
    _write_yaml(root, "execution/reviews.yaml", {"reviews": [review]})
    assert cli.run(["validate", "execution"], root=root) != 0


def test_state_preconditions_are_never_rechecked(exec_repo, capsys):
    # A blocker legally created while the node was available can sit on a
    # node whose derived readiness later flipped to locked. Valid history.
    root = exec_repo({NODE: "locked"})
    blocker = {
        "id": f"blk.{NODE}.001",
        "node_id": NODE,
        "status": "open",
        "description": "created before the curriculum edit locked the node",
        "created_at": "2026-07-01",
    }
    _write_yaml(root, "execution/blockers.yaml", {"blockers": [blocker]})

    rc = cli.run(["validate", "execution"], root=root)
    assert rc == 0
    assert "validate execution: OK" in capsys.readouterr().out
