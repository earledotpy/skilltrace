"""`skilltrace start`: the session-opening path, end to end.

Drives the real CLI on a temp repo and verifies through public loaders only:
one open session with a date-scoped id, one work item tied to it, the node
asserted `active`, and exactly one audit event.
"""

from __future__ import annotations

import re

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.execution.sessions import load_sessions
from skilltrace.execution.work import load_session_work
from skilltrace.graph.state import load_state

NODE = "testing.execution.start_target_01"


def test_start_opens_session_records_first_work_and_marks_node_active(exec_repo):
    root = exec_repo({NODE: "available"})

    rc = cli.run(["start", NODE], root=root)
    assert rc == 0

    sessions = load_sessions(root)
    assert len(sessions) == 1
    session = sessions[0]
    assert session.status == "open"
    assert re.fullmatch(r"ses\.\d{4}-\d{2}-\d{2}\.01", session.id)
    assert session.started_at
    assert session.ended_at is None

    work = load_session_work(root)
    assert len(work) == 1
    assert work[0].id == f"wk.{session.id}.01"
    assert work[0].session_id == session.id
    assert work[0].node_id == NODE

    assert load_state(root).state_of(NODE) == "active"

    events = load_events(root)
    assert len(events) == 1
    assert events[0]["command"] == "start"


def test_start_records_an_optional_template_label(exec_repo, capsys):
    root = exec_repo({NODE: "available"})

    rc = cli.run(["start", NODE, "--template", "deep"], root=root)
    assert rc == 0
    assert load_sessions(root)[0].template == "deep"
    # 'deep' is a seeded preset — no warning.
    assert "no seed preset" not in capsys.readouterr().out


def test_start_warns_on_a_template_with_no_preset(exec_repo, capsys):
    root = exec_repo({NODE: "available"})

    rc = cli.run(["start", NODE, "--template", "mega"], root=root)
    assert rc == 0  # warn-only, track-style
    assert load_sessions(root)[0].template == "mega"
    assert "no seed preset" in capsys.readouterr().out


def test_start_refuses_while_a_session_is_open(exec_repo):
    root = exec_repo({NODE: "available", "testing.execution.other_01": "available"})
    assert cli.run(["start", NODE], root=root) == 0

    rc = cli.run(["start", "testing.execution.other_01"], root=root)
    assert rc != 0

    # Nothing new written: one session, one work item, one event (the first start).
    assert len(load_sessions(root)) == 1
    assert len(load_session_work(root)) == 1
    assert len(load_events(root)) == 1
    # And the refused node was not activated.
    assert load_state(root).state_of("testing.execution.other_01") == "available"
