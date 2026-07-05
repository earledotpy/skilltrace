"""`skilltrace blocker create` / `blocker resolve`: persistent stuckness.

A Blocker is a deliberate, explicit act — legal in any node state except
locked (what cannot be started cannot be stuck), each naming its own
obstacle. A second open blocker on the same node warns as a likely
duplicate but is legal. Resolution requires a summary and is terminal.
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.execution.blockers import load_blockers

NODE = "testing.execution.stuck_node_01"


def test_blocker_create_writes_an_open_blocker(exec_repo):
    root = exec_repo({NODE: "active"})

    rc = cli.run(
        ["blocker", "create", NODE, "--description", "chain rule over matrices"],
        root=root,
    )
    assert rc == 0

    blockers = load_blockers(root)
    assert len(blockers) == 1
    blocker = blockers[0]
    assert blocker.id == f"blk.{NODE}.001"
    assert blocker.node_id == NODE
    assert blocker.status == "open"
    assert blocker.description == "chain rule over matrices"
    assert [e["command"] for e in load_events(root)] == ["blocker create"]


def test_blocker_create_refuses_on_a_locked_node(exec_repo):
    root = exec_repo({NODE: "locked"})

    rc = cli.run(["blocker", "create", NODE, "--description", "stuck"], root=root)
    assert rc != 0
    assert load_blockers(root) == []
    assert load_events(root) == []


def test_blocker_create_is_legal_on_a_passed_node(exec_repo):
    root = exec_repo({NODE: "passed"})

    rc = cli.run(
        ["blocker", "create", NODE, "--description", "lost it during revision"],
        root=root,
    )
    assert rc == 0
    assert load_blockers(root)[0].status == "open"


def test_second_open_blocker_on_same_node_warns_but_is_legal(exec_repo, capsys):
    root = exec_repo({NODE: "active"})
    assert cli.run(["blocker", "create", NODE, "--description", "one"], root=root) == 0
    capsys.readouterr()

    rc = cli.run(["blocker", "create", NODE, "--description", "two"], root=root)
    assert rc == 0

    out = capsys.readouterr().out.lower()
    assert "warning" in out and "open blocker" in out

    blockers = load_blockers(root)
    assert [b.status for b in blockers] == ["open", "open"]
    assert blockers[1].id == f"blk.{NODE}.002"


def test_blocker_resolve_requires_and_records_the_summary(exec_repo):
    root = exec_repo({NODE: "active"})
    assert cli.run(["blocker", "create", NODE, "--description", "stuck"], root=root) == 0

    rc = cli.run(
        ["blocker", "resolve", f"blk.{NODE}.001", "--summary", "re-derived it by hand"],
        root=root,
    )
    assert rc == 0

    blocker = load_blockers(root)[0]
    assert blocker.status == "resolved"
    assert blocker.resolution_summary == "re-derived it by hand"
    assert blocker.resolved_at is not None
    assert [e["command"] for e in load_events(root)] == ["blocker create", "blocker resolve"]


def test_blocker_resolve_refuses_unknown_or_already_resolved(exec_repo):
    root = exec_repo({NODE: "active"})
    assert cli.run(["blocker", "create", NODE, "--description", "stuck"], root=root) == 0
    blocker_id = f"blk.{NODE}.001"

    assert cli.run(["blocker", "resolve", "blk.nope.001", "--summary", "x"], root=root) != 0
    assert cli.run(["blocker", "resolve", blocker_id, "--summary", "done"], root=root) == 0

    rc = cli.run(["blocker", "resolve", blocker_id, "--summary", "again"], root=root)
    assert rc != 0

    blocker = load_blockers(root)[0]
    assert blocker.resolution_summary == "done"  # first resolution stands
    assert len([e for e in load_events(root) if e["command"] == "blocker resolve"]) == 1
