"""`LearningResource` model and strict registry loader.

A LearningResource is a curriculum pointer to study material: a human-readable
slug ID, an optional URL and/or local path (at least one required), and the list
of node IDs it supports. Linking lives here on the resource — node frontmatter
stays clean and `edges.yaml` remains strictly node-to-node (invariant), so the
registry is the *only* place a resource-to-node link is recorded.

Closed schema, mirroring the evidence loaders (`artifact_specs.yaml` is the same
shape — a single YAML list file, not markdown frontmatter): the allowed set is
exactly the fields the registry uses, and anything else fails naming the
resource. A later v0.7 slice widens `_ALLOWED_FIELDS` with verification metadata
(`last_verified`, the broken marker); the claim fields land here.

Per-record semantics enforced here: the slug ID is a non-empty kebab string; a
resource must point at *something* (URL or local path); `url`/`local_path` are
strings; `cost` is the required two-value enum `free`|`paid` — the only place
cost lives, so a free/paid contradiction is unrepresentable rather than checked;
`free_tier`/`certificate` are optional booleans and `license` optional free
text; and `supports`, when present, is a list of node-ID strings. Whole-registry
checks — duplicate IDs, dangling node references, the orphan warning, and the
redundant free-tier-on-free-cost warning — belong to `validation.py`, not the
loader, exactly as the evidence layer splits per-record shape from cross-record
integrity. (The loader raises only errors; a warning like redundant free tier
must stay representable, so it is judged in `validation.py`.)
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_REGISTRY_RELPATH = Path("graph") / "resources.yaml"
_TOP_KEY = "resources"
_KIND = "learning resource"

# The closed schema: exactly the fields a resource may carry.
_ALLOWED_FIELDS: frozenset[str] = frozenset(
    {"id", "url", "local_path", "cost", "free_tier", "certificate", "license", "supports"}
)

# Cost is a single claim with exactly two values — the only place cost lives, so
# "free and paid at once" is unrepresentable, not merely rejected downstream.
_COST_VALUES: frozenset[str] = frozenset({"free", "paid"})

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

    `cost` is always one of `free`/`paid` (the loader guarantees it). `free_tier`
    and `certificate` are boolean claims (default `False` — unclaimed); a
    `free_tier` claim is only meaningful on a paid resource, so `free_tier` on a
    free one is a redundancy warning raised in `validation.py`. `license` is
    optional portfolio-relevant free text.
    """

    id: str
    cost: str
    url: str | None = None
    local_path: str | None = None
    free_tier: bool = False
    certificate: bool = False
    license: str | None = None
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
    with neither URL nor local path, a missing or unknown `cost`, a non-boolean
    `free_tier`/`certificate`, a non-string `license`, or a `supports` that is
    not a list of non-empty strings.
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

    cost = data.get("cost")
    if cost is None:
        raise ResourceLoadError(
            f"{where}{ident} has no cost — every resource must claim a cost "
            "(one of: free, paid)."
        )
    if not isinstance(cost, str) or cost not in _COST_VALUES:
        # `isinstance` first so an unhashable cost (`cost: [free]`) is a clean
        # error, not a TypeError from testing membership of a list in the set.
        raise ResourceLoadError(
            f"{where}{ident} has unknown cost {cost!r} — expected one of: "
            f"{', '.join(sorted(_COST_VALUES))}."
        )

    free_tier = _load_flag(data.get("free_tier"), "free_tier", where, ident)
    certificate = _load_flag(data.get("certificate"), "certificate", where, ident)

    license_ = data.get("license")
    if license_ is not None and not isinstance(license_, str):
        raise ResourceLoadError(
            f"{where}{ident} has non-string license {license_!r}."
        )

    supports = _load_supports(data.get("supports"), where, ident)

    return LearningResource(
        id=resource_id,
        cost=cost,
        url=url,
        local_path=local_path,
        free_tier=free_tier,
        certificate=certificate,
        license=license_,
        supports=supports,
        source_path=source_path,
    )


def _load_flag(raw: Any, field_name: str, where: str, ident: str) -> bool:
    """Validate an optional boolean claim; absent means `False` (unclaimed).

    Strict about type — a bare `bool`, never a truthy string or int — so a
    malformed claim like ``free_tier: yes`` is a reported error, not a value
    silently coerced true. (YAML's `1`/`0` are ints, not bools, and are
    rejected here for the same reason `url: 3` is.)
    """
    if raw is None:
        return False
    if not isinstance(raw, bool):
        raise ResourceLoadError(
            f"{where}{ident} has non-boolean {field_name} {raw!r} — expected "
            "true or false."
        )
    return raw


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


def resources_for_node(
    node_id: str, resources: Iterable[LearningResource]
) -> list[LearningResource]:
    """The reverse index: every resource whose `supports` names `node_id`.

    Derived on demand from the resource entries' `supports` lists — nothing
    stored, consistent with the engine's derived-facts discipline. Registry
    (file) order is preserved as the natural stable ordering; membership of
    `node_id` in the graph is the caller's concern (an unknown node is an error
    the CLI reports, not something this filter can tell from an empty result).
    """
    return [resource for resource in resources if node_id in resource.supports]
