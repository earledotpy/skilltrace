"""`skilltrace check-resources` — minimal batch sweep over resource URLs (v1.8 G-Batch).

Runs the v1.7 `check_url` sequentially (via the `batch()` helper: no token
bucket, no `robots.txt`, no retry loop) over a selector of registry entries.
Read-only: prints one line per resource plus a summary, exits 0 on answered
sweeps (a BROKEN verdict is the resource's, not the command's), writes
nothing (never sets `last_verified`, never clears or writes `broken`) and
emits no audit event.
"""

from __future__ import annotations

from ..dispatch import Command, CommandResult, Context, Kind, Registry
from ..execution.overdue import utc_today
from ..resources.registry import ResourceLoadError, load_resources
from ..resources.status import VerificationStatus, derive_status, stale_after_days
from ..resources.web_check import batch, resolve_web_verification_policy


def check_resources(ctx: Context) -> CommandResult:
    """Sweep a selector of resources' URLs and report per-resource verdicts."""
    root = ctx.root

    try:
        resources = load_resources(root)
    except ResourceLoadError as exc:
        print(f"check-resources: FAILED — {exc}")
        return CommandResult(exit_code=1)

    policy = resolve_web_verification_policy(root)
    if not policy.enabled:
        print("check-resources: FAILED — web check is disabled by policy.")
        return CommandResult(exit_code=1)

    if getattr(ctx.args, "stale_only", False):
        today = utc_today(clock=ctx.clock)
        window = stale_after_days(root)
        selected = [
            resource
            for resource in resources
            if derive_status(resource, today=today, stale_after_days=window)
            is VerificationStatus.STALE
        ]
    else:
        selected = list(resources)

    for resource in selected:
        if not resource.url:
            print(
                f"check-resources: FAILED — resource {resource.id} has no url."
            )
            return CommandResult(exit_code=1)

    timeout = ctx.args.timeout if ctx.args.timeout is not None else policy.timeout_seconds
    method = ctx.args.method if ctx.args.method is not None else policy.check_method
    follow_redirects = (
        ctx.args.follow_redirects
        if ctx.args.follow_redirects is not None
        else policy.follow_redirects
    )
    user_agent = (
        ctx.args.user_agent
        if ctx.args.user_agent is not None
        else "skilltrace/1.8 check-resources"
    )

    try:
        pairs = batch(
            [resource.url for resource in selected],
            timeout_seconds=timeout,
            follow_redirects=follow_redirects,
            method=method,
            user_agent=user_agent,
        )
    except ValueError as exc:
        print(f"check-resources: FAILED — {exc}")
        return CommandResult(exit_code=1)

    ok_count = 0
    for resource, (_, result) in zip(selected, pairs):
        if result.ok:
            ok_count += 1
            print(
                f"check-resources: OK {resource.id} — status "
                f"{result.status_code}, final_url {result.final_url}"
            )
        elif result.status_code is not None:
            print(
                f"check-resources: BROKEN {resource.id} — status "
                f"{result.status_code}: {result.reason}"
            )
        else:
            print(f"check-resources: BROKEN {resource.id} — {result.reason}")

    checked = len(selected)
    print(
        f"check-resources: {checked} checked, {ok_count} OK, "
        f"{checked - ok_count} BROKEN"
    )
    return CommandResult(exit_code=0)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="check-resources",
            kind=Kind.READ_ONLY,
            handler=check_resources,
            help="Check reachability of all (or stale-only) resource URLs (read-only, exits 0 on answered sweep).",
        )
    )
