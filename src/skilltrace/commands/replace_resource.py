"""`skilltrace replace-resource <broken_id> <candidate_id> [--dry-run]` (v1.7 §4.3).

Human-initiated mutating command to retire an ailing (broken or stale) resource
and transfer its coverage to a live, verified candidate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..dispatch import Command, CommandResult, Context, Kind, Registry
from ..execution.overdue import utc_today
from ..graph.nodes import NodeLoadError, load_nodes
from ..resources.registry import ResourceLoadError, load_resources
from ..resources.replacement import record_replacement
from ..resources.status import VerificationStatus, derive_status, stale_after_days
from ..resources.validation import check_resources


def replace_resource(ctx: Context) -> CommandResult:
    """Retire broken_id and transfer its coverage to candidate_id."""
    root = ctx.root
    broken_id = ctx.args.broken_id
    candidate_id = ctx.args.candidate_id
    dry_run = getattr(ctx.args, "dry_run", False)

    if not broken_id or not candidate_id or broken_id == candidate_id:
        print("replace-resource: FAILED — source and candidate resource IDs must be non-empty and distinct.")
        return CommandResult(exit_code=1)

    today = utc_today(clock=ctx.clock)
    window = (
        ctx.joined.policy.resource_stale_after_days
        if ctx.joined is not None
        else stale_after_days(root)
    )

    try:
        nodes = load_nodes(root)
        resources = load_resources(root)
    except (NodeLoadError, ResourceLoadError) as exc:
        print(f"replace-resource: FAILED — {exc}")
        return CommandResult(exit_code=1)

    node_ids = [node.id for node in nodes]
    validation = check_resources(node_ids, resources)
    if not validation.ok:
        print(f"replace-resource: FAILED — invalid registry data: {validation.errors[0]}")
        return CommandResult(exit_code=1)

    source = next((r for r in resources if r.id == broken_id), None)
    if source is None:
        print(f"replace-resource: FAILED — unknown resource {broken_id}.")
        return CommandResult(exit_code=1)

    candidate = next((r for r in resources if r.id == candidate_id), None)
    if candidate is None:
        print(f"replace-resource: FAILED — unknown candidate resource {candidate_id}.")
        return CommandResult(exit_code=1)

    if candidate.retired:
        print(f"replace-resource: FAILED — candidate {candidate_id} is retired.")
        return CommandResult(exit_code=1)

    cand_status = derive_status(candidate, today=today, stale_after_days=window)
    if cand_status != VerificationStatus.VERIFIED:
        print(
            f"replace-resource: FAILED — candidate {candidate_id} is {cand_status.value}; "
            "candidate must be verified."
        )
        return CommandResult(exit_code=1)

    if source.retired:
        print(f"replace-resource: FAILED — source resource {broken_id} is already retired.")
        return CommandResult(exit_code=1)

    src_status = derive_status(source, today=today, stale_after_days=window)
    if src_status not in (VerificationStatus.BROKEN, VerificationStatus.STALE):
        print(
            f"replace-resource: FAILED — source resource {broken_id} is {src_status.value}; "
            "source must be broken or stale."
        )
        return CommandResult(exit_code=1)

    shared_nodes = [n for n in source.supports if n in candidate.supports]
    if not shared_nodes:
        print(f"replace-resource: FAILED — resources {broken_id} and {candidate_id} share no node.")
        return CommandResult(exit_code=1)

    nodes_to_add = [n for n in source.supports if n not in candidate.supports]
    if not nodes_to_add:
        print(
            f"replace-resource: FAILED — candidate {candidate_id} already covers "
            f"every node supported by {broken_id}."
        )
        return CommandResult(exit_code=1)

    supports_after = list(candidate.supports) + nodes_to_add
    date_str = today.isoformat()

    if dry_run:
        payload = {
            "command": "replace-resource",
            "broken_id": broken_id,
            "candidate_id": candidate_id,
            "retired_at": date_str,
            "candidate": {
                "supports_before": list(candidate.supports),
                "supports_after": supports_after,
                "supports_added": nodes_to_add,
            },
            "broken": {
                "retired": True,
                "retired_at": date_str,
                "replaced_by": candidate_id,
            },
            "writes": [],
        }
        print(json.dumps(payload, separators=(",", ":")))
        return CommandResult(exit_code=0)

    record_replacement(
        root,
        broken_id=broken_id,
        candidate_id=candidate_id,
        retired_at=date_str,
        supports_after=supports_after,
    )
    print(f"replace-resource: {broken_id} replaced by {candidate_id} (retired {date_str}).")
    return CommandResult(records_touched=[broken_id, candidate_id])


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="replace-resource",
            kind=Kind.MUTATING,
            handler=replace_resource,
            help="Retire a broken or stale resource and transfer coverage to a candidate.",
            add_parser=add_parser,
        )
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `replace-resource` parser to the top-level `subparsers` (issue #204).

    Co-located owner of the `replace-resource` argparse surface; `cli.build_parser`
    calls this for the new path and skips its legacy `replace-resource` block.
    """
    replace_resource_parser = subparsers.add_parser(
        "replace-resource",
        help="Retire an ailing resource and transfer its coverage to an active verified candidate.",
    )
    replace_resource_parser.add_argument(
        "broken_id", help="Resource ID of the broken or stale resource to retire."
    )
    replace_resource_parser.add_argument(
        "candidate_id", help="Resource ID of the verified replacement candidate."
    )
    replace_resource_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and output planned changes as JSON without writing.",
    )
    replace_resource_parser.set_defaults(_command_name="replace-resource")
