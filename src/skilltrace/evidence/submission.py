"""The `evidence submit` decision — a pure planner over already-loaded data.

Submitting *is* the act of judgment (ADR 0003): acceptance is decided at
submission and frozen into the record; there is no pending state and no
defaulted verdict. This module is the pure core of that decision, mirroring the
`check_evidence` / `load_and_validate_evidence` seam in `validation.py`:
`plan_submit` takes the already-loaded specs/gate/records plus the parsed
request and two injected callables — a **gate runner** and an **artifact
hasher** — and returns *what to write, what to say, and the exit code*, touching
no disk. The command handler (`commands/submit.py`) binds the real subprocess
runner, the real hasher, and the record append.

Two rules that are subtle enough to state up front (both from the advisor review
and ADR 0003 / `dispatch.py`):

- **A rejected record is still a successful, audited mutation.** A non-zero gate
  exit is the *verdict*, not the submit command's exit: the rejected record is
  written and the outcome exits 0 so the dispatcher logs its one event. Only a
  *refusal* (nothing to judge, illegal flags, a broken supersede) or a gate that
  *cannot run at all* exits non-zero and writes nothing.
- **"Unable to run" is not a judgment.** The injected runner returns an exit code
  (any code is a verdict) or raises `GateUnrunnable` (the spawn failed — no
  verdict, error, nothing written).

All refusable conditions are checked *before* the objective gate command runs,
so a refused submit never executes a side-effecting command.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .eligibility import live_accepted_count as _live_accepted_count
from .ids import allocate_evidence_id
from .records import EvidenceRecord
from .specs import ArtifactSpec

# The gate runner returns the objective command's exit code, or raises
# `GateUnrunnable` when the command could not be spawned at all. Kept as a seam
# so the pure planner needs no subprocess: the command binds the real adapter,
# tests inject a fake that returns a code or raises.
GateRunner = Callable[[str], int]

# The hasher maps a record's `location` to the `sha256:<hex>` frozen into the
# record. The command binds `hash the file bytes, else hash the location string`
# (see the handler); tests inject a deterministic stub.
ArtifactHasher = Callable[[str], str]


class GateUnrunnable(Exception):
    """The objective gate command could not be spawned — no verdict is possible.

    Inability to judge is not a judgment (ADR 0003): the runner raises this
    rather than returning a code, and the planner turns it into an error with
    nothing written.
    """


# Exit codes the outcome may carry. Zero is a *written* submit (accepted *or*
# rejected); refusals mirror the automation boundary's refusal code; an
# unrunnable gate is an operational failure like a loader failure elsewhere.
_EXIT_OK = 0
_EXIT_REFUSED = 2
_EXIT_GATE_UNRUNNABLE = 1

# The two states that are an *asserted pass* — the ones the supersede-drops-
# eligibility warning protects (ADR 0003: a drop never revokes an asserted pass).
# `active` is asserted progress but not a pass, so it is deliberately excluded:
# a started-but-unpassed node has no pass to stand.
_PASS_STATES: frozenset[str] = frozenset({"passed", "mastered"})


@dataclass
class SubmitOutcome:
    """What the handler should write, print, and exit with.

    `record` is the mapping to append to `evidence_records.yaml`, or `None` when
    nothing is written (a refusal or an unrunnable gate). `records_touched` feeds
    the audit event and is non-empty only when a record is written. `messages`
    are informational lines (the loud gate command + exit code, the verdict);
    `warnings` are advisory (locked node, eligibility drop); `errors` are refusal
    or failure reasons.
    """

    record: dict | None = None
    records_touched: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    exit_code: int = _EXIT_OK


def _refuse(reason: str) -> SubmitOutcome:
    return SubmitOutcome(errors=[reason], exit_code=_EXIT_REFUSED)


@dataclass(frozen=True)
class GateInfo:
    """The minimal gate facts the planner needs: its authority and command.

    A thin stand-in for `ValidationGate` so the planner does not depend on the
    gate loader's full model; the handler builds it from the node's gate, or
    passes `None` for a gateless node.
    """

    authority: str
    command: str | None = None


def _is_pass_eligible(
    records: list[EvidenceRecord], specs_for_node: list[ArtifactSpec]
) -> bool:
    """Narrow pass-eligibility: every required spec meets its live accepted count.

    Deliberately minimal — only what the supersede-drops-eligibility warning
    needs. The authoritative `eligibility` command is issue #14. A node with no
    required spec is never eligible (matching `validate evidence`'s warning).
    """
    required = [s for s in specs_for_node if s.required]
    if not required:
        return False
    return all(
        _live_accepted_count(records, spec.id) >= spec.minimum_count
        for spec in required
    )


def plan_submit(
    node_id: str,
    specs_for_node: list[ArtifactSpec],
    gate: GateInfo | None,
    existing_records: list[EvidenceRecord],
    node_state: str,
    *,
    spec_id: str | None,
    location: str,
    note: str | None,
    accept: bool,
    reject: bool,
    supersedes: str | None,
    supersede_reason: str | None,
    run_gate: GateRunner,
    hasher: ArtifactHasher,
    now: str,
) -> SubmitOutcome:
    """Decide one submission. Pure: no disk, no subprocess (both injected).

    Order matters: every refusable condition (spec resolution, gate presence,
    flag legality, supersede rules) is checked *before* the objective gate
    command runs, so a refused submit never executes a side-effecting command.
    """
    # --- Resolve the artifact spec -----------------------------------------
    spec = _resolve_spec(node_id, specs_for_node, spec_id)
    if isinstance(spec, SubmitOutcome):
        return spec
    resolved_spec_id = spec.id

    # --- Gate presence: a gateless node has no authority to judge ----------
    if gate is None:
        return _refuse(
            f"node {node_id} has no gate — no authority exists to judge evidence; "
            "nothing submitted."
        )

    # --- Flag legality vs authority ----------------------------------------
    flag_refusal = _check_flags(gate, accept, reject)
    if flag_refusal is not None:
        return flag_refusal

    # --- Supersede rules ----------------------------------------------------
    supersede_refusal = _check_supersede(
        existing_records, resolved_spec_id, supersedes, supersede_reason
    )
    if supersede_refusal is not None:
        return supersede_refusal

    # --- Verdict (manual reads the flag; objective runs the command) -------
    messages: list[str] = []
    if gate.authority == "manual":
        accepted = accept
        accepted_by = "learner_manual"
    else:  # objective — command decides; flags already refused above
        assert gate.command is not None  # objective gates always carry a command
        messages.append(f"gate command: {gate.command}")
        try:
            code = run_gate(gate.command)
        except GateUnrunnable as exc:
            return SubmitOutcome(
                messages=messages,
                errors=[
                    f"gate command could not be run ({exc}); inability to judge is "
                    "not a judgment — nothing submitted."
                ],
                exit_code=_EXIT_GATE_UNRUNNABLE,
            )
        messages.append(f"gate exit code: {code}")
        accepted = code == 0
        accepted_by = "objective_gate"
    messages.append(f"verdict: {'ACCEPTED' if accepted else 'REJECTED'}")

    # --- Build the record ---------------------------------------------------
    record_id = allocate_evidence_id(node_id, [r.id for r in existing_records])
    record: dict = {
        "id": record_id,
        "artifact_spec_id": resolved_spec_id,
        "location": location,
    }
    if note:
        record["note"] = note
    record["accepted"] = accepted
    record["accepted_by"] = accepted_by
    record["artifact_hash"] = hasher(location)
    if supersedes is not None:
        record["supersedes"] = supersedes
        record["supersede_reason"] = supersede_reason
    record["created_at"] = now

    # --- Advisory warnings (never block a written submit) ------------------
    warnings = _submit_warnings(
        node_id,
        node_state,
        specs_for_node,
        existing_records,
        record,
        supersedes,
    )

    return SubmitOutcome(
        record=record,
        records_touched=[record_id],
        messages=messages,
        warnings=warnings,
        exit_code=_EXIT_OK,
    )


def _resolve_spec(
    node_id: str, specs_for_node: list[ArtifactSpec], spec_id: str | None
) -> ArtifactSpec | SubmitOutcome:
    """Return the chosen spec, or a refusal outcome.

    `--spec` is optional only when the node has exactly one spec; with several,
    omitting it refuses and lists them; with none, there is nothing to submit
    against; a named spec that is not one of the node's specs refuses.
    """
    by_id = {s.id: s for s in specs_for_node}
    if spec_id is not None:
        chosen = by_id.get(spec_id)
        if chosen is None:
            available = ", ".join(sorted(by_id)) or "(none)"
            return _refuse(
                f"--spec {spec_id} is not an artifact spec of node {node_id}; "
                f"its specs are: {available}."
            )
        return chosen
    if not specs_for_node:
        return _refuse(
            f"node {node_id} has no artifact spec — there is nothing to submit "
            "evidence against."
        )
    if len(specs_for_node) > 1:
        listed = ", ".join(sorted(by_id))
        return _refuse(
            f"node {node_id} has several artifact specs; name one with --spec. "
            f"Choices: {listed}."
        )
    return specs_for_node[0]


def _check_flags(gate: GateInfo, accept: bool, reject: bool) -> SubmitOutcome | None:
    """Refuse an illegal `--accept`/`--reject` combination for the gate's authority.

    Manual: exactly one of the two is mandatory (absence refuses, both refuses).
    Objective: both are refused outright, not ignored — the command judges.
    """
    if gate.authority == "manual":
        if accept and reject:
            return _refuse(
                "cannot both --accept and --reject; a manual gate takes one verdict."
            )
        if not accept and not reject:
            return _refuse(
                "manual-authority node requires an explicit verdict: pass --accept "
                "or --reject."
            )
        return None
    # objective
    if accept or reject:
        return _refuse(
            "objective-authority node: --accept/--reject are refused — the gate "
            "command decides the verdict, not the learner."
        )
    return None


def _check_supersede(
    existing_records: list[EvidenceRecord],
    resolved_spec_id: str,
    supersedes: str | None,
    supersede_reason: str | None,
) -> SubmitOutcome | None:
    """Enforce the four supersede rules at submit, or return None if clean.

    Pairing (both-or-neither with a reason), target exists, same spec as this
    submission, and the target has no existing successor (one live head).
    """
    if supersedes is None and supersede_reason is None:
        return None
    if supersedes is None:
        return _refuse("--reason was given without --supersedes; name the record to supersede.")
    if supersede_reason is None:
        return _refuse("--supersedes requires --reason; a correction must state why.")

    by_id = {r.id: r for r in existing_records}
    target = by_id.get(supersedes)
    if target is None:
        return _refuse(
            f"--supersedes names record {supersedes}, which does not exist."
        )
    if target.artifact_spec_id != resolved_spec_id:
        return _refuse(
            f"--supersedes {supersedes} targets spec {target.artifact_spec_id}, but "
            f"this submission is against {resolved_spec_id} — a correction stays "
            "within one artifact spec."
        )
    successor = next(
        (r.id for r in existing_records if r.supersedes == supersedes), None
    )
    if successor is not None:
        return _refuse(
            f"--supersedes {supersedes} is already superseded by {successor} — a "
            "correction chain has one live head."
        )
    return None


def _submit_warnings(
    node_id: str,
    node_state: str,
    specs_for_node: list[ArtifactSpec],
    existing_records: list[EvidenceRecord],
    record: dict,
    supersedes: str | None,
) -> list[str]:
    """Advisory warnings for a written submit — never block it.

    Two signals: submitting against a `locked` node, and a supersede that drops
    pass-eligibility while an asserted pass stands (the pass is preserved; only
    the drop is surfaced, per ADR 0003).
    """
    warnings: list[str] = []
    if node_state == "locked":
        warnings.append(
            f"node {node_id} is locked; evidence is recorded, but the node is not "
            "yet available to work."
        )

    if supersedes is not None and node_state in _PASS_STATES:
        projected = existing_records + [_projected_record(record)]
        was_eligible = _is_pass_eligible(existing_records, specs_for_node)
        now_eligible = _is_pass_eligible(projected, specs_for_node)
        if was_eligible and not now_eligible:
            warnings.append(
                f"this supersede drops pass-eligibility for node {node_id}, but its "
                f"asserted {node_state} state stands and is not revoked."
            )
    return warnings


def _projected_record(record: dict) -> EvidenceRecord:
    """A minimal `EvidenceRecord` view of the pending record for eligibility math.

    Only the fields `_live_accepted_count` reads are populated; this never
    touches disk and is discarded after the warning check.
    """
    return EvidenceRecord(
        id=record["id"],
        artifact_spec_id=record["artifact_spec_id"],
        location=record["location"],
        accepted=record["accepted"],
        accepted_by=record["accepted_by"],
        artifact_hash=record["artifact_hash"],
        supersedes=record.get("supersedes"),
        supersede_reason=record.get("supersede_reason"),
    )
