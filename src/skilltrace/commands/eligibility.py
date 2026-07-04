"""`skilltrace eligibility <node_id>` — is a node pass-eligible, and why.

Read-only (issue #14): loads the evidence trail plus the progress store, computes
the pure `compute_eligibility` verdict, and prints it with the per-required-spec
counts and the reasons behind a negative verdict. It never runs a gate command
and never mutates — the dispatcher appends no audit event.

The exit code reports whether the *question* was answered, not the answer: any
verdict (eligible or not) exits 0; only an operational failure — an unknown node
id, or unloadable evidence/graph/state data — exits non-zero. A gateless,
spec-less, or under-backed node is a valid "not eligible" verdict, not an error.

State feeds only the advisory `passed-but-not-backed` line: when a node's
asserted pass is no longer backed by evidence, that is surfaced, but the pass
stands and is not revoked (ADR 0003).
"""

from __future__ import annotations

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence._schema import EvidenceLoadError
from ..evidence.eligibility import EligibilityResult, compute_eligibility
from ..evidence.gates import load_validation_gates
from ..evidence.records import load_evidence_records
from ..evidence.specs import load_artifact_specs
from ..graph.nodes import NodeLoadError, load_nodes
from ..graph.state import ProgressStoreError, load_state


def eligibility(ctx: Context) -> CommandResult:
    """Load the graph + evidence trail + state, compute eligibility, and print it.

    Loader failures and an unknown node id are operational failures (non-zero exit,
    no event); any actual verdict exits 0.
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
        print(f"eligibility: FAILED — {exc}")
        return CommandResult(exit_code=1)

    if node_id not in node_ids:
        print(f"eligibility: FAILED — unknown node {node_id}.")
        return CommandResult(exit_code=1)

    result = compute_eligibility(
        node_id,
        [s for s in specs if s.node_id == node_id],
        has_gate=any(g.node_id == node_id for g in gates),
        records=records,
        node_state=store.state_of(node_id),
    )

    _report(result)
    return CommandResult(exit_code=0)


def _report(result: EligibilityResult) -> None:
    verdict = "ELIGIBLE" if result.eligible else "NOT ELIGIBLE"
    print(f"eligibility {result.node_id}: {verdict}")
    for spec in result.specs:
        mark = "met" if spec.met else "below minimum"
        print(
            f"  spec {spec.spec_id}: {spec.accepted_count}/{spec.minimum_count} "
            f"accepted ({mark})"
        )
    if not result.specs:
        print("  (no required artifact spec)")
    # The per-spec breakdown above already shows each below-minimum count; print
    # only the structural reasons (no gate / no required spec) so the CLI does not
    # restate a count it just displayed. The pure result keeps every reason for
    # its callers.
    for reason in result.reasons:
        if reason.startswith("spec "):
            continue
        print(f"  - {reason}")
    if result.passed_but_not_backed:
        print(
            f"[warning] node {result.node_id} is asserted passed but its evidence no "
            "longer backs eligibility — the pass stands and is not revoked."
        )


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="eligibility",
            kind=Kind.READ_ONLY,
            handler=eligibility,
            help="Report whether a node is pass-eligible, with per-spec counts.",
        )
    )
