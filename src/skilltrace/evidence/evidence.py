"""Deep evidence record loader — one module for all evidence YAML I/O.

Collapses four shallow loader modules (specs, gates, records, attempts) into a
single deep module that owns:

* reading all four evidence YAML files in one pass
* shape-checking each record type against its schema descriptor
* mapping to typed dataclasses
* returning a single structured result ``EvidenceRecords``

The per-type single-item loaders (``load_artifact_spec`` etc.) and per-type
list loaders (``load_artifact_specs`` etc.) remain public for direct callers
(validation, commands) that need a single type and expect an
``EvidenceLoadError`` on shape failure. The combined ``load_evidence``
aggregates per-type results and never raises for expected shape/YAML errors;
instead it populates ``EvidenceRecords.errors`` so the joined-view seam can
decide whether to collect errors (strict) or degrade (lenient) per record
type — mirroring ``execution.records.load_execution``.

Each dataclass is paired with a schema descriptor (allowed fields, required
fields, file relpath, top key, kind string) consumed by the generic
``_load_typed_list`` helper. The generic ``_schema.py`` helpers
(``check_shape``, ``read_yaml_list``, ``where_prefix``) do the uniform work;
the descriptors supply the evidence-specific policy (which file, which
schema). Adding a new evidence record type means registering one descriptor,
not creating a new module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..graph.nodes import is_valid_node_id
from ._schema import EvidenceLoadError, check_shape, read_yaml_list, where_prefix
from .ids import is_valid_evidence_id, split_attempt_id

# ---------------------------------------------------------------------------
# Schema descriptors — one per record type, co-located with its dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceSchema:
    """What the generic loader needs to load one evidence record type.

    ``kind`` names the record in error messages, ``relpath`` locates the YAML
    file under the repo root, ``top_key`` is the expected top-level mapping
    key, and ``allowed``/``required`` are the closed-schema field sets.
    """

    kind: str
    relpath: Path
    top_key: str
    allowed: frozenset[str]
    required: tuple[str, ...]


# The two — and only two — acceptance authorities. AI is not among them and
# cannot be added here without changing the meaning of the engine.
AUTHORITIES: frozenset[str] = frozenset({"objective", "manual"})

# The two authorities that may appear on a record — the record-side vocabulary,
# distinct from a gate's authority enum. AI is absent here too, by the same rule.
ACCEPTED_BY_VALUES: frozenset[str] = frozenset({"objective_gate", "learner_manual"})

# The two — and only two — outcomes. No scores, no third "partial".
OUTCOMES: frozenset[str] = frozenset({"passed", "failed"})

# v2.2 gate-run receipts: the optional provenance mapping an objective-gate
# record may carry. The key set is closed inside the closed record schema —
# unknown keys inside `gate_run` fail exactly like unknown record keys. Hash
# fields must be `sha256:` over the captured stream (raw output is never
# stored); `tool`/`version` are schema placeholders that stay unpopulated in
# v2.2 (populating them means probing subprocesses — the future gate-runner).
GATE_RUN_KEY = "gate_run"
GATE_RUN_ALLOWED: frozenset[str] = frozenset(
    {
        "command_argv",
        "inputs",
        "exit_class",
        "exit_code",
        "stdout_hash",
        "stderr_hash",
        "tool",
        "version",
    }
)
GATE_RUN_REQUIRED: tuple[str, ...] = ("command_argv", "inputs", "exit_class")
# The two — and only two — exit classes. Inability to run is not an exit class:
# a gate that cannot be spawned produces no record at all.
EXIT_CLASSES: frozenset[str] = frozenset({"passed", "failed"})
_HASH_PREFIX = "sha256:"

SPEC_SCHEMA = EvidenceSchema(
    kind="artifact spec",
    relpath=Path("evidence") / "artifact_specs.yaml",
    top_key="artifact_specs",
    allowed=frozenset(
        {
            "id",
            "node_id",
            "title",
            "artifact_kind",
            "description",
            "required",
            "minimum_count",
            "expected_location_hint",
            "example_filename",
            "acceptance_summary",
            "created_at",
            "updated_at",
        }
    ),
    required=(
        "id",
        "node_id",
        "title",
        "artifact_kind",
        "required",
        "minimum_count",
    ),
)

GATE_SCHEMA = EvidenceSchema(
    kind="validation gate",
    relpath=Path("evidence") / "validation_gates.yaml",
    top_key="validation_gates",
    allowed=frozenset(
        {
            "id",
            "node_id",
            "authority",
            "command",
            "title",
            "description",
            "created_at",
            "updated_at",
        }
    ),
    required=("id", "node_id", "authority"),
)

RECORD_SCHEMA = EvidenceSchema(
    kind="evidence record",
    relpath=Path("evidence") / "evidence_records.yaml",
    top_key="evidence_records",
    allowed=frozenset(
        {
            "id",
            "artifact_spec_id",
            "location",
            "note",
            "accepted",
            "accepted_by",
            "artifact_hash",
            GATE_RUN_KEY,
            "supersedes",
            "supersede_reason",
            "created_at",
        }
    ),
    required=(
        "id",
        "artifact_spec_id",
        "location",
        "accepted",
        "accepted_by",
        "artifact_hash",
        "created_at",
    ),
)

ATTEMPT_SCHEMA = EvidenceSchema(
    kind="assessment attempt",
    relpath=Path("evidence") / "attempts.yaml",
    top_key="attempts",
    allowed=frozenset({"id", "node_id", "outcome", "note", "created_at"}),
    required=("id", "node_id", "outcome", "created_at"),
)


# ---------------------------------------------------------------------------
# Dataclasses — schema, shape-checker, and factory co-located
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArtifactSpec:
    """One kind of evidence a node expects — its node linkage, count, and status.

    `required` distinguishes a counted spec (must meet `minimum_count` accepted
    records for the node to be pass-eligible) from an optional slot (kept and
    shown, never counted). `minimum_count` is always ``>= 1``.
    """

    id: str
    node_id: str
    title: str
    artifact_kind: str
    required: bool
    minimum_count: int
    description: str | None = None
    expected_location_hint: str | None = None
    example_filename: str | None = None
    acceptance_summary: str | None = None
    created_at: Any = None
    updated_at: Any = None
    source_path: Path | None = None


@dataclass(frozen=True)
class ValidationGate:
    """A node's closing gate: which single authority judges its evidence.

    `command` is present iff `authority == "objective"` — the verification
    command run at submission whose exit code is the verdict. A manual gate
    leaves it `None`; the learner states the verdict explicitly at submission.
    """

    id: str
    node_id: str
    authority: str
    command: str | None = None
    title: str | None = None
    description: str | None = None
    created_at: Any = None
    updated_at: Any = None
    source_path: Path | None = None


@dataclass(frozen=True)
class EvidenceRecord:
    """One item of submitted evidence — its verdict frozen at creation.

    `frozen=True` is the model-level guarantee that matches the domain rule:
    records are never edited or deleted. A correction is a new record whose
    `supersedes` names the old one; superseded status is derived from that
    pointer, never written onto the old record.
    """

    id: str
    artifact_spec_id: str
    location: str
    accepted: bool
    accepted_by: str
    artifact_hash: str
    note: str | None = None
    supersedes: str | None = None
    supersede_reason: str | None = None
    gate_run: dict | None = None
    created_at: Any = None
    source_path: Path | None = None


@dataclass(frozen=True)
class AssessmentAttempt:
    """One attempt at a node's skill — passed or failed, immutable, no supersede."""

    id: str
    node_id: str
    outcome: str
    note: str | None = None
    created_at: Any = None
    source_path: Path | None = None


@dataclass
class EvidenceRecords:
    """Structured result of loading all evidence YAML files.

    ``errors`` maps the JoinedView attribute name (``"specs"``, ``"gates"``,
    ``"records"``, ``"attempts"``) to the ``EvidenceLoadError`` message for
    that file. A missing or malformed file yields an empty list for that
    attribute and an entry in ``errors``; the other three types still load.
    """

    specs: list[ArtifactSpec] = field(default_factory=list)
    gates: list[ValidationGate] = field(default_factory=list)
    records: list[EvidenceRecord] = field(default_factory=list)
    attempts: list[AssessmentAttempt] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Per-type single-item loaders — semantic checks live here
# ---------------------------------------------------------------------------


def load_artifact_spec(
    data: Any, *, source_path: Path | None = None, index: int | None = None
) -> ArtifactSpec:
    """Validate one spec mapping into an `ArtifactSpec`.

    Raises `EvidenceLoadError` (naming the spec) on a non-mapping, an unknown
    field, a missing required field, a malformed `node_id`, a non-boolean
    `required`, or a `minimum_count` that is not an integer ``>= 1``.
    """
    check_shape(
        data,
        kind=SPEC_SCHEMA.kind,
        allowed=SPEC_SCHEMA.allowed,
        required=SPEC_SCHEMA.required,
        source_path=source_path,
        index=index,
    )
    ident = f"{SPEC_SCHEMA.kind} {data['id']!r}"
    where = where_prefix(source_path)

    node_id = data["node_id"]
    if not isinstance(node_id, str) or not is_valid_node_id(node_id):
        raise EvidenceLoadError(f"{where}{ident} has invalid node_id {node_id!r}.")

    required = data["required"]
    if not isinstance(required, bool):
        raise EvidenceLoadError(
            f"{where}{ident} has non-boolean required {required!r} — expected "
            "true/false."
        )

    minimum_count = data["minimum_count"]
    # `bool` is a subclass of `int`; a stray `true`/`false` here is a schema
    # error, not the integer 1/0 it would coerce to.
    if (
        not isinstance(minimum_count, int)
        or isinstance(minimum_count, bool)
        or minimum_count < 1
    ):
        raise EvidenceLoadError(
            f"{where}{ident} has invalid minimum_count {minimum_count!r} — expected "
            "an integer >= 1 (an optional spec uses required: false, not a zero "
            "count)."
        )

    return ArtifactSpec(
        id=data["id"],
        node_id=node_id,
        title=data["title"],
        artifact_kind=data["artifact_kind"],
        required=required,
        minimum_count=minimum_count,
        description=data.get("description"),
        expected_location_hint=data.get("expected_location_hint"),
        example_filename=data.get("example_filename"),
        acceptance_summary=data.get("acceptance_summary"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        source_path=source_path,
    )


def load_validation_gate(
    data: Any, *, source_path: Path | None = None, index: int | None = None
) -> ValidationGate:
    """Validate one gate mapping into a `ValidationGate`.

    Raises `EvidenceLoadError` (naming the gate) on a non-mapping, an unknown
    field, a missing required field, a malformed `node_id`, an `authority`
    outside the two values, or a `command` that is present on a manual gate or
    absent on an objective one.
    """
    check_shape(
        data,
        kind=GATE_SCHEMA.kind,
        allowed=GATE_SCHEMA.allowed,
        required=GATE_SCHEMA.required,
        source_path=source_path,
        index=index,
    )
    ident = f"{GATE_SCHEMA.kind} {data['id']!r}"
    where = where_prefix(source_path)

    node_id = data["node_id"]
    if not isinstance(node_id, str) or not is_valid_node_id(node_id):
        raise EvidenceLoadError(f"{where}{ident} has invalid node_id {node_id!r}.")

    authority = data["authority"]
    if authority not in AUTHORITIES:
        raise EvidenceLoadError(
            f"{where}{ident} has unknown authority {authority!r} — expected one of "
            f"{', '.join(sorted(AUTHORITIES))} (an AI acceptance authority is not "
            "representable)."
        )

    command = data.get("command")
    if authority == "objective" and not (isinstance(command, str) and command):
        raise EvidenceLoadError(
            f"{where}{ident} is an objective gate but has no command string — the "
            "verification command is what an objective gate runs to judge evidence."
        )
    if authority == "manual" and command is not None:
        raise EvidenceLoadError(
            f"{where}{ident} is a manual gate but carries a command {command!r} — "
            "a manual gate is judged by the learner, not a command."
        )

    return ValidationGate(
        id=data["id"],
        node_id=node_id,
        authority=authority,
        command=command,
        title=data.get("title"),
        description=data.get("description"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        source_path=source_path,
    )


def load_evidence_record(
    data: Any, *, source_path: Path | None = None, index: int | None = None
) -> EvidenceRecord:
    """Validate one record mapping into an `EvidenceRecord`.

    Raises `EvidenceLoadError` (naming the record) on a non-mapping, an unknown
    field (a stray `node_id` included), a missing required field, a malformed
    ``ev.<node_id>.NNN`` ID, a non-boolean `accepted`, an `accepted_by` outside
    the two values, or a `supersedes`/`supersede_reason` pair that is not
    both-or-neither.
    """
    check_shape(
        data,
        kind=RECORD_SCHEMA.kind,
        allowed=RECORD_SCHEMA.allowed,
        required=RECORD_SCHEMA.required,
        source_path=source_path,
        index=index,
    )
    ident = f"{RECORD_SCHEMA.kind} {data['id']!r}"
    where = where_prefix(source_path)

    record_id = data["id"]
    if not is_valid_evidence_id(record_id):
        raise EvidenceLoadError(
            f"{where}{ident} has malformed id — expected ev.<node_id>.NNN."
        )

    accepted = data["accepted"]
    if not isinstance(accepted, bool):
        raise EvidenceLoadError(
            f"{where}{ident} has non-boolean accepted {accepted!r} — expected "
            "true/false."
        )

    accepted_by = data["accepted_by"]
    if accepted_by not in ACCEPTED_BY_VALUES:
        raise EvidenceLoadError(
            f"{where}{ident} has unknown accepted_by {accepted_by!r} — expected one "
            f"of {', '.join(sorted(ACCEPTED_BY_VALUES))}."
        )

    supersedes = data.get("supersedes")
    supersede_reason = data.get("supersede_reason")
    if (supersedes is None) != (supersede_reason is None):
        raise EvidenceLoadError(
            f"{where}{ident} must carry supersedes and supersede_reason together — "
            "a correction names its target and gives a reason, or neither."
        )
    if supersedes is not None and not is_valid_evidence_id(supersedes):
        raise EvidenceLoadError(
            f"{where}{ident} supersedes malformed id {supersedes!r} — expected "
            "ev.<node_id>.NNN."
        )

    gate_run = _check_gate_run(data, ident, where)

    return EvidenceRecord(
        id=record_id,
        artifact_spec_id=data["artifact_spec_id"],
        location=data["location"],
        accepted=accepted,
        accepted_by=accepted_by,
        artifact_hash=data["artifact_hash"],
        note=data.get("note"),
        supersedes=supersedes,
        supersede_reason=supersede_reason,
        gate_run=gate_run,
        created_at=data.get("created_at"),
        source_path=source_path,
    )


def _check_gate_run(data: dict, ident: str, where: str) -> dict | None:
    """Validate the optional `gate_run` receipt mapping (v2.2 spec §1/§3).

    Present on the record (even as null) it must be a mapping carrying exactly
    `command_argv`/`inputs`/`exit_class`, with `exit_class` one of the two
    values, `exit_code` an int when present, both hash fields `sha256:<hex>`
    when present, and no key outside the closed receipt set. A *missing*
    `gate_run` is valid — pre-v2.2 and manual records carry none.
    """
    if GATE_RUN_KEY not in data:
        return None
    raw = data[GATE_RUN_KEY]
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise EvidenceLoadError(
            f"{where}{ident} has non-mapping {GATE_RUN_KEY} {raw!r} — expected a "
            "gate-run receipt mapping."
        )
    unknown = sorted(set(raw) - GATE_RUN_ALLOWED)
    if unknown:
        raise EvidenceLoadError(
            f"{where}{ident} has unknown {GATE_RUN_KEY} field(s): "
            f"{', '.join(unknown)}."
        )
    missing = [key for key in GATE_RUN_REQUIRED if raw.get(key) is None]
    if missing:
        raise EvidenceLoadError(
            f"{where}{ident} has {GATE_RUN_KEY} missing required field(s): "
            f"{', '.join(missing)}."
        )
    for key in ("command_argv", "inputs"):
        value = raw[key]
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise EvidenceLoadError(
                f"{where}{ident} has non-string-list {GATE_RUN_KEY}.{key} "
                f"{value!r}."
            )
    # A receipt referencing nothing is not provenance (spec §3): an empty
    # command_argv fails (spec §1's verb-first seed contract means empty argv
    # is never a legitimate receipt); an empty inputs list is legitimate
    # (out-of-repo / URL artifacts).
    if not raw["command_argv"]:
        raise EvidenceLoadError(
            f"{where}{ident} has empty {GATE_RUN_KEY}.command_argv — a receipt "
            "referencing nothing is not provenance."
        )
    exit_class = raw["exit_class"]
    if exit_class not in EXIT_CLASSES:
        raise EvidenceLoadError(
            f"{where}{ident} has unknown {GATE_RUN_KEY}.exit_class "
            f"{exit_class!r} — expected one of {', '.join(sorted(EXIT_CLASSES))}."
        )
    exit_code = raw.get("exit_code")
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool)
    ):
        raise EvidenceLoadError(
            f"{where}{ident} has non-integer {GATE_RUN_KEY}.exit_code "
            f"{exit_code!r}."
        )
    # tool/version are v2.2 schema placeholders — the planner never writes
    # them (populating them means probing subprocesses, the future
    # gate-runner's job), so a non-null value is a malformed receipt, not
    # provenance (spec §1, D-Normalize).
    for key in ("tool", "version"):
        if raw.get(key) is not None:
            raise EvidenceLoadError(
                f"{where}{ident} has populated {GATE_RUN_KEY}.{key} "
                f"{raw[key]!r} — tool/version stay unpopulated in v2.2."
            )
    for key in ("stdout_hash", "stderr_hash"):
        value = raw.get(key)
        if value is None:
            continue
        if (
            not isinstance(value, str)
            or not value.startswith(_HASH_PREFIX)
            or len(value) <= len(_HASH_PREFIX)
            or any(c not in "0123456789abcdef" for c in value[len(_HASH_PREFIX):])
        ):
            raise EvidenceLoadError(
                f"{where}{ident} has malformed {GATE_RUN_KEY}.{key} {value!r} — "
                f"expected sha256:<hex> over the captured stream."
            )
    return dict(raw)


def load_assessment_attempt(
    data: Any, *, source_path: Path | None = None, index: int | None = None
) -> AssessmentAttempt:
    """Validate one attempt mapping into an `AssessmentAttempt`.

    Raises `EvidenceLoadError` (naming the attempt) on a non-mapping, an unknown
    field, a missing required field, a malformed ``att.<node_id>.NNN`` ID, an
    `outcome` outside the two values, or an ID whose embedded node disagrees with
    the `node_id` field.
    """
    check_shape(
        data,
        kind=ATTEMPT_SCHEMA.kind,
        allowed=ATTEMPT_SCHEMA.allowed,
        required=ATTEMPT_SCHEMA.required,
        source_path=source_path,
        index=index,
    )
    ident = f"{ATTEMPT_SCHEMA.kind} {data['id']!r}"
    where = where_prefix(source_path)

    node_id = data["node_id"]
    if not isinstance(node_id, str) or not is_valid_node_id(node_id):
        raise EvidenceLoadError(f"{where}{ident} has invalid node_id {node_id!r}.")

    outcome = data["outcome"]
    if outcome not in OUTCOMES:
        raise EvidenceLoadError(
            f"{where}{ident} has unknown outcome {outcome!r} — expected one of "
            f"{', '.join(sorted(OUTCOMES))}."
        )

    parsed = split_attempt_id(data["id"])
    if parsed is None:
        raise EvidenceLoadError(
            f"{where}{ident} has malformed id — expected att.<node_id>.NNN."
        )
    if parsed[0] != node_id:
        raise EvidenceLoadError(
            f"{where}{ident} embeds node {parsed[0]!r} but declares node_id "
            f"{node_id!r} — the id and the field must name the same node."
        )

    return AssessmentAttempt(
        id=data["id"],
        node_id=node_id,
        outcome=outcome,
        note=data.get("note"),
        created_at=data.get("created_at"),
        source_path=source_path,
    )


# ---------------------------------------------------------------------------
# Generic layer loader — descriptors drive the file reads
# ---------------------------------------------------------------------------


def _load_typed_list(
    root: Path,
    schema: EvidenceSchema,
    factory: Callable[..., Any],
) -> list[Any]:
    """Read one evidence YAML file and map each entry via `factory`.

    The schema descriptor supplies which file, which top key, and which
    shape to enforce; `factory` performs the type's semantic checks. Raises
    `EvidenceLoadError` naming the record on any failure.
    """
    path = root / schema.relpath
    raw = read_yaml_list(path, top_key=schema.top_key, kind=schema.kind)
    return [
        factory(item, source_path=path, index=i) for i, item in enumerate(raw)
    ]


def _resolve_root(root: Path | str | None) -> Path:
    from ..paths import find_root

    return Path(root) if root is not None else find_root()


def load_artifact_specs(root: Path | str | None = None) -> list[ArtifactSpec]:
    """Load every spec from `evidence/artifact_specs.yaml` (default root: auto).

    Returns the raw list in file order; duplicate-ID and dangling-reference
    detection belong to `validate evidence` (issue #11), not the loader.
    """
    return _load_typed_list(_resolve_root(root), SPEC_SCHEMA, load_artifact_spec)


def load_validation_gates(root: Path | str | None = None) -> list[ValidationGate]:
    """Load every gate from `evidence/validation_gates.yaml` (default root: auto).

    Returns the raw list in file order; two-gates-on-one-node and dangling
    `node_id` detection belong to `validate evidence` (issue #11).
    """
    return _load_typed_list(_resolve_root(root), GATE_SCHEMA, load_validation_gate)


def load_evidence_records(root: Path | str | None = None) -> list[EvidenceRecord]:
    """Load every record from `evidence/evidence_records.yaml` (default root: auto).

    Returns the raw list in file order; duplicate-ID, dangling-`supersedes`,
    cross-spec-supersede, and double-supersede detection belong to
    `validate evidence` (issue #11).
    """
    return _load_typed_list(_resolve_root(root), RECORD_SCHEMA, load_evidence_record)


def load_assessment_attempts(
    root: Path | str | None = None,
) -> list[AssessmentAttempt]:
    """Load every attempt from `evidence/attempts.yaml` (default root: auto).

    Returns the raw list in file order; duplicate-ID and dangling-`node_id`
    detection belong to `validate evidence` (issue #11).
    """
    return _load_typed_list(
        _resolve_root(root), ATTEMPT_SCHEMA, load_assessment_attempt
    )


# ---------------------------------------------------------------------------
# Combined loader — one call, many records, per-type error aggregation
# ---------------------------------------------------------------------------


def load_evidence(root: Path | str | None = None) -> EvidenceRecords:
    """Load all four evidence record types in one pass.

    Each file is attempted independently; an `EvidenceLoadError` for one
    type degrades that type to an empty list and records the error in
    ``EvidenceRecords.errors`` without aborting the other three. Unexpected
    exceptions propagate.

    This is the single seam for the joined-view evidence layer — one call,
    many records, per-type degradation captured for the caller to decide
    (strict -> errors, lenient -> degraded).
    """
    root_path = _resolve_root(root)
    result = EvidenceRecords()
    errors: dict[str, str] = {}

    try:
        result.specs = _load_typed_list(root_path, SPEC_SCHEMA, load_artifact_spec)
    except EvidenceLoadError as exc:
        errors["specs"] = str(exc)
        result.specs = []

    try:
        result.gates = _load_typed_list(root_path, GATE_SCHEMA, load_validation_gate)
    except EvidenceLoadError as exc:
        errors["gates"] = str(exc)
        result.gates = []

    try:
        result.records = _load_typed_list(
            root_path, RECORD_SCHEMA, load_evidence_record
        )
    except EvidenceLoadError as exc:
        errors["records"] = str(exc)
        result.records = []

    try:
        result.attempts = _load_typed_list(
            root_path, ATTEMPT_SCHEMA, load_assessment_attempt
        )
    except EvidenceLoadError as exc:
        errors["attempts"] = str(exc)
        result.attempts = []

    result.errors = errors
    return result
