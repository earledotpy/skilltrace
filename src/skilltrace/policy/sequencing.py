"""Advisory sequencing signal (v2.1 D-Surface / D-EventLog).

The adaptive-sequencing overlay re-ranks ``next`` / ``today``
recommendations by advisory factors and reason strings. The headline
factor, ``retention_urgency``, answers "a candidate's foundations are
fading": for each ``available``/``active`` node we count how many of its
active hard-prerequisite sources are passed/mastered but *below the
retention threshold* (that is, due a retention review). Building on a
decayed foundation is exactly the case the overlay nudges — words, never
writes.

Pure of I/O and wall-clock calls: callers pass an already-loaded joined
view and an explicit ``today``. A missing retention seed makes every
node urgency zero (advisory stands down), never an error.
"""

from __future__ import annotations

from datetime import date

from .retention_model import derive_memory_states


def prereq_retention_urgency(joined, today: date) -> dict[str, int]:
    """Map each available/active node to the number of its below-threshold hard prereqs.

    Only active ``hard_prerequisite`` edges gate a candidate here (the same
    edges readiness treats as locking); soft and remediation edges never do.
    The retention model is read for ordering only — loss of the event log
    loses signal, never state (D-EventLog).
    """
    seed = joined.policy.retention
    if seed is None:
        return {}
    prereq_sources: dict[str, list[str]] = {}
    for edge in joined.edges:
        if edge.active and edge.edge_type == "hard_prerequisite":
            prereq_sources.setdefault(edge.target, []).append(edge.source)

    states = derive_memory_states(
        nodes=joined.nodes,
        store=joined.store,
        reviews=joined.reviews,
        seed=seed,
        today=today,
    )
    below = {s.node_id for s in states if s.below_threshold}

    urgency: dict[str, int] = {}
    for node in joined.nodes:
        state = joined.store.state_of(node.id)
        if state not in ("available", "active"):
            continue
        count = sum(1 for source in prereq_sources.get(node.id, ()) if source in below)
        if count:
            urgency[node.id] = count
    return urgency