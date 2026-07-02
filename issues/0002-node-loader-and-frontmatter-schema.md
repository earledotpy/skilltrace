---
id: 2
title: Node loader with strict frontmatter schema; migrate seed nodes
milestone: v0.3.0-rc1
labels: [graph, migration]
status: open
depends_on: [1]
---

## Context

Decisions 3, 14, 18 and ADR 0001: node files are pure curriculum. The
loader must make drift impossible, not merely discouraged.

## Scope

- `SkillNode` model: id, title, summary, domain, track (opaque label),
  roadmap_anchors (`reference_only` enforced), estimated_effort,
  micro_session_fit, competency_dimensions, mastery_policy, tags,
  timestamps.
- Loader **rejects** frontmatter containing `state`, `prerequisites`,
  `unlocks`, or `node_type` with a clear error naming the offending file.
- Node ID format validation; journal sections in the body are ignored.
- One-time migration: strip the four forbidden keys from the 24 scaffold
  seed nodes.

## Acceptance

- Tests: valid node loads; each forbidden key fails with the file named;
  malformed frontmatter fails; non-`reference_only` anchor fails.
- All migrated seed nodes load; `git diff` on seed nodes shows only key
  removals.
