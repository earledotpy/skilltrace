---
id: 9
title: Evidence schema migration and compiler scaffold retirement
milestone: v0.4.0-rc1
labels: [evidence, migration]
status: done
depends_on: [8]
---

## Context

Grilling session 2026-07-03: gates collapse to a two-value authority enum
with AI authority unrepresentable (CONTEXT.md "ValidationGate", "Acceptance
authority"). The scaffold `compiler/` package is the only reader of the old
gate fields; its contract was "reference until v0.3", which has expired —
updating it would be extending it (forbidden), leaving it is a silent trap.

## Scope

- Migrate `evidence/validation_gates.yaml` to the target schema:
  `id, node_id, authority (objective | manual), command (required iff
  objective, forbidden iff manual), title, description` + timestamps.
  - `objective_eval` → `objective` (keep `command`)
  - `manual_check` / `checklist` / `rubric` → `manual` (the distinction may
    survive as wording in `description`, never as an enum)
  - `consecutive_passes` → `manual`; its "3" already lives on the matching
    artifact spec's `minimum_count: 3` — verify, don't duplicate
- Drop `gate_kind`, `ai_advisory_only`, `can_close_node`,
  `required_consecutive_passes` everywhere.
- Delete `compiler/` entirely.
- Update `CLAUDE.md`: remove the scaffold smoke-check lines and the
  `compiler/` repo-layout entry; note the interface layer's replacement
  history stays in ADR 0002 / roadmap.

## Acceptance

- No file in the repo contains `gate_kind`, `ai_advisory_only`,
  `can_close_node`, or `consecutive_passes` (except docs/history).
- `compiler/` no longer exists; `pytest` and `skilltrace validate graph`
  still pass.
- All 24 gates carry exactly one of the two authorities; every `objective`
  gate has a `command`; no `manual` gate does.
