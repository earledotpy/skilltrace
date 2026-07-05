"""The automation boundary is a code-authoritative floor, not policy-derived."""

from __future__ import annotations

import textwrap

from skilltrace.automation import FORBIDDEN_ACTIONS, check_automation


def _write_policy(root, action: str, permission: str) -> None:
    policy_dir = root / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "automation_boundary.yaml").write_text(
        textwrap.dedent(
            f"""
            automation_boundary_policy:
              rules:
                - action: {action}
                  permission: {permission}
                  reason: test
            """
        ),
        encoding="utf-8",
    )


def test_hard_boundary_actions_are_the_expected_three():
    assert FORBIDDEN_ACTIONS == frozenset(
        {"pass_node", "master_node", "delete_record"}
    )


def test_forbidden_actions_refused_with_no_policy_file(tmp_path):
    for action in ("pass_node", "master_node", "delete_record"):
        verdict = check_automation(action, tmp_path)
        assert verdict.forbidden
        assert verdict.source == "code"


def test_forbidden_action_refused_even_if_policy_says_allowed(tmp_path):
    # Editing the policy YAML must never work around a hard boundary.
    _write_policy(tmp_path, "pass_node", "allowed")
    verdict = check_automation("pass_node", tmp_path)
    assert verdict.forbidden
    assert verdict.source == "code"


def test_policy_may_permit_a_non_floor_action(tmp_path):
    _write_policy(tmp_path, "sync_readiness", "allowed")
    verdict = check_automation("sync_readiness", tmp_path)
    assert verdict.allowed
    assert verdict.source == "policy"


def test_retired_confirmation_tier_fails_closed(tmp_path):
    # The permission model is two-level (allowed/forbidden); the old
    # `allowed_with_confirmation` tier is an unrecognized permission and
    # must refuse, not permit.
    _write_policy(tmp_path, "sync_readiness", "allowed_with_confirmation")
    assert check_automation("sync_readiness", tmp_path).forbidden


def test_policy_may_add_a_forbidden_action(tmp_path):
    _write_policy(tmp_path, "some_action", "forbidden")
    assert check_automation("some_action", tmp_path).forbidden


def test_unknown_action_fails_closed(tmp_path):
    # No policy file, action not in the code floor -> refuse.
    assert check_automation("mystery_action", tmp_path).forbidden


def test_malformed_policy_fails_closed_not_crashes(tmp_path):
    # A hand-edited, parseable-but-empty policy must refuse a non-floor action,
    # not raise.
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    (policy_dir / "automation_boundary.yaml").write_text(
        "automation_boundary_policy:\n", encoding="utf-8"
    )
    assert check_automation("some_action", tmp_path).forbidden
