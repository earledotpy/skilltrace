"""The acceptance gate: the real post-#9 seed evidence trail loads clean.

Issue #10 acceptance — "seed files load clean post-#9". This is the check that
catches an allowed-set drawn too narrow: it runs all four loaders against the
actual repo, not hand-built fixtures.
"""

from __future__ import annotations

from pathlib import Path

from skilltrace.evidence import (
    load_artifact_specs,
    load_assessment_attempts,
    load_evidence_records,
    load_validation_gates,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_full_seed_evidence_trail_loads():
    specs = load_artifact_specs(REPO_ROOT)
    gates = load_validation_gates(REPO_ROOT)
    records = load_evidence_records(REPO_ROOT)
    attempts = load_assessment_attempts(REPO_ROOT)

    assert len(specs) == 24
    assert len(gates) == 24
    assert records == []
    assert attempts == []


def test_seed_has_one_objective_gate_rest_manual():
    # The slope-calculator portfolio node is the only objective gate; every other
    # seed gate is manual review. A regression that dropped `command` handling
    # would flip this.
    gates = load_validation_gates(REPO_ROOT)
    objective = [g for g in gates if g.authority == "objective"]
    assert len(objective) == 1
    assert objective[0].node_id == "portfolio.project.slope_calculator_01"
    assert objective[0].command
