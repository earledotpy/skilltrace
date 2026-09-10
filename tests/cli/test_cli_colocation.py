"""CLI co-location expand (issue #204): co-located `add_parser` beside `register`.

The legacy mega-parser in `cli.build_parser` remains valid; commands carrying
a co-located builder own their surface while the rest fall back to the old
path. No YAML registry; dispatch Kind and audit behaviour unchanged.
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.dispatch import Kind
from skilltrace.events import load_events


def test_colocated_builders_are_registered_alongside_handlers():
    for name in ("health", "sync"):
        command = cli.REGISTRY.get(name)
        assert command is not None
        assert callable(command.add_parser)


def test_unmigrated_commands_still_use_the_legacy_path():
    command = cli.REGISTRY.get("next")
    assert command is not None
    assert command.add_parser is None


def test_parser_covers_both_paths_without_duplicates():
    parser = cli.build_parser()
    for argv, expected in (
        (["health"], "health"),
        (["sync"], "sync"),
        (["next"], "next"),
        (["validate", "graph"], "validate graph"),
    ):
        args = parser.parse_args(argv)
        assert args._command_name == expected


def test_dispatch_kind_and_audit_unchanged_across_paths(tmp_path):
    assert cli.REGISTRY.get("health").kind is Kind.READ_ONLY
    assert cli.REGISTRY.get("sync").kind is Kind.MUTATING
    assert cli.REGISTRY.get("next").kind is Kind.READ_ONLY

    assert cli.run(["health"], root=tmp_path) in (0, 1)
    assert load_events(tmp_path) == []

    assert cli.run(["sync"], root=tmp_path) == 0
    events = load_events(tmp_path)
    assert len(events) == 1
    assert events[0]["command"] == "sync"


def test_no_yaml_command_registry_introduced():
    import pathlib

    repo = pathlib.Path(__file__).resolve().parents[2]
    assert not (repo / "graph" / "commands.yaml").exists()
    assert not (repo / "src" / "skilltrace" / "commands.yaml").exists()
