"""`skilltrace validate policy` — the policy layer's structural check."""

from __future__ import annotations

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
