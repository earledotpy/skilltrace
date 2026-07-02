"""`skilltrace next` — recommend what to study next.

Placeholder for this issue; the real recommendation (prerequisite-safe,
policy-weighted, sized to available minutes, each with a stated reason) lands in
issue #7. Read-only: appends no audit event.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry


def recommend_next(ctx: Context) -> CommandResult:
    print(
        "next: not yet implemented (v0.3 issue #7); dispatcher wiring only "
        f"(minutes={ctx.args.minutes}, limit={ctx.args.limit}, "
        f"show_locked={ctx.args.show_locked})."
    )
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="next",
            kind=Kind.READ_ONLY,
            handler=recommend_next,
            help="Recommend prerequisite-safe nodes sized to available minutes.",
        )
    )
