"""Mastery eligibility — a derived fact, computed on demand, never stored.

CONTEXT.md: the node is passed, accepted evidence is on file, and at least
one satisfactory post-pass review was completed with the policy-configured
day spacing. Reviews can only ever be scheduled on passed/mastered nodes
(v0.5), so every completed review here is post-pass by construction; the
spacing check compares calendar days between the recorded pass transition
and the review's completion.

This module is the pure core plus its two thin fact-resolvers; asserting
`mastered` is `skilltrace master`'s job alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from ..evidence.eligibility import live_accepted_count
from ..evidence.records import EvidenceRecord
from ..evidence.specs import ArtifactSpec
from ..execution.reviews import Review
from .loading import PolicyLoadError, load_policy_doc

# Engine fallbacks when the seed file cannot supply a value; the seed
# (policy/mastery_promotion.yaml) is the intended source.
_DEFAULT_MIN_ACCEPTED_EVIDENCE = 1
_DEFAULT_MIN_DAYS_PASS_TO_REVIEW = 3


@dataclass
class MasteryValues:
    """The two seed values the mastery derivation reads."""

    min_accepted_evidence: int = _DEFAULT_MIN_ACCEPTED_EVIDENCE
    min_days_pass_to_review: int = _DEFAULT_MIN_DAYS_PASS_TO_REVIEW


def load_mastery_values(root: Path | str) -> MasteryValues:
    """Read the mastery seed values, falling back to engine defaults."""
    try:
        doc = load_policy_doc(root, "mastery_promotion.yaml")
    except PolicyLoadError:
        return MasteryValues()
    values = MasteryValues()
    if isinstance(doc.get("min_accepted_evidence"), int):
        values.min_accepted_evidence = doc["min_accepted_evidence"]
    if isinstance(doc.get("min_days_pass_to_review"), int):
        values.min_days_pass_to_review = doc["min_days_pass_to_review"]
    return values


@dataclass
class MasteryEligibility:
    """The derived verdict and every reason it is (not yet) positive."""

    node_id: str
    eligible: bool
    reasons: list[str] = field(default_factory=list)


def _day_of(timestamp: str) -> date | None:
    try:
        return date.fromisoformat(str(timestamp)[:10])
    except ValueError:
        return None


def compute_mastery_eligibility(
    node_id: str,
    *,
    current_state: str,
    passed_at: str | None,
    specs: list[ArtifactSpec],
    records: list[EvidenceRecord],
    reviews: list[Review],
    values: MasteryValues,
) -> MasteryEligibility:
    """Derive mastery eligibility from live facts. Pure: no disk, no clock."""
    reasons: list[str] = []

    if current_state == "mastered":
        reasons.append(f"node {node_id} is already mastered.")
    elif current_state != "passed":
        reasons.append(
            f"node {node_id} is {current_state!r} — mastery requires a passed node."
        )

    accepted = sum(live_accepted_count(records, spec.id) for spec in specs)
    if accepted < values.min_accepted_evidence:
        reasons.append(
            f"accepted evidence: {accepted} of {values.min_accepted_evidence} "
            "required live accepted record(s)."
        )

    pass_day = _day_of(passed_at) if passed_at is not None else None
    if current_state == "passed" and pass_day is None:
        reasons.append(
            f"node {node_id} has no recorded pass date; spacing cannot be derived."
        )

    if pass_day is not None:
        if not _has_spaced_satisfactory_review(
            reviews, node_id, pass_day, values.min_days_pass_to_review
        ):
            reasons.append(
                "no satisfactory completed review at least "
                f"{values.min_days_pass_to_review} day(s) after the pass "
                f"({pass_day.isoformat()})."
            )

    return MasteryEligibility(node_id=node_id, eligible=not reasons, reasons=reasons)


@dataclass
class MasterOutcome:
    """What the `master` handler should write, print, and exit with.

    Mirrors `evidence.passing.PassOutcome`: `proceed` is the explicit "write
    `mastered`" signal, kept apart from `exit_code` because success is a state
    transition, not a returned document. Refusals use exit 2 (the automation
    boundary's refusal code), operational failures stay the handler's concern.
    """

    node_id: str
    proceed: bool = False
    records_touched: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    exit_code: int = 0


def plan_master(node_id: str, *, eligibility: MasteryEligibility) -> MasterOutcome:
    """Decide whether to assert `mastered`. Pure: no disk, no clock.

    Mastery eligibility already folds in every precondition (passed state —
    which excludes locked and already-mastered — accepted evidence, spaced
    satisfactory review), so the decision is exactly its verdict.
    """
    if not eligibility.eligible:
        return MasterOutcome(
            node_id=node_id,
            proceed=False,
            errors=[
                f"node {node_id} is not mastery-eligible; nothing mastered.",
                *eligibility.reasons,
            ],
            exit_code=2,
        )
    return MasterOutcome(
        node_id=node_id,
        proceed=True,
        records_touched=[node_id],
        messages=[f"master {node_id}: mastery eligibility holds; asserting mastered."],
    )


def _has_spaced_satisfactory_review(
    reviews: list[Review], node_id: str, pass_day: date, min_days: int
) -> bool:
    for review in reviews:
        if review.node_id != node_id or review.status != "completed":
            continue
        if review.outcome != "satisfactory" or review.completed_at is None:
            continue
        review_day = _day_of(review.completed_at)
        if review_day is not None and (review_day - pass_day).days >= min_days:
            return True
    return False
