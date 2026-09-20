---
id: 8
title: v0.3 exit gate — fixtures, invalid-graph suite, gate script
milestone: v0.3.0-rc1
labels: [tests, release]
status: done
depends_on: [5, 6, 7]
---

## Outcome (2026-07-02)

Assembled the RC-level proof:

- `tests/graph/conftest.py` — `GraphBuilder` writes real mini-repos so tests
  exercise the loader path (`load_and_validate`), not just the pure
  `check_graph` seam; `set_asserted` sets pass preconditions via the store,
  never a command.
- `tests/graph/test_exit_gate_fixtures.py` — invalid-fixture matrix through the
  loader, including the two loader-only rejections (frontmatter `state`, edge
  `strength`) that the pure seam cannot see.
- `tests/graph/test_exit_gate_integration.py` — composed `validate graph` →
  `sync` → `next` sequence on a fresh seed-data copy; exits 0, logs exactly one
  (sync) event, sync idempotent.
- `tests/graph/test_roadmap_anchor.py` — anchors never lock or reorder.
- `src/skilltrace/__main__.py` — `python -m skilltrace` (PATH-independent entry).
- `scripts/exit_gate_v03.py` — repeatable exit-gate runner carrying the durable
  roadmap-v0.3-test-list → test traceability map.

Full suite green (154 passed); `python scripts/exit_gate_v03.py` passes offline.

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
