"""`LearningResource` model and strict registry loader.

A LearningResource is a curriculum pointer to study material: a human-readable
slug ID, an optional URL and/or local path (at least one required), and the list
of node IDs it supports. Linking lives here on the resource — node frontmatter
stays clean and `edges.yaml` remains strictly node-to-node (invariant), so the
registry is the *only* place a resource-to-node link is recorded.

Closed schema, mirroring the evidence loaders (`artifact_specs.yaml` is the same
shape — a single YAML list file, not markdown frontmatter): the allowed set is
exactly the fields this slice uses, and anything else fails naming the resource.
Later v0.7 slices widen `_ALLOWED_FIELDS` with cost, license, and verification
metadata; this slice is deliberately minimal.

Per-record semantics enforced here: the slug ID is a non-empty kebab string; a
resource must point at *something* (URL or local path); `url`/`local_path` are
strings; and `supports`, when present, is a list of node-ID strings. Whole-
registry checks — duplicate IDs, dangling node references, and the orphan
warning — belong to `validation.py`, not the loader, exactly as the evidence
layer splits per-record shape from cross-record integrity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_REGISTRY_RELPATH = Path("graph") / "resources.yaml"
_TOP_KEY = "resources"
_KIND = "learning resource"

# The closed schema for this slice: exactly the fields it uses.
_ALLOWED_FIELDS: frozenset[str] = frozenset({"id", "url", "local_path", "supports"})

# A resource ID is a human-readable kebab slug — lowercase alphanumeric words
# joined by hyphens. Deliberately looser than a node ID (no dots, no numeric
# sequence suffix): resources have no progress history to protect, so identity is
# a plain slug the learner chooses, not a sequenced address.
_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class ResourceLoadError(Exception):
    """A registry entry could not be loaded or violates the resource schema.

    The message names the offending resource (by ID when present, else file
    position) so a validation run points the learner straight at it.
    """


@dataclass(frozen=True)
class LearningResource:
    """One curriculum pointer to study material.

    `supports` is the list of node IDs this resource serves (many-to-many, so
    one book can back several nodes without duplication); an empty list is a
    curriculum-quality warning, not an error. At least one of `url`/`local_path`
    is always set — a resource must point at something.
    """

    id: str
    url: str | None = None
    local_path: str | None = None
    supports: tuple[str, ...] = ()
    source_path: Path | None = None


def _ident(data: Any, index: int | None) -> str:
    """A human-pointing identifier: ``learning resource '<id>'`` or ``#<index>``."""
    if isinstance(data, dict) and isinstance(data.get("id"), str) and data["id"]:
        return f"{_KIND} {data['id']!r}"
    if index is not None:
        return f"{_KIND} #{index}"
    return _KIND


def load_resource(
    data: Any, *, source_path: Path | None = None, index: int | None = None
) -> LearningResource:
    """Validate one registry mapping into a `LearningResource`.

    Raises `ResourceLoadError` (naming the resource) on a non-mapping, an unknown
    field, a missing/invalid slug ID, a non-string `url`/`local_path`, a resource
    with neither URL nor local path, or a `supports` that is not a list of
    non-empty strings.
    """
    where = f"{source_path}: " if source_path is not None else ""
    ident = _ident(data, index)

    if not isinstance(data, dict):
        raise ResourceLoadError(f"{where}{ident} is not a mapping.")

    unknown = sorted(set(data) - _ALLOWED_FIELDS)
    if unknown:
        raise ResourceLoadError(
            f"{where}{ident} has unknown field(s): {', '.join(unknown)}."
        )

    resource_id = data.get("id")
    if not isinstance(resource_id, str) or not _SLUG_RE.fullmatch(resource_id):
        raise ResourceLoadError(
            f"{where}{ident} has invalid id {resource_id!r} — expected a "
            "human-readable slug (lowercase words joined by hyphens)."
        )

    url = data.get("url")
    if url is not None and not isinstance(url, str):
        raise ResourceLoadError(f"{where}{ident} has non-string url {url!r}.")
    local_path = data.get("local_path")
    if local_path is not None and not isinstance(local_path, str):
        raise ResourceLoadError(
            f"{where}{ident} has non-string local_path {local_path!r}."
        )
    if not url and not local_path:
        raise ResourceLoadError(
            f"{where}{ident} has neither a url nor a local_path — every resource "
            "must point at something."
        )

    supports = _load_supports(data.get("supports"), where, ident)

    return LearningResource(
        id=resource_id,
        url=url,
        local_path=local_path,
        supports=supports,
        source_path=source_path,
    )


def _load_supports(raw: Any, where: str, ident: str) -> tuple[str, ...]:
    """Validate the `supports` field into a tuple of node-ID strings.

    Absent is an empty list (an orphan warning at validation time, not a load
    error). Existence of each referenced node is a whole-registry check in
    `validation.py`; here only the *shape* — a list of non-empty strings — is
    enforced, so a dangling but well-formed reference reaches the dangling check.
    """
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ResourceLoadError(f"{where}{ident} has a non-list supports field.")
    for entry in raw:
        if not isinstance(entry, str) or not entry:
            raise ResourceLoadError(
                f"{where}{ident} has an invalid supports entry {entry!r} — "
                "expected a node ID string."
            )
    return tuple(raw)


def load_resources(root: Path | str | None = None) -> list[LearningResource]:
    """Load every entry from `graph/resources.yaml` (default root: auto-detected).

    Returns the raw list in file order; duplicate-ID and dangling-reference
    detection belong to `validate resources`, not the loader. An empty registry
    is valid — the shipped repo ships `resources: []`.
    """
    from ..paths import find_root

    root_path = Path(root) if root is not None else find_root()
    path = root_path / _REGISTRY_RELPATH

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ResourceLoadError(f"{path}: cannot read resource registry: {exc}") from exc

    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ResourceLoadError(f"{path}: unparseable registry YAML: {exc}") from exc

    if not isinstance(doc, dict) or _TOP_KEY not in doc:
        raise ResourceLoadError(f"{path}: expected a top-level '{_TOP_KEY}:' mapping.")

    raw = doc[_TOP_KEY]
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ResourceLoadError(f"{path}: '{_TOP_KEY}' must be a list.")

    return [
        load_resource(item, source_path=path, index=i) for i, item in enumerate(raw)
    ]
