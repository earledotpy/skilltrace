"""Automation-boundary enforcement.

This is one of the two cross-cutting rules the dispatcher owns: before an action
carrying an `automation_action` label is dispatched, it is checked here, and a
forbidden action is refused with a non-zero exit.

Hard boundary (CLAUDE.md): passing, mastering, and deleting records are never
automated. That guarantee is **code-authoritative** here, not policy-derived:
`pass_node`, `master_node`, and `delete_record` are refused unconditionally, with
or without a policy file, and even if the policy YAML were edited to mark them
allowed. Policy may only *add* forbidden actions; it can never loosen these three.
Code is the floor; the policy file is the audit/messaging layer above it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

# The hard-boundary floor. Never remove or narrow this set; policy cannot
# override it. These are the actions CLAUDE.md forbids from any automated path.
FORBIDDEN_ACTIONS: frozenset[str] = frozenset(
    {"pass_node", "master_node", "delete_record"}
)

_ALLOWED_PERMISSIONS = frozenset({"allowed", "allowed_with_confirmation"})

_POLICY_RELPATH = Path("policy") / "automation_boundary.yaml"


@dataclass(frozen=True)
class AutomationVerdict:
    """Result of an automation-boundary check."""

    action: str
    allowed: bool
    reason: str
    source: str  # "code" (hard floor) or "policy" (advisory layer)

    @property
    def forbidden(self) -> bool:
        return not self.allowed


def _policy_permission(action: str, root: Path) -> str | None:
    """Return the policy permission for `action`, or None if unavailable.

    The policy file is advisory context only; a missing or malformed file must
    never *loosen* the code floor, so callers treat None as "no opinion" and
    fall through to fail-closed handling.
    """
    path = root / _POLICY_RELPATH
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None
    policy = data.get("automation_boundary_policy") if isinstance(data, dict) else None
    if not isinstance(policy, dict):
        # Malformed-but-parseable policy (e.g. an empty key) must not crash the
        # fail-closed path; treat it as "no opinion" so the caller refuses.
        return None
    for rule in policy.get("rules", []) or []:
        if isinstance(rule, dict) and rule.get("action") == action:
            return rule.get("permission")
    return None


def check_automation(action: str, root: Path | str | None = None) -> AutomationVerdict:
    """Decide whether `action` may proceed via an automated dispatch path.

    Order of authority:
    1. Code floor — the three hard-boundary actions are always forbidden.
    2. Policy — an explicit `allowed` / `allowed_with_confirmation` permits.
    3. Fail closed — anything else (policy `forbidden`, unknown action, or no
       policy file) is refused.
    """
    if action in FORBIDDEN_ACTIONS:
        return AutomationVerdict(
            action=action,
            allowed=False,
            reason=(
                f"'{action}' is a hard-boundary action and can never be "
                "automated; it requires an explicit learner command."
            ),
            source="code",
        )

    root_path = Path(root) if root is not None else Path.cwd()
    permission = _policy_permission(action, root_path)
    if permission in _ALLOWED_PERMISSIONS:
        return AutomationVerdict(
            action=action,
            allowed=True,
            reason=f"Policy permits '{action}' ({permission}).",
            source="policy",
        )

    if permission == "forbidden":
        reason = f"Policy forbids '{action}'."
    elif permission is None:
        reason = f"No policy rule permits '{action}'; refusing (fail closed)."
    else:
        reason = f"Unrecognized permission '{permission}' for '{action}'; refusing."
    return AutomationVerdict(action=action, allowed=False, reason=reason, source="policy")
