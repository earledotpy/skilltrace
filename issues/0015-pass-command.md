---
id: 15
title: skilltrace pass
milestone: v0.4.0-rc1
labels: [evidence, cli, safety]
status: open
depends_on: [14]
---

## Context

CONTEXT.md "Passing": an asserted act performed only by the learner via an
explicit command. Refuses without eligibility and on a locked node (no
hard-prerequisite override). `active` is never a precondition — the state
chain is an ordering, not a mandatory itinerary; `available → passed` is
legal. Review auto-scheduling attaches in v0.5/v0.6 — **do not stub it**.

## Scope

`skilltrace pass <node_id>` does exactly three things:

1. Verify: node exists; not locked; not already passed/mastered;
   pass-eligible per #14. Any failure → refuse, non-zero exit, printed
   reason.
2. Write `passed` through the guarded asserted-progress store API (v0.3).
3. Append one event via the dispatcher.

Nothing else — no review scheduling, no sync side-effects.

## Acceptance

- Tests: refuses without eligibility; refuses on locked regardless of
  evidence; succeeds from `available` (skipping `active`) and from
  `active`; refuses on already-passed/mastered; exactly one event; state
  written via the guarded API only; no other file touched.
- Safety: no code path added by this issue can pass a node without this
  explicit command (grep-level check that nothing else calls the asserted
  writer with `passed`).
