"""`validate policy` — structural truth for the policy layer.

Checks that the seed documents load and hold together. Like the other
layers' validators this is read-only and never blocks on advisory content;
errors are structural (a file that cannot serve its readers).
"""

from __future__ import annotations

import math
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
        if filename == "retention_model.yaml":
            result.errors.extend(_retention_value_ranges(doc, root, filename))
        if filename == "recommendation.yaml":
            result.errors.extend(_recommendation_weight_checks(doc, root, filename))
        if filename == "analytics.yaml":
            result.errors.extend(_analytics_value_ranges(doc, root, filename))
        if filename == "portfolio.yaml":
            result.errors.extend(_portfolio_value_ranges(doc, root, filename))
        if filename == "resource_web_verification.yaml":
            result.errors.extend(_resource_web_verification_value_ranges(doc, root, filename))
    return result


def _retention_value_ranges(doc: dict, root: Path | str, filename: str) -> list[str]:
    """Tier 2 + v2.1 value-range checks for the retention policy seed.

    Each numeric seed is a policy *value* (G-Surfaces D4) — not an engine
    constant — but bad values break the math silently, so the umbrella
    ``validate policy`` command surfaces them as hard errors. Ranges come
    from ``docs/spec-tier2-retention-analytics.md`` §3.2 and the v2.1
    delay-aware/analytics additions (§3 T-Weights).
    """
    errors: list[str] = []
    policy_path = Path(root) / "policy" / filename
    h = doc.get("default_half_life_days")
    if not isinstance(h, (int, float)) or isinstance(h, bool) or not (0 < h <= 365):
        errors.append(
            f"{policy_path}: default_half_life_days must be in (0, 365]; got {h!r}."
        )
    # Flat multipliers are optional in v1.0+ (superseded by the delay table);
    # when present they must still satisfy the Tier 2 ranges.
    up = doc.get("satisfactory_growth_factor")
    if up is not None and (not isinstance(up, (int, float)) or isinstance(up, bool) or not up > 1):
        errors.append(
            f"{policy_path}: satisfactory_growth_factor must be > 1; got {up!r}."
        )
    down = doc.get("unsatisfactory_reduction_factor")
    if down is not None and (
        not isinstance(down, (int, float)) or isinstance(down, bool) or not (0 < down < 1)
    ):
        errors.append(
            f"{policy_path}: unsatisfactory_reduction_factor must be in (0, 1); "
            f"got {down!r}."
        )
    threshold = doc.get("attention_threshold")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not (0 < threshold < 1):
        errors.append(
            f"{policy_path}: attention_threshold must be in (0, 1); "
            f"got {threshold!r}."
        )
    window = doc.get("on_time_window_days")
    if window is not None and (
        isinstance(window, bool) or not isinstance(window, int) or window < 0
    ):
        errors.append(
            f"{policy_path}: on_time_window_days must be a non-negative integer; "
            f"got {window!r}."
        )
    raw_table = doc.get("delay_aware_multipliers")
    if raw_table is not None:
        if not isinstance(raw_table, dict):
            errors.append(f"{policy_path}: delay_aware_multipliers must be a mapping.")
        else:
            for bucket in ("early", "on_time", "late"):
                row = raw_table.get(bucket)
                if not isinstance(row, dict):
                    errors.append(
                        f"{policy_path}: delay_aware_multipliers.{bucket} must be a "
                        f"mapping with satisfactory/unsatisfactory; got {row!r}."
                    )
                    continue
                for outcome in ("satisfactory", "unsatisfactory"):
                    value = row.get(outcome)
                    if (
                        not isinstance(value, (int, float))
                        or isinstance(value, bool)
                        or not value > 0
                    ):
                        errors.append(
                            f"{policy_path}: delay_aware_multipliers.{bucket}."
                            f"{outcome} must be > 0; got {value!r}."
                        )
    raw_domains = doc.get("domain_half_life_scales")
    if raw_domains is not None:
        if not isinstance(raw_domains, dict):
            errors.append(f"{policy_path}: domain_half_life_scales must be a mapping.")
        else:
            for name, value in raw_domains.items():
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not value > 0:
                    errors.append(
                        f"{policy_path}: domain_half_life_scales.{name} must be "
                        f"> 0; got {value!r}."
                    )
    for scale_name in ("low_velocity_scale", "incomplete_evidence_scale"):
        value = doc.get(scale_name)
        if value is not None and (
            not isinstance(value, (int, float)) or isinstance(value, bool) or not (0 < value <= 1)
        ):
            errors.append(
                f"{policy_path}: {scale_name} must be in (0, 1]; got {value!r}."
            )
    min_h = doc.get("min_half_life_days")
    max_h = doc.get("max_half_life_days")
    if min_h is not None and (isinstance(min_h, bool) or not isinstance(min_h, (int, float)) or not min_h >= 1):
        errors.append(
            f"{policy_path}: min_half_life_days must be >= 1; got {min_h!r}."
        )
    if max_h is not None and min_h is not None and isinstance(max_h, (int, float)) and isinstance(min_h, (int, float)):
        if not max_h >= min_h:
            errors.append(
                f"{policy_path}: max_half_life_days must be >= min_half_life_days; "
                f"got {max_h!r} < {min_h!r}."
            )
    return errors


def _recommendation_weight_checks(doc: dict, root: Path | str, filename: str) -> list[str]:
    """v2.1 factor-weight checks for the recommendation seed.

    The dormant ``review_due`` placeholder is superseded by the active
    ``retention_urgency`` factor; no second dormant key may survive, and
    every factor weight must be a finite number (D-Weights, spec §3).
    """
    errors: list[str] = []
    policy_path = Path(root) / "policy" / filename
    factor_weights = doc.get("factor_weights")
    if not isinstance(factor_weights, dict):
        errors.append(f"{policy_path}: factor_weights must be a mapping.")
        return errors
    if "review_due" in factor_weights:
        errors.append(
            f"{policy_path}: 'review_due' is retired — use 'retention_urgency'; "
            "no dormant key may survive (D-Weights)."
        )
    if "retention_urgency" not in factor_weights:
        errors.append(
            f"{policy_path}: missing required factor weight 'retention_urgency' "
            "(v2.1 sequencing)."
        )
    for name, value in factor_weights.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(
                f"{policy_path}: factor weight {name!r} must be a finite number; "
                f"got {value!r}."
            )
        elif not math.isfinite(float(value)):
            errors.append(
                f"{policy_path}: factor weight {name!r} must be finite; got {value!r}."
            )
    return errors
def _analytics_value_ranges(doc: dict, root: Path | str, filename: str) -> list[str]:
    """v1.6 value-range checks for the analytics policy seed (spec §3.2).

    Each numeric seed is a policy *value*, but a bad one silently skews
    every derivation window and advisory threshold, so the umbrella
    ``validate policy`` command surfaces violations as hard errors.
    The ranges live in ``analytics.policy`` (the single seam); this
    function only threads the repo-relative path through.
    """
    from ..analytics.policy import validate_analytics_policy

    policy_path = Path(root) / "policy" / filename
    return validate_analytics_policy(doc, policy_path)


def _portfolio_value_ranges(doc: dict, root: Path | str, filename: str) -> list[str]:
    """v2.0 value-range checks for the portfolio policy seed (spec §7.2).

    Each value is policy seed data, but a bad one silently skews every
    portfolio selection default and honesty-banner window, so the umbrella
    ``validate policy`` command surfaces violations as hard errors.
    """
    errors: list[str] = []
    policy_path = Path(root) / "policy" / filename

    track = doc.get("default_track")
    if not isinstance(track, str) or not track.strip():
        errors.append(
            f"{policy_path}: default_track must be a non-empty string; got {track!r}."
        )

    fmt = doc.get("default_format")
    if fmt not in ("md", "html", "json"):
        errors.append(
            f"{policy_path}: default_format must be one of md, html, json; got {fmt!r}."
        )

    window = doc.get("resource_staleness_days")
    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        errors.append(
            f"{policy_path}: resource_staleness_days must be >= 1; got {window!r}."
        )

    return errors


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


def _resource_web_verification_value_ranges(
    doc: dict, root: Path | str, filename: str
) -> list[str]:
    """v1.7 value-range checks for the resource web verification policy seed.

    Enforces booleans for enabled/follow_redirects, integer in [1, 120] for timeout,
    'HEAD' or 'GET' for check_method, non-empty user_agent, and rejects unknown fields.
    """
    errors: list[str] = []
    policy_path = Path(root) / "policy" / filename

    allowed_fields = {
        "id",
        "status",
        "title",
        "description",
        "enabled",
        "timeout_seconds",
        "follow_redirects",
        "check_method",
        "user_agent",
        "created_at",
        "updated_at",
    }
    unknown = sorted(set(doc) - allowed_fields)
    if unknown:
        errors.append(
            f"{policy_path}: unknown field(s): {', '.join(unknown)}."
        )

    required_fields = (
        "id",
        "status",
        "title",
        "description",
        "enabled",
        "timeout_seconds",
        "follow_redirects",
        "check_method",
        "user_agent",
    )
    for req in required_fields:
        if req not in doc:
            errors.append(f"{policy_path}: missing required field {req!r}.")

    enabled = doc.get("enabled")
    if enabled is not None and not isinstance(enabled, bool):
        errors.append(f"{policy_path}: enabled must be a boolean; got {enabled!r}.")

    timeout = doc.get("timeout_seconds")
    if timeout is not None and (
        isinstance(timeout, bool) or not isinstance(timeout, int) or not (1 <= timeout <= 120)
    ):
        errors.append(
            f"{policy_path}: timeout_seconds must be an integer in [1, 120]; got {timeout!r}."
        )

    follow = doc.get("follow_redirects")
    if follow is not None and not isinstance(follow, bool):
        errors.append(f"{policy_path}: follow_redirects must be a boolean; got {follow!r}.")

    method = doc.get("check_method")
    if method is not None and method not in ("HEAD", "GET"):
        errors.append(
            f"{policy_path}: check_method must be 'HEAD' or 'GET'; got {method!r}."
        )

    ua = doc.get("user_agent")
    if ua is not None and (not isinstance(ua, str) or not ua.strip()):
        errors.append(
            f"{policy_path}: user_agent must be a non-empty string; got {ua!r}."
        )

    return errors

