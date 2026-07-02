---
id: 3
title: Edge loader with pruned schema; migrate edges.yaml
milestone: v0.3.0-rc1
labels: [graph, migration]
status: done
depends_on: [1]
---

## Outcome (2026-07-02)

Done. `skilltrace.graph.edges` provides the `GraphEdge` model and a strict
`load_edge`/`load_edges` loader. Mirror-image of the node loader: where nodes
*tolerate* unknown keys, edges use a **closed** schema — any field outside
`{id, source, target, edge_type, reason, active, created_at, updated_at}` fails
validation naming the edge (by id, else file position). That is what permanently
retires `strength`/`can_override`/`activation_rule`: they fail as ordinary
unknown fields (with a hint naming them), so leftover scaffold data can't slip
back in. Exactly three edge types are accepted (`hard_prerequisite`,
`soft_prerequisite`, `remediation`); an unknown type fails naming the edge and
value. `active` is checked for *presence* (not truthiness) and must be a bool, so
`active: false` loads correctly. Shape validation only — referential integrity,
duplicate ids, and cycles stay issue #5's job; `load_edges` hands over the raw
list. The 24 seed edges were migrated by textual line-removal (no YAML
round-trip): `git diff --stat` shows 0 insertions / 72 deletions (24 edges × 3
fields), and all 24 load; both in-use types (`hard`/`soft`) are preserved.
Tests: `tests/graph/test_edges.py` (20 cases: valid load, `active: false`, each
known type, unknown type, each pruned field named, arbitrary unknown field,
missing required field, non-bool active, non-mapping, and the seed integration
load). Full suite 64 passing.

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
