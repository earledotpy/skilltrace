"""`validate policy` — structural truth for the policy layer.

Checks that the seed documents load and hold together. Like the other
layers' validators this is read-only and never blocks on advisory content;
errors are structural (a file that cannot serve its readers).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..automation import FORBIDDEN_ACTIONS
from .loading import POLICY_FILES, PolicyLoadError, load_policy_doc

_BOUNDARY_FILE = "automation_boundary.yaml"


@dataclass
class PolicyValidationResult:
    file_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def load_and_validate_policy(root: Path | str) -> PolicyValidationResult:
    result = PolicyValidationResult()
    for filename in sorted(POLICY_FILES):
        try:
            doc = load_policy_doc(root, filename)
        except PolicyLoadError as exc:
            result.errors.append(str(exc))
            continue
        result.file_count += 1
        if filename == _BOUNDARY_FILE:
            result.errors.extend(_boundary_disagreements(doc))
    return result


def _boundary_disagreements(doc: dict) -> list[str]:
    """ADR 0004: the boundary file must mirror the engine's hard constants.

    Each code-forbidden action must appear with permission `forbidden`; a
    missing, softened, or unrecognized entry is a disagreement, and the repo
    is invalid until the file again matches the constants.
    """
    errors: list[str] = []
    permissions: dict[str, object] = {}
    for rule in doc.get("rules") or []:
        if isinstance(rule, dict) and "action" in rule:
            permissions[str(rule["action"])] = rule.get("permission")
            if rule.get("permission") not in ("allowed", "forbidden"):
                errors.append(
                    f"automation boundary: rule for {rule['action']!r} has "
                    f"permission {rule.get('permission')!r} — the model is "
                    "two-level, allowed or forbidden only (CONTEXT.md)."
                )

    for action in sorted(FORBIDDEN_ACTIONS):
        permission = permissions.get(action)
        if permission is None:
            errors.append(
                f"automation boundary: hard-boundary action {action!r} is not "
                "declared; the file must mirror the engine constants (ADR 0004)."
            )
        elif permission != "forbidden":
            errors.append(
                f"automation boundary: hard-boundary action {action!r} is marked "
                f"{permission!r} but the engine forbids it unconditionally; the "
                "file disagrees with the constants (ADR 0004)."
            )
    return errors
