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

v2.2: objective judgments freeze a bounded `gate_run` receipt onto the record
(the planner's `_build_gate_run` in `..evidence.submission`) — the gate
command's argv, root-relative inputs, exit class, and output hashes; manual
submits never carry one, and a gate that cannot run still writes nothing at
all.
"""

from __future__ import annotations

import argparse
import hashlib
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..dispatch import Command, Context, CommandResult, Kind, Registry
from ..evidence._schema import EvidenceLoadError, read_yaml_list
from ..evidence.artifacts import hash_artifact
from ..evidence.evidence import (
    load_validation_gates,
    load_evidence_records,
    load_artifact_specs,
)
from ..evidence.submission import (
    GateInfo,
    GateUnrunnable,
    SubmitOutcome,
    plan_submit,
)
from ..graph.state import ProgressStoreError, load_state

_RECORDS_RELPATH = Path("evidence") / "evidence_records.yaml"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_gate(command: str):
    """Run an objective gate command loudly and return its run result.

    `shell=False` is what makes "unable to run" distinguishable from "ran and
    failed": a missing executable raises `OSError` (→ `GateUnrunnable`, no
    verdict), whereas a command that runs and exits non-zero returns that code
    (→ a rejection verdict).

    v2.2 (D-Capture): output is captured (`capture_output=True`), hashed by
    the planner into the receipt, and then echoed to the terminal — stdout,
    then stderr — so the "loud" run survives in content and order, at the
    cost of the interleaving. Shipped checkers are short deterministic
    scripts; streaming (`Popen` pump loops) is explicitly rejected for v2.2.
    Returns a `GateRunResult` (the planner's seam value).
    """
    from ..evidence.submission import GateRunResult, GateUnrunnable as _Unrunnable

    argv = shlex.split(command)
    if not argv:
        raise _Unrunnable("gate command is empty")
    try:
        completed = subprocess.run(  # noqa: S603 — curriculum-authored gate
            argv, capture_output=True
        )
    except OSError as exc:
        raise _Unrunnable(str(exc)) from exc
    stdout = completed.stdout.decode("utf-8", errors="replace") if completed.stdout else ""
    stderr = completed.stderr.decode("utf-8", errors="replace") if completed.stderr else ""
    # Platform-stable provenance funnels through the receipt module's single
    # normalization place (spec §1, D-Normalize): the builder hashes the same
    # normalized bytes, so CRLF captures hash identically everywhere.
    from ..evidence.gate_receipt import normalize_stream

    stdout = normalize_stream(stdout)
    stderr = normalize_stream(stderr)
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr)
    return GateRunResult(exit_code=completed.returncode, stdout=stdout, stderr=stderr)


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
        root=root,
        exists=lambda p: p.is_file(),
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
            add_parser=add_parser,
        )
    )


def _add_evidence_submit_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach `evidence submit`'s arguments to `parser`.

    Shared by the canonical `evidence submit` parser and the top-level
    `submit` alias so the two stay in lockstep.
    """
    parser.add_argument("node_id", help="Node the evidence is submitted against.")
    parser.add_argument(
        "--spec", default=None, help="Artifact spec id (optional when the node has exactly one)."
    )
    parser.add_argument(
        "--location", required=True, help="Repo-relative path or URL of the artifact."
    )
    parser.add_argument("--note", default=None, help="Optional note attached to the record.")
    verdict = parser.add_mutually_exclusive_group()
    verdict.add_argument(
        "--accept", action="store_true", help="Manual-gate verdict: accept (refused on objective nodes)."
    )
    verdict.add_argument(
        "--reject", action="store_true", help="Manual-gate verdict: reject (refused on objective nodes)."
    )
    parser.add_argument(
        "--supersedes", default=None, help="Evidence record id this submission corrects."
    )
    parser.add_argument(
        "--reason", default=None, help="Why the correction supersedes (required with --supersedes)."
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `evidence submit` parser plus the `submit` alias (issue #207 contract).

    Co-located owner of the `evidence submit` argparse surface (issue #207 contract: sole source of CLI flags and help text).
    """
    evidence_parser = subparsers.add_parser(
        "evidence", help="Evidence-trail commands (submit)."
    )
    evidence_commands = evidence_parser.add_subparsers(dest="_evidence_cmd", metavar="<command>")
    evidence_commands.required = True
    submit_parser = evidence_commands.add_parser(
        "submit", help="Submit one item of evidence against a node (judged at submission)."
    )
    _add_evidence_submit_arguments(submit_parser)
    submit_parser.set_defaults(_command_name="evidence submit")

    submit_alias_parser = subparsers.add_parser(
        "submit", help="Alias for `evidence submit`."
    )
    _add_evidence_submit_arguments(submit_alias_parser)
    submit_alias_parser.set_defaults(_command_name="evidence submit")
