"""The dispatcher owns the audit rule and the automation guard."""

from __future__ import annotations

import argparse

import pytest

from skilltrace.dispatch import (
    Command,
    Context,
    CommandResult,
    Kind,
    Registry,
    dispatch,
)
from skilltrace.events import load_events


def _ctx(root, **args):
    return Context(root=root, args=argparse.Namespace(**args))


def _record(calls):
    def handler(ctx):
        calls.append(ctx)
        return CommandResult()

    return handler


def test_registry_rejects_duplicate_names():
    registry = Registry()
    registry.register(Command("x", Kind.READ_ONLY, _record([])))
    with pytest.raises(ValueError):
        registry.register(Command("x", Kind.READ_ONLY, _record([])))


def test_mutating_command_appends_exactly_one_event(tmp_path):
    def handler(ctx):
        return CommandResult(records_touched=["node.a", "node.b"])

    cmd = Command("do-thing", Kind.MUTATING, handler)
    rc = dispatch(cmd, _ctx(tmp_path, minutes=30))
    assert rc == 0

    events = load_events(tmp_path)
    assert len(events) == 1
    event = events[0]
    assert event["command"] == "do-thing"
    assert event["records_touched"] == ["node.a", "node.b"]
    assert event["args"] == {"minutes": 30}
    assert "timestamp" in event


def test_read_only_command_appends_no_event(tmp_path):
    cmd = Command("look", Kind.READ_ONLY, _record([]))
    rc = dispatch(cmd, _ctx(tmp_path))
    assert rc == 0
    assert load_events(tmp_path) == []


def test_failed_mutating_command_appends_no_event(tmp_path):
    def handler(ctx):
        return CommandResult(exit_code=1)

    cmd = Command("break", Kind.MUTATING, handler)
    rc = dispatch(cmd, _ctx(tmp_path))
    assert rc == 1
    assert load_events(tmp_path) == []


def test_event_args_exclude_internal_and_root_fields(tmp_path):
    cmd = Command("m", Kind.MUTATING, lambda ctx: CommandResult())
    # A namespace carrying plumbing fields (_command_name, root) alongside a real
    # arg; only the real arg should land in the event.
    args = argparse.Namespace(minutes=15, _command_name="m", root="ignored")
    dispatch(cmd, Context(root=tmp_path, args=args))
    event = load_events(tmp_path)[0]
    assert event["args"] == {"minutes": 15}


def test_forbidden_automation_action_is_refused(tmp_path):
    calls = []
    cmd = Command(
        "danger",
        Kind.MUTATING,
        _record(calls),
        automation_action="pass_node",
    )
    rc = dispatch(cmd, _ctx(tmp_path))

    assert rc != 0  # non-zero exit
    assert calls == []  # handler did not run
    assert load_events(tmp_path) == []  # nothing logged


def test_unknown_automation_action_fails_closed_at_dispatch(tmp_path):
    # A command carrying a non-floor automation_action with no permitting policy
    # is refused (fail closed): the handler never runs.
    calls = []
    cmd = Command(
        "maybe",
        Kind.READ_ONLY,
        _record(calls),
        automation_action="some_non_floor_action",
    )
    rc = dispatch(cmd, _ctx(tmp_path))
    assert rc != 0
    assert calls == []
