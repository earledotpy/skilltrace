"""The named Portfolio states as fixture repos — one builder, two gates.

The golden snapshot suite and the axe harness must render the **same** named
Portfolio states from the same kind of fixture, or a state could be pinned by
one gate and left unchecked by the other. This module owns the mutations that
turn a pinned repo into each state the Portfolio contract names
(spec-v3-study-day §11.7, SC-00a):

* ``populated`` — the pinned repo unchanged: a finished skill with live
  evidence, so the configurator has something to offer;
* ``empty`` — a fresh learner with nothing finished, so the export is
  explicitly not configured rather than silently empty;
* ``limited`` — a finished skill whose history contains superseded
  evidence, so the honesty banner and the redaction outcome are both
  visible before anything leaves;
* ``failure`` — a malformed evidence store, so the preview (which reads
  strict truth) is a failure that writes nothing and preserves selection.

The mutations are fixture data; no engine write path runs here.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from fixture_repo import fresh_learner_store, materialise_variant, write_yaml

PORTFOLIO_VARIANTS: tuple[str, ...] = ("empty", "limited", "failure")

#: The finished skill the pinned repo's portfolio selects.
NODE_FINISHED = "programming.python.variables_01"
SPEC_FINISHED = "spec.programming.python.variables"


def _read_yaml(root: Path, relpath: str) -> dict:
    return yaml.safe_load((root / relpath).read_text(encoding="utf-8")) or {}


def _empty(root: Path) -> None:
    """A fresh learner: nothing is passed or mastered, so nothing is selected."""
    fresh_learner_store(root)


def _limited(root: Path) -> None:
    """A finished skill with a superseded correction — honest, but limited."""
    doc = _read_yaml(root, "evidence/evidence_records.yaml")
    records = doc.get("evidence_records", [])
    records.append(
        {
            "id": f"ev.{NODE_FINISHED}.001",
            "artifact_spec_id": SPEC_FINISHED,
            "location": "evidence/artifacts/programming/variables.py",
            "accepted": True,
            "accepted_by": "learner_manual",
            "artifact_hash": "sha256:" + "d" * 64,
            "created_at": "2026-10-01T10:00:00Z",
            "note": "first working solution",
        }
    )
    records.append(
        {
            "id": f"ev.{NODE_FINISHED}.002",
            "artifact_spec_id": SPEC_FINISHED,
            "location": "evidence/artifacts/programming/variables.py",
            "accepted": True,
            "accepted_by": "learner_manual",
            "artifact_hash": "sha256:" + "e" * 64,
            "created_at": "2026-10-05T10:00:00Z",
            "note": "corrected the average expression",
            "supersedes": f"ev.{NODE_FINISHED}.001",
            "supersede_reason": "the first solution divided before summing",
        }
    )
    doc["evidence_records"] = records
    write_yaml(root, "evidence/evidence_records.yaml", doc)


def _failure(root: Path) -> None:
    """A malformed evidence record: strict truth cannot load for the preview."""
    write_yaml(
        root,
        "evidence/evidence_records.yaml",
        {"evidence_records": [{"id": "not-a-record", "unknown_field": True}]},
    )


_MUTATIONS = {
    "empty": _empty,
    "limited": _limited,
    "failure": _failure,
}


def build_portfolio_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one Portfolio state."""
    return materialise_variant(
        pinned, kind, prefix=f"portfolio-{kind}", mutations=_MUTATIONS
    )
