"""Shared closed-schema plumbing for the four evidence loaders.

The evidence layer has four record types where the graph layer had two, so the
boilerplate every strict loader repeats — reject non-mappings, reject unknown
fields (the closed schema), require the mandatory fields — is factored here once
rather than copied four times. Each loader still owns its *semantic* checks
(enum values, both-or-neither pairs, ID shape); this module only enforces the
uniform shape rules and produces error messages that name the offending record.

One `EvidenceLoadError` covers all four types: they form a single layer, and the
`validate evidence` command (issue #11) catches the base to surface loader
failures uniformly. The message always names the record type and its ID (or file
position when the ID is absent) so a validation run points straight at it.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any


class EvidenceLoadError(Exception):
    """An evidence-layer record could not be loaded or violates its schema."""


def record_ident(kind: str, data: Any, index: int | None) -> str:
    """A human-pointing identifier: ``<kind> '<id>'``, else ``<kind> #<index>``."""
    if isinstance(data, dict) and isinstance(data.get("id"), str) and data["id"]:
        return f"{kind} {data['id']!r}"
    if index is not None:
        return f"{kind} #{index}"
    return kind


def where_prefix(source_path: Path | None) -> str:
    """``'<path>: '`` when a file is known, else empty — mirrors the edge loader."""
    return f"{source_path}: " if source_path is not None else ""


def check_shape(
    data: Any,
    *,
    kind: str,
    allowed: Iterable[str],
    required: Iterable[str],
    source_path: Path | None,
    index: int | None,
) -> dict[str, Any]:
    """Run the three uniform checks and return the mapping, or raise.

    Rejects a non-mapping, any field outside `allowed` (closed schema), and any
    missing `required` field. `required` is checked for *presence*, not
    truthiness, so a legitimately falsey value (``accepted: false``,
    ``required: false``) is not mistaken for an absent field.
    """
    ident = record_ident(kind, data, index)
    where = where_prefix(source_path)

    if not isinstance(data, dict):
        raise EvidenceLoadError(f"{where}{ident} is not a mapping.")

    unknown = sorted(set(data) - set(allowed))
    if unknown:
        raise EvidenceLoadError(
            f"{where}{ident} has unknown field(s): {', '.join(unknown)}."
        )

    missing = [key for key in required if key not in data]
    if missing:
        raise EvidenceLoadError(
            f"{where}{ident} is missing required field(s): {', '.join(missing)}."
        )

    return data


def read_yaml_list(
    path: Path, *, top_key: str, kind: str
) -> list[Any]:
    """Read a ``<top_key>:`` list from a YAML file, or raise `EvidenceLoadError`.

    Returns the raw items (each still to be validated by the type's loader). An
    empty list is valid — the seed `evidence_records.yaml` / `attempts.yaml`
    ship empty.
    """
    import yaml

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvidenceLoadError(f"{path}: cannot read {kind} file: {exc}") from exc

    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise EvidenceLoadError(f"{path}: unparseable {kind} YAML: {exc}") from exc

    if not isinstance(doc, dict) or top_key not in doc:
        raise EvidenceLoadError(f"{path}: expected a top-level '{top_key}:' mapping.")

    raw = doc[top_key]
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise EvidenceLoadError(f"{path}: '{top_key}' must be a list.")
    return raw
