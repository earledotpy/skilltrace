# AGENTS.md — SkillTrace

SkillTrace is a local-first, CLI-first, single-learner learning engine: a
skill graph with evidence-gated progress. It operates a personal AI-study
curriculum but the engine is curriculum-agnostic — curriculum protocols
enter only as seed data and policy values, never as engine code.

## Read first

- `CONTEXT.md` — the ubiquitous language. Use these terms exactly; do not
  invent synonyms for states, eligibility, authorities, or record types.
- `docs/POST_V2_ROADMAP.md` — active slot sequence (signposting, not spec)
  plus the slot's `docs/spec-<slot>.md`.
- `docs/skilltrace-application-roadmap.md` — frozen v1 history only.
- `docs/adr/` — structural rationale (0001 progress store; 0002 superseded by
  0007 interface sublayer; 0006 stdlib serve; 0008 JS posture; 0009 web views
  package + facade).

## Safety rules (hard boundaries — never violate, never work around)

- **Never automate `pass_node`, `master_node`, or `delete_record`.** Passing
  and mastering are explicit learner commands; nothing else flips those
  states. No CLI command, test helper, or migration may do it implicitly.
- **AI review is never an acceptance authority.** It may attach advisory
  commentary to evidence only.
- **Asserted progress (`active`/`passed`/`mastered`) never moves backward.**
  No sync, edit, or command demotes it.
- **No hard-prerequisite override.**
- Evidence records are immutable: corrections supersede, never edit/delete.
- Advisory policies (workload, cadence, remediation pressure) warn and
  reorder recommendations; they never block a human-initiated action.

## Invariants to preserve in code

- `graph/edges.yaml` is the sole source of truth for node relationships.
  Node frontmatter must not contain `state`, `prerequisites`, `unlocks`, or
  `node_type` (loader rejects).
- Learner state lives in the progress store (`graph/state.yaml`), never in
  curriculum files (ADR 0001). Sync writes only derived readiness
  (`locked`/`available`).
- Eligibility (pass/mastery) is derived on demand, never stored as truth.
- Markdown/YAML files are the only source of truth; SQLite/Markdown exports
  and backups are disposable and never read back by the engine.
- The event log is audit-only: every mutating command appends one event;
  events are never read to compute state.
- Node IDs are immutable and never reused; the numeric suffix is a sequence,
  not a version.
- Five engine layers: graph, evidence, execution, policy, release
  (`criterion.layers.present` stays 5). Plus one web-only interface sublayer
  in `src/skilltrace/web/interface/` (ADR 0007: web reads engine, never the
  reverse). Do not promote it to an engine layer, add release criteria for
  it, or restore `archive/scaffold-v0.1/interface/` YAMLs without a new ADR.
  JS posture: tier-0 default, tier-1 tooltip-only grant per ADR 0008.
- Roadmap anchors are `reference_only` and never control locking or
  recommendation.

## Repo layout

- `graph/` — node markdown (curriculum) + `edges.yaml` + `resources.yaml`
  (the LearningResource registry) + progress store
- `evidence/` — artifact specs, gates, attempts, evidence records
- `execution/` — sessions, work, blockers, remediation, reviews, event log
- `policy/` — hard-boundary and advisory policy values (seed data)
- `release/` — release manifest, tests, criteria
- `src/skilltrace/` — installable CLI+web engine (dispatcher registry;
  web-only sublayer at `web/interface/`; mentor/advisory seam). The v0.1
  `compiler/` scaffold it replaced was retired in v0.4; its interface-layer
  history lives in ADR 0002 and the roadmap.
- `docs/` — roadmap, ADRs, framework references (background reading)
- `archive/scaffold-v0.1/` — read-only scaffold history (`interface/`, `generation_manifest.json`, `web-app-vision/`, `templates/`, `examples/`, `schemas/`, `research/`, `issues/`) per ADR 0005; never read by the engine — see `archive/scaffold-v0.1/README.md`



## Agent skills

### Issue tracker

Issues are tracked on GitHub using the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles map to label strings `needs-triage`,
`needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See
`docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: one `CONTEXT.md` at the repo root plus `docs/adr`.
See `docs/agents/domain.md`.

### Fixture clock

Simulated-day/fixture runs inject `Context.clock` through
`cli.run(..., clock=)` so the engine dates the records it writes — not the
wall clock. Coverage, and what stays wall-clock, is listed in
`docs/agents/fixture-clock.md`.

## Working conventions

- Active direction: `docs/POST_V2_ROADMAP.md` slot table + linked
  `docs/spec-<slot>.md`. Last shipped: see `docs/RELEASE_NOTES.md` top entry
  (no version number cached here). Follow the slot sequence.
- Tests: `pytest` (per-layer suites under `tests/<layer>`). Every slot's spec
  §7 + safety/doc gates must pass on the merged tree.
- When a domain term is added or changed, update `CONTEXT.md` in the same
  change. Glossary only — no implementation details there.
- Offer an ADR only for hard-to-reverse, surprising, genuine-trade-off
  decisions.
