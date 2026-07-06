"""Derived resource verification status (v0.7 slice 5).

A resource's verification status is *always* derived, never stored (CONTEXT.md):
the registry holds only two verification facts — the human-asserted
`last_verified` date and the stored `broken` marker — and every status word is
computed from them against a policy window:

- **unverified** — no `last_verified` (the resource has never been checked);
- **verified** — `last_verified` within the staleness window;
- **stale** — `last_verified` older than the window;
- **broken** — a `broken` marker is present. Broken *dominates* the other three
  (CONTEXT.md): a resource once verified and later found broken reports broken
  until a human re-verifies or edits the curriculum.

The window (`stale_after_days`) is seed data read from
`policy/resource_verification.yaml`; the derivation is engine. Everything here is
pure and read-only — resource status is advice, so nothing in this module can
affect readiness, eligibility, or node state.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from pathlib import Path

from ..policy.loading import PolicyLoadError, load_policy_doc
from .registry import LearningResource

# The engine's safety-net window, used only when the seed value is missing or
# malformed. The normal path reads `stale_after_days` from the policy seed —
# the window is seed data, not an engine constant.
DEFAULT_STALE_AFTER_DAYS = 180

_POLICY_FILE = "resource_verification.yaml"


class VerificationStatus(str, Enum):
    """The four derived verification words (CONTEXT.md's ubiquitous language).

    Ordered worst-first for report grouping: broken and stale are the statuses
    that call for the next verification or replacement action, so they sort
    ahead of unverified and verified.
    """

    BROKEN = "broken"
    STALE = "stale"
    UNVERIFIED = "unverified"
    VERIFIED = "verified"


# Report grouping order: broken first (it dominates and demands action), then
# stale, then unverified, then verified. A lower rank floats to the top.
_GROUP_RANK: dict[VerificationStatus, int] = {
    VerificationStatus.BROKEN: 0,
    VerificationStatus.STALE: 1,
    VerificationStatus.UNVERIFIED: 2,
    VerificationStatus.VERIFIED: 3,
}


def group_rank(status: VerificationStatus) -> int:
    """The report sort key for a status — lower floats to the top."""
    return _GROUP_RANK[status]


def derive_status(
    resource: LearningResource, *, today: date, stale_after_days: int
) -> VerificationStatus:
    """Derive one resource's verification status. Pure; nothing stored.

    A `broken` marker dominates (returns broken regardless of any
    `last_verified`). Otherwise: absent `last_verified` is unverified; a
    `last_verified` older than `stale_after_days` is stale; within the window is
    verified. An unparseable `last_verified` (the loader guarantees only a
    non-empty string, not a real date) cannot confirm freshness, so it reads as
    unverified rather than crashing the report.
    """
    if resource.broken is not None:
        return VerificationStatus.BROKEN
    if not resource.last_verified:
        return VerificationStatus.UNVERIFIED
    try:
        verified_on = date.fromisoformat(resource.last_verified)
    except ValueError:
        return VerificationStatus.UNVERIFIED
    if (today - verified_on).days > stale_after_days:
        return VerificationStatus.STALE
    return VerificationStatus.VERIFIED


def stale_after_days(root: Path | str) -> int:
    """The staleness window: the seed value if present and sane, else the default.

    Reads `stale_after_days` from `policy/resource_verification.yaml` exactly as
    the other advisory readers pull their seed values (suggest.py's grace window,
    staleness.py's stale-session hours). A missing/unparseable seed or a
    non-positive value falls back to the engine safety net — but the normal path
    reads the seed, so the window is seed data, not a hardcoded constant.
    """
    try:
        doc = load_policy_doc(root, _POLICY_FILE)
    except PolicyLoadError:
        return DEFAULT_STALE_AFTER_DAYS
    value = doc.get("stale_after_days")
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return DEFAULT_STALE_AFTER_DAYS
    return value


def replacement_candidates(
    broken: LearningResource, resources: list[LearningResource]
) -> list[LearningResource]:
    """Live resources that could replace a broken one, in registry order.

    A replacement candidate is just another resource linked to one of the broken
    resource's nodes (CONTEXT.md); there is no `replaces` field, and promotion is
    a human curriculum edit retiring the ailing entry. "Live" means not itself
    broken — a second dead link is no replacement. The broken resource is
    excluded, and each candidate appears once even if it shares several nodes.
    """
    nodes = set(broken.supports)
    seen: set[str] = set()
    candidates: list[LearningResource] = []
    for resource in resources:
        if resource.id == broken.id or resource.id in seen:
            continue
        if resource.broken is not None:
            continue
        if nodes.intersection(resource.supports):
            candidates.append(resource)
            seen.add(resource.id)
    return candidates
