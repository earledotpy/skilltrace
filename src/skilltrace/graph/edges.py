"""`GraphEdge` model and strict edge loader.

`edges.yaml` is the *sole* source of truth for node relationships (invariant),
and the semantics of a relationship live entirely in its `edge_type` — there are
exactly three types and nothing else qualifies them. So the edge loader is the
mirror-image of the node loader: where nodes tolerate unknown frontmatter keys,
edges use a **closed** schema. Any field outside the allowed set is a hard load
error naming the offending edge. That is what permanently retires the three
pruned qualifier fields (`strength`, `can_override`, `activation_rule`, decisions
4/5) rather than merely dropping them from the seed data once.

This loader validates the *shape* of each edge only. It does not check that
`source`/`target` name real nodes, detect duplicate edge ids, or find cycles —
all of that is graph validation (issue #5), which is handed the raw list.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..paths import find_root

# The three — and only three — relationship types. The semantics of a
# relationship live here, in the type, not in per-edge qualifier fields.
EDGE_TYPES: frozenset[str] = frozenset(
    {"hard_prerequisite", "soft_prerequisite", "remediation"}
)

# The qualifier fields removed in the v0.3 migration (decisions 4/5): edge
# semantics moved into the type, so these are dropped. They are not special-cased
# in the loader — they fail as ordinary unknown fields — but naming them lets a
# validation run point at leftover scaffold data explicitly.
PRUNED_EDGE_FIELDS: frozenset[str] = frozenset(
    {"strength", "can_override", "activation_rule"}
)

# The closed schema: every key an edge may carry. Anything else fails.
_ALLOWED_FIELDS: frozenset[str] = frozenset(
    {"id", "source", "target", "edge_type", "reason", "active", "created_at", "updated_at"}
)

# Fields that must be present on every edge. `active` is checked for *presence*,
# not truthiness — `active: false` is a legitimate value, not an absent field.
_REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "source",
    "target",
    "edge_type",
    "reason",
    "active",
)

_EDGES_RELPATH = Path("graph") / "edges.yaml"


class EdgeLoadError(Exception):
    """An edge could not be loaded or violates the edge schema.

    The message always names the offending edge — by id when available, else by
    its position in the file — so a validation run points straight at it.
    """


@dataclass(frozen=True)
class GraphEdge:
    """One relationship between two nodes — pure structure, no qualifiers.

    The relationship's meaning is its `edge_type`; there are no strength,
    override, or activation-rule fields. `active` toggles whether the edge is in
    force without deleting it (edges, like evidence, are not silently removed).
    """

    id: str
    source: str
    target: str
    edge_type: str
    reason: str
    active: bool
    created_at: Any = None
    updated_at: Any = None
    source_path: Path | None = None


def _edge_ident(data: Any, index: int | None) -> str:
    """A human-pointing identifier for error messages: edge id, else position."""
    if isinstance(data, dict) and isinstance(data.get("id"), str) and data["id"]:
        return f"edge {data['id']!r}"
    if index is not None:
        return f"edge #{index}"
    return "edge"


def load_edge(
    data: Any, *, source_path: Path | None = None, index: int | None = None
) -> GraphEdge:
    """Validate one edge mapping into a `GraphEdge`.

    Raises `EdgeLoadError` (naming the edge) on a non-mapping, an unknown field
    (including a leftover pruned field), a missing required field, an unknown
    `edge_type`, or a non-boolean `active`.
    """
    ident = _edge_ident(data, index)
    where = f"{source_path}: " if source_path is not None else ""

    if not isinstance(data, dict):
        raise EdgeLoadError(f"{where}{ident} is not a mapping.")

    unknown = sorted(set(data) - _ALLOWED_FIELDS)
    if unknown:
        pruned = [key for key in unknown if key in PRUNED_EDGE_FIELDS]
        hint = (
            f" (pruned field(s) {', '.join(pruned)} — edge semantics live in the "
            "edge type, decisions 4/5)"
            if pruned
            else ""
        )
        raise EdgeLoadError(
            f"{where}{ident} has unknown field(s): {', '.join(unknown)}{hint}."
        )

    missing = [key for key in _REQUIRED_FIELDS if key not in data]
    if missing:
        raise EdgeLoadError(
            f"{where}{ident} is missing required field(s): {', '.join(missing)}."
        )

    edge_type = data["edge_type"]
    if not isinstance(edge_type, str) or edge_type not in EDGE_TYPES:
        raise EdgeLoadError(
            f"{where}{ident} has unknown edge_type {edge_type!r} — expected one of "
            f"{', '.join(sorted(EDGE_TYPES))}."
        )

    active = data["active"]
    if not isinstance(active, bool):
        raise EdgeLoadError(
            f"{where}{ident} has non-boolean active {active!r} — expected true/false."
        )

    return GraphEdge(
        id=data["id"],
        source=data["source"],
        target=data["target"],
        edge_type=edge_type,
        reason=data["reason"],
        active=active,
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        source_path=source_path,
    )


def load_edges(root: Path | str | None = None) -> list[GraphEdge]:
    """Load every edge from `graph/edges.yaml` (default root: auto-detected).

    Returns a list in file order. Duplicate ids are *not* collapsed here — the
    raw list is handed to graph validation (issue #5), which is where
    duplicate-edge and referential-integrity detection belong.
    """
    root_path = Path(root) if root is not None else find_root()
    path = root_path / _EDGES_RELPATH

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EdgeLoadError(f"{path}: cannot read edges file: {exc}") from exc

    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise EdgeLoadError(f"{path}: unparseable edges YAML: {exc}") from exc

    if not isinstance(doc, dict) or "edges" not in doc:
        raise EdgeLoadError(f"{path}: expected a top-level 'edges:' mapping.")

    raw = doc["edges"]
    if not isinstance(raw, list):
        raise EdgeLoadError(f"{path}: 'edges' must be a list.")

    return [
        load_edge(item, source_path=path, index=i) for i, item in enumerate(raw)
    ]
