"""`skilltrace blockers` / `skilltrace reviews` — read-only listings.

Listings log no audit events. `reviews` derives overdue on the fly (a
scheduled review past its date); overdue is never stored.
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.events import load_events

NODE = "testing.execution.listed_node_01"


def test_blockers_lists_open_blockers_and_logs_nothing(exec_repo, capsys):
    root = exec_repo({NODE: "active"})
    assert cli.run(["blocker", "create", NODE, "--description", "stuck on X"], root=root) == 0
    events_before = len(load_events(root))
    capsys.readouterr()

    rc = cli.run(["blockers"], root=root)
    assert rc == 0

    out = capsys.readouterr().out
    assert f"blk.{NODE}.001" in out
    assert "stuck on X" in out
    assert len(load_events(root)) == events_before


def test_resolved_blockers_are_not_listed(exec_repo, capsys):
    root = exec_repo({NODE: "active"})
    assert cli.run(["blocker", "create", NODE, "--description", "stuck"], root=root) == 0
    assert cli.run(
        ["blocker", "resolve", f"blk.{NODE}.001", "--summary", "fixed"], root=root
    ) == 0
    capsys.readouterr()

    assert cli.run(["blockers"], root=root) == 0
    assert f"blk.{NODE}.001" not in capsys.readouterr().out


def test_reviews_marks_overdue_as_derived(exec_repo, capsys):
    root = exec_repo({NODE: "passed"})
    assert cli.run(["review", "schedule", NODE, "--date", "2020-01-01"], root=root) == 0
    assert cli.run(["review", "schedule", NODE, "--date", "2999-01-01"], root=root) == 0
    capsys.readouterr()

    rc = cli.run(["reviews"], root=root)
    assert rc == 0

    lines = capsys.readouterr().out.splitlines()
    past = next(line for line in lines if f"rev.{NODE}.001" in line)
    future = next(line for line in lines if f"rev.{NODE}.002" in line)
    assert "overdue" in past.lower()
    assert "overdue" not in future.lower()


def test_cancelled_reviews_are_not_overdue_and_not_listed(exec_repo, capsys):
    root = exec_repo({NODE: "passed"})
    assert cli.run(["review", "schedule", NODE, "--date", "2020-01-01"], root=root) == 0
    assert cli.run(
        ["review", "cancel", f"rev.{NODE}.001", "--reason", "moot"], root=root
    ) == 0
    capsys.readouterr()

    assert cli.run(["reviews"], root=root) == 0
    assert f"rev.{NODE}.001" not in capsys.readouterr().out
