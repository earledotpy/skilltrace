"""`skilltrace validate policy` — the policy layer's structural check."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from skilltrace import cli


def test_shipped_policy_seeds_validate_clean(policy_repo, capsys):
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 0
    assert "validate policy: OK" in capsys.readouterr().out


def test_boundary_file_marking_pass_node_allowed_fails_validation(policy_repo, capsys):
    # ADR 0004: editing the YAML must never soften a hard boundary — a file
    # that disagrees with the engine constants makes the repo invalid.
    _rewrite_boundary_rule(policy_repo, "pass_node", "allowed")

    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert "pass_node" in out


def test_removing_a_hard_boundary_rule_fails_validation(policy_repo, capsys):
    path = policy_repo / "policy" / "automation_boundary.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["automation_boundary_policy"]["rules"] = [
        rule
        for rule in doc["automation_boundary_policy"]["rules"]
        if rule["action"] != "master_node"
    ]
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    assert "master_node" in capsys.readouterr().out


def test_retired_confirmation_tier_fails_validation(policy_repo, capsys):
    # The permission model is two-level (CONTEXT.md): any other value is a
    # schema error, not a soft synonym.
    _rewrite_boundary_rule(policy_repo, "sync_readiness", "allowed_with_confirmation")

    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    assert "allowed_with_confirmation" in capsys.readouterr().out


def _rewrite_boundary_rule(root, action: str, permission: str) -> None:
    """Set one rule's permission in the copied automation_boundary.yaml."""
    path = root / "policy" / "automation_boundary.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for rule in doc["automation_boundary_policy"]["rules"]:
        if rule["action"] == action:
            rule["permission"] = permission
            break
    else:
        doc["automation_boundary_policy"]["rules"].append(
            {"action": action, "permission": permission, "reason": "test"}
        )
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


# --- Tier 2 retention_model value-range checks (spec §3.2) -----------------


def _retention_path(root) -> Path:
    return root / "policy" / "retention_model.yaml"


def _set_retention_field(root, key: str, value) -> None:
    path = _retention_path(root)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["retention_model_policy"][key] = value
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


@pytest.mark.parametrize(
    "key,bad_value",
    [
        ("default_half_life_days", 0),
        ("default_half_life_days", -1),
        ("default_half_life_days", 366),
        ("default_half_life_days", "seven"),
        ("satisfactory_growth_factor", 1),
        ("satisfactory_growth_factor", 0.5),
        ("unsatisfactory_reduction_factor", 0),
        ("unsatisfactory_reduction_factor", 1),
        ("unsatisfactory_reduction_factor", 1.5),
        ("attention_threshold", 0),
        ("attention_threshold", 1),
        ("attention_threshold", 1.5),
    ],
)
def test_retention_seed_value_range_violation_fails_validation(policy_repo, capsys, key, bad_value):
    _set_retention_field(policy_repo, key, bad_value)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert key in out
