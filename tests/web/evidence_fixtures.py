"""The named evidence-workspace states as fixture repos — one builder, two gates.

The golden snapshot suite and the axe harness must render the **same** named
evidence states from the same kind of fixture, or a state could be pinned by
one gate and left unchecked by the other. This module owns the mutations that
turn a pinned repo into each state the evidence workspace contract names
(spec-v3-study-day §10.9, SC-00a):

* ``populated`` — the pinned repo unchanged: an objective gate with a live
  accepted record, a rejection and a visible correction;
* ``empty`` — the requirements exist but nothing has been submitted yet;
* ``limited`` — records exist, but a required minimum is not met yet;
* ``failure`` — the evidence store cannot be read, so the workspace claims
  nothing and points at Health (never an empty state);
* ``manual`` — a manual gate with no records, so the explicit Accept/Reject
  choice is the form the learner sees.

The mutations are fixture data; no engine write path runs here.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from fixture_repo import materialise_variant, write_yaml

NODE = "data.pandas.dataframe_basics_01"
SPEC = "spec.data.pandas.dataframe_basics"
GATE = "gate.data.pandas.dataframe_basics.closure"

EVIDENCE_VARIANTS: tuple[str, ...] = ("empty", "limited", "failure", "manual")

#: The repository-index states (spec-v3-study-day §11.2, SC-00a): the index
#: has no per-record minimum, so ``limited`` is not one of its states.
EVIDENCE_INDEX_VARIANTS: tuple[str, ...] = ("empty", "failure")


def _read_yaml(root: Path, relpath: str) -> dict:
    return yaml.safe_load((root / relpath).read_text(encoding="utf-8")) or {}


def _empty(root: Path) -> None:
    """The requirements stay; the learner has submitted nothing yet."""
    write_yaml(root, "evidence/evidence_records.yaml", {"evidence_records": []})
    write_yaml(root, "execution/events.yaml", {"events": []})


def _limited(root: Path) -> None:
    """One accepted record against a required minimum of three."""
    path = root / "evidence" / "artifact_specs.yaml"
    doc = _read_yaml(root, "evidence/artifact_specs.yaml")
    for spec in doc["artifact_specs"]:
        if spec["id"] == SPEC:
            spec["minimum_count"] = 3
            break
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _failure(root: Path) -> None:
    """A malformed evidence record: the store cannot be read."""
    write_yaml(
        root,
        "evidence/evidence_records.yaml",
        {"evidence_records": [{"id": "not-a-record", "unknown_field": True}]},
    )


def _manual(root: Path) -> None:
    """A manual gate, with no records yet — the explicit verdict form."""
    _empty(root)
    path = root / "evidence" / "validation_gates.yaml"
    doc = _read_yaml(root, "evidence/validation_gates.yaml")
    for gate in doc["validation_gates"]:
        if gate["id"] == GATE:
            gate["authority"] = "manual"
            gate.pop("command", None)
            break
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


_MUTATIONS = {
    "empty": _empty,
    "limited": _limited,
    "failure": _failure,
    "manual": _manual,
}


def build_evidence_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one evidence state."""
    return materialise_variant(
        pinned, kind, prefix=f"evidence-{kind}", mutations=_MUTATIONS
    )


def build_evidence_index_variant(pinned: Path, kind: str) -> Path:
    """A read-only copy of ``pinned`` reshaped into one repository-index state.

    ``empty`` and ``failure`` are the index's own named states; they share the
    workspace's mutations so the two gates can never disagree about what an
    unreadable store looks like.
    """
    return materialise_variant(
        pinned, kind, prefix=f"evidence-index-{kind}", mutations=_MUTATIONS
    )
