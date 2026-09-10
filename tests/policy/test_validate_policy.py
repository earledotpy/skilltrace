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


# --- v1.6 analytics value-range checks (spec §3.2) -------------------------


def _analytics_path(root) -> Path:
    return root / "policy" / "analytics.yaml"


def _set_analytics_field(root, key: str, value) -> None:
    path = _analytics_path(root)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["analytics_policy"][key] = value
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _set_analytics_threshold(root, key: str, value) -> None:
    path = _analytics_path(root)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["analytics_policy"]["advisory_thresholds"][key] = value
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


@pytest.mark.parametrize(
    "key,bad_value",
    [
        ("default_window_days", 0),
        ("default_window_days", 366),
        ("default_window_days", "30"),
        ("min_sessions_for_full_data", 0),
        ("min_sessions_for_full_data", -1),
    ],
)
def test_analytics_seed_value_range_violation_fails_validation(policy_repo, capsys, key, bad_value):
    _set_analytics_field(policy_repo, key, bad_value)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert key in out


@pytest.mark.parametrize(
    "key,bad_value",
    [
        ("review_completion_below_target", 0),
        ("review_completion_below_target", 1),
        ("evidence_coverage_below_target", 1.5),
        ("velocity_below_target_per_week", -1),
        ("blockers_active_threshold", -2),
    ],
)
def test_analytics_threshold_range_violation_fails_validation(policy_repo, capsys, key, bad_value):
    _set_analytics_threshold(policy_repo, key, bad_value)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert key in out


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


# --- v1.7 resource web verification value-range checks (spec §3) -------------


def _web_check_policy_path(root) -> Path:
    return root / "policy" / "resource_web_verification.yaml"


def _set_web_check_field(root, key: str, value) -> None:
    path = _web_check_policy_path(root)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["resource_web_verification_policy"][key] = value
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


@pytest.mark.parametrize(
    "key,bad_value",
    [
        ("enabled", "yes"),
        ("enabled", 1),
        ("follow_redirects", "true"),
        ("timeout_seconds", 0),
        ("timeout_seconds", 121),
        ("timeout_seconds", True),
        ("timeout_seconds", "10"),
        ("check_method", "POST"),
        ("check_method", "head"),
        ("user_agent", ""),
        ("user_agent", "   "),
    ],
)
def test_resource_web_verification_value_range_violation_fails_validation(
    policy_repo, capsys, key, bad_value
):
    _set_web_check_field(policy_repo, key, bad_value)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert key in out


def test_resource_web_verification_unknown_field_fails_validation(policy_repo, capsys):
    _set_web_check_field(policy_repo, "extra_unexpected_field", 123)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert "unknown field" in out


def test_resource_web_verification_missing_field_fails_validation(policy_repo, capsys):
    path = _web_check_policy_path(policy_repo)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    del doc["resource_web_verification_policy"]["timeout_seconds"]
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert "missing required field 'timeout_seconds'" in out
# --- v2.1 recommendation factor-weight checks + retention extras (§3 T-Weights)


def _recommendation_path(root) -> Path:
    return root / "policy" / "recommendation.yaml"


def _set_factor(root, name: str, value, *, remove: bool = False) -> None:
    path = _recommendation_path(root)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    weights = doc["recommendation_policy"]["factor_weights"]
    if remove:
        weights.pop(name, None)
    else:
        weights[name] = value
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def test_reintroducing_dormant_review_due_fails_validation(policy_repo, capsys):
    """The retired `review_due` placeholder must not be re-added (D-Weights)."""
    _set_factor(policy_repo, "review_due", 2.0)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert "review_due" in out


def test_missing_retention_urgency_fails_validation(policy_repo, capsys):
    """The active sequencing factor is required; absence is a hard error."""
    _set_factor(policy_repo, "retention_urgency", None, remove=True)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert "retention_urgency" in out


@pytest.mark.parametrize("bad_value", ["high", True, float("nan")])
def test_non_numeric_factor_weight_fails_validation(policy_repo, capsys, bad_value):
    _set_factor(policy_repo, "agent_signal", bad_value)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert "agent_signal" in out


def test_delay_table_out_of_range_fails_validation(policy_repo, capsys):
    path = policy_repo / "policy" / "retention_model.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["retention_model_policy"]["delay_aware_multipliers"]["early"]["satisfactory"] = 0
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert "delay_aware_multipliers" in out


def test_domain_scale_must_be_positive(policy_repo, capsys):
    path = policy_repo / "policy" / "retention_model.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["retention_model_policy"]["domain_half_life_scales"] = {"math.linear": 0}
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert "domain_half_life_scales" in out


# --- v2.3 polite sweep value-range checks ------------------------------------


def _polite_sweep_path(root) -> Path:
    return root / "policy" / "polite_sweep.yaml"


def _set_polite_sweep_field(root, key: str, value, *, remove: bool = False) -> None:
    path = _polite_sweep_path(root)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if remove:
        doc["polite_sweep_policy"].pop(key, None)
    else:
        doc["polite_sweep_policy"][key] = value
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


@pytest.mark.parametrize(
    "key,bad_value",
    [
        ("per_host_delay_seconds", -1),
        ("per_host_delay_seconds", 601),
        ("per_host_delay_seconds", True),
        ("backoff_max_attempts", 0),
        ("backoff_max_attempts", 11),
        ("backoff_max_attempts", True),
        ("backoff_max_attempts", 2.5),
        ("respect_robots", "yes"),
        ("backoff_base_seconds", 0),
        ("backoff_base_seconds", 61),
        ("backoff_max_seconds", 0),
        ("backoff_max_seconds", 601),
        ("enabled", "true"),
    ],
)
def test_polite_sweep_seed_value_range_violation_fails_validation(policy_repo, capsys, key, bad_value):
    _set_polite_sweep_field(policy_repo, key, bad_value)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "validate policy: FAILED" in out
    assert key in out


def test_polite_sweep_backoff_base_above_max_fails_validation(policy_repo, capsys):
    _set_polite_sweep_field(policy_repo, "backoff_base_seconds", 30)
    _set_polite_sweep_field(policy_repo, "backoff_max_seconds", 10)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "must not exceed" in out


def test_polite_sweep_missing_field_fails_validation(policy_repo, capsys):
    _set_polite_sweep_field(policy_repo, "respect_robots", None, remove=True)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "missing required field 'respect_robots'" in out


def test_polite_sweep_unknown_field_fails_validation(policy_repo, capsys):
    _set_polite_sweep_field(policy_repo, "aggressiveness", "maximum")
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    out = capsys.readouterr().out
    assert "unknown field" in out


def test_polite_sweep_disabled_seed_still_validates_clean(policy_repo, capsys):
    """Disabling the sweep policy is valid — the sweep degrades to v1.8."""
    _set_polite_sweep_field(policy_repo, "enabled", False)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 0
    assert "validate policy: OK" in capsys.readouterr().out


