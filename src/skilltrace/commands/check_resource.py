"""`skilltrace check-resource <resource_id>` — pure read-only URL checker (v1.7 §4.1).

Performs an advisory-only reachability check on a single resource's URL.
Read-only, never writes a marker or changes last_verified, emits no audit event.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..dispatch import Command, CommandResult, Context, Kind, Registry
from ..resources.registry import ResourceLoadError, load_resources
from ..resources.web_check import check_url, resolve_web_verification_policy


def check_resource(ctx: Context) -> CommandResult:
    """Run an advisory URL reachability check against one resource."""
    root = ctx.root
    resource_id = ctx.args.resource_id

    try:
        resources = load_resources(root)
    except ResourceLoadError as exc:
        print(f"check-resource: FAILED — {exc}")
        return CommandResult(exit_code=1)

    target = next((r for r in resources if r.id == resource_id), None)
    if target is None:
        print(f"check-resource: FAILED — unknown resource {resource_id}.")
        return CommandResult(exit_code=1)

    if not target.url:
        print(f"check-resource: FAILED — resource {resource_id} has no url.")
        return CommandResult(exit_code=1)

    policy = resolve_web_verification_policy(root)
    if not policy.enabled:
        print(f"check-resource: FAILED — web check is disabled by policy.")
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
        else "skilltrace/1.7 resource-check"
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
        print(f"check-resource: FAILED — {exc}")
        return CommandResult(exit_code=1)

    if result.ok:
        print(f"check-resource: OK {resource_id} — status {result.status_code}, final_url {result.final_url}")
    else:
        if result.status_code is not None:
            print(f"check-resource: BROKEN {resource_id} — status {result.status_code}: {result.reason}")
        else:
            print(f"check-resource: BROKEN {resource_id} — {result.reason}")

    return CommandResult(exit_code=0)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="check-resource",
            kind=Kind.READ_ONLY,
            handler=check_resource,
            help="Check reachability of a single resource's URL (read-only, exits 0 on answered check).",
            add_parser=add_parser,
        )
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `check-resource` parser to the top-level `subparsers` (issue #207 contract).

    Co-located owner of the `check-resource` argparse surface (issue #207 contract: sole source of CLI flags and help text).
    """
    check_resource_parser = subparsers.add_parser(
        "check-resource",
        help="Check reachability of a single resource's URL (read-only, exits 0 on answered check).",
    )
    check_resource_parser.add_argument(
        "resource_id", help="Resource whose URL to check."
    )
    check_resource_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds (default: from policy).",
    )
    check_resource_parser.add_argument(
        "--method",
        choices=["HEAD", "GET"],
        default=None,
        help="HTTP method to use (default: from policy).",
    )
    check_resource_parser.add_argument(
        "--follow-redirects",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Follow HTTP redirects (default: from policy).",
    )
    check_resource_parser.add_argument(
        "--user-agent",
        default=None,
        help="Custom User-Agent string.",
    )
    check_resource_parser.set_defaults(_command_name="check-resource")
