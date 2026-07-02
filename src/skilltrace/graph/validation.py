"""Graph validation — the Layer 1 cross-reference contract (issue #5).

The node and edge loaders validate the *shape* of one file at a time; they
deliberately do **not** collapse duplicate ids, check that an edge names a real
node, or find cycles (see their module docstrings). That whole-graph integrity
check lives here, composed from the raw loaded lists, so the contract is:

- **unique** node ids and edge ids;
- every edge `source`/`target` names a real node (checked for *all* edges,
  active or not — a dangling endpoint is a data error even when the edge is
  parked, and node ids are immutable/never-reused so it is always a typo);
- **no cycle among active hard prerequisites** (`active` means "in force", and
  only in-force hard prereqs lock a node), reported with the closing path;
- **no dangling progress reference** — every progress entry names a real node
  (the immutable-ID safety net, decision 14), reusing `check_state_references`.

Soft-prerequisite issues are **warnings**, never errors: a soft-prerequisite
cycle is surfaced (it is the one warning this layer emits today) but does not
change `ok` or the command's exit code, because soft prerequisites never lock.

Note — "unmapped tracks" (issue #5 scope) is intentionally *not* implemented:
there is no track registry to map against, and hardcoding an allowlist of track
names in engine code would violate the curriculum-agnostic invariant (tracks are
seed data, not engine constants). It is deferred pending a track registry.

The seam mirrors the loaders: `check_graph(nodes, edges, store)` is a pure
function over already-loaded data (the TDD/unit seam); `load_and_validate(root)`
loads the three sources — folding load errors and missing-file cases into the
result — and calls it. The `validate graph` command renders the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from ..paths import find_root
from .edges import EdgeLoadError, GraphEdge, load_edges
from .nodes import NodeLoadError, SkillNode, load_nodes
from .state import (
    ProgressStore,
    ProgressStoreError,
    check_state_references,
    load_state,
)

_EDGES_RELPATH = Path("graph") / "edges.yaml"


@dataclass
class ValidationResult:
    """The outcome of a whole-graph validation run.

    `errors` are contract violations that fail the run (`ok` is false and the
    command exits non-zero); `warnings` are advisory and never affect `ok`. The
    counts feed the command's summary line.
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    active_edge_count: int = 0
    state_counts: dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def _duplicates(ids: Iterable[str]) -> list[str]:
    """Return, in first-seen order, every id that appears more than once."""
    seen: set[str] = set()
    dupes: dict[str, None] = {}  # ordered set
    for value in ids:
        if value in seen:
            dupes.setdefault(value, None)
        seen.add(value)
    return list(dupes)


def _find_cycle(edges: list[GraphEdge]) -> list[str] | None:
    """Return the node ids of one directed cycle (closed: first == last), or None.

    Edges are followed `source -> target` (prerequisite -> dependent). Iterative
    DFS with a gray/black colouring; when a gray node is re-entered the path is
    reconstructed from the current stack so the closure is visible.
    """
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge.source, []).append(edge.target)

    WHITE, GRAY, BLACK = 0, 1, 2
    colour: dict[str, int] = {}

    for start in adjacency:
        if colour.get(start, WHITE) != WHITE:
            continue
        # `path` doubles as the DFS stack and the gray chain; `iters[-1]` is the
        # successor cursor for `path[-1]`.
        path: list[str] = [start]
        colour[start] = GRAY
        iters: list[Iterator[str]] = [iter(adjacency.get(start, ()))]
        while path:
            try:
                nxt = next(iters[-1])
            except StopIteration:
                colour[path.pop()] = BLACK
                iters.pop()
                continue
            state = colour.get(nxt, WHITE)
            if state == GRAY:
                # Cycle: nxt is on the current path; close it from that point.
                idx = path.index(nxt)
                return path[idx:] + [nxt]
            if state == WHITE:
                colour[nxt] = GRAY
                path.append(nxt)
                iters.append(iter(adjacency.get(nxt, ())))
    return None


def check_graph(
    nodes: list[SkillNode], edges: list[GraphEdge], store: ProgressStore
) -> ValidationResult:
    """Validate already-loaded graph data. Pure — no I/O; reports *every* issue.

    See the module docstring for the contract. Node/edge *shape* is assumed
    already validated by the loaders; this checks the graph as a whole.
    """
    result = ValidationResult(
        node_count=len(nodes),
        edge_count=len(edges),
        active_edge_count=sum(1 for e in edges if e.active),
    )

    for entry in store.entries.values():
        result.state_counts[entry.state] = result.state_counts.get(entry.state, 0) + 1

    known_ids = {node.id for node in nodes}

    # Duplicate node ids.
    for dup in _duplicates(node.id for node in nodes):
        result.errors.append(f"duplicate node id: {dup} appears more than once.")

    # Duplicate edge ids.
    for dup in _duplicates(edge.id for edge in edges):
        result.errors.append(f"duplicate edge id: {dup} appears more than once.")

    # Edge endpoints must name real nodes — all edges, active or not.
    for edge in edges:
        for role, endpoint in (("source", edge.source), ("target", edge.target)):
            if endpoint not in known_ids:
                result.errors.append(
                    f"edge {edge.id}: {role} names unknown node {endpoint}."
                )

    # Cycle among active hard prerequisites (in-force locking edges only).
    hard = [
        e for e in edges if e.active and e.edge_type == "hard_prerequisite"
    ]
    cycle = _find_cycle(hard)
    if cycle is not None:
        result.errors.append(
            "hard-prerequisite cycle (nodes lock each other forever): "
            + " -> ".join(cycle)
        )

    # Dangling progress references — reuse the tested state-store check.
    try:
        check_state_references(store, known_ids)
    except ProgressStoreError as exc:
        result.errors.append(str(exc))

    # Soft-prerequisite cycle — advisory only (soft prereqs never lock).
    soft = [e for e in edges if e.active and e.edge_type == "soft_prerequisite"]
    soft_cycle = _find_cycle(soft)
    if soft_cycle is not None:
        result.warnings.append(
            "soft-prerequisite cycle (advisory, does not lock): "
            + " -> ".join(soft_cycle)
        )

    return result


def load_and_validate(root: Path | str | None = None) -> ValidationResult:
    """Load nodes, edges, and the progress store, then `check_graph` them.

    Loader failures are *folded into* the result's errors (a validation command
    reports bad data, it does not traceback). A missing `edges.yaml` or empty
    `graph/nodes/` is treated as an empty graph — a fresh repo is valid, not
    broken — mirroring `load_state`'s missing-file handling.
    """
    root_path = Path(root) if root is not None else find_root()
    result_errors: list[str] = []

    try:
        nodes = load_nodes(root_path)
    except NodeLoadError as exc:
        nodes = []
        result_errors.append(str(exc))

    edges: list[GraphEdge] = []
    if (root_path / _EDGES_RELPATH).exists():
        try:
            edges = load_edges(root_path)
        except EdgeLoadError as exc:
            result_errors.append(str(exc))

    try:
        store = load_state(root_path)
    except ProgressStoreError as exc:
        store = ProgressStore()
        result_errors.append(str(exc))

    result = check_graph(nodes, edges, store)
    # Load errors come first — they explain any downstream emptiness.
    result.errors[:0] = result_errors
    return result
