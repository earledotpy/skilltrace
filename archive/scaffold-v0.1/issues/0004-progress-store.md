---
id: 4
title: Progress store (graph/state.yaml) with five-state model
milestone: v0.3.0-rc1
labels: [graph, foundation]
status: done
depends_on: [2]
---

## Outcome

Shipped `skilltrace.graph.state`: `ProgressStore` with two guarded writers —
`write_readiness` (derived `locked`/`available` only, refuses to touch asserted
progress, not forward-only) and `write_asserted` (asserted states only,
forward-only along the state order). `load_state` validates the state enum
(shape only); `check_state_references` is the separate dangling-node-id check
that issue #5's `validate graph` will compose. Seed `graph/state.yaml` created
with all 24 seed nodes in derived states — 12 `locked` (targets of active
`hard_prerequisite` edges), 12 `available` — no asserted progress seeded.
Tests in `tests/graph/test_state.py` (27) cover the enum, all four write
guards, backward-transition refusal, dangling references, round-trip, and the
seed store.

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
