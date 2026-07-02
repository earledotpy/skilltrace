---
id: 7
title: Next-node recommendation v1
milestone: v0.3.0-rc1
labels: [graph, recommendation]
status: open
depends_on: [5, 6]
---

## Context

Goal 1 of the PRD. Decision 18: the engine knows no track names — track
weights come from `policy/recommendation.yaml` as an opaque map. Full
policy machinery is v0.6; v0.3 reads just the weight map.

## Scope

- `skilltrace next --minutes N --limit K --show-locked`: rank
  `available`/`active` nodes whose hard prerequisites are satisfied.
- Scoring v1: track weight (from policy map, default 0 + warning for
  unmapped tracks) + downstream leverage (outgoing edge count) + session
  fit (micro_session_fit vs `--minutes`) + small bonus for already-active
  nodes.
- Every recommendation prints a reason line (decision: "Why that node?").
- `--show-locked` appends locked nodes with the unsatisfied prerequisites
  named. Read-only command: no event.

## Acceptance

- Tests: locked node never recommended as available; recommendation reason
  present for every result; track weights read from policy file (fixture
  with a custom map changes ordering); unmapped track warns; `--minutes 15`
  prefers 15-minute-fit nodes.
- `skilltrace next --minutes 60 --limit 5 --show-locked` exits 0 on seed
  data.
