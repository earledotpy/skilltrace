"""`suggest remediation` / `suggest reviews` — read-only policy guidance.

Both commands answer "what corrective or retention work is due?" from
derived pressure and the policy seeds. They are advisory output only:
always exit 0, never write a record, never append an event.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from skilltrace import cli
from skilltrace.events import load_events

from .conftest import NODE, _write_node, _write_yaml

TARGET = NODE
REM = "testing.policy.remedial_node_01"


def _pressure_repo(root, *, with_edge: bool, blocker_open: bool):
    _write_node(root, TARGET)
    _write_node(root, REM)
    edges = (
        [
            {
                "id": "edge.remedial_rescues_target",
                "source": REM,
                "target": TARGET,
                "edge_type": "remediation",
                "reason": "rescues the target when it is stuck",
                "active": True,
            }
        ]
        if with_edge
        else []
    )
    _write_yaml(root, "graph/edges.yaml", {"edges": edges})
    _write_yaml(
        root,
        "graph/state.yaml",
        {
            "progress": {
                node: {"state": "available", "changed_at": "2026-07-01T10:00:00+00:00"}
                for node in (TARGET, REM)
            }
        },
    )
    if blocker_open:
        _write_yaml(
            root,
            "execution/blockers.yaml",
            {
                "blockers": [
                    {
                        "id": f"blk.{TARGET}.001",
                        "node_id": TARGET,
                        "status": "open",
                        "description": "stuck on the core idea",
                        "created_at": "2026-07-02T10:00:00+00:00",
                    }
                ]
            },
        )
    return root


def _run(root, capsys, *argv) -> str:
    rc = cli.run(list(argv), root=root)
    assert rc == 0
    assert load_events(root) == []  # read-only: no audit event
    return capsys.readouterr().out


def test_suggest_remediation_points_at_the_active_edge(policy_repo, capsys):
    root = _pressure_repo(policy_repo, with_edge=True, blocker_open=True)
    out = _run(root, capsys, "suggest", "remediation")
    assert REM in out and TARGET in out
    # The suggestion carries the policy defaults (30 min, due tomorrow).
    assert "30" in out
    tomorrow = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()
    assert tomorrow in out


def test_suggest_remediation_proposes_adhoc_action_for_uncovered_blocker(
    policy_repo, capsys
):
    root = _pressure_repo(policy_repo, with_edge=False, blocker_open=True)
    out = _run(root, capsys, "suggest", "remediation")
    assert f"blk.{TARGET}.001" in out
    assert "remediation create" in out  # the manual command it hands the learner


def test_suggest_remediation_with_no_pressure_says_so(policy_repo, capsys):
    root = _pressure_repo(policy_repo, with_edge=True, blocker_open=False)
    out = _run(root, capsys, "suggest", "remediation")
    assert "nothing to suggest" in out


def test_suggest_reviews_lists_only_due_and_overdue(policy_repo, capsys):
    today = datetime.now(timezone.utc).date()
    _write_yaml(
        policy_repo,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": f"rev.{TARGET}.001",
                    "node_id": TARGET,
                    "status": "scheduled",
                    "scheduled_for": (today - timedelta(days=5)).isoformat(),
                    "created_at": "2026-06-01T10:00:00+00:00",
                },
                {
                    "id": f"rev.{TARGET}.002",
                    "node_id": TARGET,
                    "status": "scheduled",
                    "scheduled_for": (today + timedelta(days=30)).isoformat(),
                    "created_at": "2026-06-01T10:00:00+00:00",
                },
            ]
        },
    )
    out = _run(policy_repo, capsys, "suggest", "reviews")
    assert f"rev.{TARGET}.001" in out
    assert f"rev.{TARGET}.002" not in out
    # Five days late is past the seeded 2-day grace — the suggestion says so.
    assert "overdue" in out
    assert "grace" in out


def test_suggest_reviews_with_nothing_due_says_so(policy_repo, capsys):
    _write_yaml(policy_repo, "execution/reviews.yaml", {"reviews": []})
    out = _run(policy_repo, capsys, "suggest", "reviews")
    assert "nothing due" in out
