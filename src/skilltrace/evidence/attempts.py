"""`AssessmentAttempt` model and strict loader.

An attempt is one attempt at demonstrating a node's skill against its gate's
standard. Its `outcome` is two-valued — ``passed`` or ``failed``, no scores —
and it is immutable with no supersede mechanism (unlike an evidence record). A
failed attempt is the canonical record of assessment failure; attempts never
feed pass eligibility.

Unlike an evidence record, an attempt *does* carry a `node_id` field, and its ID
is ``att.<node_id>.NNN``. Because the node appears in two places on the same
record, the loader enforces that they agree — an intra-record consistency check,
so it belongs here (issue #10), not in cross-record validation (issue #11).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..graph.nodes import is_valid_node_id
from ._schema import EvidenceLoadError, check_shape, read_yaml_list, where_prefix
from .ids import split_attempt_id

_KIND = "assessment attempt"
_ATTEMPTS_RELPATH = Path("evidence") / "attempts.yaml"

# The two — and only two — outcomes. No scores, no third "partial".
OUTCOMES: frozenset[str] = frozenset({"passed", "failed"})

_ALLOWED_FIELDS: frozenset[str] = frozenset(
    {"id", "node_id", "outcome", "note", "created_at"}
)

_REQUIRED_FIELDS: tuple[str, ...] = ("id", "node_id", "outcome", "created_at")


@dataclass(frozen=True)
class AssessmentAttempt:
    """One attempt at a node's skill — passed or failed, immutable, no supersede."""

    id: str
    node_id: str
    outcome: str
    note: str | None = None
    created_at: Any = None
    source_path: Path | None = None


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
        kind=_KIND,
        allowed=_ALLOWED_FIELDS,
        required=_REQUIRED_FIELDS,
        source_path=source_path,
        index=index,
    )
    ident = f"{_KIND} {data['id']!r}"
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


def load_assessment_attempts(root: Path | str | None = None) -> list[AssessmentAttempt]:
    """Load every attempt from `evidence/attempts.yaml` (default root: auto).

    Returns the raw list in file order; duplicate-ID and dangling-`node_id`
    detection belong to `validate evidence` (issue #11).
    """
    from ..paths import find_root

    root_path = Path(root) if root is not None else find_root()
    path = root_path / _ATTEMPTS_RELPATH
    raw = read_yaml_list(path, top_key="attempts", kind=_KIND)
    return [
        load_assessment_attempt(item, source_path=path, index=i)
        for i, item in enumerate(raw)
    ]
