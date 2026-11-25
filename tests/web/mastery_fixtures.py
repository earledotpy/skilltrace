"""The mastery journey's fixture repos — one builder, two gates.

The golden snapshot suite and the axe harness must render the mastery
journey from the *same* fixture, or a state could be pinned by one gate
and left unchecked by the other. This module owns the mutation that turns
the pinned repo into the mastery-ready state (spec-v3-study-day §10.8):

* ``ready`` — the passed skill (``NODE_PASSED``) gains the accepted proof
  its required specification asks for, so both mastery steps render the
  eligible journey: the continue affordance on step 1, the permanent
  confirmation on step 2. The pass date and the spaced satisfactory
  review are already pinned by the shared fixture; the one missing fact
  is the proof.

The ineligible states need no reshaping: a skill that is not passed is
mastery's structural wall, rendered from the pinned repo as it stands.

The authored record is *fixture data* — a stand-in learner's history,
never the output of an engine write path (see AGENTS.md safety rule).
Dates are absolute so the fixture is wall-clock independent, matching the
frozen-clock convention of the suites that consume it. The shared
mechanics (variant materialisation) live in :mod:`fixture_repo`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fixture_repo import materialise_variant

#: The named mastery states a fixture can be reshaped into.
MASTERY_VARIANTS: tuple[str, ...] = ("ready",)

#: The passed skill the mastery journey renders, and its required spec.
MASTERY_NODE = "programming.python.variables_01"
MASTERY_SPEC = "spec.programming.python.variables"

# Absolute dates: the pass the pinned store records is 2026-10-18, and the
# pinned satisfactory review (2026-10-29) already clears the 3-day spacing.
_PROOF_DAY = "2026-10-10"


def _author_the_proof(root: Path) -> None:
    """One accepted record against the passed skill's required spec.

    The record is what the mastery derivation counts (accepted,
    non-superseded, required specification). It carries the gate-run
    receipt the skill's objective gate writes, dated before the pass.
    """
    path = root / "evidence" / "evidence_records.yaml"
    doc: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    records = doc.get("evidence_records") or []
    records.append(
        {
            "id": f"ev.{MASTERY_NODE}.001",
            "artifact_spec_id": MASTERY_SPEC,
            "location": "evidence/artifacts/programming/python_variables_solution.py",
            "accepted": True,
            "accepted_by": "objective_gate",
            "artifact_hash": "sha256:" + "4" * 64,
            "gate_run": {
                "command_argv": [
                    "python",
                    "evidence/checks/programming.python.variables_check.py",
                ],
                "inputs": [
                    "evidence/artifacts/programming/python_variables_solution.py"
                ],
                "exit_class": "passed",
                "exit_code": 0,
                "stdout_hash": "sha256:" + "d" * 64,
            },
            "created_at": f"{_PROOF_DAY}T09:00:00+00:00",
        }
    )
    doc["evidence_records"] = records
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def build_mastery_variant(pinned: Path, kind: str = "ready") -> Path:
    """A read-only copy of ``pinned`` reshaped into one named mastery state."""
    return materialise_variant(
        pinned,
        kind,
        prefix="mastery-fixture-",
        mutations={"ready": _author_the_proof},
    )
