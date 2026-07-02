# SkillTrace application roadmap

This is the **SkillTrace application roadmap**, not the 36-month AI study
curriculum itself. Version 1 ships a stable local-first learning engine that
can operate the early AI roadmap and expand safely; it does not try to ship a
full LMS, AI tutor, BKT engine, badge platform, or all 36 months of content
in one release. The AI Learning Roadmap contributes **seed data and default
policy values only** — the engine stays curriculum-agnostic.

Domain terms used below are defined in `CONTEXT.md` (the ubiquitous
language). Structural decisions are recorded in `docs/adr/`.

## Version 1 target

**SkillTrace v1.0** means: a local-first, CLI-first application that can
reliably answer —

- "What should I study next?"
- "Why that node?"
- "What evidence proves progress?"
- "What happens if I fail?"
- "What review or remediation is due?"
- "Can this node be passed or mastered safely?"

It includes real tested implementations for graph, evidence, execution,
policy, and release validation, SQLite export, and the first
production-quality seed graph for Phase 0–1. Roadmap anchors remain
`reference_only` metadata, and `passed` stays distinct from `mastered`.

## Governing design decisions

Settled 2026-07-02 (grilling session); see `CONTEXT.md` for definitions and
`docs/adr/` for rationale.

1. **Five node states** — `locked → available → active → passed → mastered`.
   Failure is never a node state; it lives on attempts and blockers.
2. **Derived vs. asserted** — `locked/available` are derived readiness,
   recomputable at any time; `active/passed/mastered` are asserted progress
   and never move backward. No sync or automated process writes asserted
   progress.
3. **Progress store** (ADR 0001) — node markdown files are pure curriculum;
   all learner state lives in `graph/state.yaml`. The loader rejects
   `state`, `prerequisites`, `unlocks`, and `node_type` in frontmatter.
4. **edges.yaml is the sole source of truth for relationships.** Edge schema
   is pruned to `id, source, target, edge_type, reason, active` (+
   timestamps); `strength`, `can_override`, and `activation_rule` are
   deleted — semantics live in the edge type.
5. **Three edge types** — `hard_prerequisite` (locks), `soft_prerequisite`
   (warns only), `remediation` (advisory pressure: activates on an open
   blocker or a policy-configured number of failed attempts; never locks the
   target; deactivates on pass or resolution).
6. **Two policy classes** — hard boundaries (automation of pass/master/
   delete and hard-prerequisite override: commands refuse, non-zero exit)
   and advisory policies (workload, cadence, remediation pressure: warn and
   reorder recommendations, never block a human action).
7. **Eligibility vs. assertion** — pass/mastery eligibility are derived
   facts, computed on demand; passing and mastering are explicit learner
   commands that refuse unless eligibility holds. A green gate never passes
   a node by itself.
8. **Mastery is permanent in v1** — requires a satisfactory post-pass review
   on a different day (spacing is a policy value); no decay, no demotion.
9. **Supersede model** — evidence records are never edited or deleted;
   corrections are new records with `supersedes` + reason. A pass already
   asserted stands; discrepancies surface as advisory warnings.
10. **Event log is audit-only** — every mutating command appends one event;
    events are never read back to compute state.
11. **Interface layer is cut from v1** (ADR 0002) — five layers: graph,
    evidence, execution, policy, release.
12. **Files are truth** — Markdown/YAML are the only source of truth;
    SQLite/Markdown exports and backups are disposable derived artifacts,
    never read back by the engine. `data/*.db` is gitignored.
13. **One CLI from v0.3** — a single installable `skilltrace` package and
    entry point with subcommands; the scaffold's `python -m compiler.*`
    modules are throwaway reference.
14. **Node IDs are immutable and never reused** — the numeric suffix is a
    sequence, not a version. Material redefinition of a skill is a new node;
    old history remains true.
15. **Sessions contain work items** — one session open at a time; each work
    item ties to one node, so interleaving is first-class. Starting work is
    what marks a node `active`.
16. **Reviews are scheduled retention checks** — auto-scheduled on pass
    (allowed automation: bookkeeping, not judgment); overdue reviews warn,
    never block.
17. **Resources are pure advice** — zero coupling to node state. "Verified"
    is a dated human assertion; staleness is derived against a policy
    window.
18. **Tracks are opaque labels** — priorities are seed policy values; no
    engine mechanic keys off a track name. `node_type` is dropped until a
    mechanic needs it.
19. **Engine/curriculum split** — protocols from the AI Learning Roadmap
    (3-attempt threshold, cadences, session presets, track priorities) enter
    only as seed policy values.
20. **Single-learner by design** — one repo is one learner; no user fields.
    A second learner forks the curriculum without the progress store.

## Release-candidate roadmap

| RC | Timeline | Purpose | Definition of done |
| --- | --- | --- | --- |
| **v0.1.0-rc1** | Complete | Scaffold baseline | Generated scaffold exists (historical; includes an interface layer since cut by ADR 0002). |
| **v0.2.0-rc1** | Weeks 1–2 | Operating base | `CLAUDE.md`, `CONTEXT.md`, PRD, ADRs, issues, first milestone plan. |
| **v0.3.0-rc1** | Weeks 3–4 | Graph core + CLI package | Installable `skilltrace` CLI; loaders, progress store, validation, cycle detection, readiness sync, next-node v1. |
| **v0.4.0-rc1** | Weeks 5–6 | Evidence core | Artifact specs, gates, attempts, evidence records, supersede model, pass eligibility, explicit pass command. |
| **v0.5.0-rc1** | Weeks 7–8 | Execution workflow | Sessions, work items, blockers, remediation, reviews, audit event log, mutation commands. |
| **v0.6.0-rc1** | Weeks 9–10 | Policy engine | Hard boundaries enforced; advisory policies warn; mastery eligibility and explicit master command. |
| **v0.7.0-rc1** | Weeks 11–12 | Resource registry | Resource schema, verification workflow, replacement candidates, resource report. |
| **v0.8.0-rc1** | Weeks 13–14 | Phase 0–1 seed graph | 60–90 production nodes with gates, resources, review cadence. |
| **v0.9.0-rc1** | Weeks 15–16 | Daily-use polish | Readable output, today/home views, reports, Markdown/SQLite export, backup. |
| **v1.0.0-rc1** | Weeks 17–18 | Release hardening | Schema freeze, fixtures, docs, install/Windows pass, known limitations. |
| **v1.0.0 final** | Weeks 19–20 | Stable release | Blocker fixes only; tag, freeze schema v1, publish docs, open post-v1 backlog. |

## v0.1.0-rc1 — Scaffold baseline

Status: complete (historical).

The generated release candidate containing the original six conceptual
layers, compiler stubs, release tests, and seed data. It is architectural
reference only — do not build features on its assumptions. Decisions 3, 4,
11, 13, and 18 deliberately depart from it: the interface layer is cut, the
`compiler` package is throwaway, and its node frontmatter / edge schemas are
superseded.

## v0.2.0-rc1 — Operating base

Purpose: make the repo safe for iterative agent-assisted work (Claude Code).

Deliverables:

- `CLAUDE.md`
- `CONTEXT.md` — ubiquitous language *(created 2026-07-02, maintained continuously)*
- `docs/PRD.md` — defines v1 as a local-first CLI learning engine, not an LMS
- `docs/adr/` — ADR 0001 and 0002 exist; new ADRs as decisions warrant
- `issues/` + milestone labels + first issue batch
- repo conventions and test command policy
- the "no automated pass/master/delete" rule stated in every relevant doc

Exit gate: an agent can open the repo, read the governing documents,
understand the domain terms, and implement one issue without re-deriving the
architecture.

## v0.3.0-rc1 — Graph core and CLI package

Purpose: replace scaffold graph logic with a real, tested implementation
behind the final interface.

Scope:

- installable `skilltrace` package (`pyproject.toml`, console entry point,
  subcommand dispatcher that owns event logging and automation checks)
- `SkillNode` model — pure curriculum; loader **rejects** `state`,
  `prerequisites`, `unlocks`, `node_type` in frontmatter
- `GraphEdge` model — pruned schema (`id, source, target, edge_type, reason,
  active` + timestamps); unknown edge types fail validation
- progress store `graph/state.yaml` — five-state enum validated; sync may
  write only derived readiness, never asserted progress
- node ID validation, duplicate detection, edge endpoint validation,
  dangling-reference check (progress/evidence referencing missing node IDs)
- hard-prerequisite cycle detection
- readiness sync and next-node recommendation v1

CLI:

```bash
skilltrace validate graph
skilltrace sync
skilltrace next --minutes 60 --limit 5 --show-locked
```

Tests:

- valid seed graph passes; duplicate node ID fails; missing edge
  source/target fails; hard-prerequisite cycle fails
- frontmatter containing `state`/`prerequisites`/`unlocks` fails loading
- sync never writes `active`/`passed`/`mastered`
- adding a hard prerequisite re-locks an un-started node but never an
  active/passed/mastered one
- locked node is never recommended as available
- roadmap anchor never controls locking

Exit gate:

```bash
pytest tests/graph
skilltrace validate graph
skilltrace next --minutes 60 --limit 5 --show-locked
```

## v0.4.0-rc1 — Evidence core

Purpose: make progress provable.

Scope:

- `ArtifactSpec`, `ValidationGate`, `AssessmentAttempt`, `EvidenceRecord`
- evidence loader and validation
- acceptance authority: objective gate (command exits 0) or learner manual
  review; AI review is advisory commentary only, never authority
- supersede model: records immutable; corrections via `supersedes` + reason;
  superseded records excluded from eligibility
- pass eligibility (derived, computed on demand)
- explicit `skilltrace pass` — refuses without eligibility; schedules the
  first review (see v0.5/v0.6)

CLI:

```bash
skilltrace validate evidence
skilltrace evidence submit <node_id> ...
skilltrace attempt record <node_id> ...
skilltrace eligibility <node_id>
skilltrace pass <node_id>
```

Tests:

- missing node/gate reference fails
- AI-advisory gate cannot close a node; accepted evidence requires non-AI
  authority
- green objective gate alone never flips node state
- `pass` refuses without eligibility; succeeds with it; appends event
- superseding accepted evidence removes eligibility but never revokes an
  asserted pass (warning surfaced instead)
- evidence records cannot be edited or deleted by any command

Exit gate:

```bash
pytest tests/evidence
skilltrace validate evidence
skilltrace eligibility math.arithmetic.order_operations_01
```

## v0.5.0-rc1 — Execution workflow

Purpose: make the application usable during real study sessions.

Scope:

- sessions (one open at a time; completed requires start/end timestamps;
  stale open session warns)
- session work items (one node each; interleaving = many items per session;
  starting work marks the node `active`)
- session templates (micro/standard/deep) as seed presets
- blockers, remediation actions, review items
- audit-only event log: every mutating command appends one event; events are
  never read back

CLI:

```bash
skilltrace start <node_id>
skilltrace work <node_id> ...
skilltrace session close
skilltrace blocker create <node_id> ...
skilltrace blocker resolve <blocker_id> ...
skilltrace remediation create ...
skilltrace review schedule <node_id> ...
skilltrace blockers
skilltrace reviews
skilltrace validate execution
```

Tests:

- planned session validates; completed session requires timestamps
- second concurrent session refused; stale open session warns
- blocked work requires notes; resolved blocker requires resolution summary
- completed remediation/review requires result summary
- every mutating command appends exactly one event; read-only commands
  append none
- execution references valid graph/evidence IDs

Exit gate:

```bash
pytest tests/execution
skilltrace validate execution
skilltrace blockers
skilltrace reviews
```

## v0.6.0-rc1 — Policy engine

Purpose: enforce the safety rules and encode the advisory ones.

Scope:

- hard boundaries (refuse, non-zero exit): no AI-only pass, no AI-only or
  automatic mastery, no automatic deletion, no hard-prerequisite override
- advisory policies (warn/reorder only): workload, review cadence,
  remediation pressure, recommendation weights
- remediation policy: activation threshold (e.g. 3 failed attempts) is a
  **seed value**, not an engine constant
- track priorities as a weight map in `policy/recommendation.yaml`; unmapped
  track = weight 0 + warning
- mastery eligibility (passed + satisfactory post-pass review on a different
  day; spacing is a policy value) and explicit `skilltrace master`
- review auto-scheduling on pass per cadence policy (allowed automation)
- policy-adjusted recommendation reasons

CLI:

```bash
skilltrace validate policy
skilltrace check-automation pass_node
skilltrace check-automation master_node
skilltrace check-automation delete_record
skilltrace eligibility <node_id> --mastery
skilltrace master <node_id>
skilltrace suggest remediation
skilltrace suggest reviews
```

Tests:

- `pass_node`/`master_node`/`delete_record` automation forbidden
- `master` refuses without: passed state, accepted evidence, satisfactory
  post-pass review, day-spacing satisfied
- mastered state is never demoted by any command or sync
- advisory violations (workload exceeded, overdue reviews, high remediation
  backlog) warn but never block a human command
- remediation edge activates on blocker / threshold attempts; deactivates on
  pass or resolution; never locks its target
- recommendation output explains policy effects

Exit gate:

```bash
pytest tests/policy
skilltrace validate policy
skilltrace check-automation pass_node
skilltrace check-automation master_node
skilltrace check-automation delete_record
```

## v0.7.0-rc1 — Resource registry and verification workflow

Purpose: separate stable app logic from volatile online-resource assumptions.

Scope:

- `LearningResource`: provider, URL, local fallback path, cost status,
  license, free/certification flags, `last_verified`, verification status,
  replacement candidates, resource-to-node linking
- zero coupling: resource status never affects readiness, eligibility, or
  state — problems are warnings in health/resource reports only
- "verified" = dated human assertion (URL resolves, claims hold); staleness
  derived against a policy window; no web checks in v1 (backlog v1.1)
- verification report

CLI:

```bash
skilltrace validate resources
skilltrace resources --node-id <node_id>
skilltrace verify-resource <resource_id>
skilltrace resource-report
```

Tests:

- every resource has a URL or local path; missing node reference fails
- unverified resources are allowed but warned; stale `last_verified` warns
- a dead resource never changes node readiness or blocks pass/mastery
- paid resource cannot be marked free; replacement resources validate

Exit gate:

```bash
pytest tests/resources
skilltrace validate resources
skilltrace resource-report
```

## v0.8.0-rc1 — Phase 0–1 production seed graph

Purpose: make SkillTrace usable for the first year of the AI learning
roadmap. This RC is **seed data**, not engine work.

Scope:

- 60–90 production-grade nodes
- Phase 0: arithmetic review, algebra, functions, statistics, calculus
  intuition, linear algebra
- Phase 1: Python, CLI, Git, SQL, CSV, Pandas, visualization, README writing
- first portfolio nodes, consolidation nodes (a track with seed priority,
  not an engine concept), remediation nodes with remediation edges
- resource registry entries; evidence gates for every node; review cadence
  values
- web verification of resources before they become seeded production data

Representative graph bands:

```text
math.arithmetic.*        math.algebra.*         math.functions.*
math.statistics.*        math.calculus_intuition.*  math.linear_algebra.*
programming.python.*     tooling.cli.*          tooling.git.*
data.sql.*               data.csv.*             data.pandas.*
communication.readme.*   portfolio.phase1.*     consolidation.*
```

Exit gate:

```bash
pytest
skilltrace validate graph
skilltrace validate evidence
skilltrace validate resources
skilltrace next --minutes 60 --limit 5 --show-locked
```

Acceptance standard: every available/locked/active node has a clear reason,
evidence gate, resource path, and next action.

## v0.9.0-rc1 — Daily-use polish and reports

Purpose: make SkillTrace pleasant enough to use every study day. (The CLI
package and command surface exist since v0.3 — this RC is output quality,
reports, and export.)

Scope:

- readable terminal output and command aliases
- daily home view (`today`): open session, due reviews, active blockers,
  top recommendations
- next-node explanation view; node detail view (joins curriculum + progress
  + evidence + resources)
- blocker / review / evidence / progress reports
- Markdown export, SQLite export (disposable; `data/*.db` gitignored),
  timestamped backup

CLI:

```bash
skilltrace health
skilltrace today
skilltrace next --minutes 60
skilltrace node <node_id>
skilltrace export sqlite
skilltrace export markdown
skilltrace backup
```

Tests:

- every read-only command exits 0 on seed data
- every mutating command requires explicit arguments
- no command silently passes or masters a node
- Markdown export contains graph/evidence/session summary
- SQLite export contains graph, edges, evidence, execution, policy,
  resources — and no engine code path reads it back
- backup creates a timestamped archive

Exit gate:

```bash
pytest
skilltrace health
skilltrace today
skilltrace next --minutes 60
skilltrace node math.arithmetic.order_operations_01
skilltrace export markdown
skilltrace backup
```

## v1.0.0-rc1 — Release hardening

Purpose: freeze the Version 1 candidate.

Scope:

- schema freeze — the **YAML/frontmatter** schemas; SQLite has no
  migrations (regenerate instead)
- migration scripts for pre-freeze YAML changes; test fixtures
- docs pass, install pass, Windows pass, clean repo structure
- release notes, troubleshooting guide, known limitations (including
  single-learner by design), post-v1 backlog

Docs required:

```text
README.md            CLAUDE.md              CONTEXT.md
docs/INSTALL.md      docs/RUNBOOK.md        docs/USER_GUIDE.md
docs/DEVELOPER_GUIDE.md  docs/RELEASE_NOTES.md
docs/SAFETY_BOUNDARIES.md  docs/POST_V1_BACKLOG.md
docs/adr/
```

Release tests:

```bash
pytest
skilltrace health
skilltrace today
skilltrace next --minutes 60
skilltrace node math.arithmetic.order_operations_01
skilltrace check-automation pass_node
skilltrace check-automation master_node
skilltrace check-automation delete_record
skilltrace export sqlite
skilltrace backup
```

v1.0.0-rc1 is accepted only if a fresh clone can install, validate,
recommend, start a session, record work, submit evidence, check pass
eligibility, schedule review, export data, and enforce automation boundaries
without internet access.

## v1.0.0 final — Stable v1

Purpose: tag the first stable product release. Only blocker fixes after
v1.0.0-rc1; no new features.

Final acceptance criteria:

- all tests and smoke tests pass
- seed graph, evidence, resources, policy, and release metadata validate
- install docs, daily workflow, and backup/restore tested
- no hidden AI-only grading path; no automated pass/master/delete path
- asserted progress is never moved backward by any code path
- exports are never read back by the engine
- roadmap anchors remain `reference_only`

Tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Post-v1 backlog

These do not block v1.

- **v1.1** — resource web-verification automation and stale-resource
  replacement suggestions
- **v1.2** — Phase 2 ML seed graph (Google ML Crash Course, Andrew Ng, ISLR,
  Kaggle, FastAPI, Docker)
- **v1.3** — Phase 3 LLM/agents/MCP seed graph
- **v1.4** — optional local dashboard or static HTML report; its view model
  is designed fresh from real usage (ADR 0002), not from the cut scaffold
  interface layer
- **v1.5** — analytics v1: study velocity, blockers by domain, review
  completion, evidence coverage (mine the event log)
- **v1.6** — portfolio builder and GitHub project report
- **v2.0** — adaptive sequencing beyond rule-based recommendations;
  retention/confidence modeling as a derived overlay (mastery state remains
  permanent)

The framework document's advanced ideas — diagnostic analytics, Elo/BKT-style
mastery modeling, adaptive sequencing, badge issuance, generative AI
tutoring — belong after the stable v1 engine, not before it.
