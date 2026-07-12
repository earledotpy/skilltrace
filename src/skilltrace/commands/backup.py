"""`skilltrace backup` — zip the five data layers to a timestamped archive.

Mutating (the #33 resolution): the learner's explicit call still appends one
audit event. Takes no arguments beyond the subcommand itself; `records_touched`
is empty because backup mutates no domain record, only a fresh file under
`backups/`.
"""

from __future__ import annotations

from ..backup import create_backup
from ..dispatch import Command, Context, CommandResult, Kind, Registry


def backup(ctx: Context) -> CommandResult:
    path = create_backup(ctx.root)
    print(f"backup: wrote {path.relative_to(ctx.root).as_posix()}")
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="backup",
            kind=Kind.MUTATING,
            handler=backup,
            help="Zip graph/evidence/execution/policy/release into a timestamped archive under backups/.",
        )
    )
