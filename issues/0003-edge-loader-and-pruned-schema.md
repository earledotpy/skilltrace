---
id: 3
title: Edge loader with pruned schema; migrate edges.yaml
milestone: v0.3.0-rc1
labels: [graph, migration]
status: open
depends_on: [1]
---

## Context

Decisions 4–5: `edges.yaml` is the sole source of truth for relationships;
semantics live in the edge type, so `strength`, `can_override`, and
`activation_rule` are deleted.

## Scope

- `GraphEdge` model: `id, source, target, edge_type, reason, active` +
  timestamps. Unknown fields and unknown edge types fail validation.
- Exactly three edge types: `hard_prerequisite`, `soft_prerequisite`,
  `remediation`.
- One-time migration: drop the three pruned fields from all 24 scaffold
  edges (all seed edges keep their current types).

## Acceptance

- Tests: valid edge loads; unknown `edge_type` fails; leftover `strength`/
  `can_override`/`activation_rule` field fails with the edge id named.
- Migrated `edges.yaml` loads; diff shows only field removals.
