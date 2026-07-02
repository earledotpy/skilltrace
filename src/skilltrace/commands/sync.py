"""`skilltrace sync` — recompute derived readiness.

Placeholder for this issue; the real readiness sync (writing only
`locked`/`available` over derived states, never asserted progress) lands in
issue #6. Mutating: the dispatcher appends exactly one audit event listing the
records touched. The placeholder touches nothing, so the event carries an empty
list — which stays true and faithful once #6 makes it real.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry


def sync(ctx: Context) -> CommandResult:
    print("sync: not yet implemented (v0.3 issue #6); dispatcher wiring only.")
    return CommandResult(records_touched=[])


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="sync",
            kind=Kind.MUTATING,
            handler=sync,
            help="Recompute derived readiness (locked/available) for every node.",
        )
    )
