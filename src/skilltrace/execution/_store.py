"""Raw YAML plumbing for the execution record files.

Execution files are top-key lists like the evidence files, with one deliberate
difference: a *missing* file reads as empty. Evidence files ship with the seed
and their absence is a defect; execution files describe what the learner has
done, and a fresh repo simply hasn't done anything yet (mirroring
`events.yaml`). Appends read raw and re-dump so existing rows are preserved
byte-for-byte apart from YAML re-serialization.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ExecutionLoadError(Exception):
    """An execution-layer record could not be loaded or violates its schema."""


def read_records(root: Path | str, relpath: Path, *, top_key: str, kind: str) -> list[Any]:
    """Read a `<top_key>:` list; a missing file is an empty history."""
    path = Path(root) / relpath
    if not path.exists():
        return []

    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ExecutionLoadError(f"{path}: unparseable {kind} YAML: {exc}") from exc

    if not isinstance(doc, dict) or top_key not in doc:
        raise ExecutionLoadError(f"{path}: expected a top-level '{top_key}:' mapping.")
    raw = doc[top_key]
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ExecutionLoadError(f"{path}: '{top_key}' must be a list.")
    return raw


def write_records(root: Path | str, relpath: Path, *, top_key: str, records: list[Any]) -> None:
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({top_key: records}, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def append_record(
    root: Path | str, relpath: Path, *, top_key: str, kind: str, record: dict
) -> None:
    """Append one record, leaving existing rows untouched."""
    records = read_records(root, relpath, top_key=top_key, kind=kind)
    records.append(record)
    write_records(root, relpath, top_key=top_key, records=records)
