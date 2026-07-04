---
id: 16
title: v0.4 exit gate — fixtures, invalid matrix, integration sequence
milestone: v0.4.0-rc1
labels: [evidence, release]
status: open
depends_on: [9, 10, 11, 12, 13, 14, 15]
---

## Context

Mirror of issue #8 for the evidence layer: shared fixtures, an
invalid-input matrix covering every refusal decided in the 2026-07-03
grilling session, and one end-to-end integration sequence.

## Scope

- Shared evidence fixtures under `tests/evidence/` (valid + invalid
  variants of specs, gates, records, attempts).
- Invalid matrix: every loader/validator error from #10/#11 exercised
  end-to-end through the CLI.
- Integration sequence on a fixture repo: submit accepted evidence to
  minimum count → `eligibility` verdict flips → `pass` succeeds → supersede
  one accepted record → eligibility drops → discrepancy warning surfaces →
  pass state unchanged.
- Roadmap exit-gate commands green:

```bash
pytest tests/evidence
skilltrace validate evidence
skilltrace eligibility math.arithmetic.order_operations_01
```

## Acceptance

- All of the above pass on a fresh clone with no network access.
- `pytest` (full suite) green — graph tests unaffected by the evidence
  layer landing.
