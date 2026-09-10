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

import argparse

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..resources.registry import ResourceLoadError, load_resources
from ..resources.verification import record_verification, today_iso
from ..resources.web_check import check_url, resolve_web_verification_policy


def verify_resource(ctx: Context) -> CommandResult:
    """Record a verification verdict for one resource.

    Loader failures and an unknown resource id fail the command (exit 1, no
    event); `--broken` without `--reason` is a usage failure (exit 1, no event).
    A recorded verdict — success or broken — exits 0 so the dispatcher logs its
    one event.

    With `--check-url`, runs an automated URL preflight check. A failed preflight
    records a dated broken marker (exit 0, one event). A successful preflight
    never sets `last_verified` or clears `broken` (positive-verification safety;
    writes nothing positive, exit 0, one event).
    """
    root = ctx.root
    resource_id = ctx.args.resource_id
    broken = ctx.args.broken
    reason = ctx.args.reason
    check_url_flag = getattr(ctx.args, "check_url", False)

    if check_url_flag and (broken or reason):
        print(
            "verify-resource: FAILED — cannot combine --check-url with --broken or --reason."
        )
        return CommandResult(exit_code=1)

    try:
        resources = load_resources(root)
    except ResourceLoadError as exc:
        print(f"verify-resource: FAILED — {exc}")
        return CommandResult(exit_code=1)

    target = next((r for r in resources if r.id == resource_id), None)
    if target is None:
        print(f"verify-resource: FAILED — unknown resource {resource_id}.")
        return CommandResult(exit_code=1)

    if check_url_flag:
        if not target.url:
            print(f"verify-resource: FAILED — resource {resource_id} has no url.")
            return CommandResult(exit_code=1)

        policy = resolve_web_verification_policy(root)
        if not policy.enabled:
            print(
                f"verify-resource: FAILED — web check is disabled by policy."
            )
            return CommandResult(exit_code=1)

        timeout = (
            ctx.args.timeout
            if ctx.args.timeout is not None
            else policy.timeout_seconds
        )
        method = (
            ctx.args.method
            if ctx.args.method is not None
            else policy.check_method
        )
        follow_redirects = (
            ctx.args.follow_redirects
            if ctx.args.follow_redirects is not None
            else policy.follow_redirects
        )
        user_agent = (
            ctx.args.user_agent
            if ctx.args.user_agent is not None
            else "skilltrace/1.7 verify-resource"
        )

        try:
            result = check_url(
                target.url,
                timeout_seconds=timeout,
                follow_redirects=follow_redirects,
                method=method,
                user_agent=user_agent,
            )
        except ValueError as exc:
            print(f"verify-resource: FAILED — {exc}")
            return CommandResult(exit_code=1)

        date = today_iso()
        if not result.ok:
            if result.status_code is not None:
                broken_reason = f"status {result.status_code}: {result.reason}"
            else:
                broken_reason = str(result.reason)
            record_verification(
                root,
                resource_id,
                date=date,
                broken_reason=broken_reason,
                status_code=result.status_code,
                final_url=result.final_url,
            )
            print(
                f"verify-resource: {resource_id} marked broken ({date}) — {broken_reason}."
            )
        else:
            # Positive-verification safety: check-url success never sets last_verified or clears broken
            print(
                f"verify-resource: OK {resource_id} — status {result.status_code}, final_url {result.final_url}; positive verification not recorded."
            )
        return CommandResult(records_touched=[resource_id])

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
            add_parser=add_parser,
        )
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `verify-resource` parser to the top-level `subparsers` (issue #207 contract).

    Co-located owner of the `verify-resource` argparse surface (issue #207 contract: sole source of CLI flags and help text).
    """
    verify_resource_parser = subparsers.add_parser(
        "verify-resource",
        help="Record a resource verification (success by default; --broken with --reason for a failed check).",
    )
    verify_resource_parser.add_argument(
        "resource_id", help="Resource whose URL and claims were checked."
    )
    verify_resource_parser.add_argument(
        "--broken",
        action="store_true",
        help="Record a failed check (the dated broken marker) instead of a verification; requires --reason.",
    )
    verify_resource_parser.add_argument(
        "--reason",
        default=None,
        help="Why the resource is broken (required with --broken).",
    )
    verify_resource_parser.add_argument(
        "--check-url",
        action="store_true",
        help="Run automated URL preflight check before recording (records broken on failure; never sets last_verified).",
    )
    verify_resource_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds for --check-url (default: from policy).",
    )
    verify_resource_parser.add_argument(
        "--method",
        choices=["HEAD", "GET"],
        default=None,
        help="HTTP method for --check-url (default: from policy).",
    )
    verify_resource_parser.add_argument(
        "--follow-redirects",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Follow HTTP redirects for --check-url (default: from policy).",
    )
    verify_resource_parser.add_argument(
        "--user-agent",
        default=None,
        help="Custom User-Agent string for --check-url.",
    )
    verify_resource_parser.set_defaults(_command_name="verify-resource")
