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

    assert len(specs) == 69
    assert len(gates) == 69
    assert records == []
    assert attempts == []


def test_seed_objective_gates_carry_a_command():
    # v0.8 slice 3 made objective gates real on the programming/tooling code and
    # Git nodes (the slope-calculator portfolio gate was demoted to manual — a
    # project is judged, never proxied). Every objective gate must carry the
    # `command` its authority runs; a regression that dropped `command` handling
    # would flip this. The exact count is a curriculum choice, not asserted here.
    gates = load_validation_gates(REPO_ROOT)
    objective = [g for g in gates if g.authority == "objective"]
    assert objective, "the seed should carry objective gates on its code/Git nodes"
    assert all(g.command for g in objective)
    # The portfolio project is judged manually, not by an exit code.
    portfolio = [g for g in gates if g.node_id == "portfolio.project.slope_calculator_01"]
    assert portfolio and portfolio[0].authority == "manual"
