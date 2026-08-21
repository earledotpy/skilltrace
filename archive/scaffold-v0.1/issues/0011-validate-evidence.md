---
id: 11
title: skilltrace validate evidence
milestone: v0.4.0-rc1
labels: [evidence, validation]
status: done
depends_on: [10]
---

## Context

Grilling Q14: `validate evidence` checks curriculum + evidence-trail
internal consistency only and never reads the progress store — its output
is stable regardless of learner state. State-dependent warnings surface at
submit time and in `eligibility` output (issues #12, #14); the one-stop
cross-layer view is `health` (v0.9), not this command.

## Scope

Errors (non-zero exit):

- duplicate IDs across specs / gates / records / attempts
- dangling references: spec→node, gate→node, record→spec, attempt→node,
  supersedes→record
- two gates on one node
- cross-spec supersede; double-supersede (target already has a successor)
- schema violations the loaders catch (surfaced through this command)

Warnings (exit 0):

- node with no gate (cannot accept evidence, never pass-eligible)
- node with no required spec (never pass-eligible)
- artifact drift: `location` missing or content hash no longer matching
  `artifact_hash`

## Acceptance

- Tests for every error and warning above, plus: clean post-#9 seed data
  validates with warnings only where seeded; output never varies with
  `graph/state.yaml` contents.
- `skilltrace validate evidence` wired into the dispatcher (read-only — no
  event appended).
