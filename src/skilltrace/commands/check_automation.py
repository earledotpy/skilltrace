"""`skilltrace check-automation <action>` — query the automation boundary.

A read-only question, not an attempted action: it reports whether the named
action may ever run on an automated path and where that answer comes from
(the code floor or the policy file). Answering is success — exit 0 even when
the answer is "forbidden"; the command fails only if it cannot answer.
"""

from __future__ import annotations

import argparse

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
            add_parser=add_parser,
        )
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `check-automation` parser (issue #206, expand–contract).

    Co-located owner of the `check-automation` argparse surface;
    `cli.build_parser` calls this for the new path and skips its legacy
    `check-automation` block.
    """
    check_parser = subparsers.add_parser(
        "check-automation",
        help="Report whether an action may run on an automated path.",
    )
    check_parser.add_argument(
        "action", help="Automation action label, e.g. pass_node or schedule_review."
    )
    check_parser.set_defaults(_command_name="check-automation")
