"""Surgical registry writer for resource replacement (`replace-resource`, v1.7 §4.3).

Replacement is a human-initiated mutating command that retires an ailing
(broken or stale) resource and transfers its coverage to an active verified
candidate.

Edits both target entries in place in raw YAML:
- Candidate's `supports` becomes the ordered union of existing candidate nodes
  followed by new source nodes.
- Source receives `retired: True`, `retired_at: <ISO-date>`, and `replaced_by: <candidate_id>`,
  while preserving its URL/path, claims, `supports`, `last_verified`, and existing `broken` marker.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .registry import _REGISTRY_RELPATH, _TOP_KEY, ResourceLoadError
from .verification import _find_entry


def record_replacement(
    root: Path | str,
    *,
    broken_id: str,
    candidate_id: str,
    retired_at: str,
    supports_after: list[str],
) -> None:
    """Surgically write replacement into `graph/resources.yaml`.

    Updates candidate coverage and marks source retired with pointer and date.
    Preserves all other fields, ordering, and resources.
    """
    path = Path(root) / _REGISTRY_RELPATH

    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ResourceLoadError(f"{path}: cannot read resource registry: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ResourceLoadError(f"{path}: unparseable registry YAML: {exc}") from exc

    entries = doc.get(_TOP_KEY) if isinstance(doc, dict) else None
    if not isinstance(entries, list):
        raise ResourceLoadError(f"{path}: expected a top-level '{_TOP_KEY}:' list.")

    candidate_entry = _find_entry(entries, candidate_id)
    if candidate_entry is None:
        raise ResourceLoadError(f"{path}: no resource with id {candidate_id!r}.")

    broken_entry = _find_entry(entries, broken_id)
    if broken_entry is None:
        raise ResourceLoadError(f"{path}: no resource with id {broken_id!r}.")

    candidate_entry["supports"] = list(supports_after)

    broken_entry["retired"] = True
    broken_entry["retired_at"] = retired_at
    broken_entry["replaced_by"] = candidate_id

    path.write_text(
        yaml.safe_dump(doc, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
