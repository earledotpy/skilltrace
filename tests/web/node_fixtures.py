"""Named SkillNode detail states shared by golden and accessibility gates."""

from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

NODE_ID = "data.pandas.dataframe_basics_01"
SPEC_ID = "spec.data.pandas.dataframe_basics"
OPTIONAL_SPEC_ID = "spec.data.pandas.dataframe_basics.optional"
_VARIANT_DIRS: list[Path] = []


@atexit.register
def _cleanup_variants() -> None:
    for path in _VARIANT_DIRS:
        shutil.rmtree(path, ignore_errors=True)


def _read_yaml(root: Path, relpath: str) -> dict[str, Any]:
    return yaml.safe_load((root / relpath).read_text(encoding="utf-8"))


def _write_yaml(root: Path, relpath: str, doc: dict[str, Any]) -> None:
    (root / relpath).write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def populate_records(root: Path) -> None:
    """Give the populated case an AssessmentAttempt and RemediationAction too."""
    _write_yaml(
        root,
        "evidence/attempts.yaml",
        {
            "attempts": [
                {
                    "id": f"att.{NODE_ID}.001",
                    "node_id": NODE_ID,
                    "outcome": "failed",
                    "note": "groupby aggregation needs another pass",
                    "created_at": "2026-11-16T08:00:00+00:00",
                }
            ]
        },
    )
    _write_yaml(
        root,
        "execution/remediation_actions.yaml",
        {
            "remediation_actions": [
                {
                    "id": "rem.snapshot.001",
                    "node_id": NODE_ID,
                    "blocker_id": "blk.snapshot.001",
                    "status": "open",
                    "description": "Redo the groupby examples with a smaller frame",
                    "created_at": "2026-11-16T08:30:00+00:00",
                }
            ]
        },
    )


def _empty(root: Path) -> None:
    edges = _read_yaml(root, "graph/edges.yaml")
    edges["edges"] = [
        edge
        for edge in edges["edges"]
        if edge["source"] != NODE_ID and edge["target"] != NODE_ID
    ]
    _write_yaml(root, "graph/edges.yaml", edges)

    resources = _read_yaml(root, "graph/resources.yaml")
    for resource in resources["resources"]:
        resource["supports"] = [
            node_id for node_id in resource.get("supports", []) if node_id != NODE_ID
        ]
    _write_yaml(root, "graph/resources.yaml", resources)

    for relpath, key in (
        ("evidence/artifact_specs.yaml", "artifact_specs"),
        ("evidence/validation_gates.yaml", "validation_gates"),
    ):
        doc = _read_yaml(root, relpath)
        doc[key] = [item for item in doc[key] if item["node_id"] != NODE_ID]
        _write_yaml(root, relpath, doc)

    _write_yaml(root, "evidence/evidence_records.yaml", {"evidence_records": []})
    _write_yaml(root, "evidence/attempts.yaml", {"attempts": []})
    for relpath, key in (
        ("execution/blockers.yaml", "blockers"),
        ("execution/remediation_actions.yaml", "remediation_actions"),
        ("execution/reviews.yaml", "reviews"),
        ("execution/session_work.yaml", "session_work"),
    ):
        doc = _read_yaml(root, relpath)
        doc[key] = [item for item in doc[key] if item["node_id"] != NODE_ID]
        _write_yaml(root, relpath, doc)
    _write_yaml(root, "execution/events.yaml", {"events": []})


def _limited(root: Path) -> None:
    records = _read_yaml(root, "evidence/evidence_records.yaml")
    records["evidence_records"] = [
        record
        for record in records["evidence_records"]
        if not record["accepted"]
    ]
    _write_yaml(root, "evidence/evidence_records.yaml", records)

    specs = _read_yaml(root, "evidence/artifact_specs.yaml")
    specs["artifact_specs"].append(
        {
            "id": OPTIONAL_SPEC_ID,
            "node_id": NODE_ID,
            "title": "Optional DataFrame design notes",
            "artifact_kind": "notes",
            "description": "Additional design notes, if useful.",
            "required": False,
            "minimum_count": 0,
        }
    )
    _write_yaml(root, "evidence/artifact_specs.yaml", specs)


_MUTATIONS = {"populated": populate_records, "empty": _empty, "limited": _limited}


def build_node_variant(pinned: Path, kind: str) -> Path:
    """Copy ``pinned`` into one named SkillNode detail state."""
    if kind not in _MUTATIONS:
        raise ValueError(f"unknown SkillNode detail variant: {kind!r}")
    dest = Path(tempfile.mkdtemp(prefix=f"node-{kind}-"))
    _VARIANT_DIRS.append(dest)
    shutil.copytree(pinned, dest, dirs_exist_ok=True)
    _MUTATIONS[kind](dest)
    return dest
