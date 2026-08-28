# Release Notes

All releases and historical milestone records for SkillTrace. For future direction, see [`docs/POST_V1_ROADMAP.md`](POST_V1_ROADMAP.md).

---

## v1.5 (released)

Tier 2: FSRS retention analytics overlay. Introduces memory stability modeling and decay-aware review recommendations on top of passed curriculum nodes.

### Features
- **FSRS Retention Engine:** Implementation of Free Spaced Repetition Scheduler modeling to derive memory stability, review difficulty, and retention confidence on passed skills.
- **`skilltrace retention status`:** New CLI inspection surface reporting overall retention health, active memory stability, and recall confidence metrics.
- **Decay-Aware Review Suggestions:** `skilltrace suggest reviews` expanded to recommend review candidates prioritized by retention decay below target thresholds.
- **Disposable SQLite Analytics Table:** Adds `retention_confidence` table to `skilltrace export sqlite` for querying memory state.
- **Policy Seed Integration:** `policy/retention_model.yaml` defines default FSRS parameters ($w$ weights, retention targets, interval bounds).

### Decisions Recorded
- FSRS algorithm survey and parameter lock (#87).
- Advisory scheduling authority vs. writing scheduled reviews (#88).
- Review outcome rating semantics (#89).
- Retention state derived on demand vs. caching (#90).
- Surfaces and CLI integration (#91).

---

## v1.4 (released)

Tier 1: Web UI and Dashboard. Introduces a zero-dependency, stdlib-pure localhost web server and self-contained HTML export.

### Features
- **Localhost Web Dashboard (`skilltrace serve` / `st ui`):** Server-rendered, zero-JavaScript web interface on `http://127.0.0.1:8341`.
- **Daily Cockpit Views:** Browser views for Today dashboard (`/`), Recommendations (`/next`), Node detail (`/nodes/<id>`), and Health roll-up (`/health`).
- **Interactive State Mutations:** Start sessions, append work notes, and submit evidence directly from the browser.
- **Safe Confirmation Modals:** Explicit confirmation flows for `pass` and `master` actions, enforcing the exact same safety invariants as the CLI.
- **Static HTML Export (`skilltrace export html`):** Generates `data/export.html`, a single-file, disposable snapshot of progress, blockers, reviews, evidence, and resource health.

### Decisions Recorded
- Stdlib `ThreadingHTTPServer` architecture without external web framework dependencies (ADR 0006, #67).
- Tier 1 MVP boundary and daily loop focus (#64).
- Web mutation dispatch through unified command registry (#66).
- Disposable static HTML snapshot design (#68).
- UI token and card layout design (#76, #77, #80, #81).

---

## v1.0.0 (released)

The first stable release of SkillTrace as a local-first, CLI-first, single-learner skill graph engine.

### What's New Since v0.9.0-rc1
- Standardized documentation suite: `USER_GUIDE.md`, `RUNBOOK.md`, `SAFETY_BOUNDARIES.md`, `SCHEMA_REFERENCE.md`, `POST_V1_ROADMAP.md`.
- YAML and frontmatter schema freeze across all five engine layers.
- Production release validation manifest and automated exit-gate suite.
- Clean Windows-first, offline-capable installation lifecycle.

### Release Assets
Attached assets in the v1.0.0 GitHub release:
- `release/manifest.yaml` — release manifest
- `release/test_results.yaml` — test run summary
- `release/skilltrace-v1.0.0-release-assets.zip` — complete release artifacts

---

## v0.9.0-rc1

Daily-use polish and reports. The CLI becomes pleasant for everyday study.

### Features
- `skilltrace health` — roll-up of all five validate targets plus liveness warnings.
- `skilltrace today` — Mentor-voice daily study view: open session, due reviews, active blockers, top recommendation.
- `skilltrace node <node_id>` — Mentor-voice detail view joining curriculum, progress, evidence, resources, and execution for one node.
- `skilltrace report <target>` — unified report subcommand family (progress, blockers, reviews, evidence, resources).
- Enriched `skilltrace next` — Mentor-voice output with ranked candidates, contrastive briefs, and unlock paths.
- Command aliases: `st` (entry point), `submit` (evidence submit), `close` (session close).
- Stdlib-pure terminal rendering via `src/skilltrace/render.py`.

---

## v0.8.0-rc1

Foundations production seed graph — 81 nodes, 124 edges, 29 verified resources across math, programming, data, and tooling bands.

### What's Included
- Production-grade seed graph with evidence gates, resources, and review cadence for every node.
- Backfilled prior learning from Khan Academy (8 Algebra 1 nodes).
- Objective and manual evidence gates.
- Resource registry with 29 verified learning materials.
- Seed acceptance test suite.

---

## v0.7.0-rc1

Resource registry and verification workflow.

### Features
- `LearningResource` schema with provider, URL, cost, license, verification status, and replacement candidates.
- `skilltrace resources --node-id` — per-node reverse index.
- `skilltrace verify-resource` — record verification or broken status.
- `skilltrace resource-report` — whole-registry verification snapshot.
- Zero coupling: resource status never affects readiness or eligibility.

---

## v0.6.0-rc1

Policy engine — hard boundaries enforced, advisory policies warn.

### Features
- Hard boundaries: no AI-only pass, no AI-only mastery, no automatic deletion, no hard-prerequisite override.
- Advisory policies: workload, review cadence, remediation pressure, recommendation weights.
- `skilltrace master` — explicit learner mastery assertion.
- `skilltrace check-automation` — boundary verification.
- Mastery eligibility: passed + accepted evidence + spaced satisfactory review.

---

## v0.5.0-rc1

Execution workflow — sessions, work items, blockers, reviews, audit log.

### Features
- Sessions (open/completed, one at a time, start/end timestamps).
- Session work items (one node each, optional minutes).
- Blockers (explicit create/resolve, notes required).
- Remediation actions (ad-hoc intervention log).
- Reviews (schedule on passed/mastered, overdue derived).
- Audit-only event log (every mutating command appends one event).

---

## v0.4.0-rc1

Evidence core — progress becomes provable.

### Features
- `ArtifactSpec`, `ValidationGate`, `AssessmentAttempt`, `EvidenceRecord`.
- Evidence loader and validation.
- Acceptance authority: objective gate or learner manual review.
- Supersede model: records immutable, corrections via supersedes + reason.
- Pass eligibility (derived, computed on demand).
- `skilltrace pass` — explicit learner pass assertion.

---

## v0.3.0-rc1

Graph core and CLI package.

### Features
- Installable `skilltrace` package with console entry point.
- `SkillNode` model — pure curriculum, loader rejects state/prerequisites/unlocks/node_type in frontmatter.
- `GraphEdge` model — pruned schema with three edge types.
- Progress store `graph/state.yaml` — five-state enum.
- Node ID validation, duplicate detection, edge validation, cycle detection.
- Readiness sync and next-node recommendation v1.

---

## v0.2.0-rc1

Operating base — repo safe for iterative agent-assisted work.

### What's Included
- AGENTS.md, CONTEXT.md (ubiquitous language).
- PRD defining v1 as local-first CLI learning engine.
- ADRs 0001 and 0002.
- Issue tracker and milestone labels.

---

## v0.1.0-rc1

Scaffold baseline — the original generated release candidate. Historical reference only; superseded by v0.3+ decisions.
