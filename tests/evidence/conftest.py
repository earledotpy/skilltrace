"""Shared on-disk evidence fixtures for the v0.4 exit-gate suite (issue #16).

Mirror of `tests/graph/conftest.py`'s `GraphBuilder`: the unit tests hand-build
`ArtifactSpec`/`ValidationGate`/… objects and drive the pure `check_evidence`
seam — the right seam for *logic*, but it bypasses the four loaders and the CLI,
so it cannot prove the loader-only rejections (an `ai` authority, a stray
`node_id` on a record, a structurally broken YAML file) or that every cross-record
error survives the real `load_and_validate_evidence` round trip on real files.

`EvidenceBuilder` writes a real mini-repo under `tmp_path` — `graph/nodes/*.md`
plus the four `evidence/*.yaml` files — so a test can exercise the whole
loader→validate→CLI path. It is deliberately curriculum-agnostic scaffolding: each
record type has a minimal-valid dict factory plus `overrides`/`omit` escape
hatches, so a test can construct exactly one defect (a forbidden enum value, a
missing required field, a duplicated id) and assert on its distinctive message.

A minimal node is re-declared here rather than imported from the graph conftest,
so the two suites stay decoupled (the evidence layer needs only a valid node id
to reference; it does not exercise node frontmatter rules).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

def _apply(
    base: dict[str, Any],
    overrides: dict[str, Any] | None,
    omit: tuple[str, ...],
) -> dict[str, Any]:
    """Merge `overrides` into `base`, then drop every key named in `omit`.

    `overrides` sets or replaces fields (an unknown field, a bad enum value);
    `omit` removes a field entirely, so a test can build a record that is
    *missing* a required field — distinct from setting it to None, which is a
    present-but-null field.
    """
    if overrides:
        base.update(overrides)
    for key in omit:
        base.pop(key, None)
    return base


class EvidenceBuilder:
    """Writes a real SkillTrace mini-repo so tests hit the loader + CLI path.

    Chainable: mutators return `self`. Collections are set wholesale (like
    `GraphBuilder.edges`) so a test can pass a deliberately malformed entry — a
    non-mapping, a duplicate id — that a per-field setter could not express.
    `raw_file` overrides one evidence file with literal text for the structural
    YAML errors (unparseable, missing top key, non-list). `write()` dumps
    everything and returns the repo root the CLI operates on.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "graph" / "nodes").mkdir(parents=True, exist_ok=True)
        (root / "evidence").mkdir(parents=True, exist_ok=True)
        self._node_ids: list[str] = []
        self._specs: list[Any] = []
        self._gates: list[Any] = []
        self._records: list[Any] = []
        self._attempts: list[Any] = []
        self._raw: dict[str, str] = {}

    # --- Minimal-valid dict factories --------------------------------------

    @staticmethod
    def spec_dict(
        spec_id: str,
        node_id: str,
        *,
        required: bool = True,
        minimum_count: int = 1,
        overrides: dict[str, Any] | None = None,
        omit: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        return _apply(
            {
                "id": spec_id,
                "node_id": node_id,
                "title": f"Spec {spec_id}",
                "artifact_kind": "problem_set",
                "required": required,
                "minimum_count": minimum_count,
            },
            overrides,
            omit,
        )

    @staticmethod
    def gate_dict(
        gate_id: str,
        node_id: str,
        *,
        authority: str = "manual",
        command: str | None = None,
        overrides: dict[str, Any] | None = None,
        omit: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        gate: dict[str, Any] = {"id": gate_id, "node_id": node_id, "authority": authority}
        if command is not None:
            gate["command"] = command
        return _apply(gate, overrides, omit)

    @staticmethod
    def record_dict(
        record_id: str,
        spec_id: str,
        *,
        accepted: bool = True,
        accepted_by: str = "learner_manual",
        location: str = "evidence/a.md",
        artifact_hash: str = "sha256:aaa",
        supersedes: str | None = None,
        supersede_reason: str | None = None,
        overrides: dict[str, Any] | None = None,
        omit: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "id": record_id,
            "artifact_spec_id": spec_id,
            "location": location,
            "accepted": accepted,
            "accepted_by": accepted_by,
            "artifact_hash": artifact_hash,
            "created_at": "2026-07-04",
        }
        if supersedes is not None:
            record["supersedes"] = supersedes
        if supersede_reason is not None:
            record["supersede_reason"] = supersede_reason
        return _apply(record, overrides, omit)

    @staticmethod
    def attempt_dict(
        attempt_id: str,
        node_id: str,
        *,
        outcome: str = "passed",
        overrides: dict[str, Any] | None = None,
        omit: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        return _apply(
            {
                "id": attempt_id,
                "node_id": node_id,
                "outcome": outcome,
                "created_at": "2026-07-04",
            },
            overrides,
            omit,
        )

    # --- Collectors ---------------------------------------------------------

    def node(self, node_id: str) -> "EvidenceBuilder":
        self._node_ids.append(node_id)
        return self

    def specs(self, specs: list[Any]) -> "EvidenceBuilder":
        self._specs = specs
        return self

    def gates(self, gates: list[Any]) -> "EvidenceBuilder":
        self._gates = gates
        return self

    def records(self, records: list[Any]) -> "EvidenceBuilder":
        self._records = records
        return self

    def attempts(self, attempts: list[Any]) -> "EvidenceBuilder":
        self._attempts = attempts
        return self

    def raw_file(self, relpath: str, text: str) -> "EvidenceBuilder":
        """Override one file (e.g. `evidence/attempts.yaml`) with literal text."""
        self._raw[relpath] = text
        return self

    # --- Persist ------------------------------------------------------------

    def _write_node(self, node_id: str) -> None:
        frontmatter = {
            "id": node_id,
            "title": f"Title for {node_id}",
            "summary": f"Summary for {node_id}.",
            "domain": "testing",
            "track": "foundational",
            "micro_session_fit": {
                "can_fit_15_min": True,
                "can_fit_30_min": True,
                "requires_long_block": False,
            },
        }
        block = yaml.safe_dump(frontmatter, sort_keys=False)
        text = f"---\n{block}---\n\n# {node_id}\n"
        (self.root / "graph" / "nodes" / f"{node_id}.md").write_text(text, encoding="utf-8")

    def _write_list(self, relpath: str, top_key: str, items: list[Any]) -> None:
        if relpath in self._raw:
            (self.root / relpath).write_text(self._raw[relpath], encoding="utf-8")
            return
        doc = yaml.safe_dump({top_key: items}, sort_keys=False)
        (self.root / relpath).write_text(doc, encoding="utf-8")

    def write(self) -> Path:
        """Write nodes + the four evidence files (or their raw overrides)."""
        for node_id in self._node_ids:
            self._write_node(node_id)
        self._write_list("evidence/artifact_specs.yaml", "artifact_specs", self._specs)
        self._write_list("evidence/validation_gates.yaml", "validation_gates", self._gates)
        self._write_list("evidence/evidence_records.yaml", "evidence_records", self._records)
        self._write_list("evidence/attempts.yaml", "attempts", self._attempts)
        return self.root


@pytest.fixture
def evidence_builder(tmp_path: Path) -> EvidenceBuilder:
    """An `EvidenceBuilder` rooted at a fresh temp repo."""
    return EvidenceBuilder(tmp_path)
