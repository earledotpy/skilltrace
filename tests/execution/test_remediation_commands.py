"""`skilltrace remediation create` / `remediation complete`.

A RemediationAction is an ad-hoc intervention log: tied to one node,
optionally naming the Blocker it addresses, with zero mechanical effect —
completing one never resolves a blocker, never touches state.
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.execution.blockers import load_blockers
from skilltrace.execution.remediation import load_remediation_actions
from skilltrace.graph.state import load_state

NODE = "testing.execution.rescue_target_01"


def test_remediation_create_writes_an_open_action(exec_repo):
    root = exec_repo({NODE: "active"})

    rc = cli.run(
        ["remediation", "create", NODE, "--description", "re-derive chain rule by hand"],
        root=root,
    )
    assert rc == 0

    actions = load_remediation_actions(root)
    assert len(actions) == 1
    action = actions[0]
    assert action.id == f"rem.{NODE}.001"
    assert action.node_id == NODE
    assert action.status == "open"
    assert action.blocker_id is None
    assert [e["command"] for e in load_events(root)] == ["remediation create"]


def test_remediation_create_validates_the_blocker_link(exec_repo):
    root = exec_repo({NODE: "active"})

    rc = cli.run(
        ["remediation", "create", NODE, "--description", "x", "--blocker", "blk.nope.001"],
        root=root,
    )
    assert rc != 0
    assert load_remediation_actions(root) == []

    assert cli.run(["blocker", "create", NODE, "--description", "stuck"], root=root) == 0
    blocker_id = f"blk.{NODE}.001"
    rc = cli.run(
        ["remediation", "create", NODE, "--description", "x", "--blocker", blocker_id],
        root=root,
    )
    assert rc == 0
    assert load_remediation_actions(root)[0].blocker_id == blocker_id


def test_remediation_complete_records_summary_and_touches_nothing_else(exec_repo):
    root = exec_repo({NODE: "active"})
    assert cli.run(["blocker", "create", NODE, "--description", "stuck"], root=root) == 0
    blocker_id = f"blk.{NODE}.001"
    assert (
        cli.run(
            ["remediation", "create", NODE, "--description", "x", "--blocker", blocker_id],
            root=root,
        )
        == 0
    )
    action_id = f"rem.{NODE}.001"

    rc = cli.run(
        ["remediation", "complete", action_id, "--summary", "worked through 3 examples"],
        root=root,
    )
    assert rc == 0

    action = load_remediation_actions(root)[0]
    assert action.status == "completed"
    assert action.result_summary == "worked through 3 examples"
    # Zero mechanical effect: the linked blocker stays open, state untouched.
    assert load_blockers(root)[0].status == "open"
    assert load_state(root).state_of(NODE) == "active"


def test_remediation_complete_refuses_unknown_or_completed(exec_repo):
    root = exec_repo({NODE: "active"})
    assert (
        cli.run(["remediation", "create", NODE, "--description", "x"], root=root) == 0
    )
    action_id = f"rem.{NODE}.001"

    assert cli.run(["remediation", "complete", "rem.nope.001", "--summary", "s"], root=root) != 0
    assert cli.run(["remediation", "complete", action_id, "--summary", "done"], root=root) == 0
    assert cli.run(["remediation", "complete", action_id, "--summary", "again"], root=root) != 0

    assert load_remediation_actions(root)[0].result_summary == "done"
