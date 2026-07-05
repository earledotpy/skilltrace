"""`skilltrace work`: adding work items to the open session."""

from __future__ import annotations

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.execution.blockers import load_blockers
from skilltrace.execution.sessions import load_sessions
from skilltrace.execution.work import load_session_work
from skilltrace.graph.state import load_state

NODE = "testing.execution.first_node_01"
OTHER = "testing.execution.second_node_01"


def test_work_appends_an_item_to_the_open_session(exec_repo):
    root = exec_repo({NODE: "available", OTHER: "available"})
    assert cli.run(["start", NODE], root=root) == 0

    rc = cli.run(["work", OTHER], root=root)
    assert rc == 0

    work = load_session_work(root)
    assert len(work) == 2
    session_id = load_sessions(root)[0].id
    assert work[1].id == f"wk.{session_id}.02"
    assert work[1].session_id == session_id
    assert work[1].node_id == OTHER
    assert load_state(root).state_of(OTHER) == "active"

    events = load_events(root)
    assert [e["command"] for e in events] == ["start", "work"]


def test_work_refuses_on_a_locked_node(exec_repo):
    root = exec_repo({NODE: "available", OTHER: "locked"})
    assert cli.run(["start", NODE], root=root) == 0

    rc = cli.run(["work", OTHER], root=root)
    assert rc != 0

    assert len(load_session_work(root)) == 1  # only the start's item
    assert load_state(root).state_of(OTHER) == "locked"
    assert [e["command"] for e in load_events(root)] == ["start"]


def test_start_refuses_on_a_locked_node(exec_repo):
    root = exec_repo({NODE: "locked"})

    rc = cli.run(["start", NODE], root=root)
    assert rc != 0

    assert load_sessions(root) == []
    assert load_session_work(root) == []
    assert load_events(root) == []


def test_work_never_demotes_asserted_progress(exec_repo):
    states = {
        NODE: "available",
        "testing.execution.already_active_01": "active",
        "testing.execution.done_01": "passed",
        "testing.execution.retained_01": "mastered",
    }
    root = exec_repo(states)
    assert cli.run(["start", NODE], root=root) == 0

    for node_id in list(states)[1:]:
        assert cli.run(["work", node_id], root=root) == 0, node_id

    store = load_state(root)
    assert store.state_of("testing.execution.already_active_01") == "active"
    assert store.state_of("testing.execution.done_01") == "passed"
    assert store.state_of("testing.execution.retained_01") == "mastered"
    # All four work items recorded: revisiting is history, never a regression.
    assert len(load_session_work(root)) == 4


def test_blocked_work_requires_notes(exec_repo):
    root = exec_repo({NODE: "available"})
    assert cli.run(["start", NODE], root=root) == 0

    rc = cli.run(["work", NODE, "--blocked"], root=root)
    assert rc != 0

    assert len(load_session_work(root)) == 1  # nothing added
    assert [e["command"] for e in load_events(root)] == ["start"]


def test_blocked_work_is_recorded_and_creates_no_blocker(exec_repo):
    root = exec_repo({NODE: "available"})
    assert cli.run(["start", NODE], root=root) == 0

    rc = cli.run(
        ["work", NODE, "--blocked", "--notes", "chain rule over matrices lost me"],
        root=root,
    )
    assert rc == 0

    work = load_session_work(root)
    assert len(work) == 2
    assert work[1].blocked is True
    assert work[1].notes == "chain rule over matrices lost me"
    # Blocked work is a session-scoped observation — never a Blocker.
    assert load_blockers(root) == []


def test_work_minutes_are_optional_and_recorded_when_given(exec_repo):
    root = exec_repo({NODE: "available"})
    assert cli.run(["start", NODE], root=root) == 0

    assert cli.run(["work", NODE, "--minutes", "45"], root=root) == 0
    assert cli.run(["work", NODE], root=root) == 0

    work = load_session_work(root)
    assert work[1].minutes == 45
    assert work[2].minutes is None


def test_work_refuses_without_an_open_session(exec_repo):
    root = exec_repo({NODE: "available"})

    rc = cli.run(["work", NODE], root=root)
    assert rc != 0

    assert load_session_work(root) == []
    assert load_events(root) == []
    assert load_state(root).state_of(NODE) == "available"
