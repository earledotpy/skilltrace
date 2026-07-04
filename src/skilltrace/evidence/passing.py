"""The `skilltrace pass` decision — a pure planner over already-resolved facts.

Passing is an asserted act performed only by the learner via an explicit command
(CONTEXT.md "Passing"): the command refuses unless pass eligibility holds, and
refuses on a locked node regardless of evidence (no hard-prerequisite override).
`active` is never a precondition — the state chain is an ordering, not a
mandatory itinerary, so `available -> passed` is legal.

This module is the pure core of that decision, mirroring the `plan_submit` /
`plan_attempt` seam: it takes the node's stored state and its computed
`EligibilityResult` (issue #14) and returns *whether to write `passed`, what to
say, and the exit code* — touching no disk and re-running no gate. The command
handler (`commands/pass_.py`) resolves those facts, then binds the two real side
effects a proceed entails: `store.write_asserted(node_id, "passed")` and the
audit event the dispatcher appends. Nothing else — no review scheduling, no sync.

The three refusals mirror the automation boundary's refusal exit code (2); the
handler keeps operational failures (unknown node, unloadable data) at exit 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .eligibility import EligibilityResult

# Refusing a valid-but-not-permitted pass uses the same exit code as the
# automation boundary's refusal, distinct from an operational failure (1).
_EXIT_OK = 0
_EXIT_REFUSED = 2

# The two asserted states that already *are* a pass — passing again is refused
# (idempotent re-assertion is not this command's job; the pass already stands).
_ALREADY_PASSED_STATES: frozenset[str] = frozenset({"passed", "mastered"})


@dataclass
class PassOutcome:
    """What the handler should write, print, and exit with.

    `proceed` is the explicit "write `passed`" signal — the handler asserts
    progress only when it is true. It is kept distinct from `exit_code` because a
    pass writes no record of its own (unlike `evidence submit`), so success is a
    state transition, not a returned document. `records_touched` feeds the audit
    event and names the passed node only on a proceed. `messages` are
    informational; `errors` are refusal reasons.
    """

    node_id: str
    proceed: bool = False
    records_touched: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    exit_code: int = _EXIT_OK


def _refuse(node_id: str, reasons: list[str]) -> PassOutcome:
    return PassOutcome(node_id=node_id, proceed=False, errors=reasons, exit_code=_EXIT_REFUSED)


def plan_pass(
    node_id: str, *, current_state: str, eligibility: EligibilityResult
) -> PassOutcome:
    """Decide whether to assert `passed` for one node. Pure: no disk, no gate.

    Checks, in the issue's order: not locked, not already passed/mastered, and
    pass-eligible. Any failure refuses (exit 2) and writes nothing; only an
    eligible, non-locked, not-yet-passed node proceeds.
    """
    if current_state == "locked":
        return _refuse(
            node_id,
            [
                f"node {node_id} is locked — a hard prerequisite is unmet, and there "
                "is no hard-prerequisite override; nothing passed."
            ],
        )

    if current_state in _ALREADY_PASSED_STATES:
        return _refuse(
            node_id,
            [
                f"node {node_id} is already {current_state}; asserted progress is not "
                "re-asserted and never moves backward."
            ],
        )

    if not eligibility.eligible:
        # Lead with the headline, then carry the per-spec / structural reasons
        # from #14 so the learner sees exactly what is missing.
        return _refuse(
            node_id,
            [f"node {node_id} is not pass-eligible; nothing passed.", *eligibility.reasons],
        )

    return PassOutcome(
        node_id=node_id,
        proceed=True,
        records_touched=[node_id],
        messages=[f"pass {node_id}: eligibility holds from state {current_state!r}; asserting passed."],
        exit_code=_EXIT_OK,
    )
