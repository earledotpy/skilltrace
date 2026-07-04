---
id: 10
title: Evidence models and strict loaders
milestone: v0.4.0-rc1
labels: [evidence, foundation]
status: open
depends_on: [9]
---

## Context

CONTEXT.md: ArtifactSpec, ValidationGate, EvidenceRecord (ADR 0003),
AssessmentAttempt. Same strict-loader pattern as the v0.3 node/edge
loaders: closed schemas, unknown fields and unknown enum values fail.

## Scope

- `skilltrace.evidence` package with models + loaders for the four types,
  reading `evidence/artifact_specs.yaml`, `evidence/validation_gates.yaml`,
  `evidence/evidence_records.yaml`, `evidence/attempts.yaml`.
- ValidationGate: two-value `authority` enum; any other value fails loading
  (AI authority is unrepresentable — the boundary is the schema).
- ArtifactSpec: `required` bool, `minimum_count >= 1`.
- EvidenceRecord: `id` (`ev.<node_id>.NNN`), `artifact_spec_id` (sole
  linkage — no `node_id` field; the node is derived through the spec),
  `location`, `note?`, `accepted` bool, `accepted_by`
  (`objective_gate | learner_manual`), `artifact_hash`, `supersedes?` +
  `supersede_reason?` (both-or-neither), `created_at`. Frozen at creation;
  no loader or model API mutates a record.
- AssessmentAttempt: `id` (`att.<node_id>.NNN`), `node_id`, `outcome`
  (`passed | failed` — no scores), `note?`, `created_at`. Immutable; no
  supersede mechanism.
- ID allocation helper: per-node sequence, never reused, never backfilled.

## Acceptance

- Tests: unknown authority fails; `command` on manual / missing on
  objective fails; unknown fields fail; `minimum_count: 0` fails;
  `supersedes` without reason fails; outcome outside the two values fails;
  malformed IDs fail; seed files load clean post-#9.
