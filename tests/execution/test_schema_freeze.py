"""Closed-schema enforcement for execution-layer record types.

Each execution record type (Session, SessionWork, Blocker, Review,
RemediationAction) rejects unknown fields at load time. This verifies
that the v1.0 schema freeze is enforced.
"""

from __future__ import annotations

import pytest
import yaml

from skilltrace.execution._store import ExecutionLoadError
from skilltrace.execution.sessions import load_sessions
from skilltrace.execution.work import load_session_work
from skilltrace.execution.blockers import load_blockers
from skilltrace.execution.reviews import load_reviews
from skilltrace.execution.remediation import load_remediation_actions


def _write_yaml(root, relpath: str, doc: dict) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


class TestSessionSchema:
    def test_unknown_field_fails(self, tmp_path):
        _write_yaml(tmp_path, "execution/sessions.yaml", {
            "sessions": [{
                "id": "ses.test.01",
                "status": "open",
                "started_at": "2026-01-01T00:00:00+00:00",
                "bogus_field": "should fail",
            }]
        })
        with pytest.raises(ExecutionLoadError, match="unknown field"):
            load_sessions(tmp_path)

    def test_valid_session_loads(self, tmp_path):
        _write_yaml(tmp_path, "execution/sessions.yaml", {
            "sessions": [{
                "id": "ses.test.01",
                "status": "open",
                "started_at": "2026-01-01T00:00:00+00:00",
            }]
        })
        sessions = load_sessions(tmp_path)
        assert len(sessions) == 1
        assert sessions[0].id == "ses.test.01"


class TestSessionWorkSchema:
    def test_unknown_field_fails(self, tmp_path):
        _write_yaml(tmp_path, "execution/session_work.yaml", {
            "session_work": [{
                "id": "wrk.test.01",
                "session_id": "ses.test.01",
                "node_id": "testing.schema_01",
                "created_at": "2026-01-01T00:00:00+00:00",
                "extra_data": True,
            }]
        })
        with pytest.raises(ExecutionLoadError, match="unknown field"):
            load_session_work(tmp_path)

    def test_valid_work_loads(self, tmp_path):
        _write_yaml(tmp_path, "execution/session_work.yaml", {
            "session_work": [{
                "id": "wrk.test.01",
                "session_id": "ses.test.01",
                "node_id": "testing.schema_01",
                "created_at": "2026-01-01T00:00:00+00:00",
            }]
        })
        items = load_session_work(tmp_path)
        assert len(items) == 1


class TestBlockerSchema:
    def test_unknown_field_fails(self, tmp_path):
        _write_yaml(tmp_path, "execution/blockers.yaml", {
            "blockers": [{
                "id": "blk.test.01",
                "node_id": "testing.schema_01",
                "status": "open",
                "description": "stuck",
                "created_at": "2026-01-01T00:00:00+00:00",
                "priority": "high",
            }]
        })
        with pytest.raises(ExecutionLoadError, match="unknown field"):
            load_blockers(tmp_path)

    def test_valid_blocker_loads(self, tmp_path):
        _write_yaml(tmp_path, "execution/blockers.yaml", {
            "blockers": [{
                "id": "blk.test.01",
                "node_id": "testing.schema_01",
                "status": "open",
                "description": "stuck",
                "created_at": "2026-01-01T00:00:00+00:00",
            }]
        })
        blockers = load_blockers(tmp_path)
        assert len(blockers) == 1


class TestReviewSchema:
    def test_unknown_field_fails(self, tmp_path):
        _write_yaml(tmp_path, "execution/reviews.yaml", {
            "reviews": [{
                "id": "rev.test.01",
                "node_id": "testing.schema_01",
                "status": "scheduled",
                "scheduled_for": "2026-02-01",
                "created_at": "2026-01-01T00:00:00+00:00",
                "notes": "extra",
            }]
        })
        with pytest.raises(ExecutionLoadError, match="unknown field"):
            load_reviews(tmp_path)

    def test_valid_review_loads(self, tmp_path):
        _write_yaml(tmp_path, "execution/reviews.yaml", {
            "reviews": [{
                "id": "rev.test.01",
                "node_id": "testing.schema_01",
                "status": "scheduled",
                "scheduled_for": "2026-02-01",
                "created_at": "2026-01-01T00:00:00+00:00",
            }]
        })
        reviews = load_reviews(tmp_path)
        assert len(reviews) == 1


class TestRemediationActionSchema:
    def test_unknown_field_fails(self, tmp_path):
        _write_yaml(tmp_path, "execution/remediation_actions.yaml", {
            "remediation_actions": [{
                "id": "rem.test.01",
                "node_id": "testing.schema_01",
                "status": "open",
                "description": "drill",
                "created_at": "2026-01-01T00:00:00+00:00",
                "assigned_to": "learner",
            }]
        })
        with pytest.raises(ExecutionLoadError, match="unknown field"):
            load_remediation_actions(tmp_path)

    def test_valid_action_loads(self, tmp_path):
        _write_yaml(tmp_path, "execution/remediation_actions.yaml", {
            "remediation_actions": [{
                "id": "rem.test.01",
                "node_id": "testing.schema_01",
                "status": "open",
                "description": "drill",
                "created_at": "2026-01-01T00:00:00+00:00",
            }]
        })
        actions = load_remediation_actions(tmp_path)
        assert len(actions) == 1
