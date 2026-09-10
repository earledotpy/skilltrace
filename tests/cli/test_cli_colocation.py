"""CLI co-location migrate (issue #206): every command owns its `add_parser`.

`cli.build_parser` only orchestrates the co-located builders; no legacy
mega-parser blocks remain. No YAML registry; dispatch Kind and audit
behaviour unchanged.
"""

from __future__ import annotations

from skilltrace import cli
from skilltrace.dispatch import Kind
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


def test_no_yaml_command_registry_introduced():
    import pathlib

    repo = pathlib.Path(__file__).resolve().parents[2]
    assert not (repo / "graph" / "commands.yaml").exists()
    assert not (repo / "src" / "skilltrace" / "commands.yaml").exists()
