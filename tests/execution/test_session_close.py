"""`skilltrace session close`: completing the open session, honestly.

Covers the plain close (end = now), the retroactive close for a forgotten
session (`--end` must land after the start and not in the future), and the
stale-open-session warning (threshold is seed data with an engine fallback;
warn-only, never blocks).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import yaml

from skilltrace import cli
from skilltrace.events import load_events
from skilltrace.execution.sessions import load_sessions

NODE = "testing.execution.close_target_01"


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _backdate_open_session(root, hours: float) -> None:
    """Rewrite the open session's start to `hours` ago (fixture surgery)."""
    path = root / "execution" / "sessions.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    started = datetime.now(timezone.utc) - timedelta(hours=hours)
    doc["sessions"][0]["started_at"] = _iso(started)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def test_close_completes_the_open_session(exec_repo):
    root = exec_repo({NODE: "available"})
    assert cli.run(["start", NODE], root=root) == 0

    rc = cli.run(["session", "close"], root=root)
    assert rc == 0

    session = load_sessions(root)[0]
    assert session.status == "completed"
    assert session.ended_at is not None
    assert session.ended_at >= session.started_at
    assert [e["command"] for e in load_events(root)] == ["start", "session close"]


def test_close_refuses_without_an_open_session(exec_repo):
    root = exec_repo({NODE: "available"})

    rc = cli.run(["session", "close"], root=root)
    assert rc != 0
    assert load_events(root) == []


def test_retroactive_close_records_the_honest_end(exec_repo):
    root = exec_repo({NODE: "available"})
    assert cli.run(["start", NODE], root=root) == 0
    _backdate_open_session(root, hours=14)

    end = _iso(datetime.now(timezone.utc) - timedelta(hours=12))
    rc = cli.run(["session", "close", "--end", end], root=root)
    assert rc == 0

    session = load_sessions(root)[0]
    assert session.status == "completed"
    assert session.ended_at == end


def test_close_alias_behaves_like_session_close_and_audits_canonical(exec_repo):
    root = exec_repo({NODE: "available"})
    assert cli.run(["start", NODE], root=root) == 0

    rc = cli.run(["close"], root=root)
    assert rc == 0

    session = load_sessions(root)[0]
    assert session.status == "completed"
    assert session.ended_at is not None
    # Audited under the canonical command name regardless of the form typed.
    assert [e["command"] for e in load_events(root)] == ["start", "session close"]


def test_close_refuses_an_end_before_the_start(exec_repo):
    root = exec_repo({NODE: "available"})
    assert cli.run(["start", NODE], root=root) == 0

    end = _iso(datetime.now(timezone.utc) - timedelta(hours=1))
    rc = cli.run(["session", "close", "--end", end], root=root)
    assert rc != 0
    assert load_sessions(root)[0].status == "open"


def test_close_refuses_an_end_in_the_future(exec_repo):
    root = exec_repo({NODE: "available"})
    assert cli.run(["start", NODE], root=root) == 0

    end = _iso(datetime.now(timezone.utc) + timedelta(hours=2))
    rc = cli.run(["session", "close", "--end", end], root=root)
    assert rc != 0
    assert load_sessions(root)[0].status == "open"


def test_stale_open_session_warns_but_never_blocks(exec_repo, capsys):
    root = exec_repo({NODE: "available"})
    assert cli.run(["start", NODE], root=root) == 0
    _backdate_open_session(root, hours=14)  # past the 12h default threshold
    capsys.readouterr()

    rc = cli.run(["work", NODE], root=root)
    assert rc == 0  # warn-only

    out = capsys.readouterr().out.lower()
    assert "stale" in out


def test_fresh_open_session_does_not_warn(exec_repo, capsys):
    root = exec_repo({NODE: "available"})
    assert cli.run(["start", NODE], root=root) == 0
    capsys.readouterr()

    assert cli.run(["work", NODE], root=root) == 0
    assert "stale" not in capsys.readouterr().out.lower()
