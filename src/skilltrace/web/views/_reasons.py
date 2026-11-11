"""
The human "why this?" copy — one wording for both surfaces.

``/next`` and ``/`` (Today) both explain *why* a skill sits where it does.
The explanations must agree: a count of waiting skills that differs between
two pages about the same curriculum is a lie on one of them, and the
learner cannot tell which (R7, C20).

So the copy lives here once. Both surfaces call it, and the counts it
states come from the same source on both pages.

What this module deliberately does **not** do: expose the ranker. Scores,
factor weights, leverage counts, flag names and node identifiers never
render (VS-4, R1). The learner gets conditions they can check for
themselves — "it is available", "three other skills are waiting on it" —
never the arithmetic that produced the order.
"""

from __future__ import annotations

from ._shared import plural

#: The session window the reasons speak about. It matches the window the
#: ``/next`` route uses by default, so the same skill never gets two
#: different reasons on two pages.
DEFAULT_MINUTES = 60


def downstream_count(view, node_id: str) -> int:
    """How many other skills are waiting on this one.

    The honest form of the ranker's leverage term: only the **active hard
    prerequisites** count, because only those make a skill wait. The
    relationship comes from the edge file alone (HB-8).
    """
    return sum(
        1
        for edge in view.edges
        if edge.active
        and edge.edge_type == "hard_prerequisite"
        and edge.source == node_id
    )


def facts_for(view, rec, *, minutes: int = DEFAULT_MINUTES) -> list[str]:
    """The contributing conditions behind one recommendation's place.

    Each fact is a derived condition the learner can check for themselves;
    nothing here is a score, a weight or a flag name.
    """
    facts: list[str] = []
    if rec.is_active:
        facts.append("You have already started it, so it comes first.")
    if minutes <= 30:
        if rec.fits_session:
            facts.append(f"It fits a {minutes}-minute session.")
        else:
            facts.append(f"It does not fit a {minutes}-minute session.")
    if rec.prereq_reviews_due:
        facts.append(
            "A skill you have already passed is fading below retention, "
            "and this one builds on it."
        )
    if rec.open_blocked:
        facts.append("You have an open blocker recorded on it.")
    if rec.remediation_boosted:
        facts.append("It is a remediation step for a skill you are stuck on.")
    if rec.agent_boosted:
        facts.append("An advisory signal ranks it higher than the rest.")
    waiting = downstream_count(view, rec.node_id)
    if waiting:
        facts.append(
            f"{waiting} other skill{plural(waiting)} "
            f'{"is" if waiting == 1 else "are"} waiting on it.'
        )
    return facts


def reason_for(rec, facts: list[str], *, only_candidate: bool = False) -> str:
    """One honest sentence: why this skill sits where it does.

    The lead states the skill's own standing; the facts that follow are the
    conditions behind it. When nothing else is holding the skill up, the
    sentence says so plainly rather than inventing a reason.
    """
    lead = (
        "You have already started it"
        if rec.is_active
        else "It is available now"
    )
    others = [
        fact.rstrip(".")
        for fact in facts
        if not fact.startswith("You have already started")
    ]
    if not others:
        if only_candidate and not rec.is_active:
            return "It is the only skill available to start right now."
        return f"{lead} and nothing is holding it up."
    return f"{lead}, and " + ", and ".join(others) + "."
