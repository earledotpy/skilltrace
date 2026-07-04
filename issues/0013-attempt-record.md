---
id: 13
title: skilltrace attempt record
milestone: v0.4.0-rc1
labels: [evidence, cli]
status: open
depends_on: [10]
---

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
