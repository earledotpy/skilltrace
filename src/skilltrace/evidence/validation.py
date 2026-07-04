"""Evidence-layer validation — the cross-record integrity contract (issue #11).

The four loaders validate the *shape* of one record at a time; they deliberately
do not collapse duplicate ids, check that a reference names a real node/spec, or
follow supersede chains (see their module docstrings). That whole-trail check
lives here, composed from the raw loaded lists plus the graph's node ids.

The contract, as the issue draws it:

**Errors** (fail the run, non-zero exit):

- duplicate ids within specs / gates / records / attempts;
- dangling references — spec→node, gate→node, record→spec, attempt→node, and a
  record's supersedes→record;
- two gates on one node (a node closes through exactly one authority);
- a supersede that crosses artifact specs, or a target superseded more than once
  (a correction chain has one live head — CONTEXT.md, ADR 0003);
- schema violations the loaders raise, folded in by `load_and_validate_evidence`
  so a bad file is a reported error, not a traceback.

**Warnings** (advisory, exit 0):

- a node with no gate (cannot accept evidence, never pass-eligible);
- a node with no *required* spec (never pass-eligible);
- artifact drift — a record's `location` is missing, or the file no longer
  hashes to the record's frozen `artifact_hash`.

Two design rules match the graph layer:

1. **State-independent.** This command never reads `graph/state.yaml`; its output
   is a property of the curriculum + evidence trail alone, stable across every
   learner state. Cross-layer, state-dependent views are `submit`/`eligibility`
   (issues #12, #14) and `health` (v0.9), not this.
2. **Deterministic order.** Sets are used only for membership; every error and
   warning is emitted by iterating an ordered list (first-seen), so the report
   does not reorder run-to-run under a randomized hash seed.

The seam mirrors `graph.validation`: pure `check_evidence(...)` over already-
loaded data (the unit/TDD seam), and `load_and_validate_evidence(root)` which
loads the five sources, folds load errors into the result, and binds the real
artifact probe. Drift is checked only when a `probe` is supplied — pure logic
tests omit it; the command always passes one.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from ..graph.nodes import NodeLoadError, load_nodes
from ._schema import EvidenceLoadError
from .artifacts import probe_hash
from .attempts import AssessmentAttempt, load_assessment_attempts
from .gates import ValidationGate, load_validation_gates
from .records import EvidenceRecord, load_evidence_records
from .specs import ArtifactSpec, load_artifact_specs

# A probe maps a record's repo-relative `location` to the artifact's current
# `sha256:<hex>`, or None when nothing readable is there. Kept as a seam so the
# pure check needs no disk: the command binds the real one, tests inject a fake.
ArtifactProbe = Callable[[str], "str | None"]


@dataclass
class EvidenceValidationResult:
    """The outcome of an evidence-trail validation run.

    `errors` fail the run (`ok` false, command exits non-zero); `warnings` are
    advisory and never affect `ok`. The counts feed the command's summary line.
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    spec_count: int = 0
    gate_count: int = 0
    record_count: int = 0
    attempt_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def _duplicates(ids: Iterable[str]) -> list[str]:
    """Return, in first-seen order, every id that appears more than once."""
    seen: set[str] = set()
    dupes: dict[str, None] = {}  # ordered set
    for value in ids:
        if value in seen:
            dupes.setdefault(value, None)
        seen.add(value)
    return list(dupes)


def _unique_in_order(values: Iterable[str]) -> list[str]:
    """The distinct `values`, first-seen order (dedup so warnings don't double)."""
    return list(dict.fromkeys(values))


def check_evidence(
    node_ids: list[str],
    specs: list[ArtifactSpec],
    gates: list[ValidationGate],
    records: list[EvidenceRecord],
    attempts: list[AssessmentAttempt],
    *,
    probe: ArtifactProbe | None = None,
) -> EvidenceValidationResult:
    """Validate an already-loaded evidence trail. Pure — reports *every* issue.

    `node_ids` is the graph's node ids (for the four dangling-reference checks
    and the per-node warnings); shape of each record is assumed already validated
    by its loader. Drift is checked only when `probe` is given — see the module
    docstring.
    """
    result = EvidenceValidationResult(
        spec_count=len(specs),
        gate_count=len(gates),
        record_count=len(records),
        attempt_count=len(attempts),
    )

    # --- Duplicate ids, per record type ------------------------------------
    for kind, ids in (
        ("artifact spec", [s.id for s in specs]),
        ("validation gate", [g.id for g in gates]),
        ("evidence record", [r.id for r in records]),
        ("assessment attempt", [a.id for a in attempts]),
    ):
        for dup in _duplicates(ids):
            result.errors.append(f"duplicate {kind} id: {dup} appears more than once.")

    known_nodes = set(node_ids)
    spec_ids = {s.id for s in specs}
    record_ids = {r.id for r in records}

    # --- Dangling references ------------------------------------------------
    for spec in specs:
        if spec.node_id not in known_nodes:
            result.errors.append(
                f"artifact spec {spec.id}: node_id names unknown node {spec.node_id}."
            )
    for gate in gates:
        if gate.node_id not in known_nodes:
            result.errors.append(
                f"validation gate {gate.id}: node_id names unknown node {gate.node_id}."
            )
    for record in records:
        if record.artifact_spec_id not in spec_ids:
            result.errors.append(
                f"evidence record {record.id}: artifact_spec_id names unknown spec "
                f"{record.artifact_spec_id}."
            )
    for attempt in attempts:
        if attempt.node_id not in known_nodes:
            result.errors.append(
                f"assessment attempt {attempt.id}: node_id names unknown node "
                f"{attempt.node_id}."
            )
    for record in records:
        if record.supersedes is not None and record.supersedes not in record_ids:
            result.errors.append(
                f"evidence record {record.id}: supersedes names unknown record "
                f"{record.supersedes}."
            )

    # --- Two gates on one node ---------------------------------------------
    gates_by_node: dict[str, list[str]] = {}
    for gate in gates:
        gates_by_node.setdefault(gate.node_id, []).append(gate.id)
    for node_id, gate_id_list in gates_by_node.items():
        if len(gate_id_list) > 1:
            result.errors.append(
                f"node {node_id} has more than one gate ({', '.join(gate_id_list)}) — "
                "a node closes through exactly one authority."
            )

    # --- Supersede chain: cross-spec and double-supersede ------------------
    spec_of_record = {r.id: r.artifact_spec_id for r in records}
    superseders_of: dict[str, list[str]] = {}
    for record in records:
        if record.supersedes is None:
            continue
        superseders_of.setdefault(record.supersedes, []).append(record.id)
        # Cross-spec: only when the target exists (a dangling target is already
        # an error above); a correction must target the same artifact spec.
        target_spec = spec_of_record.get(record.supersedes)
        if target_spec is not None and target_spec != record.artifact_spec_id:
            result.errors.append(
                f"evidence record {record.id}: supersedes {record.supersedes}, which "
                f"targets a different spec ({target_spec} vs {record.artifact_spec_id}) "
                "— a correction stays within one artifact spec."
            )
    for target, superseders in superseders_of.items():
        if len(superseders) > 1:
            result.errors.append(
                f"evidence record {target} is superseded more than once (by "
                f"{', '.join(superseders)}) — a correction chain has one live head."
            )

    # --- Warnings: per-node coverage ---------------------------------------
    nodes_with_gate = {g.node_id for g in gates}
    nodes_with_required_spec = {s.node_id for s in specs if s.required}
    for node_id in _unique_in_order(node_ids):
        if node_id not in nodes_with_gate:
            result.warnings.append(
                f"node {node_id} has no gate — it cannot accept evidence and is never "
                "pass-eligible."
            )
        if node_id not in nodes_with_required_spec:
            result.warnings.append(
                f"node {node_id} has no required artifact spec — it is never "
                "pass-eligible."
            )

    # --- Warnings: artifact drift (every record fingerprints an artifact) ---
    # Checked across all records, superseded ones included: a superseded record
    # still asserts what its artifact was, and a drifted fingerprint is worth
    # surfacing regardless of whether the record currently counts.
    if probe is not None:
        for record in records:
            current = probe(record.location)
            if current is None:
                result.warnings.append(
                    f"artifact drift: evidence record {record.id} location "
                    f"{record.location!r} is missing."
                )
            elif current != record.artifact_hash:
                result.warnings.append(
                    f"artifact drift: evidence record {record.id} artifact at "
                    f"{record.location!r} no longer matches its recorded hash."
                )

    return result


def _safe_load(loader: Callable[[Path], list], root: Path, errors: list[str]) -> list:
    """Run one evidence loader, folding an `EvidenceLoadError` into `errors`.

    A schema violation the loader raises becomes a reported error (issue #11
    scope: "schema violations the loaders catch, surfaced through this command"),
    not a traceback; the run continues with an empty list for that type.
    """
    try:
        return loader(root)
    except EvidenceLoadError as exc:
        errors.append(str(exc))
        return []


def load_and_validate_evidence(
    root: Path | str | None = None,
) -> EvidenceValidationResult:
    """Load nodes + the four evidence sources, then `check_evidence` them.

    Loader failures (node or evidence) are folded into the result's errors so the
    command reports bad data rather than tracebacking. Binds the real artifact
    probe (rooted at `root`) so drift is checked against the files on disk.
    """
    from ..paths import find_root

    root_path = Path(root) if root is not None else find_root()
    load_errors: list[str] = []

    try:
        node_ids = [node.id for node in load_nodes(root_path)]
    except NodeLoadError as exc:
        node_ids = []
        load_errors.append(str(exc))

    specs = _safe_load(load_artifact_specs, root_path, load_errors)
    gates = _safe_load(load_validation_gates, root_path, load_errors)
    records = _safe_load(load_evidence_records, root_path, load_errors)
    attempts = _safe_load(load_assessment_attempts, root_path, load_errors)

    result = check_evidence(
        node_ids,
        specs,
        gates,
        records,
        attempts,
        probe=lambda location: probe_hash(root_path, location),
    )
    # Load errors come first — they explain any downstream emptiness.
    result.errors[:0] = load_errors
    return result
