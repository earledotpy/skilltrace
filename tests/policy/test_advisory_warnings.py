"""Advisory warnings on `start` — warn at the moment of taking on work.

Workload pressure (active-node count), overdue reviews, and a remediation
backlog over the advisory maximum each print a `[warning]` line, and none
of them ever blocks the start (advisory policies never block a
human-initiated action).
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.events import load_events

from .conftest import NODE, _write_yaml

BUSY_A = "testing.policy.busy_node_01"
BUSY_B = "testing.policy.busy_node_02"


def _pile_on_pressure(root) -> None:
    """Two nodes already active, one overdue review, six open remediations."""
    _write_yaml(
        root,
        "graph/state.yaml",
        {
            "progress": {
                NODE: {"state": "available", "changed_at": "2026-07-01T10:00:00+00:00"},
                BUSY_A: {"state": "active", "changed_at": "2026-07-01T10:00:00+00:00"},
                BUSY_B: {"state": "active", "changed_at": "2026-07-01T10:00:00+00:00"},
            }
        },
    )
    _write_yaml(
        root,
        "execution/reviews.yaml",
        {
            "reviews": [
                {
                    "id": f"rev.{BUSY_A}.001",
                    "node_id": BUSY_A,
                    "status": "scheduled",
                    "scheduled_for": "2026-01-01",
                    "created_at": "2025-12-31T10:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        root,
        "execution/remediation_actions.yaml",
        {
            "remediation_actions": [
                {
                    "id": f"rem.{BUSY_A}.{n:03d}",
                    "node_id": BUSY_A,
                    "status": "open",
                    "description": "redo the drills",
                    "created_at": "2026-07-01T10:00:00+00:00",
                }
                for n in range(1, 7)
            ]
        },
    )


def test_start_warns_on_every_advisory_pressure_but_proceeds(mastery_repo, capsys):
    root = mastery_repo(state="available", passed_at=None)
    _pile_on_pressure(root)

    rc = cli.run(["start", NODE], root=root)
    assert rc == 0  # advisory warnings never block a human-initiated action

    out = capsys.readouterr().out
    warnings = [line for line in out.splitlines() if line.startswith("[warning]")]
    assert any("active" in w for w in warnings)
    assert any("overdue" in w for w in warnings)
    assert any("remediation" in w for w in warnings)

    # The start itself went through untouched: session opened, one audit event.
    events = load_events(root)
    assert len(events) == 1
    assert events[0]["command"] == "start"


def test_start_without_pressure_prints_no_warnings(mastery_repo, capsys):
    root = mastery_repo(state="available", passed_at=None)

    rc = cli.run(["start", NODE], root=root)
    assert rc == 0
    assert "[warning]" not in capsys.readouterr().out


def test_missing_policy_seeds_degrade_to_silence(mastery_repo, capsys):
    root = mastery_repo(state="available", passed_at=None)
    _pile_on_pressure(root)
    (root / "policy" / "workload.yaml").unlink()
    (root / "policy" / "remediation.yaml").unlink()

    rc = cli.run(["start", NODE], root=root)
    assert rc == 0
    out = capsys.readouterr().out
    warnings = [line for line in out.splitlines() if line.startswith("[warning]")]
    # The review backlog needs no policy file; the workload and remediation
    # advisories quietly stand down without their seeds.
    assert not any("active" in w for w in warnings)
    assert not any("remediation" in w for w in warnings)
