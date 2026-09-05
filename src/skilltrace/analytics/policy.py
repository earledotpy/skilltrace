"""Analytics policy seed — loading, defaults, and value-range checks (v1.6 G3).

This module is the single seam for ``policy/analytics.yaml`` (spec §3):

- :func:`load_analytics_doc` reads the document (the mapping under the
  ``analytics_policy`` top-level key); unreadable files raise
  :class:`PolicyLoadError` and callers fail open to the module defaults.
- :func:`resolve_analytics_defaults` defensively coerces a raw document to
  ``(window_days, group_by, min_sessions)`` — malformed values collapse to
  the defaults so read paths never need their own try/except.
- :func:`validate_analytics_policy` enforces the §3.2 value ranges as hard
  errors (non-zero exit, message names the field); ``validate policy``
  calls it.
- :func:`limited_data_head` / :data:`LIMITED_DATA_FOLLOWUP` carry the
  canonical §4.3 soft-data wording so the CLI, exports, and Serve cannot
  drift into parallel vocabularies.

All values here are policy *values*, not engine constants: the learner may
edit them and changes take effect at the next invocation.
"""

from __future__ import annotations

from pathlib import Path

from ..policy.loading import PolicyLoadError, load_policy_doc

ANALYTICS_POLICY_FILE = "analytics.yaml"

DEFAULT_WINDOW_DAYS = 30
DEFAULT_GROUP_BY = "prefix"
DEFAULT_MIN_SESSIONS_FOR_FULL_DATA = 3

GROUP_BY_CHOICES = ("prefix", "track")

# Canonical §4.3 soft-data wording. The CLI renders the head through
# ``render.advisory`` and the follow-up indented by ``len("[advisory] ")``;
# exports and Serve join the two sentences into their own banner shapes.
LIMITED_DATA_FOLLOWUP = "Results may not reflect your full activity."


def limited_data_head(min_sessions: int, window_days: int) -> str:
    """First sentence of the §4.3 soft-data advisory (unprefixed)."""
    return (
        f"Limited data — fewer than {min_sessions} sessions "
        f"in the last {window_days} days."
    )


def limited_data_sentence(min_sessions: int, window_days: int) -> str:
    """Single-sentence §4.3 wording for joined-banner shapes (HTML/JSON/Serve).

    The CLI and Markdown render the verbatim two-line form instead
    (head through ``render.advisory`` plus the indented follow-up) — both
    forms are built from this module's pieces, never reworded per surface.
    """
    return f"{limited_data_head(min_sessions, window_days)} {LIMITED_DATA_FOLLOWUP}"


def load_analytics_doc(root: Path | str) -> dict:
    """Load the analytics policy document; raises :class:`PolicyLoadError`."""
    return load_policy_doc(root, ANALYTICS_POLICY_FILE)


def resolve_analytics_defaults(doc: dict) -> tuple[int, str, int]:
    """Coerce a raw policy document to ``(window_days, group_by, min_sessions)``.

    Non-mapping input, missing keys, bools, and out-of-range numbers all
    collapse to the module defaults (fail open — read paths never raise).
    """
    if not isinstance(doc, dict):
        doc = {}
    window = doc.get("default_window_days", DEFAULT_WINDOW_DAYS)
    if not isinstance(window, int) or isinstance(window, bool) or window <= 0:
        window = DEFAULT_WINDOW_DAYS
    group_by = doc.get("default_group_by", DEFAULT_GROUP_BY)
    if group_by not in GROUP_BY_CHOICES:
        group_by = DEFAULT_GROUP_BY
    min_sessions = doc.get("min_sessions_for_full_data", DEFAULT_MIN_SESSIONS_FOR_FULL_DATA)
    if (
        not isinstance(min_sessions, int)
        or isinstance(min_sessions, bool)
        or min_sessions <= 0
    ):
        min_sessions = DEFAULT_MIN_SESSIONS_FOR_FULL_DATA
    return window, group_by, min_sessions


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_analytics_policy(doc: dict, policy_path: Path | str) -> list[str]:
    """Enforce the §3.2 value ranges; each violation names its field.

    Returns a list of error strings (empty when valid). Every check is a
    hard error on load — the caller (`validate policy`) exits non-zero.
    """
    errors: list[str] = []
    window = doc.get("default_window_days")
    if (
        not isinstance(window, int)
        or isinstance(window, bool)
        or not (1 <= window <= 365)
    ):
        errors.append(
            f"{policy_path}: default_window_days must satisfy 1 <= value <= 365; "
            f"got {window!r}."
        )
    min_sessions = doc.get("min_sessions_for_full_data")
    if (
        not isinstance(min_sessions, int)
        or isinstance(min_sessions, bool)
        or min_sessions < 1
    ):
        errors.append(
            f"{policy_path}: min_sessions_for_full_data must be >= 1; "
            f"got {min_sessions!r}."
        )
    thresholds = doc.get("advisory_thresholds")
    if not isinstance(thresholds, dict):
        errors.append(
            f"{policy_path}: advisory_thresholds must be a mapping; "
            f"got {thresholds!r}."
        )
        return errors
    review_target = thresholds.get("review_completion_below_target")
    if not _is_number(review_target) or not (0 < review_target < 1):
        errors.append(
            f"{policy_path}: advisory_thresholds.review_completion_below_target "
            f"must satisfy 0 < value < 1; got {review_target!r}."
        )
    evidence_target = thresholds.get("evidence_coverage_below_target")
    if not _is_number(evidence_target) or not (0 < evidence_target < 1):
        errors.append(
            f"{policy_path}: advisory_thresholds.evidence_coverage_below_target "
            f"must satisfy 0 < value < 1; got {evidence_target!r}."
        )
    velocity_target = thresholds.get("velocity_below_target_per_week")
    if not _is_number(velocity_target) or velocity_target < 0:
        errors.append(
            f"{policy_path}: advisory_thresholds.velocity_below_target_per_week "
            f"must be >= 0; got {velocity_target!r}."
        )
    blockers_threshold = thresholds.get("blockers_active_threshold")
    if not _is_number(blockers_threshold) or blockers_threshold < 0:
        errors.append(
            f"{policy_path}: advisory_thresholds.blockers_active_threshold "
            f"must be >= 0; got {blockers_threshold!r}."
        )
    return errors


__all__ = [
    "ANALYTICS_POLICY_FILE",
    "DEFAULT_GROUP_BY",
    "DEFAULT_MIN_SESSIONS_FOR_FULL_DATA",
    "DEFAULT_WINDOW_DAYS",
    "GROUP_BY_CHOICES",
    "LIMITED_DATA_FOLLOWUP",
    "PolicyLoadError",
    "limited_data_head",
    "limited_data_sentence",
    "load_analytics_doc",
    "resolve_analytics_defaults",
    "validate_analytics_policy",
]
