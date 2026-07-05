"""`skilltrace verify-resource <resource_id>` — the human verification workflow.

Verified is a dated human assertion that a resource's URL resolves and its
recorded claims still hold (CONTEXT.md). This command is the registry's *only*
mutating operation, and the sole setter of `last_verified` — positive
verification is a human act forever, so no automated path ever writes it. It
carries **no** `automation_action`: nothing fires verification as a side effect
of another command, so there is no automation to gate; the boundary layer stops
side-effect automation, not this explicit learner act.

Two verdicts:

- **Success** (the default — the command name *is* the verdict): sets
  `last_verified` to today and clears any broken marker.
- **Failure** (`--broken`, `--reason` required): records the dated broken marker
  with that reason and leaves `last_verified` untouched — a failed check is not a
  verification.

Both verdicts are a *successful command invocation* (exit 0): "failure" is the
resource's verdict, not the command's, so the dispatcher appends exactly one
audit event either way. An unknown resource id, or `--broken` without a reason,
is a command failure (non-zero exit) that writes nothing and logs nothing —
existence and arguments are checked before any write, so "no record is written"
holds. There is no verification-history store: the event log is the audit trail
and the resource carries only current truth.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..resources.registry import ResourceLoadError, load_resources
from ..resources.verification import record_verification, today_iso


def verify_resource(ctx: Context) -> CommandResult:
    """Record a verification verdict for one resource.

    Loader failures and an unknown resource id fail the command (exit 1, no
    event); `--broken` without `--reason` is a usage failure (exit 1, no event).
    A recorded verdict — success or broken — exits 0 so the dispatcher logs its
    one event.
    """
    root = ctx.root
    resource_id = ctx.args.resource_id
    broken = ctx.args.broken
    reason = ctx.args.reason

    try:
        resources = load_resources(root)
    except ResourceLoadError as exc:
        print(f"verify-resource: FAILED — {exc}")
        return CommandResult(exit_code=1)

    if not any(resource.id == resource_id for resource in resources):
        print(f"verify-resource: FAILED — unknown resource {resource_id}.")
        return CommandResult(exit_code=1)

    if broken and not reason:
        print(
            "verify-resource: FAILED — a broken check requires --reason; "
            "a failed check must record why."
        )
        return CommandResult(exit_code=1)
    if reason and not broken:
        print(
            "verify-resource: FAILED — --reason only applies to a broken check "
            "(--broken); a successful verification records no reason."
        )
        return CommandResult(exit_code=1)

    date = today_iso()
    record_verification(
        root, resource_id, date=date, broken_reason=reason if broken else None
    )

    if broken:
        print(f"verify-resource: {resource_id} marked broken ({date}) — {reason}.")
    else:
        print(f"verify-resource: {resource_id} verified on {date}.")
    return CommandResult(records_touched=[resource_id])


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="verify-resource",
            kind=Kind.MUTATING,
            handler=verify_resource,
            help="Record a resource verification (success by default; --broken with --reason for a failed check).",
        )
    )
