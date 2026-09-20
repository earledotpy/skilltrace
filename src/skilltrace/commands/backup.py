"""`skilltrace backup` — zip the five data layers to a timestamped archive.

Mutating (the #33 resolution): the learner's explicit call still appends one
audit event. Takes no arguments beyond the subcommand itself; `records_touched`
is empty because backup mutates no domain record, only a fresh file under
`backups/`.
"""

from __future__ import annotations

import argparse
from datetime import datetime

from ..backup import create_backup
from ..dispatch import Command, Context, CommandResult, Kind, Registry


def _backup_moment(clock) -> datetime | None:
    """The dispatcher's clock override as a `create_backup` moment, or None.

    ``create_backup(now=None)`` reads the wall clock itself, so production
    behavior is unchanged; a fixture clock is threaded through so the
    timestamped archive name follows the simulation (issue #308).
    """
    return clock() if clock is not None else None


def backup(ctx: Context) -> CommandResult:
    path = create_backup(ctx.root, now=_backup_moment(ctx.clock))
    print(f"backup: wrote {path.relative_to(ctx.root).as_posix()}")
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="backup",
            kind=Kind.MUTATING,
            handler=backup,
            help="Zip graph/evidence/execution/policy/release into a timestamped archive under backups/.",
            add_parser=add_parser,
        )
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `backup` parser (issue #207 contract).

    Co-located owner of the `backup` argparse surface (issue #207 contract: sole source of CLI flags and help text).
    """
    backup_parser = subparsers.add_parser(
        "backup",
        help="Zip graph/evidence/execution/policy/release into a timestamped archive under backups/.",
    )
    backup_parser.set_defaults(_command_name="backup")
