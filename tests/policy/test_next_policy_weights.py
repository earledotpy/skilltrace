"""`next` scored through the policy factor-weight map (v0.6).

With the shipped seeds, score = Σ factor_weight × factor_value: the track
term is track_priority × the node's track weight, an active remediation
edge boosts its remediation node by remediation_priority, and an open
blocker drags its node down by blocker_penalty — and every policy effect
is reflected in the candidate's ordering and Mentor-voice prose.
"""

from __future__ import annotations

import re

from skilltrace import cli

from .conftest import NODE, _write_node, _write_yaml

TARGET = NODE  # foundational (track weight 3)
REM = "testing.policy.remedial_node_01"  # core (track weight 2)
OTHER = "testing.policy.other_node_01"  # foundational (track weight 3)


def _weighted_repo(root, *, blocker_open: bool):
    _write_node(root, TARGET, track="foundational")
    _write_node(root, OTHER, track="foundational")
    _write_node(root, REM, track="core")
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
                    "active": True,
                }
            ]
        },
    )
    _write_yaml(
        root,
        "graph/state.yaml",
        {
            "progress": {
                node: {"state": "available", "changed_at": "2026-07-01T10:00:00+00:00"}
                for node in (TARGET, OTHER, REM)
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


def _ranked_ids(out: str) -> list[str]:
    """Extract node IDs in rank order from Mentor-voice output.

    Mentor-voice (issue #44): node IDs appear in the DO THIS NEXT action line
    as '--node <node_id>'. One per OPTION block, in kicker order.
    """
    return re.findall(r"--node\s+([^\s`]+)", out)


def _block_for(out: str, node_id: str) -> str:
    """Return the text of the OPTION block that contains node_id's action line."""
    # Split on the separator between options and find the block containing node_id.
    blocks = re.split(r"\n---\n", out)
    for block in blocks:
        if f"--node {node_id}" in block:
            return block
    raise AssertionError(f"{node_id} not found in any OPTION block:\n{out}")


def test_policy_pressure_reorders_the_ranking(policy_repo, capsys):
    root = _weighted_repo(policy_repo, blocker_open=True)

    rc = cli.run(["next", "--minutes", "30", "--limit", "5"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    # Shipped seeds: REM = 3.0*2 + 2.0*1 + 1.0 + 4.0 = 13;
    # OTHER = 3.0*3 + 1.0 = 10; TARGET = 10 - 3.0 = 7.
    assert _ranked_ids(out) == [REM, OTHER, TARGET]

    # The Mentor-voice block for the remediation-boosted node names the boost.
    assert "remediation" in _block_for(out, REM).lower()
    # The block for the blocker-penalized node mentions the blocker.
    assert "blocker" in _block_for(out, TARGET).lower()


def test_without_pressure_the_boost_and_penalty_vanish(policy_repo, capsys):
    root = _weighted_repo(policy_repo, blocker_open=False)

    rc = cli.run(["next", "--minutes", "30", "--limit", "5"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    # No active edge, no open blocker: the track term decides (10 vs 9).
    ranked = _ranked_ids(out)
    assert ranked.index(OTHER) < ranked.index(REM)
    assert ranked.index(TARGET) < ranked.index(REM)
    assert "remediation" not in _block_for(out, REM).lower()
    assert "blocker" not in _block_for(out, TARGET).lower()
