# Release Notes

All releases and historical milestone records for SkillTrace. For future direction, see [`docs/POST_V1_ROADMAP.md`](POST_V1_ROADMAP.md) (shipped v1.6–v2.0) and [`docs/POST_V2_ROADMAP.md`](POST_V2_ROADMAP.md) (shipped v2.1; next slots v2.2–v2.4).

---

## v2.2.0 (released)

Provenance & graph-impact diagnostics (R-Provenance #194). Advisory-only throughout: gate-run receipts record how an objective gate ran, and the `graph impact` diagnostic reports what a curriculum edit would change — neither ever flips or blocks. Verified on the merged tree: full test suite green, v2.2 §7 functional gates exit 0 on seed, safety + doc gates green.

### Features
- **Gate-run receipts:** objective-gate evidence records gain an optional immutable `gate_run` borrowing the executed argv, root-relative input files, exit class (`passed`/`failed`), optional exit code, and `sha256:` output hashes — raw gate output is never stored. Unrunnable gates write no record, no receipt, no event; manual-gate records never carry one; a receipt never changes eligibility or readiness.
- **`graph impact` (read-only):** advisory comparison of the working tree against a git-ref baseline (or `--baseline <path>` second checkout), reporting readiness flips on non-asserted nodes, asserted progress that stands against a baseline-edge edit, recommendation-list changes under identical store/weights, dangling references, and no-op edges. Appends no audit event and exits 0 whenever it can compute.
- **Redaction:** receipt `command_argv`/`inputs` are classified under the existing portfolio **paths** dimension (default-deny, `--include-paths` overrides per export).

### Decisions Recorded
- v2.2 spec written to the hand-off gate with all D-* decisions filled; see [`docs/spec-v2.2-provenance-impact.md`](spec-v2.2-provenance-impact.md).
- D-Flip: asserted progress is reported as standing, never revoked; the diagnostic reads relationships only from `edges.yaml` and never blocks a human action.

---

## v2.1.0 (released)

Adaptive sequencing + retention overlay (FSRS), carried fixed from the POST_V1 roadmap. Advisory-only throughout: the retention overlay reorders recommendations and names fading prerequisites; it never gates, blocks, or flips learner state. Verified on the merged tree: full test suite green, v2.1 §7 functional gates exit 0 on seed, safety + doc gates green.

### Features
- **Retention-urgency sequencing:** `next` and `today` boost candidates whose active hard-prerequisite sources are fading below the retention threshold, with a named reason clause on each card.
- **Agent signal (advisory):** recommendations can carry an agent boost sourced from `data/agent_recommendations.yaml`; a missing file is silent, malformed entries are warn-and-ignore, and the engine never writes the file — AI input stays non-authoritative.
- **Delay-aware retention model:** per-node half-life from review history with early/on-time/late × satisfactory/unsatisfactory multipliers, per-node base scales (domain, evidence gaps, velocity), and half-life clamps (policy seeds `policy.recommendation.default_v0_7` + `policy.retention.default_v1_0`).
- **`suggest reviews` retention section:** derived below-threshold suggestions under the calendar-due list, with a count-based warning line; calendar ordering is never reordered by retention pressure.
- **`retention status --node-id`:** filter the derived memory-state report to a single node.
- **Policy validation:** `validate policy` enforces the new seed value ranges, requires `retention_urgency`, and rejects the retired `review_due` dormant weight.

### Decisions Recorded
- v2.1 spec written to the hand-off gate with all formula stubs filled (T-Personalization, T-Weights, T-AgentInput, T-Rendering, T-Storage-guard); see [`docs/spec-v2.1-adaptive-sequencing.md`](spec-v2.1-adaptive-sequencing.md).
- D-Weights: no dormant factor weight survives; `review_due` is superseded by `retention_urgency`.

---

## v2.0.0 (released)

Portfolio builder plus the full post-v1 slot sequence (v1.6–v1.9). Verified on the merged tree: 100 SkillNodes / 157 GraphEdges (all active) / 45 LearningResources, full test suite green, all per-slot exit gates green, hard boundaries intact.

### Features
- **v1.6 — Event-log analytics:** study velocity, blockers by domain, review completion, evidence coverage themes with rolling windows, Serve dashboard, and advisory-only pressure surfacing in `today`.
- **v1.7 — Resource web-verification:** automated reachability checks with descriptive-only broken markers, stale-resource replacement, and warning-only retired-resource handling.
- **v1.8 — Phase 2 ML seed graph:** four verified classical-ML sources plus the house-prices Capstone integration node.
- **v1.9 — Phase 3 agent seed graph:** nine verified LLM/agent/MCP sources, a FastAPI + container-engine deployment primer, and the deployed-agent Capstone integration node.
- **v2.0 — Portfolio builder:** default-deny Share profile with per-invocation redaction overrides, trigger-naming Honesty banners, preview/export sharing one pipeline, and a disposable bundle layout (Markdown index, HTML preview, JSON contract, manifest).
- **Contract repairs:** disambiguated Portfolio bundle manifest vs. JSON contract names, single analytics state-filter field, Portfolio JSON shape matching the implementation, registry path corrected to the graph-side registry.
- **Architecture ruling:** the cut interface layer stays cut (docs-only background, no engine read path).

### Decisions Recorded
- v2.0 readiness remediation spec and ticket order (#183–#190).
- Interface-layer cut stands; any future revival needs its own hard-to-reverse decision record.

### Release Assets
Attached assets in the v2.0.0 GitHub release:
- `release/manifest.yaml` — release manifest
- `release/test_results.yaml` — test run summary
- `release/skilltrace-v2.0.0-release-assets.zip` — complete release artifacts

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
