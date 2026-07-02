---
id: 4
title: Progress store (graph/state.yaml) with five-state model
milestone: v0.3.0-rc1
labels: [graph, foundation]
status: open
depends_on: [2]
---

## Context

ADR 0001 and decisions 1–2: learner state lives outside curriculum files;
`locked/available` are derived readiness, `active/passed/mastered` are
asserted progress that never moves backward.

## Scope

- `graph/state.yaml`: map of node id → `{state, changed_at}` (+ optional
  per-transition timestamps). Nodes absent from the store default to
  derived readiness.
- Five-state enum validated; anything else fails.
- Write API used by all commands: one function for derived readiness (may
  only write `locked`/`available`, and only over derived states) and one
  for asserted progress (forward-only transitions, learner-command-only).
- Progress entries referencing missing node ids fail validation
  (dangling-reference check).

## Acceptance

- Tests: unknown state fails; readiness writer refuses to touch an
  asserted state; asserted writer refuses backward transitions
  (`passed → active`, `mastered → passed`); dangling node id fails.
- Seed progress store created with all seed nodes in derived states.
