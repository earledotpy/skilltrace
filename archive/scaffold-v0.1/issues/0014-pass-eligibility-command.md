---
id: 14
title: Pass eligibility computation and skilltrace eligibility
milestone: v0.4.0-rc1
labels: [evidence, cli]
status: done
depends_on: [10]
---

## Context

CONTEXT.md "Pass eligibility": every required artifact spec has at least
its minimum count of accepted, non-superseded evidence records. Evidence
records are the only input; computing eligibility never executes anything.

## Scope

- Eligibility function: pure arithmetic over loaded records — per required
  spec, count accepted records with no successor; optional specs ignored;
  attempts ignored; no gate command ever re-run.
- A node with no gate or no required spec is never eligible.
- `skilltrace eligibility <node_id>`: prints the verdict with per-spec
  counts and reasons; reports the discrepancy when the node is already
  passed but eligibility no longer holds (advisory — the pass stands).
- Exit code reports whether the question was answered, not the answer:
  0 for any verdict (eligible or not); non-zero only for errors (unknown
  node, unloadable data). Read-only — no event.

## Acceptance

- Tests: below-minimum count not eligible; superseded records don't count;
  rejected records don't count; optional-spec records don't count; passing
  attempts don't count; gateless/spec-less node never eligible; "not
  eligible" exits 0; unknown node exits non-zero; passed-but-not-backed
  discrepancy reported.
