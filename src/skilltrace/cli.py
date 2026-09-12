"""`skilltrace` command-line entry point.

Builds the argparse surface, resolves the repo root, and hands the parsed
command to the dispatcher (which owns audit logging and the automation
boundary). The full surface is pinned by tests/cli — graph (`validate`,
`sync`, `next`), evidence (`evidence submit`, `attempt record`,
`eligibility`, `pass`, `master`), execution (`start`, `work`, `session
close`, blockers/remediation/reviews), policy (`validate policy`,
`check-automation`, `suggest`), data-out (`export markdown`,
`export sqlite`, `backup`), and the cross-layer roll-up (`health`). Top-level
aliases `submit` and `close` wrap `evidence submit` and `session close`
respectively, sharing the same handler and `_command_name`, as does `ui` for
`serve` (the Tier 1 local web UI, ADR 0006); the `st`
console-script entry point (see `pyproject.toml`) is a second name for this
same `main`.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Callable

from .commands import register_all
from .dispatch import Context, Registry, dispatch
from .paths import find_root

# The process-wide command registry. Handlers are placeholders in this issue;
# the dispatcher contract they exercise is final.
REGISTRY: Registry = register_all(Registry())


def build_parser() -> argparse.ArgumentParser:
    """Construct the full `skilltrace` argument parser.

    Command names are attached as `_command_name` defaults matching the registry
    keys, so `run` can look the command up without re-deriving it from argparse
    internals. Every registered command owns its argparse surface via a
    co-located `add_parser` builder in its command module (issue #207
    contract: the builders are the sole source of CLI flags); this function
    only orchestrates those builders. Shared builders (one module
    registering several commands, e.g. `validate`) run once.
    """
    parser = argparse.ArgumentParser(
        prog="skilltrace",
        description="Local-first, CLI-first, single-learner learning engine.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="SkillTrace repo root (default: auto-detect from the working directory).",
    )

    # Routing dests are underscore-prefixed so they are treated as plumbing and
    # excluded from audit-event args (see dispatch._event_args).
    subcommands = parser.add_subparsers(dest="_command", metavar="<command>")
    subcommands.required = True

    # Co-located builders (issue #207 contract): each command module owns its
    # flags and help text beside its handler registration. A command without
    # a builder would be unreachable from the CLI, so fail loudly instead of
    # skipping it silently.
    seen: set[int] = set()
    for command in REGISTRY.all():
        builder = command.add_parser
        if builder is None:
            raise ValueError(
                f"Command {command.name!r} has no co-located add_parser builder."
            )
        if id(builder) in seen:
            continue
        seen.add(id(builder))
        builder(subcommands)

    return parser


def run(
    argv: list[str] | None = None,
    root: Path | str | None = None,
    *,
    clock: Callable[[], datetime] | None = None,
) -> int:
    """Parse `argv`, resolve the root, and dispatch. Returns an exit code.

    `root` (or `--root`) overrides auto-detection; tests pass a temp copy.
    `clock` is an optional wall-clock override threaded through to handlers
    via `Context`; production callers leave it at the default.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if root is not None:
        resolved_root = Path(root)
    elif args.root is not None:
        resolved_root = Path(args.root)
    else:
        resolved_root = find_root()

    command = REGISTRY.get(getattr(args, "_command_name", ""))
    if command is None:  # pragma: no cover - guarded by required subparsers
        parser.error("no command selected")

    return dispatch(command, Context(root=resolved_root, args=args, clock=clock))


def main() -> None:
    """Console-script entry point."""
    import io
    import sys

    # Ensure UTF-8 output on Windows consoles (cp1252 default) so em dashes
    # and other Unicode characters render correctly.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(run())
