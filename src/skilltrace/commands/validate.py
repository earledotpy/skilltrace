"""`skilltrace validate graph` — read-only whole-graph validation (issue #5).

Runs `load_and_validate` (loaders + cross-reference checks), prints a summary
line plus any errors and warnings, and exits non-zero iff there are errors.
Warnings never affect the exit code. Read-only: appends no audit event.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..graph.validation import ValidationResult, load_and_validate


def _print_report(result: ValidationResult) -> None:
    states = ", ".join(f"{state}={n}" for state, n in sorted(result.state_counts.items()))
    print(
        f"graph: {result.node_count} nodes, {result.edge_count} edges "
        f"({result.active_edge_count} active)"
        + (f"; states: {states}" if states else "")
    )
    for warning in result.warnings:
        print(f"[warning] {warning}")
    for error in result.errors:
        print(f"[error] {error}")

    if result.ok:
        suffix = f" ({len(result.warnings)} warning(s))" if result.warnings else ""
        print(f"validate graph: OK{suffix}.")
    else:
        print(f"validate graph: FAILED — {len(result.errors)} error(s).")


def validate_graph(ctx: Context) -> CommandResult:
    result = load_and_validate(ctx.root)
    _print_report(result)
    return CommandResult(exit_code=0 if result.ok else 1)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="validate graph",
            kind=Kind.READ_ONLY,
            handler=validate_graph,
            help="Validate the skill graph (nodes, edges, cycles).",
        )
    )
