"""`next` scored through the policy factor-weight map (v0.6).

With the shipped seeds, score = Σ factor_weight × factor_value: the track
term is track_priority × the node's track weight, an active remediation
edge boosts its remediation node by remediation_priority, and an open
blocker drags its node down by blocker_penalty — and every policy effect
is named in the recommendation's reason line.
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
    return re.findall(r"^\s*\d+\. (\S+)", out, flags=re.MULTILINE)


def test_policy_pressure_reorders_the_ranking(policy_repo, capsys):
    root = _weighted_repo(policy_repo, blocker_open=True)

    rc = cli.run(["next", "--minutes", "30", "--limit", "5"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    # Shipped seeds: REM = 3.0*2 + 2.0*1 + 1.0 + 4.0 = 13;
    # OTHER = 3.0*3 + 1.0 = 10; TARGET = 10 - 3.0 = 7.
    assert _ranked_ids(out) == [REM, OTHER, TARGET]
    assert "(score 13)" in out
    assert "(score 7)" in out

    # The reasons name the policy effects.
    assert "remediation" in _reason_of(out, REM)
    assert "blocker" in _reason_of(out, TARGET)


def test_without_pressure_the_boost_and_penalty_vanish(policy_repo, capsys):
    root = _weighted_repo(policy_repo, blocker_open=False)

    rc = cli.run(["next", "--minutes", "30", "--limit", "5"], root=root)
    assert rc == 0
    out = capsys.readouterr().out

    # No active edge, no open blocker: the track term decides (10 vs 9).
    ranked = _ranked_ids(out)
    assert ranked.index(OTHER) < ranked.index(REM)
    assert ranked.index(TARGET) < ranked.index(REM)
    assert "remediation" not in _reason_of(out, REM)
    assert "blocker" not in _reason_of(out, TARGET)


def _reason_of(out: str, node_id: str) -> str:
    lines = out.splitlines()
    for index, line in enumerate(lines):
        if re.match(rf"\s*\d+\. {re.escape(node_id)}\s", line):
            return lines[index + 1]
    raise AssertionError(f"{node_id} not ranked in output:\n{out}")
