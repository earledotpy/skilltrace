---
id: 2
title: Node loader with strict frontmatter schema; migrate seed nodes
milestone: v0.3.0-rc1
labels: [graph, migration]
status: done
depends_on: [1]
---

## Outcome (2026-07-02)

Done. `skilltrace.graph.nodes` provides the `SkillNode` model and a strict
`load_node`/`load_nodes` loader. The loader **rejects** frontmatter carrying
`state`, `prerequisites`, `unlocks`, or `node_type` — naming the offending
file — so schema drift is impossible, not merely discouraged. It also enforces
node-ID format (dot-separated lowercase segments + numeric sequence suffix),
required fields (id/title/summary/domain/track), and `roadmap_anchors`
`source_role: reference_only`. Unknown non-forbidden keys (e.g. legacy `level`)
are tolerated; the markdown body (journal sections) is ignored. `load_nodes`
returns a raw list — no dedupe — so duplicate-ID detection stays issue #5's job.
The 24 seed nodes were migrated by textual line-removal (no YAML round-trip):
`git diff` shows 0 additions / 152 deletions, and all 24 load. Tests:
`tests/graph/test_nodes.py` (23 cases: valid load, each forbidden key names the
file, malformed/unparseable frontmatter, non-`reference_only` anchor, invalid
id, missing required field, unknown-key tolerance, and the seed integration
load). Full suite 44 passing.

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
