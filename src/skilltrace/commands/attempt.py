"""`skilltrace attempt record` — record one assessment attempt as a fact.

An attempt is one attempt at demonstrating a node's skill against its gate
standard; its outcome is `passed` or `failed` and it is immutable with no
supersede mechanism (CONTEXT.md, issue #13). It is recordable in any node state
and even on a gateless node — both warn, neither refuses — because an attempt is
a historical fact. Attempts never feed pass eligibility: this command writes only
`attempts.yaml`, so the evidence trail eligibility reads from is untouched.

The decision is the pure `plan_attempt` planner; this handler loads the facts it
needs (does the node have a gate, what attempt ids already exist, what is the
node's state), binds the append, prints the plan, and maps it to a
`CommandResult`. It is mutating: the dispatcher appends exactly one audit event
per *written* attempt — and a `failed` attempt is a written attempt, so it logs
its event just like a `passed` one. Only a malformed request refuses (exit 2,
nothing written).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence._schema import EvidenceLoadError, read_yaml_list
from ..evidence.attempt_recording import AttemptOutcome, plan_attempt
from ..evidence.attempts import load_assessment_attempts
from ..evidence.gates import load_validation_gates
from ..graph.state import ProgressStoreError, load_state

_ATTEMPTS_RELPATH = Path("evidence") / "attempts.yaml"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _append_attempt(root: Path, record: dict) -> None:
    """Append `record` to `attempts.yaml`, leaving existing rows untouched.

    Read raw and re-dump (never round-trip existing rows through the model) so the
    immutability guarantee holds: existing attempts are byte-for-byte preserved
    apart from YAML re-serialization, and only the new row is added — mirroring
    `evidence submit`'s record append.
    """
    path = root / _ATTEMPTS_RELPATH
    raw = read_yaml_list(path, top_key="attempts", kind="assessment attempt")
    raw.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"attempts": raw}, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def _node_has_gate(gates, node_id: str) -> bool:
    """Whether `node_id` carries a validation gate (drives the gateless warning)."""
    return any(gate.node_id == node_id for gate in gates)


def record(ctx: Context) -> CommandResult:
    """Load the gate/attempt/state facts, plan the attempt, and write it.

    Loader failures fail the command (non-zero exit, no event) rather than
    tracebacking, matching sync/validate/next/submit.
    """
    root = ctx.root
    args = ctx.args

    try:
        gates = load_validation_gates(root)
        attempts = load_assessment_attempts(root)
        store = load_state(root)
    except (EvidenceLoadError, ProgressStoreError) as exc:
        print(f"attempt record: FAILED — {exc}")
        return CommandResult(exit_code=1)

    node_id = args.node_id
    outcome = plan_attempt(
        node_id,
        outcome=args.outcome,
        note=args.note,
        has_gate=_node_has_gate(gates, node_id),
        existing_attempt_ids=[a.id for a in attempts],
        node_state=store.state_of(node_id),
        now=_now_iso(),
    )

    _report(outcome, node_id)

    if outcome.record is not None:
        _append_attempt(root, outcome.record)

    return CommandResult(records_touched=outcome.records_touched, exit_code=outcome.exit_code)


def _report(outcome: AttemptOutcome, node_id: str) -> None:
    for message in outcome.messages:
        print(message)
    for warning in outcome.warnings:
        print(f"[warning] {warning}")
    for error in outcome.errors:
        print(f"[error] {error}")
    if outcome.record is not None:
        print(f"attempt record: wrote {outcome.record['id']} ({outcome.record['outcome']}).")
    else:
        print(f"attempt record: refused for node {node_id} — nothing written.")


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="attempt record",
            kind=Kind.MUTATING,
            handler=record,
            help="Record one assessment attempt (passed/failed) as an immutable fact.",
        )
    )
