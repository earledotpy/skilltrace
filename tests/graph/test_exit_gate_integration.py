"""v0.3 exit gate — the composed integration sequence on fresh seed data.

The per-command CLI tests (`test_sync_command`, `test_next_command`) each drive
one command on a temp copy. This is the RC-level proof that the three commands
*compose*: on a fresh copy of the shipped seed data, the documented exit-gate
sequence — `validate graph` → `sync` → `next --minutes 60 --limit 5
--show-locked` — runs in order and every command exits 0.

Everything runs in-process against a temp copy (no network, no install step): the
only thing that is "fresh" is the seed-data copy, so the run proves the offline
fresh-clone property the acceptance criterion names. The out-of-process console
entry point is covered by the exit-gate script (`scripts/exit_gate_v03.py`),
which humans run for the RC sign-off.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from skilltrace import cli
from skilltrace.events import load_events

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def seed_repo(tmp_path: Path) -> Path:
    """A fresh temp copy of the shipped graph/ and policy/ seed data.

    `next` reads `policy/recommendation.yaml`, so both directories are copied;
    validation and sync need only graph/, but the sequence runs all three.
    """
    shutil.copytree(REPO_ROOT / "graph", tmp_path / "graph")
    shutil.copytree(REPO_ROOT / "policy", tmp_path / "policy")
    return tmp_path


def test_exit_gate_sequence_all_exit_zero(seed_repo, capsys):
    assert cli.run(["validate", "graph"], root=seed_repo) == 0
    assert cli.run(["sync"], root=seed_repo) == 0
    assert cli.run(
        ["next", "--minutes", "60", "--limit", "5", "--show-locked"], root=seed_repo
    ) == 0

    out = capsys.readouterr().out
    # Each command announced itself in the combined output.
    assert "next:" in out


def test_exit_gate_sequence_logs_exactly_one_event(seed_repo):
    # Only sync mutates: validate and next are read-only and log nothing, so the
    # whole sequence appends exactly one audit event — sync's.
    cli.run(["validate", "graph"], root=seed_repo)
    cli.run(["sync"], root=seed_repo)
    cli.run(["next", "--minutes", "60", "--limit", "5", "--show-locked"], root=seed_repo)

    events = load_events(seed_repo)
    assert [e["command"] for e in events] == ["sync"]


def test_sync_is_idempotent_across_the_sequence(seed_repo):
    # Running the sequence twice does not re-touch nodes on the second sync — the
    # seed graph is already in sync, so both sync events touch nothing.
    for _ in range(2):
        cli.run(["validate", "graph"], root=seed_repo)
        cli.run(["sync"], root=seed_repo)
        cli.run(["next", "--minutes", "60"], root=seed_repo)

    sync_events = [e for e in load_events(seed_repo) if e["command"] == "sync"]
    assert len(sync_events) == 2
    assert all(e["records_touched"] == [] for e in sync_events)
