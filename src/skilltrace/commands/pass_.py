"""`skilltrace pass <node_id>` — the learner's explicit pass assertion.

The one command that writes `passed` (CONTEXT.md "Passing"): nothing else — no
gate, sync, or AI — ever passes a node. It does exactly three things (issue #15):
verify the node exists, is not locked, is not already passed/mastered, and is
pass-eligible per #14; write `passed` through the guarded asserted-progress store
API (v0.3); and let the dispatcher append its one audit event. Nothing more — no
review scheduling (that attaches in v0.5/v0.6), no sync side-effects.

It carries **no** `automation_action`: `pass` *is* the explicit learner command,
not an automated path, so it must not be routed through the automation boundary
(which would refuse `pass_node` unconditionally). The safety guarantee that
nothing automates a pass lives in the fact that this is the sole caller of
`write_asserted(..., "passed")` — a grep-level invariant a test pins.

The decision is the pure `plan_pass` planner; this handler resolves the facts it
needs (node existence, stored state, computed eligibility), binds the single side
effect a proceed entails (`write_asserted` + `save_state`), prints the plan, and
maps it to a `CommandResult`. Loader failures and an unknown node are operational
failures (exit 1, no event); a refusal is exit 2 with nothing written.
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence._schema import EvidenceLoadError
from ..evidence.eligibility import compute_eligibility
from ..evidence.gates import load_validation_gates
from ..evidence.passing import PassOutcome, plan_pass
from ..evidence.records import load_evidence_records
from ..evidence.specs import load_artifact_specs
from ..graph.nodes import NodeLoadError, load_nodes
from ..graph.state import ProgressStoreError, load_state, save_state


def pass_node(ctx: Context) -> CommandResult:
    """Load the graph + evidence trail + state, plan the pass, and assert it.

    Loader failures and an unknown node id fail the command (exit 1, no event)
    rather than tracebacking, matching eligibility/sync/submit. A domain refusal
    (locked, already passed/mastered, not eligible) exits 2 and writes nothing.
    """
    root = ctx.root
    node_id = ctx.args.node_id

    try:
        node_ids = {node.id for node in load_nodes(root)}
        specs = load_artifact_specs(root)
        gates = load_validation_gates(root)
        records = load_evidence_records(root)
        store = load_state(root)
    except (NodeLoadError, EvidenceLoadError, ProgressStoreError) as exc:
        print(f"pass: FAILED — {exc}")
        return CommandResult(exit_code=1)

    if node_id not in node_ids:
        print(f"pass: FAILED — unknown node {node_id}.")
        return CommandResult(exit_code=1)

    eligibility = compute_eligibility(
        node_id,
        [s for s in specs if s.node_id == node_id],
        has_gate=any(g.node_id == node_id for g in gates),
        records=records,
        node_state=store.state_of(node_id),
    )

    outcome = plan_pass(
        node_id,
        current_state=store.state_of(node_id),
        eligibility=eligibility,
    )

    _report(outcome)

    if outcome.proceed:
        # The sole side effect of a pass: assert `passed` through the guarded
        # writer (which refuses any backward move as defense in depth) and persist
        # the store. The dispatcher appends the one audit event on exit 0.
        store.write_asserted(node_id, "passed")
        save_state(store, root)

    return CommandResult(records_touched=outcome.records_touched, exit_code=outcome.exit_code)


def _report(outcome: PassOutcome) -> None:
    for message in outcome.messages:
        print(message)
    for error in outcome.errors:
        print(f"[error] {error}")
    if outcome.proceed:
        print(f"pass: {outcome.node_id} is now passed.")
    else:
        print(f"pass: refused for node {outcome.node_id} — nothing passed.")


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="pass",
            kind=Kind.MUTATING,
            handler=pass_node,
            help="Assert a node passed (refuses without eligibility or on a locked node).",
        )
    )
