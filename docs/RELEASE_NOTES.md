# Release Notes

## v1.0.0 (released)

Release candidate for the first stable release. See
[POST_V1_BACKLOG.md](POST_V1_BACKLOG.md) for deferred work.

### What's new since v0.9.0-rc1

- Rewritten INSTALL.md and RUNBOOK.md for current CLI.
- New docs: USER_GUIDE.md, SAFETY_BOUNDARIES.md, POST_V1_BACKLOG.md.
- Version bumped to 1.0.0.

### Release hardening (in progress)

- YAML/frontmatter schema freeze.
- Migration scripts for pre-freeze changes.
- Clean-install-from-fresh-clone-on-Windows pass.
- Clean repo structure.
- Schema reference documentation.

### Release assets

Attached assets in the v1.0.0 GitHub release:

- release/manifest.yaml — release manifest
- release/test_results.yaml — test run summary
- release/skilltrace-v1.0.0-release-assets.zip — complete release artifacts (tests, smoke outputs, manifests)

These assets are attached to the release: https://github.com/earledotpy/skilltrace/releases/tag/v1.0.0


## v0.9.0-rc1

Daily-use polish and reports. The CLI becomes pleasant for everyday study.

### Features

- `skilltrace health` -- roll-up of all five validate targets plus liveness
  warnings, closing with one verdict line.
- `skilltrace today` -- Mentor-voice daily study view: open session, due
  reviews, active blockers, top recommendation.
- `skilltrace node <node_id>` -- Mentor-voice detail view joining curriculum,
  progress, evidence, resources, and execution for one node.
- `skilltrace report <target>` -- unified report subcommand family (progress,
  blockers, reviews, evidence, resources) with Mentor voice.
- Enriched `skilltrace next` -- Mentor-voice output with ranked candidates,
  contrastive briefs, Where to learn, How to proceed, Do this next.
- Command aliases: `st` (entry point), `submit` (evidence submit), `close`
  (session close).
- Stdlib-pure rendering via `src/skilltrace/render.py` (no rich, no ANSI).

### Decisions recorded

- Terminal rendering approach and command aliases (#32).
- Health command scope (#34).
- Output design: today, next, node detail (#30).
- Reports design: blocker, review, evidence, progress (#31).
- Post-v1 development model (#36).
- Prior learning recording: replace cover-sheet backfill (#40).

## v0.8.0-rc1

Foundations production seed graph -- 81 nodes, 124 edges, 29 verified
resources across math, programming, data, and tooling bands.

### What's included

- Production-grade seed graph with evidence gates, resources, and review
  cadence for every node.
- Backfilled prior learning from Khan Academy (8 Algebra 1 nodes).
- Objective and manual evidence gates.
- Resource registry with 29 verified learning materials.
- Seed acceptance test suite.

### Decisions recorded

- Represent prior learning: how backfilled evidence is recorded (#27).
- Backfill prior learning onto the seed graph (#28).
- Friction log: amend the v0.9 baseline from real use (#29).

## v0.7.0-rc1

Resource registry and verification workflow.

### Features

- `LearningResource` schema with provider, URL, cost, license, verification
  status, and replacement candidates.
- `skilltrace resources --node-id` -- per-node reverse index.
- `skilltrace verify-resource` -- record verification or broken status.
- `skilltrace resource-report` -- whole-registry verification snapshot.
- Zero coupling: resource status never affects readiness or eligibility.

## v0.6.0-rc1

Policy engine -- hard boundaries enforced, advisory policies warn.

### Features

- Hard boundaries: no AI-only pass, no AI-only mastery, no automatic
  deletion, no hard-prerequisite override.
- Advisory policies: workload, review cadence, remediation pressure,
  recommendation weights.
- `skilltrace master` -- explicit learner mastery assertion.
- `skilltrace check-automation` -- boundary verification.
- Mastery eligibility: passed + accepted evidence + spaced satisfactory
  review.

## v0.5.0-rc1

Execution workflow -- sessions, work items, blockers, reviews, audit log.

### Features

- Sessions (open/completed, one at a time, start/end timestamps).
- Session work items (one node each, optional minutes).
- Blockers (explicit create/resolve, notes required).
- Remediation actions (ad-hoc intervention log).
- Reviews (schedule on passed/mastered, overdue derived).
- Audit-only event log (every mutating command appends one event).

## v0.4.0-rc1

Evidence core -- progress becomes provable.

### Features

- `ArtifactSpec`, `ValidationGate`, `AssessmentAttempt`, `EvidenceRecord`.
- Evidence loader and validation.
- Acceptance authority: objective gate or learner manual review.
- Supersede model: records immutable, corrections via supersedes + reason.
- Pass eligibility (derived, computed on demand).
- `skilltrace pass` -- explicit learner pass assertion.

## v0.3.0-rc1

Graph core and CLI package.

### Features

- Installable `skilltrace` package with console entry point.
- `SkillNode` model -- pure curriculum, loader rejects state/prerequisites/
  unlocks/node_type in frontmatter.
- `GraphEdge` model -- pruned schema with three edge types.
- Progress store `graph/state.yaml` -- five-state enum.
- Node ID validation, duplicate detection, edge validation, cycle detection.
- Readiness sync and next-node recommendation v1.

## v0.2.0-rc1

Operating base -- repo safe for iterative agent-assisted work.

### What's included

- AGENTS.md, CONTEXT.md (ubiquitous language).
- PRD defining v1 as local-first CLI learning engine.
- ADRs 0001 and 0002.
- Issue tracker and milestone labels.

## v0.1.0-rc1

Scaffold baseline -- the original generated release candidate. Historical
reference only; superseded by v0.3+ decisions.
