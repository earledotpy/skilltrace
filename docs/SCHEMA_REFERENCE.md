# Schema Reference

This document is the frozen schema reference for SkillTrace v1.0.0. The
schemas it describes are the source of truth for validation. Any future change
requires a new ADR and a migration script.

## Node frontmatter

**Source:** `src/skilltrace/graph/nodes.py`
**Schema:** Open (unknown keys tolerated; only forbidden keys rejected)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Must match node ID regex (see below) |
| `title` | string | yes | |
| `summary` | string | yes | |
| `domain` | string | yes | |
| `track` | string | yes | |
| `roadmap_anchors` | list[dict] | no | Each must declare `source_role: "reference_only"` |
| `estimated_effort` | dict | no | Opaque structured metadata |
| `micro_session_fit` | dict | no | Opaque structured metadata |
| `competency_dimensions` | dict | no | Opaque structured metadata |
| `mastery_policy` | dict | no | Opaque structured metadata |
| `tags` | list[string] | no | |
| `created_at` | string | no | ISO timestamp |
| `updated_at` | string | no | ISO timestamp |

**Forbidden keys** (hard load error): `state`, `prerequisites`, `unlocks`,
`node_type`

**Node ID regex:** Two or more dot-separated segments of `[a-z0-9]+`,
last segment ends in `_\d+` (e.g. `math.algebra.linear_equations_01`).

## Graph edges

**Source:** `src/skilltrace/graph/edges.py`
**Schema:** Closed (unknown fields are a load error)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Opaque curriculum string |
| `source` | string | yes | Node ID of source |
| `target` | string | yes | Node ID of target |
| `edge_type` | string | yes | Closed enum |
| `reason` | string | yes | |
| `active` | boolean | yes | Must be a real bool |
| `created_at` | string | no | ISO timestamp |
| `updated_at` | string | no | ISO timestamp |

**Edge type enum:** `hard_prerequisite`, `soft_prerequisite`, `remediation`

**Pruned fields** (rejected as unknown): `strength`, `can_override`,
`activation_rule`

## Progress store

**Source:** `src/skilltrace/graph/state.py`
**File:** `graph/state.yaml`
**Schema:** Top-level key `progress:` mapping node IDs to entries.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `state` | string | yes | Closed enum |
| `changed_at` | string | no | ISO timestamp |
| `transitions` | dict | no | Maps state name to ISO timestamp |

**State enum:** `locked`, `available`, `active`, `passed`, `mastered`

**Two-state-kind separation:**
- **Derived (readiness):** `locked`, `available` -- written by sync, may move
  backward
- **Asserted (progress):** `active`, `passed`, `mastered` -- written by
  learner only, never moves backward

## ArtifactSpec

**Source:** `src/skilltrace/evidence/specs.py`
**Schema:** Closed

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Opaque curriculum string |
| `node_id` | string | yes | Valid node ID |
| `title` | string | yes | |
| `artifact_kind` | string | yes | Free-form (not enum-constrained) |
| `required` | boolean | yes | Must be a real bool |
| `minimum_count` | integer | yes | Must be >= 1; booleans rejected |
| `description` | string | no | |
| `expected_location_hint` | string | no | |
| `example_filename` | string | no | |
| `acceptance_summary` | string | no | |
| `created_at` | string | no | ISO timestamp |
| `updated_at` | string | no | ISO timestamp |

## ValidationGate

**Source:** `src/skilltrace/evidence/gates.py`
**Schema:** Closed

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | |
| `node_id` | string | yes | Valid node ID |
| `authority` | string | yes | Closed enum |
| `command` | string | no | Required if `objective`, forbidden if `manual` |
| `title` | string | no | |
| `description` | string | no | |
| `created_at` | string | no | |
| `updated_at` | string | no | |

**Authority enum:** `objective`, `manual`

**Cross-field constraint:** `authority == "objective"` requires `command` to
be a non-empty string. `authority == "manual"` requires `command` to be absent.
`ai` authority is unrepresentable by design.

## EvidenceRecord

**Source:** `src/skilltrace/evidence/records.py`
**Schema:** Closed; model is frozen (immutable)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Must match `ev.<node_id>.NNN` |
| `artifact_spec_id` | string | yes | Links to an ArtifactSpec |
| `location` | string | yes | |
| `accepted` | boolean | yes | |
| `accepted_by` | string | yes | Closed enum |
| `artifact_hash` | string | yes | |
| `note` | string | no | |
| `supersedes` | string | no | Both-or-neither with `supersede_reason` |
| `supersede_reason` | string | no | Both-or-neither with `supersedes` |
| `created_at` | string | yes | ISO timestamp |

**Accepted-by enum:** `objective_gate`, `learner_manual`

**ID format:** `ev.<node_id>.NNN` where `<node_id>` is valid and `NNN` is
ASCII digits.

## AssessmentAttempt

**Source:** `src/skilltrace/evidence/attempts.py`
**Schema:** Closed; model is frozen

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Must match `att.<node_id>.NNN` |
| `node_id` | string | yes | Must match node embedded in `id` |
| `outcome` | string | yes | Closed enum |
| `note` | string | no | |
| `created_at` | string | yes | |

**Outcome enum:** `passed`, `failed`

## LearningResource

**Source:** `src/skilltrace/resources/registry.py`
**Schema:** Closed

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Must match kebab-slug regex |
| `cost` | string | yes | Closed enum |
| `url` | string | no | At least one of `url`/`local_path` required |
| `local_path` | string | no | At least one of `url`/`local_path` required |
| `free_tier` | boolean | no | |
| `certificate` | boolean | no | |
| `license` | string | no | |
| `supports` | list[string] | no | Node IDs; empty is a validation warning |
| `last_verified` | string | no | ISO date; absent = unverified |
| `broken` | object | no | See sub-schema |

**Cost enum:** `free`, `paid`

**ID regex:** `[a-z0-9]+(?:-[a-z0-9]+)*` (fullmatch)

**Broken sub-schema (closed):**

| Field | Type | Required |
|-------|------|----------|
| `date` | string | yes |
| `reason` | string | yes |

## Session

**Source:** `src/skilltrace/execution/sessions.py`
**Schema:** Open

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | |
| `status` | string | yes | Closed enum |
| `started_at` | string | yes | |
| `ended_at` | string | no | |
| `template` | string | no | |

**Status enum:** `open`, `completed`

At most one session may be `open` at a time.

## SessionWork

**Source:** `src/skilltrace/execution/work.py`
**Schema:** Open

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | |
| `session_id` | string | yes | |
| `node_id` | string | yes | |
| `created_at` | string | yes | |
| `blocked` | boolean | no | Session-scoped observation; defaults to false |
| `notes` | string | no | |
| `minutes` | integer | no | |

## Blocker

**Source:** `src/skilltrace/execution/blockers.py`
**Schema:** Open

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | |
| `node_id` | string | yes | |
| `status` | string | yes | Closed enum |
| `description` | string | yes | |
| `created_at` | string | yes | |
| `resolved_at` | string | no | |
| `resolution_summary` | string | no | Required when resolving |

**Status enum:** `open`, `resolved`

## Review

**Source:** `src/skilltrace/execution/reviews.py`
**Schema:** Open

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | |
| `node_id` | string | yes | |
| `status` | string | yes | Closed enum |
| `scheduled_for` | string | yes | |
| `created_at` | string | yes | |
| `completed_at` | string | no | |
| `outcome` | string | no | Closed enum |
| `result_summary` | string | no | |
| `cancelled_at` | string | no | |
| `cancel_reason` | string | no | Required when cancelling |

**Status enum:** `scheduled`, `completed`, `cancelled`

**Outcome enum:** `satisfactory`, `unsatisfactory`

`overdue` is derived (scheduled + past date), never stored.

## RemediationAction

**Source:** `src/skilltrace/execution/remediation.py`
**Schema:** Open

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | |
| `node_id` | string | yes | |
| `status` | string | yes | Closed enum |
| `description` | string | yes | |
| `created_at` | string | yes | |
| `blocker_id` | string | no | Optional link to a Blocker |
| `completed_at` | string | no | |
| `result_summary` | string | no | |

**Status enum:** `open`, `completed`

## Policy files

**Source:** `src/skilltrace/policy/loading.py`

Seven YAML files loaded as opaque dicts. Shape-level validation only (file
exists, parses, top key is a mapping). No field-level schema enforced at
load time.

## ID format conventions

| Record type | Format | Example |
|-------------|--------|---------|
| SkillNode | `<segment>.<segment._NN>` | `math.algebra.linear_equations_01` |
| GraphEdge | Opaque curriculum string | `edge.algebra.order_01` |
| ArtifactSpec | Opaque curriculum string | `spec.python.functions_01` |
| ValidationGate | Opaque curriculum string | `gate.python.functions_01` |
| EvidenceRecord | `ev.<node_id>.NNN` | `ev.math.algebra.linear_equations_01.001` |
| AssessmentAttempt | `att.<node_id>.NNN` | `att.math.algebra.linear_equations_01.001` |
| LearningResource | Kebab slug | `python-official-tutorial` |
| Session | Free string | `ses.20260701` |
| SessionWork | Free string | `wrk.math.algebra.linear_equations_01.001` |
| Blocker | Free string | `blk.math.algebra.linear_equations_01.001` |
| Review | Free string | `rev.math.algebra.linear_equations_01.001` |
| RemediationAction | Free string | `rem.math.algebra.linear_equations_01.001` |

## Schema openness summary

| Schema | Closed? | Unknown-field behavior |
|--------|---------|----------------------|
| SkillNode | No | Unknown keys tolerated; only 4 forbidden keys rejected |
| GraphEdge | Yes | Hard load error |
| ProgressEntry | Partial | `state` enum enforced; unknown top-level keys rejected |
| ArtifactSpec | Yes | Hard load error |
| ValidationGate | Yes | Hard load error |
| EvidenceRecord | Yes | Hard load error |
| AssessmentAttempt | Yes | Hard load error |
| LearningResource | Yes | Hard load error |
| Session | No | Required fields + status enum checked |
| SessionWork | No | Required fields checked |
| Blocker | No | Required fields + status enum checked |
| Review | No | Required fields + status enum checked |
| RemediationAction | No | Required fields + status enum checked |
