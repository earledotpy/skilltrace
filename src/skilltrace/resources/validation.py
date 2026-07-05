"""Resource-registry validation — the curriculum-integrity contract (v0.7).

`validate resources` judges the registry's integrity and nothing else. It is
curriculum-integrity only: it never reads verification dates and never reads the
progress store, so its output is a property of the curriculum alone, stable
across every learner state. Resource status is pure advice (CONTEXT.md); nothing
here can affect readiness, eligibility, or node state.

The contract, mirroring the evidence layer's split of per-record shape (the
loader) from cross-record integrity (here):

**Errors** (fail the run, non-zero exit):

- duplicate resource IDs within the registry;
- a dangling node reference — a `supports` entry naming a node that does not
  exist;
- schema violations the loader raises (non-mapping, unknown field, bad slug,
  neither URL nor path, malformed `supports`), folded in so a bad file is a
  reported error, not a traceback.

**Warnings** (advisory, exit 0):

- an orphan resource — one supporting no node, like a gateless node.

Two design rules match the other layers: **state-independent** (never reads
`graph/state.yaml`) and **deterministic order** (sets for membership only; every
error and warning is emitted by iterating an ordered list, first-seen).

The seam mirrors `evidence.validation`: a pure `check_resources(...)` over
already-loaded data, and `load_and_validate_resources(root)` which loads the
graph's node IDs plus the registry, folding load errors into the result.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from ..graph.nodes import NodeLoadError, load_nodes
from .registry import LearningResource, ResourceLoadError, load_resources


@dataclass
class ResourceValidationResult:
    """The outcome of a resource-registry validation run.

    `errors` fail the run (`ok` false, command exits non-zero); `warnings` are
    advisory and never affect `ok`. `resource_count` feeds the summary line.
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    resource_count: int = 0

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


def check_resources(
    node_ids: list[str], resources: list[LearningResource]
) -> ResourceValidationResult:
    """Validate an already-loaded registry against the graph's node IDs. Pure.

    Reports *every* issue: duplicate IDs and dangling node references as errors,
    orphan resources (supporting no node) as warnings. Each resource's shape is
    assumed already validated by the loader.
    """
    result = ResourceValidationResult(resource_count=len(resources))

    for dup in _duplicates(resource.id for resource in resources):
        result.errors.append(
            f"duplicate resource id: {dup} appears more than once."
        )

    known_nodes = set(node_ids)
    for resource in resources:
        for node_id in resource.supports:
            if node_id not in known_nodes:
                result.errors.append(
                    f"resource {resource.id}: supports names unknown node {node_id}."
                )
        if not resource.supports:
            result.warnings.append(
                f"resource {resource.id} supports no node — it is linked to nothing "
                "and serves no node's study."
            )

    return result


def load_and_validate_resources(
    root: Path | str | None = None,
) -> ResourceValidationResult:
    """Load the graph's node IDs + the registry, then `check_resources` them.

    Loader failures (node or registry) are folded into the result's errors so the
    command reports bad data rather than tracebacking. Node IDs come from the
    graph because the registry lives in the curriculum area and its links are
    judged against real nodes.
    """
    from ..paths import find_root

    root_path = Path(root) if root is not None else find_root()
    load_errors: list[str] = []

    try:
        node_ids = [node.id for node in load_nodes(root_path)]
    except NodeLoadError as exc:
        node_ids = []
        load_errors.append(str(exc))

    try:
        resources = load_resources(root_path)
    except ResourceLoadError as exc:
        resources = []
        load_errors.append(str(exc))

    result = check_resources(node_ids, resources)
    # Load errors come first — they explain any downstream emptiness.
    result.errors[:0] = load_errors
    return result
