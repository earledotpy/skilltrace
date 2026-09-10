"""`skilltrace check-resources` — polite batch sweep over resource URLs (v2.3).

Runs the v1.7 `check_url` sequentially (via the `polite_batch()` helper:
per-host rate limiting, `robots.txt` respect, bounded 429 backoff) over a
selector of registry entries. Read-only: prints one line per resource plus
a summary, exits 0 on answered sweeps (a BROKEN verdict is the resource's,
not the command's), writes nothing (never sets `last_verified`, never
clears or writes `broken`) and emits no audit event.

Respecting disabled seeds: with the sweep policy disabled the command
degrades to the v1.8 behavior (robots skipped, no extra delay, no 429
retries), and out-of-range CLI values fail before any fetch.
"""

from __future__ import annotations

import argparse

from ..dispatch import Command, CommandResult, Context, Kind, Registry
from ..execution.overdue import utc_today
from ..resources.registry import ResourceLoadError, load_resources
from ..resources.status import VerificationStatus, derive_status, stale_after_days
from ..resources.polite_sweep import polite_batch, resolve_polite_sweep_policy
from ..resources.web_check import resolve_web_verification_policy


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

    sweep_policy = resolve_polite_sweep_policy(root)

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
        else policy.user_agent
    )
    respect_robots = (
        False if getattr(ctx.args, "no_robots", False) or not sweep_policy.enabled
        else sweep_policy.respect_robots
    )
    backoff_max_attempts = (
        1
        if not sweep_policy.enabled
        else (
            ctx.args.backoff_attempts
            if ctx.args.backoff_attempts is not None
            else sweep_policy.backoff_max_attempts
        )
    )
    if (
        isinstance(backoff_max_attempts, bool)
        or not isinstance(backoff_max_attempts, int)
        or not (1 <= backoff_max_attempts <= 10)
    ):
        print(
            "check-resources: FAILED — --backoff-attempts must be an "
            f"integer in [1, 10]; got {ctx.args.backoff_attempts!r}."
        )
        return CommandResult(exit_code=1)
    per_host_delay = (
        0.0
        if not sweep_policy.enabled
        else (
            ctx.args.per_host_delay
            if ctx.args.per_host_delay is not None
            else sweep_policy.per_host_delay_seconds
        )
    )
    if (
        isinstance(per_host_delay, bool)
        or not isinstance(per_host_delay, (int, float))
        or not (0 <= per_host_delay <= 600)
    ):
        print(
            "check-resources: FAILED — --per-host-delay must be a number "
            f"in [0, 600]; got {ctx.args.per_host_delay!r}."
        )
        return CommandResult(exit_code=1)
    try:
        pairs = polite_batch(
            [resource.url for resource in selected],
            timeout_seconds=timeout,
            follow_redirects=follow_redirects,
            method=method,
            user_agent=user_agent,
            per_host_delay_seconds=per_host_delay,
            respect_robots=respect_robots,
            backoff_max_attempts=backoff_max_attempts,
            backoff_base_seconds=sweep_policy.backoff_base_seconds,
            backoff_max_seconds=sweep_policy.backoff_max_seconds,
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
            add_parser=add_parser,
        )
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `check-resources` parser to the top-level `subparsers` (issue #207 contract).

    Co-located owner of the `check-resources` argparse surface (issue #207 contract: sole source of CLI flags and help text).
    """
    check_resources_parser = subparsers.add_parser(
        "check-resources",
        help="Check reachability of all (or stale-only) resource URLs (read-only, exits 0 on answered sweep).",
    )
    selector = check_resources_parser.add_mutually_exclusive_group()
    selector.add_argument(
        "--all",
        action="store_true",
        help="Check every resource (the default when no selector is given).",
    )
    selector.add_argument(
        "--stale-only",
        action="store_true",
        help="Check only resources whose derived status is stale under the policy window.",
    )
    check_resources_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds (default: from policy).",
    )
    check_resources_parser.add_argument(
        "--method",
        choices=["HEAD", "GET"],
        default=None,
        help="HTTP method to use (default: from policy).",
    )
    check_resources_parser.add_argument(
        "--follow-redirects",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Follow HTTP redirects (default: from policy).",
    )
    check_resources_parser.add_argument(
        "--user-agent",
        default=None,
        help="Custom User-Agent string.",
    )
    check_resources_parser.add_argument(
        "--per-host-delay",
        type=float,
        default=None,
        help="Minimum seconds between requests to the same host (default: from polite-sweep policy).",
    )
    check_resources_parser.add_argument(
        "--no-robots",
        action="store_true",
        help="Skip robots.txt checks (default: respect robots per polite-sweep policy).",
    )
    check_resources_parser.add_argument(
        "--backoff-attempts",
        type=int,
        default=None,
        help="Max total attempts on HTTP 429 (default: from polite-sweep policy).",
    )
    check_resources_parser.set_defaults(_command_name="check-resources")
