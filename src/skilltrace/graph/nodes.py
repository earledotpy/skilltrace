"""`SkillNode` model and strict node loader.

A node markdown file is *pure curriculum*: identity, description, effort, and
policy metadata. Relationships (`edges.yaml`) and learner state (the progress
store) live elsewhere by invariant, so the loader **rejects** any frontmatter
carrying `state`, `prerequisites`, `unlocks`, or `node_type` — naming the
offending file — rather than silently ignoring it. That is what makes schema
drift impossible instead of merely discouraged (issue #2, decisions 3/14/18,
ADR 0001).

The markdown *body* (Learning target, Notes, Evidence, … journal sections) is
not part of the model and is ignored entirely; only the YAML frontmatter is
read. Unknown frontmatter keys that are not on the forbidden list (e.g. a
legacy `level`) are tolerated, not rejected — the forbidden set is the only
hard schema boundary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..paths import find_root

# The four keys that must never appear in node frontmatter. `state` is learner
# progress (progress store owns it); `prerequisites`/`unlocks` are relationships
# (edges.yaml owns them); `node_type` is dropped until a mechanic needs it
# (decision 18). Their presence is a hard load error, not a warning.
FORBIDDEN_FRONTMATTER_KEYS: frozenset[str] = frozenset(
    {"state", "prerequisites", "unlocks", "node_type"}
)

# Fields required on every node. Missing any is a load error.
_REQUIRED_FIELDS: tuple[str, ...] = ("id", "title", "summary", "domain", "track")

_NODES_RELDIR = Path("graph") / "nodes"

# A node ID is dot-separated lowercase segments (alphanumeric words joined by
# underscores), and the final segment ends in a numeric *sequence* suffix
# (`_01`, `_02`, …) — a sequence, not a version (decision 14). Derived from the
# 24 seed IDs; kept no stricter than the data supports.
_ID_SEGMENT_RE = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*")
_ID_SUFFIX_RE = re.compile(r"_\d+$")


class NodeLoadError(Exception):
    """A node file could not be loaded or violates the node schema.

    The message always names the offending file so a validation run points the
    learner straight at it.
    """


@dataclass(frozen=True)
class SkillNode:
    """One learnable skill — pure curriculum, no state and no relationships.

    `roadmap_anchors` link the node to an external roadmap for *reference only*
    (they never control locking or recommendation); the loader enforces that
    every anchor declares `source_role: reference_only`. The structured metadata
    blocks (`estimated_effort`, `micro_session_fit`, `competency_dimensions`,
    `mastery_policy`) are carried as-is; the engine reads specific keys from them
    downstream but the node model does not constrain their internal shape here.
    """

    id: str
    title: str
    summary: str
    domain: str
    track: str
    roadmap_anchors: tuple[dict[str, Any], ...] = ()
    estimated_effort: dict[str, Any] = field(default_factory=dict)
    micro_session_fit: dict[str, Any] = field(default_factory=dict)
    competency_dimensions: dict[str, Any] = field(default_factory=dict)
    mastery_policy: dict[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    created_at: Any = None
    updated_at: Any = None
    source_path: Path | None = None


def _valid_node_id(node_id: str) -> bool:
    parts = node_id.split(".")
    if len(parts) < 2:
        return False
    if not all(_ID_SEGMENT_RE.fullmatch(part) for part in parts):
        return False
    return _ID_SUFFIX_RE.search(parts[-1]) is not None


def _parse_frontmatter(text: str, path: Path) -> dict[str, Any]:
    """Return the YAML frontmatter mapping, or raise `NodeLoadError`.

    Frontmatter is the block delimited by a leading `---` line and the next
    `---` line; everything after is the ignored body.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise NodeLoadError(f"{path}: missing YAML frontmatter (no opening '---').")

    closing = next(
        (i for i in range(1, len(lines)) if lines[i].strip() == "---"), None
    )
    if closing is None:
        raise NodeLoadError(f"{path}: malformed frontmatter (no closing '---').")

    block = "\n".join(lines[1:closing])
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        raise NodeLoadError(f"{path}: unparseable frontmatter YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise NodeLoadError(f"{path}: frontmatter is not a mapping.")
    return data


def _validate_anchors(data: dict[str, Any], path: Path) -> tuple[dict[str, Any], ...]:
    raw = data.get("roadmap_anchors")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise NodeLoadError(f"{path}: roadmap_anchors must be a list.")
    anchors: list[dict[str, Any]] = []
    for anchor in raw:
        if not isinstance(anchor, dict):
            raise NodeLoadError(f"{path}: each roadmap anchor must be a mapping.")
        if anchor.get("source_role") != "reference_only":
            raise NodeLoadError(
                f"{path}: roadmap anchor must declare source_role: reference_only "
                f"(anchors never control locking or recommendation); got "
                f"{anchor.get('source_role')!r}."
            )
        anchors.append(anchor)
    return tuple(anchors)


def load_node(path: Path | str) -> SkillNode:
    """Load and validate one node markdown file into a `SkillNode`.

    Raises `NodeLoadError` (naming the file) on a missing/malformed frontmatter,
    a forbidden key, an invalid node ID, a missing required field, or a roadmap
    anchor that is not `reference_only`.
    """
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise NodeLoadError(f"{path}: cannot read node file: {exc}") from exc

    data = _parse_frontmatter(text, path)

    present_forbidden = sorted(FORBIDDEN_FRONTMATTER_KEYS & data.keys())
    if present_forbidden:
        raise NodeLoadError(
            f"{path}: node frontmatter must not contain "
            f"{', '.join(present_forbidden)} — nodes are pure curriculum; "
            "state lives in the progress store and relationships in edges.yaml."
        )

    missing = [key for key in _REQUIRED_FIELDS if not data.get(key)]
    if missing:
        raise NodeLoadError(
            f"{path}: node is missing required field(s): {', '.join(missing)}."
        )

    node_id = data["id"]
    if not isinstance(node_id, str) or not _valid_node_id(node_id):
        raise NodeLoadError(
            f"{path}: invalid node id {node_id!r} — expected dot-separated "
            "lowercase segments ending in a numeric sequence suffix "
            "(e.g. math.algebra.linear_equations_01)."
        )

    anchors = _validate_anchors(data, path)

    return SkillNode(
        id=node_id,
        title=data["title"],
        summary=data["summary"],
        domain=data["domain"],
        track=data["track"],
        roadmap_anchors=anchors,
        estimated_effort=dict(data.get("estimated_effort") or {}),
        micro_session_fit=dict(data.get("micro_session_fit") or {}),
        competency_dimensions=dict(data.get("competency_dimensions") or {}),
        mastery_policy=dict(data.get("mastery_policy") or {}),
        tags=tuple(data.get("tags") or ()),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        source_path=path,
    )


def load_nodes(root: Path | str | None = None) -> list[SkillNode]:
    """Load every node under `graph/nodes/` (default root: auto-detected).

    Returns a list in filename order. Duplicate IDs are *not* collapsed here —
    the raw list is handed to graph validation (issue #5), which is where
    duplicate-ID detection belongs.
    """
    root_path = Path(root) if root is not None else find_root()
    nodes_dir = root_path / _NODES_RELDIR
    return [load_node(path) for path in sorted(nodes_dir.glob("*.md"))]
