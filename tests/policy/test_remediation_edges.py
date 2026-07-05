"""Remediation-edge activation — derived on demand, surfaced by `next`.

A remediation edge activates when its target has an open Blocker or has
reached the policy failed-attempt threshold without a pass; it deactivates
when the remediation node is passed or the trigger clears (CONTEXT.md).
Activation is never stored, and it never locks the target.
"""

from __future__ import annotations

from skilltrace import cli

from .conftest import NODE, _write_node, _write_yaml

TARGET = NODE
REM = "testing.policy.remedial_node_01"


def _remediation_repo(
    root,
    *,
    edge_active: bool = True,
    remediation_state: str = "available",
    target_state: str = "available",
    blocker_status: str | None = None,
    failed_attempts: int = 0,
):
    _write_node(root, TARGET)
    _write_node(root, REM)
    _write_yaml(
        root,
        "graph/edges.yaml",
        {
            "edges": [
                {
                    "id": "edge.remedial_rescues_target",
                    "source": REM,
                    "target": TARGET,
                    "edge_type": "remediation",
                    "reason": "rescues the target when it is stuck",
                    "active": edge_active,
                }
            ]
        },
    )
    _write_yaml(
        root,
        "graph/state.yaml",
        {
            "progress": {
                TARGET: {"state": target_state, "changed_at": "2026-07-01T10:00:00+00:00"},
                REM: {"state": remediation_state, "changed_at": "2026-07-01T10:00:00+00:00"},
            }
        },
    )
    if blocker_status is not None:
        _write_yaml(
            root,
            "execution/blockers.yaml",
            {
                "blockers": [
                    {
                        "id": f"blk.{TARGET}.001",
                        "node_id": TARGET,
                        "status": blocker_status,
                        "description": "stuck on the core idea",
                        "created_at": "2026-07-02T10:00:00+00:00",
                    }
                ]
            },
        )
    _write_yaml(
        root,
        "evidence/attempts.yaml",
        {
            "attempts": [
                {
                    "id": f"att.{TARGET}.{n:03d}",
                    "node_id": TARGET,
                    "outcome": "failed",
                    "created_at": "2026-07-02",
                }
                for n in range(1, failed_attempts + 1)
            ]
        },
    )
    return root


def _next_output(root, capsys) -> str:
    rc = cli.run(["next", "--minutes", "30", "--limit", "5"], root=root)
    assert rc == 0  # advisory pressure never fails the command
    return capsys.readouterr().out


def test_open_blocker_activates_the_edge(policy_repo, capsys):
    root = _remediation_repo(policy_repo, blocker_status="open")

    out = _next_output(root, capsys)
    advisories = [l for l in out.splitlines() if "remediation" in l]
    assert any(REM in a and TARGET in a for a in advisories)
    # Activation never locks the target — it stays a ranked candidate.
    assert any(TARGET in line and "score" in line for line in out.splitlines())


def test_failed_attempt_threshold_activates_the_edge(policy_repo, capsys):
    root = _remediation_repo(policy_repo, failed_attempts=3)
    out = _next_output(root, capsys)
    assert any(REM in l and "remediation" in l for l in out.splitlines())


def test_below_threshold_with_resolved_blocker_stays_inactive(policy_repo, capsys):
    root = _remediation_repo(policy_repo, blocker_status="resolved", failed_attempts=2)
    out = _next_output(root, capsys)
    assert not any(REM in l and "remediation" in l for l in out.splitlines())


def test_passing_the_remediation_node_deactivates_the_edge(policy_repo, capsys):
    root = _remediation_repo(
        policy_repo, blocker_status="open", remediation_state="passed"
    )
    out = _next_output(root, capsys)
    assert not any(REM in l and "remediation" in l for l in out.splitlines())


def test_passing_the_target_clears_the_attempt_trigger(policy_repo, capsys):
    root = _remediation_repo(policy_repo, failed_attempts=3, target_state="passed")
    out = _next_output(root, capsys)
    assert not any(REM in l and "remediation" in l for l in out.splitlines())


def test_a_retired_edge_never_activates(policy_repo, capsys):
    root = _remediation_repo(policy_repo, blocker_status="open", edge_active=False)
    out = _next_output(root, capsys)
    assert not any(REM in l and "remediation" in l for l in out.splitlines())
