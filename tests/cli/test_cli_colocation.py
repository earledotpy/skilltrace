"""CLI co-location contract (issue #207): co-located builders are the sole source.

`cli.build_parser` only orchestrates the co-located `add_parser` builders;
no mega-parser blocks remain. No YAML registry; dispatch Kind and audit
behaviour unchanged.
"""

from __future__ import annotations

import pathlib

import pytest

from skilltrace import cli
from skilltrace.dispatch import Command, Kind, Registry
from skilltrace.events import load_events


def test_colocated_builders_are_registered_alongside_handlers():
    for command in cli.REGISTRY.all():
        assert callable(command.add_parser), command.name


def test_parser_covers_colocated_commands_without_duplicates():
    parser = cli.build_parser()
    for argv, expected in (
        (["health"], "health"),
        (["sync"], "sync"),
        (["next"], "next"),
        (["validate", "graph"], "validate graph"),
        (["evidence", "submit", "--location", "x", "n_01"], "evidence submit"),
        (["submit", "--location", "x", "n_01"], "evidence submit"),
        (["session", "close"], "session close"),
        (["close"], "session close"),
        (["serve"], "serve"),
        (["ui"], "serve"),
        (["graph", "impact"], "graph impact"),
        (["check-resources", "--stale-only"], "check-resources"),
        (["analytics", "export"], "analytics export"),
        (["portfolio", "preview"], "portfolio preview"),
        (["report", "evidence"], "report evidence"),
    ):
        args = parser.parse_args(argv)
        assert args._command_name == expected


def test_check_resources_politeness_flags_match_prior_behaviour():
    parser = cli.build_parser()
    args = parser.parse_args(["check-resources", "--stale-only", "--no-robots"])
    assert args.stale_only is True
    assert args.no_robots is True
    assert args.per_host_delay is None
    assert args.backoff_attempts is None
    help_text = parser.format_help()
    assert "Alias for `evidence submit`." in help_text
    assert "Alias for `session close`." in help_text
    assert "Alias for `serve`." in help_text


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


def test_cli_module_is_orchestration_only():
    """Contract: no per-command parser construction lives beside the builders.

    `cli.py` owns only the top-level parser and `--root`; every flag and
    subcommand surface comes from a co-located command-module builder.
    """
    source = (pathlib.Path(cli.__file__).resolve()).read_text(encoding="utf-8")
    assert "subparsers.add_parser(" not in source
    assert ".set_defaults(" not in source
    assert source.count("add_argument(") == 1  # `--root` only


def test_build_parser_refuses_commands_without_a_builder(monkeypatch):
    """Contract: a registered command without `add_parser` fails loudly.

    Builders are the only source of CLI flags, so a builder-less command
    must not be silently unreachable.
    """
    registry = Registry()
    registry.register(
        Command(name="orphan", kind=Kind.READ_ONLY, handler=lambda ctx: None)
    )
    monkeypatch.setattr(cli, "REGISTRY", registry)
    with pytest.raises(ValueError, match="orphan"):
        cli.build_parser()


def test_full_help_smoke_lists_every_registered_command():
    import re

    parser = cli.build_parser()
    help_text = parser.format_help()
    # Each attached subcommand renders as an indented entry in the
    # `{ <command> ... }` listing; every registered command's top level
    # must be a real entry, not prose.
    entries = set(re.findall(r"(?m)^    ([A-Za-z][\w-]*)", help_text))
    for command in cli.REGISTRY.all():
        top_level = command.name.split()[0]
        assert top_level in entries, command.name


def test_no_yaml_command_registry_introduced():
    repo = pathlib.Path(cli.__file__).resolve().parents[2]
    assert not (repo / "graph" / "commands.yaml").exists()
    assert not (repo / "src" / "skilltrace" / "commands.yaml").exists()
