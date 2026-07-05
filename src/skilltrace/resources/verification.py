"""Recording a resource verification (`verify-resource`, v0.7 slice 4).

Verification is the registry's *only* mutating operation, so this is the only
place the resource files are written after authoring. The registry is
human-authored YAML, so the writer edits the target entry's mapping **in place**
in the raw document and dumps it back — preserving every other field, every
other resource, and file order — rather than rebuilding entries from the loaded
`LearningResource` dataclass (which would normalize field order and force
decisions about re-emitting unclaimed defaults). Comments do not survive the
round-trip, matching the established writers (`save_state`, `append_event`).

The two verdicts write the two verification facts:

- **Success** (the default — the command name is the verdict): set `last_verified`
  to today and clear any `broken` marker. This is the sole setter of
  `last_verified`; positive verification is a human act forever (CONTEXT.md), so
  no other code path ever writes it.
- **Failure** (`--broken`, reason required): write the dated `broken` marker with
  that reason and leave `last_verified` untouched — a failed check is not a
  verification.

The caller (the command) has already confirmed the resource exists and the
registry loads clean; this function performs the surgical edit and persists it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .registry import _REGISTRY_RELPATH, _TOP_KEY, ResourceLoadError


def today_iso() -> str:
    """Today's date (UTC) as an ISO `YYYY-MM-DD` string.

    A date, not a timestamp: `last_verified` and the broken marker are *dated*
    facts (CONTEXT.md), and staleness is derived in whole days against a policy
    window.
    """
    return datetime.now(timezone.utc).date().isoformat()


def record_verification(
    root: Path | str,
    resource_id: str,
    *,
    date: str,
    broken_reason: str | None = None,
) -> None:
    """Write the verification verdict for `resource_id` into `graph/resources.yaml`.

    A successful verification (`broken_reason` is None) sets `last_verified` to
    `date` and clears any broken marker. A failed one (`broken_reason` given)
    writes the dated broken marker and leaves `last_verified` alone.

    Raises `ResourceLoadError` if the registry cannot be read/parsed or names no
    resource with this id — but the command validates existence up front, so that
    is a defensive guard, not the normal path.
    """
    path = Path(root) / _REGISTRY_RELPATH

    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ResourceLoadError(f"{path}: cannot read resource registry: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ResourceLoadError(f"{path}: unparseable registry YAML: {exc}") from exc

    entries = doc.get(_TOP_KEY) if isinstance(doc, dict) else None
    entry = _find_entry(entries, resource_id)
    if entry is None:
        raise ResourceLoadError(
            f"{path}: no resource with id {resource_id!r} to verify."
        )

    if broken_reason is None:
        entry["last_verified"] = date
        entry.pop("broken", None)
    else:
        entry["broken"] = {"date": date, "reason": broken_reason}

    path.write_text(
        yaml.safe_dump(doc, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def _find_entry(entries: Any, resource_id: str) -> dict | None:
    """The raw mapping for `resource_id`, or None. Tolerant of a malformed file.

    Existence and shape are the command's concern (it loads via `load_resources`
    first); here a non-list `entries` or non-mapping entry simply yields no match,
    so the caller's up-front error path — not a traceback — reports the problem.
    """
    if not isinstance(entries, list):
        return None
    for entry in entries:
        if isinstance(entry, dict) and entry.get("id") == resource_id:
            return entry
    return None
