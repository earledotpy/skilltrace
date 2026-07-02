---
id: 8
title: v0.3 exit gate — fixtures, invalid-graph suite, gate script
milestone: v0.3.0-rc1
labels: [tests, release]
status: open
depends_on: [5, 6, 7]
---

## Context

Each issue lands with its own tests; this issue assembles the RC-level
proof: shared fixtures, the invalid-fixture matrix from the roadmap's v0.3
test list, and a repeatable exit-gate run.

## Scope

- `tests/graph/` shared fixtures: minimal valid graph; duplicate-ID graph;
  missing-source/target graphs; hard-cycle graph; frontmatter-with-`state`
  node; edge-with-`strength` file.
- Integration test: fresh temp copy of seed data → install → `validate
  graph` → `sync` → `next` all exit 0.
- Exit-gate script (or documented command list) runs: `pytest tests/graph`,
  `skilltrace validate graph`, `skilltrace next --minutes 60 --limit 5
  --show-locked`.
- Roadmap-anchor test: anchors never affect locking or recommendation.

## Acceptance

- Full v0.3 exit gate green on a fresh clone, offline.
- Roadmap v0.3 test list fully covered (each item traceable to a test).
