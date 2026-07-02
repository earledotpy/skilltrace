"""`skilltrace validate graph` — read-only graph validation.

Placeholder for this issue; the real graph validation (duplicate/dangling ids,
edge endpoints, hard-prerequisite cycles) lands in issue #5. Read-only: appends
no audit event.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry


def validate_graph(ctx: Context) -> CommandResult:
    print("validate graph: not yet implemented (v0.3 issue #5); dispatcher wiring only.")
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="validate graph",
            kind=Kind.READ_ONLY,
            handler=validate_graph,
            help="Validate the skill graph (nodes, edges, cycles).",
        )
    )
