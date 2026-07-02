---
id: 5
title: Graph validation — IDs, endpoints, dangling refs, cycle detection
milestone: v0.3.0-rc1
labels: [graph, validation]
status: done
depends_on: [2, 3, 4]
---

## Outcome

Done. `skilltrace/graph/validation.py` adds `check_graph(nodes, edges, store)`
(pure, whole-graph) and `load_and_validate(root)` (loads + folds load/missing-file
cases), rendered by the `validate graph` command. Errors: duplicate node/edge
ids, edge endpoints naming unknown nodes (all edges, active or not), active
hard-prerequisite cycles (printed with closing path), and dangling progress
references (reusing `check_state_references`). Warnings (never affect exit code):
active soft-prerequisite cycles. `validate graph` exits 0 on seed data
(24 nodes / 24 edges). Tests in `tests/graph/test_validation.py`.

**Deferred:** "unmapped tracks" is intentionally not implemented — there is no
track registry to validate against, and hardcoding a track allowlist in engine
code would violate the curriculum-agnostic invariant (tracks are seed data). It
awaits a future track registry; noted in `validation.py`.

## Context

The Layer 1 contract: unique node IDs, valid edge references, no cycles
among hard prerequisites, soft prerequisites as warnings only.

## Scope

- `skilltrace validate graph`: duplicate node IDs fail; duplicate edge IDs
  fail; edge source/target must exist; hard-prerequisite cycle detection
  fails with the cycle path printed.
- Dangling-reference sweep: progress-store and (later) evidence node ids
  must exist in the graph — immutable-ID safety net (decision 14).
- Soft-prerequisite issues and unmapped tracks are warnings, not errors.
- Summary output: node/edge counts, state counts, warnings.

## Acceptance

- Tests per roadmap v0.3 list: valid seed graph passes; duplicate node ID
  fails; missing edge source fails; missing edge target fails;
  hard-prerequisite cycle fails (fixture with a 3-node cycle); warnings do
  not affect exit code.
- `skilltrace validate graph` exits 0 on migrated seed data.
