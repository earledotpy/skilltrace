"""`ValidationGate` model and strict loader.

A gate declares the single acceptance authority that judges evidence submitted
against a node. There are exactly two authorities, and the schema is the
boundary: `authority` accepts only ``objective`` or ``manual``. Any other value
— ``ai`` above all — fails to load. An AI acceptance authority is not merely
disallowed by policy; it is *unrepresentable* (CONTEXT.md, issue #10).

The two authorities differ by one field: an objective gate carries the
verification `command` it runs at submission; a manual gate carries none. So the
loader enforces the pairing both ways — a `command` on a manual gate fails, and a
missing `command` on an objective gate fails — rather than silently ignoring a
misplaced one.

Closed schema; allowed set is exactly the seed's fields, `command` included.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..graph.nodes import is_valid_node_id
from ._schema import EvidenceLoadError, check_shape, read_yaml_list, where_prefix

_KIND = "validation gate"
_GATES_RELPATH = Path("evidence") / "validation_gates.yaml"

# The two — and only two — acceptance authorities. AI is not among them and
# cannot be added here without changing the meaning of the engine.
AUTHORITIES: frozenset[str] = frozenset({"objective", "manual"})

_ALLOWED_FIELDS: frozenset[str] = frozenset(
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
)

_REQUIRED_FIELDS: tuple[str, ...] = ("id", "node_id", "authority")


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


def load_validation_gates(root: Path | str | None = None) -> list[ValidationGate]:
    """Load every gate from `evidence/validation_gates.yaml` (default root: auto).

    Returns the raw list in file order; two-gates-on-one-node and dangling
    `node_id` detection belong to `validate evidence` (issue #11).
    """
    from ..paths import find_root

    root_path = Path(root) if root is not None else find_root()
    path = root_path / _GATES_RELPATH
    raw = read_yaml_list(path, top_key="validation_gates", kind=_KIND)
    return [
        load_validation_gate(item, source_path=path, index=i)
        for i, item in enumerate(raw)
    ]
