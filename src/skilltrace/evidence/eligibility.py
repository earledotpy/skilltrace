"""Pass-eligibility computation — pure arithmetic over loaded evidence records.

CONTEXT.md "Pass eligibility": a node is pass-eligible when every *required*
artifact spec has at least its `minimum_count` of accepted, non-superseded
evidence records. This module is the authoritative home of that computation
(issue #14); the narrow warning-time check in `submission.py` predates it and
reuses the same `live_accepted_count` primitive.

Three properties the shape of this function enforces, not merely documents:

- **Evidence records are the only input.** There is no attempts parameter — so
  "assessment attempts don't count" is true by construction, not by filtering.
- **Nothing is ever re-run.** The gate arrives as a plain `has_gate: bool`, never
  a gate object carrying a command — you cannot execute what you do not hold.
- **State never touches the verdict.** `node_state` feeds *only* the advisory
  `passed_but_not_backed` overlay; the `eligible` arithmetic is state-independent,
  identical across every learner state. An asserted pass that is no longer backed
  by evidence is surfaced, never revoked (ADR 0003 / the safety rules).

A node with no gate, or with no required spec, is never eligible — there is
either no authority to accept its evidence or nothing required to satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .records import EvidenceRecord
from .specs import ArtifactSpec

# The two asserted states that are a *pass* — the ones a lost-backing discrepancy
# is worth surfacing against. `active` is asserted progress but not a pass, so a
# started-but-unpassed node under its minimum is the normal in-progress case, not
# a discrepancy. Mirrors `submission._PASS_STATES`.
_PASS_STATES: frozenset[str] = frozenset({"passed", "mastered"})


def live_accepted_count(records: list[EvidenceRecord], spec_id: str) -> int:
    """Accepted, non-superseded records against `spec_id` — what counts to pass.

    A record is *live* if nothing supersedes it; a superseded correction (whatever
    its own verdict) drops out. Only accepted, live records count toward a required
    spec's `minimum_count`. The superseded set is derived from every record's
    `supersedes` pointer, never written onto the superseded record.
    """
    superseded = {r.supersedes for r in records if r.supersedes is not None}
    return sum(
        1
        for r in records
        if r.artifact_spec_id == spec_id and r.accepted and r.id not in superseded
    )


@dataclass(frozen=True)
class SpecEligibility:
    """One required spec's standing: how many live accepted records vs its minimum."""

    spec_id: str
    minimum_count: int
    accepted_count: int

    @property
    def met(self) -> bool:
        return self.accepted_count >= self.minimum_count


@dataclass
class EligibilityResult:
    """The verdict for one node, with the per-required-spec breakdown and reasons.

    `eligible` is the state-independent verdict. `specs` is the count breakdown for
    each *required* spec (optional specs are never listed). `reasons` explains a
    negative verdict, empty when eligible. `passed_but_not_backed` is the advisory
    overlay: the node's asserted pass no longer holds, but stands regardless.
    """

    node_id: str
    eligible: bool
    has_gate: bool
    has_required_spec: bool
    specs: list[SpecEligibility] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    passed_but_not_backed: bool = False


def compute_eligibility(
    node_id: str,
    specs_for_node: list[ArtifactSpec],
    *,
    has_gate: bool,
    records: list[EvidenceRecord],
    node_state: str,
) -> EligibilityResult:
    """Decide pass-eligibility for one node. Pure: arithmetic over `records` only.

    `specs_for_node` is the node's specs (both required and optional); `records`
    is the full evidence trail (filtered by spec here). `node_state` is consulted
    solely for the `passed_but_not_backed` overlay.
    """
    required = [s for s in specs_for_node if s.required]
    breakdown = [
        SpecEligibility(
            spec_id=spec.id,
            minimum_count=spec.minimum_count,
            accepted_count=live_accepted_count(records, spec.id),
        )
        for spec in required
    ]

    reasons: list[str] = []
    if not has_gate:
        reasons.append(
            f"node {node_id} has no gate — no authority can accept its evidence, so "
            "it is never pass-eligible."
        )
    if not required:
        reasons.append(
            f"node {node_id} has no required artifact spec — it is never pass-eligible."
        )
    for spec in breakdown:
        if not spec.met:
            reasons.append(
                f"spec {spec.spec_id}: {spec.accepted_count} of {spec.minimum_count} "
                "required accepted records — below minimum."
            )

    eligible = has_gate and bool(required) and all(spec.met for spec in breakdown)
    passed_but_not_backed = (not eligible) and node_state in _PASS_STATES

    return EligibilityResult(
        node_id=node_id,
        eligible=eligible,
        has_gate=has_gate,
        has_required_spec=bool(required),
        specs=breakdown,
        reasons=reasons,
        passed_but_not_backed=passed_but_not_backed,
    )
