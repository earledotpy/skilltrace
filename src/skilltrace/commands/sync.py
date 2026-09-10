"""`skilltrace sync` — recompute derived readiness (locked/available).

Loads nodes, edges, and the progress store, recomputes derived readiness for
every non-asserted node (`..graph.readiness.sync_readiness`), and persists the
store. Mutating: the dispatcher appends exactly one audit event whose
`records_touched` is the list of node ids whose readiness flipped — empty when
the graph is already in sync (still one event, matching the audit contract).

Sync never writes asserted progress (`active`/`passed`/`mastered`); that is the
whole point of the derived/asserted split and is enforced in the readiness layer
and the store's `write_readiness` guard, not here.
"""

from __future__ import annotations

import argparse

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..graph.edges import EdgeLoadError, GraphEdge, load_edges
from ..graph.nodes import NodeLoadError, load_nodes
from ..graph.readiness import SyncResult, sync_readiness
from ..graph.state import ProgressStoreError, load_state, save_state

_EDGES_RELPATH = "graph/edges.yaml"


def _print_report(result: SyncResult) -> None:
    if not result.changes:
        print(
            f"sync: {result.node_count} node(s) checked; readiness already current "
            "(no changes)."
        )
        return
    print(f"sync: {len(result.changes)} node(s) changed readiness:")
    for change in sorted(result.changes, key=lambda c: c.node_id):
        print(f"  {change.node_id}: {change.old_state} -> {change.new_state}")


def sync(ctx: Context) -> CommandResult:
    """Recompute and persist derived readiness. Returns the changed node ids.

    Loader failures fail the command (non-zero exit, no event) rather than
    tracebacking, matching how the validation command surfaces bad data.
    """
    root = ctx.root

    try:
        nodes = load_nodes(root)
        edges: list[GraphEdge] = load_edges(root) if (root / _EDGES_RELPATH).exists() else []
        store = load_state(root)
    except (NodeLoadError, EdgeLoadError, ProgressStoreError) as exc:
        print(f"sync: FAILED — {exc}")
        return CommandResult(exit_code=1)

    result = sync_readiness(nodes, edges, store)
    if result.changes:
        save_state(store, root)
    _print_report(result)

    return CommandResult(records_touched=result.changed_ids)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="sync",
            kind=Kind.MUTATING,
            handler=sync,
            help="Recompute derived readiness (locked/available) for every node.",
            add_parser=add_parser,
        )
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach `sync`'s parser to the top-level `subparsers` (issue #204).

    Co-located owner of the `sync` argparse surface; `cli.build_parser`
    calls this for the new path and skips its legacy `sync` block.
    """
    sync_parser = subparsers.add_parser(
        "sync", help="Recompute derived readiness (locked/available) for every node."
    )
    sync_parser.set_defaults(_command_name="sync")
