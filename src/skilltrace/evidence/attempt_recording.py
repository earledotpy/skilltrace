"""The `attempt record` decision — a pure planner over already-loaded data.

An `AssessmentAttempt` is a historical fact (CONTEXT.md): it is recordable in
*any* node state and even on a gateless node — those two situations warn but
never refuse, because refusing would deny a fact that already happened. The only
refusal is an `outcome` outside the two allowed values (`passed`/`failed`),
which is a malformed request, not a fact.

This module mirrors the `plan_submit` / `commands/submit.py` seam: `plan_attempt`
takes the already-loaded facts (whether the node has a gate, the existing
attempt ids for sequence allocation, the node's state) plus the parsed request,
and returns *what to write, what to say, and the exit code*, touching no disk.
The handler (`commands/attempt.py`) binds the loaders and the append.

Two things attempts deliberately do **not** do, both load-bearing:

- **An attempt never feeds pass eligibility.** Recording one — passed or failed
  — writes only `attempts.yaml`; it leaves the evidence records untouched, so no
  eligibility computation (issue #14) can observe it.
- **A `failed` attempt is a successful mutation.** Failure is the *content* of
  the record, not an error: a failed attempt exits 0 and logs its one event,
  exactly as a rejected evidence record is still a written, audited submit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .attempts import OUTCOMES
from .ids import allocate_attempt_id

# Exit codes the outcome may carry. Zero is a *written* attempt (passed *or*
# failed — the outcome is the record's content, not its success). A malformed
# request mirrors the submit planner's refusal code.
_EXIT_OK = 0
_EXIT_REFUSED = 2


@dataclass
class AttemptOutcome:
    """What the handler should write, print, and exit with.

    `record` is the mapping to append to `attempts.yaml`, or `None` on a refusal.
    `records_touched` feeds the audit event and is non-empty only when a record
    is written. `messages` are informational, `warnings` are advisory (gateless
    node, locked node — neither blocks), `errors` are refusal reasons.
    """

    record: dict | None = None
    records_touched: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    exit_code: int = _EXIT_OK


def plan_attempt(
    node_id: str,
    *,
    outcome: str,
    note: str | None,
    has_gate: bool,
    existing_attempt_ids: list[str],
    node_state: str,
    now: str,
) -> AttemptOutcome:
    """Decide one attempt recording. Pure: no disk (the handler binds the append).

    The only refusal is an `outcome` outside the two allowed values; a gateless
    node and a locked node warn but still record, because an attempt is a fact
    that already happened.
    """
    if outcome not in OUTCOMES:
        return AttemptOutcome(
            errors=[
                f"outcome {outcome!r} is not recordable — expected one of "
                f"{', '.join(sorted(OUTCOMES))}."
            ],
            exit_code=_EXIT_REFUSED,
        )

    warnings: list[str] = []
    if not has_gate:
        warnings.append(
            f"node {node_id} has no gate; the attempt is recorded, but there is no "
            "gate standard for it to have been attempted against."
        )
    if node_state == "locked":
        warnings.append(
            f"node {node_id} is locked; the attempt is recorded, but the node is "
            "not yet available to work."
        )

    record_id = allocate_attempt_id(node_id, existing_attempt_ids)
    record: dict = {"id": record_id, "node_id": node_id, "outcome": outcome}
    if note:
        record["note"] = note
    record["created_at"] = now

    return AttemptOutcome(
        record=record,
        records_touched=[record_id],
        messages=[f"attempt {record_id}: {outcome}"],
        warnings=warnings,
        exit_code=_EXIT_OK,
    )
