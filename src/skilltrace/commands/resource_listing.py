"""`skilltrace resources --node-id <node_id>` — what to study from for a node.

Read-only (issue #11): the per-node reverse index over the resource registry, so
a learner starting work on a node can see the LearningResources supporting it,
each with its pointer (URL and/or local path) and claims (cost, free tier,
certificate, license). The index is derived on demand from each resource's
`supports` list — nothing stored — consistent with the engine's derived-facts
discipline. The dispatcher appends no audit event.

This command loads and filters; it does *not* validate. A registry with
integrity issues a `validate resources` run would flag (a duplicate ID, a
dangling reference, an orphan) still lists normally — those are curriculum-
integrity concerns, not load failures. Only a hard load error (unparseable YAML,
a schema violation) or an unloadable graph is an operational failure. The exit
code reports whether the *question* was answerable: an unknown node id or
unloadable data exits non-zero; a node that simply has no linked resources is a
valid, informational empty listing that exits 0 — many nodes legitimately need
no external material.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..graph.nodes import NodeLoadError, load_nodes
from ..resources.registry import (
    LearningResource,
    ResourceLoadError,
    load_resources,
    resources_for_node,
)


def resources(ctx: Context) -> CommandResult:
    """List the resources supporting a node, or report that it has none.

    Loader failures and an unknown node id are operational failures (non-zero
    exit); an empty listing for a real node is an informational exit 0.
    """
    root = ctx.root
    node_id = ctx.args.node_id

    try:
        node_ids = {node.id for node in load_nodes(root)}
        registry = load_resources(root)
    except (NodeLoadError, ResourceLoadError) as exc:
        print(f"resources: FAILED — {exc}")
        return CommandResult(exit_code=1)

    if node_id not in node_ids:
        print(f"resources: FAILED — unknown node {node_id}.")
        return CommandResult(exit_code=1)

    linked = resources_for_node(node_id, registry)
    if not linked:
        print(f"no resources linked to {node_id}.")
        return CommandResult()

    print(f"resources for {node_id}: {len(linked)} resource(s)")
    for resource in linked:
        print(f"  {resource.id}  [{_claims(resource)}]")
        for pointer in _pointers(resource):
            print(f"      {pointer}")
    return CommandResult()


def _claims(resource: LearningResource) -> str:
    """The resource's claims as a compact, comma-joined summary.

    `cost` is always present (the loader guarantees free|paid); the boolean
    claims and the optional license appear only when set, so the summary states
    what the resource actually claims and nothing more.
    """
    parts = [resource.cost]
    if resource.free_tier:
        parts.append("free tier")
    if resource.certificate:
        parts.append("certificate")
    if resource.license:
        parts.append(f"license: {resource.license}")
    return ", ".join(parts)


def _pointers(resource: LearningResource) -> list[str]:
    """The resource's pointer line(s): its URL and/or local path.

    At least one is always present (the loader guarantees a resource points at
    something); both are shown when both are recorded.
    """
    lines: list[str] = []
    if resource.url:
        lines.append(resource.url)
    if resource.local_path:
        lines.append(f"path: {resource.local_path}")
    return lines


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="resources",
            kind=Kind.READ_ONLY,
            handler=resources,
            help="List the resources supporting a node (the per-node reverse index).",
        )
    )
