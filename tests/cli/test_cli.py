"""End-to-end CLI surface: parser, command wiring, and the audit contract."""

from __future__ import annotations

from skilltrace import cli
from skilltrace.events import load_events


def test_help_lists_the_command_surface():
    help_text = cli.build_parser().format_help()
    for name in ("validate", "sync", "next", "evidence"):
        assert name in help_text


def test_registry_has_the_expected_commands():
    assert set(cli.REGISTRY.names()) == {
        "validate graph",
        "validate evidence",
        "sync",
        "next",
        "evidence submit",
    }


def test_main_is_callable_entry_point():
    assert callable(cli.main)


def test_sync_is_mutating_and_logs_one_event(tmp_path):
    rc = cli.run(["sync"], root=tmp_path)
    assert rc == 0
    events = load_events(tmp_path)
    assert len(events) == 1
    assert events[0]["command"] == "sync"
    # Argparse routing dests must not leak into the audit args.
    assert events[0]["args"] == {}


def test_next_is_read_only_and_logs_nothing(tmp_path):
    rc = cli.run(["next", "--minutes", "30", "--limit", "3", "--show-locked"], root=tmp_path)
    assert rc == 0
    assert load_events(tmp_path) == []


def test_validate_graph_is_read_only_and_logs_nothing(tmp_path):
    rc = cli.run(["validate", "graph"], root=tmp_path)
    assert rc == 0
    assert load_events(tmp_path) == []


def test_root_flag_overrides_detection(tmp_path):
    rc = cli.run(["--root", str(tmp_path), "sync"])
    assert rc == 0
    assert len(load_events(tmp_path)) == 1
