"""`skilltrace` command-line entry point.

Builds the argparse surface, resolves the repo root, and hands the parsed
command to the dispatcher (which owns audit logging and the automation
boundary). The v0.3 surface is `validate graph`, `sync`, and `next`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

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
    internals.
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

    # validate <target>
    validate_parser = subcommands.add_parser(
        "validate", help="Validate a layer of the repository."
    )
    validate_targets = validate_parser.add_subparsers(dest="_target", metavar="<target>")
    validate_targets.required = True
    graph_parser = validate_targets.add_parser(
        "graph", help="Validate the skill graph (nodes, edges, cycles)."
    )
    graph_parser.set_defaults(_command_name="validate graph")

    # sync
    sync_parser = subcommands.add_parser(
        "sync", help="Recompute derived readiness (locked/available) for every node."
    )
    sync_parser.set_defaults(_command_name="sync")

    # next
    next_parser = subcommands.add_parser(
        "next", help="Recommend prerequisite-safe nodes sized to available minutes."
    )
    next_parser.add_argument(
        "--minutes", type=int, default=60, help="Minutes available this session."
    )
    next_parser.add_argument(
        "--limit", type=int, default=5, help="Maximum number of recommendations."
    )
    next_parser.add_argument(
        "--show-locked",
        action="store_true",
        help="Also show locked nodes (never recommended as available).",
    )
    next_parser.set_defaults(_command_name="next")

    return parser


def run(argv: list[str] | None = None, root: Path | str | None = None) -> int:
    """Parse `argv`, resolve the root, and dispatch. Returns an exit code.

    `root` (or `--root`) overrides auto-detection; tests pass a temp copy.
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

    return dispatch(command, Context(root=resolved_root, args=args))


def main() -> None:
    """Console-script entry point."""
    raise SystemExit(run())
