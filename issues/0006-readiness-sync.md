---
id: 6
title: Readiness sync (derived states only)
milestone: v0.3.0-rc1
labels: [graph]
status: done
depends_on: [5]
---

## Context

Decision 2: `locked/available` are derived from hard-prerequisite
satisfaction and may be recomputed at any time; asserted progress is
untouchable by sync.

## Scope

- `skilltrace sync`: recompute derived readiness for every node not in an
  asserted state. A node is `available` iff every active hard-prerequisite
  edge's source is `passed` or `mastered`; otherwise `locked`.
- Curriculum edits may flip `available → locked` for un-started nodes only.
- Sync is a mutating command: one audit event, listing nodes whose
  readiness changed.
- Remediation and soft edges never affect readiness.

## Acceptance

- Tests: sync never writes over `active/passed/mastered`; adding a hard
  prerequisite re-locks an un-started node but not a started one; passing
  a source (fixture) makes targets available on next sync; soft/remediation
  edges don't lock; event appended with changed node list.
