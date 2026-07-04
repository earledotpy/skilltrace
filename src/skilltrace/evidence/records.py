"""`EvidenceRecord` model and strict loader.

An evidence record is one item of evidence submitted against a node, with its
acceptance verdict frozen in at creation (ADR 0003). It is immutable: no loader
or model API here mutates a record, and there is no mutation method — a
correction is a *new* record that supersedes the old one.

Key schema facts enforced at load:

- The ID is ``ev.<node_id>.NNN``. The record carries **no** `node_id` field:
  the sole linkage to a node is `artifact_spec_id` (the node is derived through
  the spec). A stray `node_id` therefore fails as an unknown field — the closed
  schema is what makes "the spec is the only linkage" structural, not a
  convention.
- `accepted` is a bool (the verdict); `accepted_by` names the deciding authority
  and is one of ``objective_gate`` / ``learner_manual``. These two are the
  *record's* vocabulary — distinct from a gate's ``objective`` / ``manual``
  `authority`. A rejected record still records which authority judged it.
- `supersedes` and `supersede_reason` are both-or-neither: a correction names
  its target *and* gives a reason. The referenced record's existence, same-spec
  match, and single-successor rule are cross-record checks left to
  `validate evidence` (issue #11); the loader only shapes the pair and the ID.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._schema import EvidenceLoadError, check_shape, read_yaml_list, where_prefix
from .ids import is_valid_evidence_id

_KIND = "evidence record"
_RECORDS_RELPATH = Path("evidence") / "evidence_records.yaml"

# The two authorities that may appear on a record — the record-side vocabulary,
# distinct from a gate's authority enum. AI is absent here too, by the same rule.
ACCEPTED_BY_VALUES: frozenset[str] = frozenset({"objective_gate", "learner_manual"})

_ALLOWED_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "artifact_spec_id",
        "location",
        "note",
        "accepted",
        "accepted_by",
        "artifact_hash",
        "supersedes",
        "supersede_reason",
        "created_at",
    }
)

_REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "artifact_spec_id",
    "location",
    "accepted",
    "accepted_by",
    "artifact_hash",
    "created_at",
)


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
    created_at: Any = None
    source_path: Path | None = None


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
        kind=_KIND,
        allowed=_ALLOWED_FIELDS,
        required=_REQUIRED_FIELDS,
        source_path=source_path,
        index=index,
    )
    ident = f"{_KIND} {data['id']!r}"
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
        created_at=data.get("created_at"),
        source_path=source_path,
    )


def load_evidence_records(root: Path | str | None = None) -> list[EvidenceRecord]:
    """Load every record from `evidence/evidence_records.yaml` (default root: auto).

    Returns the raw list in file order; duplicate-ID, dangling-`supersedes`,
    cross-spec-supersede, and double-supersede detection belong to
    `validate evidence` (issue #11).
    """
    from ..paths import find_root

    root_path = Path(root) if root is not None else find_root()
    path = root_path / _RECORDS_RELPATH
    raw = read_yaml_list(path, top_key="evidence_records", kind=_KIND)
    return [
        load_evidence_record(item, source_path=path, index=i)
        for i, item in enumerate(raw)
    ]
