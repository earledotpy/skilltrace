"""`skilltrace check-automation <action>` — query the automation boundary.

A read-only question, not an attempted action: it reports whether the named
action may ever run on an automated path and where that answer comes from
(the code floor or the policy file). Answering is success — exit 0 even when
the answer is "forbidden"; the command fails only if it cannot answer.
"""

from __future__ import annotations

from ..automation import check_automation
from ..dispatch import Command, Context, CommandResult, Kind, Registry


def check_automation_command(ctx: Context) -> CommandResult:
    verdict = check_automation(ctx.args.action, ctx.root)
    answer = "allowed" if verdict.allowed else "forbidden"
    print(f"check-automation {verdict.action}: {answer} (source: {verdict.source})")
    print(f"  {verdict.reason}")
    return CommandResult()


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="check-automation",
            kind=Kind.READ_ONLY,
            handler=check_automation_command,
            help="Report whether an action may run on an automated path.",
        )
    )
