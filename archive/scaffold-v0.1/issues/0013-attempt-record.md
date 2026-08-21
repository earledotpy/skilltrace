---
id: 13
title: skilltrace attempt record
milestone: v0.4.0-rc1
labels: [evidence, cli]
status: done
depends_on: [10]
---

## Outcome (2026-07-04)

Implemented as a pure `plan_attempt` planner (`evidence/attempt_recording.py`)
over already-loaded facts (has-gate, existing attempt ids, node state), plus a
thin `attempt record` handler (`commands/attempt.py`) binding the loaders and the
`attempts.yaml` append. The only refusal is an `outcome` outside
`passed`/`failed` (exit 2, nothing written); a gateless node and a locked node
warn but still record, because an attempt is a historical fact. A `failed`
attempt is a written, audited mutation (exit 0, one event) — the outcome is the
record's content, not an error — mirroring the rejected-evidence-record lesson
from #12. Notes are optional including on failures. Attempts write only
`attempts.yaml`, so the evidence trail eligibility (#14) reads from is untouched.
Records are appended raw (existing rows byte-preserved), immutable, no supersede.
Covered by `tests/evidence/test_attempt_recording.py` (planner) and
`test_attempt_command.py` (wired CLI + audit + eligibility-invariance).

## Context

CONTEXT.md "AssessmentAttempt": attempts never feed pass eligibility; failed
attempts are the canonical record of assessment failure and feed remediation
pressure (counted in v0.6).

## Scope

```bash
skilltrace attempt record <node_id> --outcome passed|failed [--note "..."]
```

- Recordable in any node state and on gateless nodes — warn in both cases,
  never refuse (an attempt is a historical fact).
- Notes optional, including on failures (blockers are where "stuck" gets
  articulated).
- Immutable once written; no supersede mechanism.
- One event appended via the dispatcher.

## Acceptance

- Tests: outcome outside the two values refuses; gateless and locked-node
  warnings emitted; attempt has zero effect on any eligibility computation
  (explicit test against #14); exactly one event per attempt.
