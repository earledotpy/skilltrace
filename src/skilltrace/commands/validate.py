"""`skilltrace validate <target>` — read-only whole-layer validation.

Two targets today: `validate graph` (issue #5) checks the skill graph's
cross-reference contract; `validate evidence` (issue #11) checks the evidence
trail's. Each runs its layer's loaders + cross-record checks, prints a summary
line plus any errors and warnings, and exits non-zero iff there are errors.
Warnings never affect the exit code. Both are read-only: they append no audit
event, and `validate evidence` never reads the progress store — its output is
stable across every learner state.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence.validation import (
    EvidenceValidationResult,
    load_and_validate_evidence,
)
from ..execution.validation import (
    ExecutionValidationResult,
    load_and_validate_execution,
)
from ..graph.validation import ValidationResult, load_and_validate
from ..policy.validation import PolicyValidationResult, load_and_validate_policy


def _print_report(result: ValidationResult) -> None:
    states = ", ".join(f"{state}={n}" for state, n in sorted(result.state_counts.items()))
    print(
        f"graph: {result.node_count} nodes, {result.edge_count} edges "
        f"({result.active_edge_count} active)"
        + (f"; states: {states}" if states else "")
    )
    for warning in result.warnings:
        print(f"[warning] {warning}")
    for error in result.errors:
        print(f"[error] {error}")

    if result.ok:
        suffix = f" ({len(result.warnings)} warning(s))" if result.warnings else ""
        print(f"validate graph: OK{suffix}.")
    else:
        print(f"validate graph: FAILED — {len(result.errors)} error(s).")


def validate_graph(ctx: Context) -> CommandResult:
    result = load_and_validate(ctx.root)
    _print_report(result)
    return CommandResult(exit_code=0 if result.ok else 1)


def _print_evidence_report(result: EvidenceValidationResult) -> None:
    print(
        f"evidence: {result.spec_count} specs, {result.gate_count} gates, "
        f"{result.record_count} records, {result.attempt_count} attempts"
    )
    for warning in result.warnings:
        print(f"[warning] {warning}")
    for error in result.errors:
        print(f"[error] {error}")

    if result.ok:
        suffix = f" ({len(result.warnings)} warning(s))" if result.warnings else ""
        print(f"validate evidence: OK{suffix}.")
    else:
        print(f"validate evidence: FAILED — {len(result.errors)} error(s).")


def validate_evidence(ctx: Context) -> CommandResult:
    result = load_and_validate_evidence(ctx.root)
    _print_evidence_report(result)
    return CommandResult(exit_code=0 if result.ok else 1)


def _print_execution_report(result: ExecutionValidationResult) -> None:
    print(
        f"execution: {result.session_count} sessions, {result.work_count} work items, "
        f"{result.blocker_count} blockers, {result.remediation_count} remediation actions, "
        f"{result.review_count} reviews"
    )
    for warning in result.warnings:
        print(f"[warning] {warning}")
    for error in result.errors:
        print(f"[error] {error}")

    if result.ok:
        suffix = f" ({len(result.warnings)} warning(s))" if result.warnings else ""
        print(f"validate execution: OK{suffix}.")
    else:
        print(f"validate execution: FAILED — {len(result.errors)} error(s).")


def validate_execution(ctx: Context) -> CommandResult:
    result = load_and_validate_execution(ctx.root)
    _print_execution_report(result)
    return CommandResult(exit_code=0 if result.ok else 1)


def _print_policy_report(result: PolicyValidationResult) -> None:
    print(f"policy: {result.file_count} policy file(s)")
    for warning in result.warnings:
        print(f"[warning] {warning}")
    for error in result.errors:
        print(f"[error] {error}")

    if result.ok:
        suffix = f" ({len(result.warnings)} warning(s))" if result.warnings else ""
        print(f"validate policy: OK{suffix}.")
    else:
        print(f"validate policy: FAILED — {len(result.errors)} error(s).")


def validate_policy(ctx: Context) -> CommandResult:
    result = load_and_validate_policy(ctx.root)
    _print_policy_report(result)
    return CommandResult(exit_code=0 if result.ok else 1)


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="validate graph",
            kind=Kind.READ_ONLY,
            handler=validate_graph,
            help="Validate the skill graph (nodes, edges, cycles).",
        )
    )
    registry.register(
        Command(
            name="validate evidence",
            kind=Kind.READ_ONLY,
            handler=validate_evidence,
            help="Validate the evidence trail (specs, gates, records, attempts).",
        )
    )
    registry.register(
        Command(
            name="validate execution",
            kind=Kind.READ_ONLY,
            handler=validate_execution,
            help="Validate the execution history (sessions, work, blockers, actions, reviews).",
        )
    )
    registry.register(
        Command(
            name="validate policy",
            kind=Kind.READ_ONLY,
            handler=validate_policy,
            help="Validate the policy seed files (six documents, boundary agreement).",
        )
    )
