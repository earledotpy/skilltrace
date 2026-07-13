"""`skilltrace health` — cross-layer roll-up plus liveness facts (issue #37).

Per the #34 resolution: health answers "is my repo sound and is anything
rotting?" It runs the same five `load_and_validate*` functions as the
`validate` suite (one summary line per layer) and adds liveness facts
`validate` deliberately doesn't cover — progress store presence, content-based
sync drift, stale open sessions, and a resource verification summary. It
inherits validate's exit contract exactly: any layer *error* fails the run;
every liveness finding is a *warning* and never affects the exit code. Health
reports the condition of the data; `today` (a later v0.9 ticket) reports the
state of the learner — recommendations, due reviews, and blockers stay out of
this command. Read-only: it appends no audit event.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .. import render
from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence.validation import EvidenceValidationResult, load_and_validate_evidence
from ..execution._store import ExecutionLoadError
from ..execution.sessions import load_sessions, open_session
from ..execution.staleness import stale_session_hours, stale_warning
from ..execution.validation import ExecutionValidationResult, load_and_validate_execution
from ..graph.nodes import NodeLoadError, load_nodes
from ..graph.state import ProgressStoreError, load_state
from ..graph.validation import ValidationResult, load_and_validate
from ..policy.validation import PolicyValidationResult, load_and_validate_policy
from ..resources.registry import ResourceLoadError, load_resources
from ..resources.status import VerificationStatus, derive_status, stale_after_days
from ..resources.validation import ResourceValidationResult, load_and_validate_resources
from ._common import now_iso

_STATE_RELPATH = Path("graph") / "state.yaml"


def _layer_line(target: str, counts: str, result) -> tuple[str, list[str]]:
    """One status line for a validate layer, plus any error lines beneath it.

    Errors print verbatim (a failing exit with hidden reasons is hostile);
    warnings print only as a count with a pointer to the focused diagnostic.
    """
    if not result.ok:
        return (
            f"{target}: {counts} — FAILED, {len(result.errors)} error(s)",
            [render.error(e) for e in result.errors],
        )
    if result.warnings:
        return (
            f"{target}: {counts} — OK, {len(result.warnings)} warning(s) "
            f"(see `skilltrace validate {target}`)",
            [],
        )
    return f"{target}: {counts} — OK", []


def _graph_counts(result: ValidationResult) -> str:
    return f"{result.node_count} nodes, {result.edge_count} edges"


def _evidence_counts(result: EvidenceValidationResult) -> str:
    return (
        f"{result.spec_count} specs, {result.gate_count} gates, "
        f"{result.record_count} records, {result.attempt_count} attempts"
    )


def _execution_counts(result: ExecutionValidationResult) -> str:
    return (
        f"{result.session_count} sessions, {result.work_count} work items, "
        f"{result.blocker_count} blockers, {result.remediation_count} remediation "
        f"actions, {result.review_count} reviews"
    )


def _policy_counts(result: PolicyValidationResult) -> str:
    return f"{result.file_count} policy file(s)"


def _resources_counts(result: ResourceValidationResult) -> str:
    return f"{result.resource_count} resource(s)"


def _liveness_lines(root: Path) -> tuple[list[str], int]:
    """Liveness facts `validate` doesn't cover. Returns (lines, warning_count).

    A missing progress store already explains every node as "not yet synced",
    so the content-based drift check is skipped in that case — otherwise it
    would double-report the same fact as "N nodes missing" on top of "no
    progress store found".
    """
    lines: list[str] = []
    warnings = 0

    store_present = (root / _STATE_RELPATH).exists()
    if not store_present:
        lines.append(render.warning("no progress store found — run `skilltrace sync`."))
        warnings += 1

    if store_present:
        try:
            store = load_state(root)
        except ProgressStoreError:
            store = None
        if store is not None:
            state_counts: dict[str, int] = {}
            for entry in store.entries.values():
                state_counts[entry.state] = state_counts.get(entry.state, 0) + 1
            counts_str = ", ".join(f"{s}={n}" for s, n in sorted(state_counts.items()))
            lines.append(
                f"progress store: {len(store.entries)} node(s)"
                + (f"; states: {counts_str}" if counts_str else "")
            )

            try:
                nodes = load_nodes(root)
            except NodeLoadError:
                nodes = None
            if nodes is not None:
                missing = [n.id for n in nodes if n.id not in store.entries]
                if missing:
                    lines.append(
                        render.warning(
                            f"{len(missing)} node(s) missing from the progress "
                            "store — run `skilltrace sync`."
                        )
                    )
                    warnings += 1

    try:
        sessions = load_sessions(root)
    except ExecutionLoadError:
        sessions = []
    current = open_session(sessions)
    if current is not None:
        message = stale_warning(
            current, now=now_iso(), threshold_hours=stale_session_hours(root)
        )
        if message:
            lines.append(render.warning(message))
            warnings += 1

    try:
        resources = load_resources(root)
    except ResourceLoadError:
        resources = None
    if resources is not None:
        today = datetime.now(timezone.utc).date()
        window = stale_after_days(root)
        by_status = Counter(
            derive_status(r, today=today, stale_after_days=window) for r in resources
        )
        summary = ", ".join(
            f"{status.value}={by_status.get(status, 0)}"
            for status in (
                VerificationStatus.VERIFIED,
                VerificationStatus.STALE,
                VerificationStatus.UNVERIFIED,
                VerificationStatus.BROKEN,
            )
        )
        lines.append(f"resources: {len(resources)} resource(s); {summary}")
        bad = by_status.get(VerificationStatus.STALE, 0) + by_status.get(
            VerificationStatus.BROKEN, 0
        )
        if bad:
            lines.append(
                render.warning(
                    f"{bad} resource(s) stale or broken — see `skilltrace resource-report`."
                )
            )
            warnings += 1

    return lines, warnings


def health(ctx: Context) -> CommandResult:
    root = ctx.root

    graph_result = load_and_validate(root)
    evidence_result = load_and_validate_evidence(root)
    execution_result = load_and_validate_execution(root)
    policy_result = load_and_validate_policy(root)
    resources_result = load_and_validate_resources(root)

    error_count = 0
    warning_count = 0

    for target, counts, result in (
        ("graph", _graph_counts(graph_result), graph_result),
        ("evidence", _evidence_counts(evidence_result), evidence_result),
        ("execution", _execution_counts(execution_result), execution_result),
        ("policy", _policy_counts(policy_result), policy_result),
        ("resources", _resources_counts(resources_result), resources_result),
    ):
        line, error_lines = _layer_line(target, counts, result)
        print(line)
        for error_line in error_lines:
            print(error_line)
        error_count += len(result.errors)
        warning_count += len(result.warnings)

    liveness_lines, liveness_warnings = _liveness_lines(root)
    for line in liveness_lines:
        print(line)
    warning_count += liveness_warnings

    print(render.verdict_line("health", error_count=error_count, warning_count=warning_count))
    return CommandResult(exit_code=0 if error_count == 0 else 1)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="health",
            kind=Kind.READ_ONLY,
            handler=health,
            help="Roll up the five validate targets plus liveness facts (read-only).",
        )
    )
