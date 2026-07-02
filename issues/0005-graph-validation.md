---
id: 5
title: Graph validation — IDs, endpoints, dangling refs, cycle detection
milestone: v0.3.0-rc1
labels: [graph, validation]
status: open
depends_on: [2, 3, 4]
---

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
