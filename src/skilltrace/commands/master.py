"""`skilltrace master <node_id>` — the learner's explicit mastery assertion.

The one command that writes `mastered` (CONTEXT.md "Mastering"): it refuses
unless mastery eligibility holds — passed state, accepted evidence, and a
satisfactory post-pass review with the policy-configured day spacing.

Like `pass`, it carries **no** `automation_action`: this *is* the explicit
learner command, so it must not route through the automation boundary (which
forbids `master_node` on any automated path). The guarantee that nothing
automates mastery lives in this being the sole caller of
`write_asserted(..., "mastered")`.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence._schema import EvidenceLoadError
from ..evidence.records import load_evidence_records
from ..evidence.specs import load_artifact_specs
from ..execution._store import ExecutionLoadError
from ..execution.reviews import load_reviews
from ..graph.nodes import NodeLoadError, load_nodes
from ..graph.state import ProgressStoreError, load_state, save_state
from ..policy.mastery import (
    MasterOutcome,
    compute_mastery_eligibility,
    load_mastery_values,
    plan_master,
)
from .eligibility import passed_at_of


def master_node(ctx: Context) -> CommandResult:
    """Resolve the facts, plan the mastery assertion, and bind its one side effect."""
    root = ctx.root
    node_id = ctx.args.node_id

    try:
        node_ids = {node.id for node in load_nodes(root)}
        specs = load_artifact_specs(root)
        records = load_evidence_records(root)
        reviews = load_reviews(root)
        store = load_state(root)
    except (NodeLoadError, EvidenceLoadError, ExecutionLoadError, ProgressStoreError) as exc:
        print(f"master: FAILED — {exc}")
        return CommandResult(exit_code=1)

    if node_id not in node_ids:
        print(f"master: FAILED — unknown node {node_id}.")
        return CommandResult(exit_code=1)

    eligibility = compute_mastery_eligibility(
        node_id,
        current_state=store.state_of(node_id),
        passed_at=passed_at_of(store, node_id),
        specs=[s for s in specs if s.node_id == node_id],
        records=records,
        reviews=reviews,
        values=load_mastery_values(root),
    )

    outcome = plan_master(node_id, eligibility=eligibility)
    _report(outcome)

    if outcome.proceed:
        store.write_asserted(node_id, "mastered")
        save_state(store, root)

    return CommandResult(records_touched=outcome.records_touched, exit_code=outcome.exit_code)


def _report(outcome: MasterOutcome) -> None:
    for message in outcome.messages:
        print(message)
    for error in outcome.errors:
        print(f"[error] {error}")
    if outcome.proceed:
        print(f"master: {outcome.node_id} is now mastered.")
    else:
        print(f"master: refused for node {outcome.node_id} — nothing mastered.")


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="master",
            kind=Kind.MUTATING,
            handler=master_node,
            help="Assert a node mastered (refuses without mastery eligibility).",
        )
    )
