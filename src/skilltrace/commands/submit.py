"""`skilltrace evidence submit` — record one item of evidence, judged now.

Submitting is the act of judgment (ADR 0003): this command resolves the node's
artifact spec and gate, decides acceptance at submission (a manual gate takes the
learner's explicit `--accept`/`--reject`; an objective gate runs its command and
the exit code is the verdict), freezes a content hash of the artifact, and writes
one immutable record. It is mutating: the dispatcher appends exactly one audit
event per *written* submit — and a rejected record is a written submit, so a
failing objective gate still logs its event (the gate's non-zero exit is the
verdict, not this command's exit).

The decision itself is the pure `plan_submit` planner; this handler only loads
the data, binds the three real side effects (run the gate via subprocess, hash
the artifact, append the record), prints the plan, and maps it to a
`CommandResult`. Refusals and an unrunnable gate exit non-zero and write nothing.
"""

from __future__ import annotations

import hashlib
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence._schema import EvidenceLoadError, read_yaml_list
from ..evidence.artifacts import hash_artifact
from ..evidence.gates import load_validation_gates
from ..evidence.records import load_evidence_records
from ..evidence.specs import load_artifact_specs
from ..evidence.submission import GateInfo, GateUnrunnable, SubmitOutcome, plan_submit
from ..graph.state import ProgressStoreError, load_state

_RECORDS_RELPATH = Path("evidence") / "evidence_records.yaml"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_gate(command: str) -> int:
    """Run an objective gate command loudly and return its exit code.

    `shell=False` is what makes "unable to run" distinguishable from "ran and
    failed": a missing executable raises `OSError` (→ `GateUnrunnable`, no
    verdict), whereas a command that runs and exits non-zero returns that code
    (→ a rejection verdict). Output is not captured, so the command's own stdout/
    stderr stream to the terminal — the "loud" run the issue calls for.
    """
    argv = shlex.split(command)
    if not argv:
        raise GateUnrunnable("gate command is empty")
    try:
        completed = subprocess.run(argv)  # noqa: S603 — curriculum-authored gate
    except OSError as exc:
        raise GateUnrunnable(str(exc)) from exc
    return completed.returncode


def _make_hasher(root: Path):
    """Bind an artifact hasher rooted at `root`.

    Hashes the file bytes at the repo-relative `location`; when nothing readable
    is there (a URL, or a not-yet-present path — `--location` accepts both), falls
    back to hashing the location string so `artifact_hash` is always populated and
    deterministic. Drift detection (`validate evidence`) only ever fingerprints
    real files, so the string fallback simply never matches a later file probe —
    which is the correct signal for a URL that cannot be content-addressed.
    """

    def hasher(location: str) -> str:
        try:
            return hash_artifact(root / location)
        except OSError:
            digest = hashlib.sha256(location.encode("utf-8")).hexdigest()
            return f"sha256:{digest}"

    return hasher


def _append_record(root: Path, record: dict) -> None:
    """Append `record` to `evidence_records.yaml`, leaving existing rows untouched.

    Read raw and re-dump (never round-trip existing rows through the model) so the
    immutability guarantee holds: existing records are byte-for-byte preserved
    apart from YAML re-serialization, and only the new row is added.
    """
    path = root / _RECORDS_RELPATH
    raw = read_yaml_list(path, top_key="evidence_records", kind="evidence record")
    raw.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"evidence_records": raw}, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def _gate_for_node(gates, node_id: str) -> GateInfo | None:
    """The node's gate as a `GateInfo`, or None if the node is gateless.

    A node has at most one gate (enforced by `validate evidence`); if data is
    malformed with several, the first is used — the planner's decision does not
    depend on which, and the duplicate is a separate reported error.
    """
    for gate in gates:
        if gate.node_id == node_id:
            return GateInfo(authority=gate.authority, command=gate.command)
    return None


def submit(ctx: Context) -> CommandResult:
    """Load the evidence trail + state, plan the submit, and write the record.

    Loader failures fail the command (non-zero exit, no event) rather than
    tracebacking, matching sync/validate/next.
    """
    root = ctx.root
    args = ctx.args

    try:
        specs = load_artifact_specs(root)
        gates = load_validation_gates(root)
        records = load_evidence_records(root)
        store = load_state(root)
    except (EvidenceLoadError, ProgressStoreError) as exc:
        print(f"evidence submit: FAILED — {exc}")
        return CommandResult(exit_code=1)

    node_id = args.node_id
    specs_for_node = [s for s in specs if s.node_id == node_id]
    gate = _gate_for_node(gates, node_id)

    outcome = plan_submit(
        node_id,
        specs_for_node,
        gate,
        records,
        store.state_of(node_id),
        spec_id=args.spec,
        location=args.location,
        note=args.note,
        accept=args.accept,
        reject=args.reject,
        supersedes=args.supersedes,
        supersede_reason=args.reason,
        run_gate=_run_gate,
        hasher=_make_hasher(root),
        now=_now_iso(),
    )

    _report(outcome, node_id)

    if outcome.record is not None:
        _append_record(root, outcome.record)

    return CommandResult(records_touched=outcome.records_touched, exit_code=outcome.exit_code)


def _report(outcome: SubmitOutcome, node_id: str) -> None:
    for message in outcome.messages:
        print(message)
    for warning in outcome.warnings:
        print(f"[warning] {warning}")
    for error in outcome.errors:
        print(f"[error] {error}")
    if outcome.record is not None:
        print(
            f"evidence submit: wrote {outcome.record['id']} "
            f"({'accepted' if outcome.record['accepted'] else 'rejected'})."
        )
    else:
        print(f"evidence submit: refused for node {node_id} — nothing written.")


def register(registry: Registry) -> None:
    registry.register(
        Command(
            name="evidence submit",
            kind=Kind.MUTATING,
            handler=submit,
            help="Submit one item of evidence against a node (judged at submission).",
        )
    )
