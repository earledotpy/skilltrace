"""ValidationGate loader: two-value authority, command iff objective.

Issue #10: unknown authority fails (AI is unrepresentable); `command` on manual
fails; missing `command` on objective fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skilltrace.evidence import AUTHORITIES, EvidenceLoadError
from skilltrace.evidence.gates import (
    ValidationGate,
    load_validation_gate,
    load_validation_gates,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_VALID_MANUAL = {
    "id": "gate.math.arithmetic.order_operations.closure",
    "node_id": "math.arithmetic.order_operations_01",
    "authority": "manual",
    "title": "Closure gate",
    "description": "Judges evidence.",
    "created_at": "2026-06-28",
    "updated_at": "2026-07-03",
}

_VALID_OBJECTIVE = {
    "id": "gate.portfolio.project.slope_calculator.closure",
    "node_id": "portfolio.project.slope_calculator_01",
    "authority": "objective",
    "command": "pytest portfolio/slope-calculator/tests",
    "title": "Closure gate",
    "created_at": "2026-06-28",
    "updated_at": "2026-07-03",
}


def test_valid_manual_gate_loads_without_command():
    gate = load_validation_gate(dict(_VALID_MANUAL))
    assert isinstance(gate, ValidationGate)
    assert gate.authority == "manual"
    assert gate.command is None


def test_valid_objective_gate_loads_with_command():
    gate = load_validation_gate(dict(_VALID_OBJECTIVE))
    assert gate.authority == "objective"
    assert gate.command == "pytest portfolio/slope-calculator/tests"


def test_authorities_are_exactly_two():
    assert AUTHORITIES == {"objective", "manual"}


@pytest.mark.parametrize("authority", ["ai", "objective_gate", "manual_review", "AI", ""])
def test_unknown_authority_fails(authority):
    data = dict(_VALID_MANUAL)
    data["authority"] = authority
    data.pop("command", None)
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_validation_gate(data)
    assert "authority" in str(excinfo.value)


def test_ai_authority_is_unrepresentable():
    data = dict(_VALID_MANUAL)
    data["authority"] = "ai"
    with pytest.raises(EvidenceLoadError):
        load_validation_gate(data)


def test_command_on_manual_gate_fails():
    data = dict(_VALID_MANUAL)
    data["command"] = "pytest"
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_validation_gate(data)
    assert "manual" in str(excinfo.value)


def test_missing_command_on_objective_gate_fails():
    data = {k: v for k, v in _VALID_OBJECTIVE.items() if k != "command"}
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_validation_gate(data)
    assert "objective" in str(excinfo.value)


def test_empty_command_on_objective_gate_fails():
    data = dict(_VALID_OBJECTIVE)
    data["command"] = ""
    with pytest.raises(EvidenceLoadError):
        load_validation_gate(data)


def test_unknown_field_fails():
    data = dict(_VALID_MANUAL)
    data["rubric_kind"] = "checklist"
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_validation_gate(data)
    assert "rubric_kind" in str(excinfo.value)


@pytest.mark.parametrize("field", ["id", "node_id", "authority"])
def test_missing_required_field_fails(field):
    data = {k: v for k, v in _VALID_MANUAL.items() if k != field}
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_validation_gate(data)
    assert field in str(excinfo.value)


def test_invalid_node_id_fails():
    data = dict(_VALID_MANUAL)
    data["node_id"] = "bogus"
    with pytest.raises(EvidenceLoadError) as excinfo:
        load_validation_gate(data)
    assert "node_id" in str(excinfo.value)


def test_all_seed_gates_load():
    gates = load_validation_gates(REPO_ROOT)
    assert len(gates) == 47
    assert all(g.authority in AUTHORITIES for g in gates)
    objective = [g for g in gates if g.authority == "objective"]
    assert all(g.command for g in objective)
    manual = [g for g in gates if g.authority == "manual"]
    assert all(g.command is None for g in manual)
