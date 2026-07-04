"""`ArtifactSpec` model and strict loader.

An ArtifactSpec defines one kind of evidence a node expects: what artifact, how
many (its `minimum_count`), and whether it is `required`. Every evidence record
is submitted against exactly one spec, and the spec is where a record's node is
recorded — the record itself carries no `node_id` (issue #10; the node is derived
through the spec).

Closed schema, mirroring the edge loader: the allowed set is exactly the fields
the seed uses, and anything else fails naming the spec. But *allowed* is wider
than *required*: the authoring/descriptive fields (`description`,
`acceptance_summary`, `expected_location_hint`, `example_filename`) are optional
even though every seed row carries them. The two engine-load-bearing checks are
`required` being a real bool and `minimum_count` being an integer ``>= 1`` — a
`minimum_count: 0` is a load error, since an optional spec is expressed by
`required: false`, never by a zero count.

`artifact_kind` is deliberately *not* enum-constrained: it is curriculum
vocabulary (like a track label), and the engine attaches no meaning to it. A new
curriculum introducing a `diagram` kind must load without an engine change.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..graph.nodes import is_valid_node_id
from ._schema import EvidenceLoadError, check_shape, read_yaml_list, where_prefix

_KIND = "artifact spec"
_SPECS_RELPATH = Path("evidence") / "artifact_specs.yaml"

# The closed schema: exactly the fields the seed uses.
_ALLOWED_FIELDS: frozenset[str] = frozenset(
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
)

# The minimum the engine needs. Descriptive text stays allowed-but-optional.
_REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "node_id",
    "title",
    "artifact_kind",
    "required",
    "minimum_count",
)


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
        raise EvidenceLoadError(
            f"{where}{ident} has invalid node_id {node_id!r}."
        )

    required = data["required"]
    if not isinstance(required, bool):
        raise EvidenceLoadError(
            f"{where}{ident} has non-boolean required {required!r} — expected "
            "true/false."
        )

    minimum_count = data["minimum_count"]
    # `bool` is a subclass of `int`; a stray `true`/`false` here is a schema
    # error, not the integer 1/0 it would coerce to.
    if not isinstance(minimum_count, int) or isinstance(minimum_count, bool) or minimum_count < 1:
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


def load_artifact_specs(root: Path | str | None = None) -> list[ArtifactSpec]:
    """Load every spec from `evidence/artifact_specs.yaml` (default root: auto).

    Returns the raw list in file order; duplicate-ID and dangling-reference
    detection belong to `validate evidence` (issue #11), not the loader.
    """
    from ..paths import find_root

    root_path = Path(root) if root is not None else find_root()
    path = root_path / _SPECS_RELPATH
    raw = read_yaml_list(path, top_key="artifact_specs", kind=_KIND)
    return [
        load_artifact_spec(item, source_path=path, index=i)
        for i, item in enumerate(raw)
    ]
