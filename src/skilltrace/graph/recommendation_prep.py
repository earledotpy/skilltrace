"""Advisory ranking preparation — the single seam behind `recommend()`.

`prepare()` consumes one loaded `JoinedView` (plus the repo root for the
opaque agent-signal file and an explicit `today`) and produces the full
`RecommendInputs` bundle `recommend()` expects: the two policy weight maps
plus the four advisory boost sets. `next`, `today`, and `graph impact` all
call this once instead of hand-assembling the recipe, so advisory diffs
stay consistent across surfaces.

`recommend()` itself stays pure over these inputs; this module owns the
derivation. The join seam stays `JoinedView` — nothing here re-reads
curriculum or progress files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from ..execution.overdue import utc_today
from ..policy.agent_input import load_agent_recommendations
from ..policy.remediation_edges import active_remediations
from ..policy.sequencing import prereq_retention_urgency

if TYPE_CHECKING:
    from ..context import JoinedView
    from ..policy.remediation_edges import ActiveRemediation


@dataclass(frozen=True)
class RecommendInputs:
    """The full advisory input bundle for `recommend()`.

    `active_remediations` carries the edge objects behind
    `remediation_boosted` so `next` can render its advisory cards without
    re-deriving pressure; `agent_warnings` rides along for the same reason
    (warn-and-ignore agent file diagnostics). Neither reaches `recommend()`
    — see `recommend_kwargs()`.
    """

    track_weights: dict[str, float] = field(default_factory=dict)
    factor_weights: dict[str, float] = field(default_factory=dict)
    remediation_boosted: frozenset[str] = frozenset()
    open_blocked: frozenset[str] = frozenset()
    prereq_reviews_due: dict[str, int] = field(default_factory=dict)
    agent_boosted: frozenset[str] = frozenset()
    active_remediations: tuple["ActiveRemediation", ...] = ()
    agent_warnings: tuple[str, ...] = ()

    def recommend_kwargs(self) -> dict:
        """The six `recommend()` inputs, as a kwargs dict."""
        return {
            "track_weights": dict(self.track_weights),
            "factor_weights": dict(self.factor_weights),
            "remediation_boosted": set(self.remediation_boosted),
            "open_blocked": set(self.open_blocked),
            "prereq_reviews_due": dict(self.prereq_reviews_due),
            "agent_boosted": set(self.agent_boosted),
        }


def prepare(
    joined: "JoinedView",
    root: Path | None = None,
    today: date | None = None,
) -> RecommendInputs:
    """Derive every advisory boost input for `recommend()` from one view.

    Pure of curriculum/progress re-reads: remediation pressure and open
    blockers come from the already-joined collections, retention urgency
    from the joined view plus `today`, and agent signals from the opaque
    agent file under `root` (missing `root` or a missing file stands the
    agent factor down with no warnings).
    """
    day = today if today is not None else utc_today()
    blocked = {b.node_id for b in joined.blockers if b.status == "open"}
    active = active_remediations(
        joined.edges,
        store=joined.store,
        blockers=joined.blockers,
        attempts=joined.attempts,
        failed_attempt_threshold=joined.policy.failed_attempt_threshold,
    )
    urgency = prereq_retention_urgency(joined, day)
    agent_recs, agent_warns = (
        load_agent_recommendations(root) if root is not None else ({}, [])
    )
    return RecommendInputs(
        track_weights=dict(joined.policy.track_weights),
        factor_weights=dict(joined.policy.factor_weights),
        remediation_boosted=frozenset(r.remediation_node for r in active),
        open_blocked=frozenset(blocked),
        prereq_reviews_due=dict(urgency),
        agent_boosted=frozenset(agent_recs),
        active_remediations=tuple(active),
        agent_warnings=tuple(agent_warns),
    )
