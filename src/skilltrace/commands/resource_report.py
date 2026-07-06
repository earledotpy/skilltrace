"""`skilltrace resource-report` — the resource verification status snapshot.

A read-only, always-exit-0 status snapshot of the whole resource registry. It is
the lowest advisory tier (issue #13): resource trouble *warns here and nowhere
else* — it never blocks a command, never changes node readiness/eligibility/
state, and never feeds recommendation ordering. Unlike `resources --node-id`
(which exits non-zero when its *question* cannot be answered), resource-report is
a snapshot that degrades gracefully: even an unreadable registry prints a loud
line and still exits 0. Integrity is `validate resources`' job (that command
exits non-zero); this one only reports current status. The dispatcher appends no
audit event.

The report, worst-first so the next verification or replacement action is
obvious:

- **per-resource derived status** — unverified / verified / stale / broken
  (CONTEXT.md's words), derived on demand, never stored, with broken and stale
  grouped first;
- **replacement candidates** surfaced alongside each broken resource — any live
  resource sharing one of its nodes (there is no `replaces` field; promotion is a
  human curriculum edit);
- **warnings** — a `local_path` that does not resolve on disk is an environment
  observation (like artifact drift), a report warning only; `validate resources`
  ignores it;
- **coverage** — nodes with no linked resource, as information, not a warning
  (many nodes legitimately need no external material).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..graph.nodes import NodeLoadError, load_nodes
from ..resources.registry import (
    LearningResource,
    ResourceLoadError,
    load_resources,
    resources_for_node,
)
from ..resources.status import (
    VerificationStatus,
    derive_status,
    group_rank,
    replacement_candidates,
    stale_after_days,
)


def resource_report(ctx: Context) -> CommandResult:
    """Print the resource verification snapshot. Always exit 0, always read-only.

    Loader failures (bad registry, unloadable graph) are reported as loud lines
    rather than a non-zero exit — this command is a status snapshot, not an
    integrity gate. Every resource's derived status, the broken/stale grouping,
    replacement candidates, missing-file warnings, and node coverage are printed
    from whatever data loads.
    """
    root = ctx.root
    today = datetime.now(timezone.utc).date()
    window = stale_after_days(root)

    resources, node_ids, load_notes = _load(root)

    print(
        f"resource-report: {len(resources)} resource(s), {len(node_ids)} node(s); "
        f"stale after {window}d."
    )
    for note in load_notes:
        print(f"[error] {note}")

    _print_statuses(resources, today=today, window=window)
    _print_warnings(root, resources)
    _print_coverage(node_ids, resources)
    return CommandResult()


def _load(
    root: Path,
) -> tuple[list[LearningResource], list[str], list[str]]:
    """Load resources and node IDs, folding any load failure into report notes.

    Each loader is tried independently so one bad file does not blank the other
    half of the report. A failure yields an empty list plus a note; the command
    stays exit 0 regardless.
    """
    notes: list[str] = []
    try:
        resources = load_resources(root)
    except ResourceLoadError as exc:
        resources = []
        notes.append(f"could not read the resource registry: {exc}")
    try:
        node_ids = [node.id for node in load_nodes(root)]
    except NodeLoadError as exc:
        node_ids = []
        notes.append(f"could not read the graph: {exc}")
    return resources, node_ids, notes


def _print_statuses(
    resources: list[LearningResource], *, today, window: int
) -> None:
    """Print every resource's derived status, worst-first (broken and stale top).

    `sorted` is stable, so within each status group resources keep registry
    (file) order — the codebase's determinism discipline. Each broken resource
    carries its reason and date and its live replacement candidates.
    """
    if not resources:
        print("no resources in the registry.")
        return

    statuses = {
        resource.id: derive_status(resource, today=today, stale_after_days=window)
        for resource in resources
    }
    ordered = sorted(resources, key=lambda r: group_rank(statuses[r.id]))

    print("resources:")
    for resource in ordered:
        status = statuses[resource.id]
        print(f"  [{status.value}] {resource.id} — {_status_detail(resource, status)}")
        if status is VerificationStatus.BROKEN:
            candidates = replacement_candidates(resource, resources)
            if candidates:
                names = ", ".join(candidate.id for candidate in candidates)
                print(f"      replacement candidates: {names}")
            else:
                print("      replacement candidates: none on its node(s)")


def _status_detail(resource: LearningResource, status: VerificationStatus) -> str:
    """The trailing clause for a status line: reason/date for the status word."""
    if status is VerificationStatus.BROKEN:
        assert resource.broken is not None  # broken status implies the marker
        return f"broken {resource.broken.date}: {resource.broken.reason}"
    if status is VerificationStatus.STALE:
        return f"last verified {resource.last_verified} (older than the window)"
    if status is VerificationStatus.VERIFIED:
        return f"last verified {resource.last_verified}"
    return "never verified"


def _print_warnings(root: Path, resources: list[LearningResource]) -> None:
    """Warn for each resource whose `local_path` does not resolve on disk.

    A missing local file is an environment observation (like artifact drift), not
    a curriculum error: it warns here only and `validate resources` ignores it. A
    resource with no `local_path` (URL-only) is never warned about.
    """
    warnings: list[str] = []
    for resource in resources:
        if resource.local_path and not _resolve(root, resource.local_path).exists():
            warnings.append(
                f"resource {resource.id}: local file {resource.local_path!r} "
                "not found on disk."
            )
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"  [warning] {warning}")


def _resolve(root: Path, local_path: str) -> Path:
    """A resource's local path resolved against the repo root (absolute as-is)."""
    candidate = Path(local_path)
    return candidate if candidate.is_absolute() else root / candidate


def _print_coverage(node_ids: list[str], resources: list[LearningResource]) -> None:
    """List nodes with no linked resource as information, not a warning.

    Coverage is stated positively — many nodes legitimately need no external
    material — so an uncovered node is surfaced for awareness, never flagged as a
    problem. Nodes keep graph load order.
    """
    uncovered = [
        node_id for node_id in node_ids if not resources_for_node(node_id, resources)
    ]
    if not node_ids:
        return
    print(
        f"coverage: {len(node_ids) - len(uncovered)}/{len(node_ids)} node(s) "
        "have a linked resource."
    )
    if uncovered:
        print(f"  {len(uncovered)} node(s) with no linked resource (informational):")
        for node_id in uncovered:
            print(f"    {node_id}")


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="resource-report",
            kind=Kind.READ_ONLY,
            handler=resource_report,
            help="Report every resource's derived verification status (always exit 0, read-only).",
        )
    )
