# CLAUDE.md — SkillTrace

SkillTrace is a local-first, CLI-first, single-learner learning engine: a
skill graph with evidence-gated progress. It operates a personal AI-study
curriculum but the engine is curriculum-agnostic — curriculum protocols
enter only as seed data and policy values, never as engine code.

## Read first

- `CONTEXT.md` — the ubiquitous language. Use these terms exactly; do not
  invent synonyms for states, eligibility, authorities, or record types.
- `docs/skilltrace-application-roadmap.md` — v1 scope, the twenty governing
  design decisions, and the per-RC plan with exit gates.
- `docs/adr/` — rationale for structural decisions (progress store,
  interface layer cut).

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
  `node_type` (target schema; scaffold files predating this are being
  migrated in v0.3).
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
- v1 has five layers: graph, evidence, execution, policy, release. The
  scaffold's interface layer is cut (ADR 0002) — do not extend it.
- Roadmap anchors are `reference_only` and never control locking or
  recommendation.

## Repo layout

- `graph/` — node markdown (curriculum) + `edges.yaml` + `resources.yaml`
  (the LearningResource registry) + progress store
- `evidence/` — artifact specs, gates, attempts, evidence records
- `execution/` — sessions, work, blockers, remediation, reviews, event log
- `policy/` — hard-boundary and advisory policy values (seed data)
- `release/` — release manifest, tests, criteria
- `src/skilltrace/` — the installable `skilltrace` CLI package (subcommands).
  The v0.1 `compiler/` scaffold it replaced was retired in v0.4; its
  interface-layer history lives in ADR 0002 and the roadmap.
- `docs/` — roadmap, ADRs, framework references (background reading)

## Working conventions

- Current phase: v0.6.0-rc1 complete (policy engine); graph, evidence, and
  execution cores also complete. v0.7 (resource registry and verification
  workflow) is next — follow the roadmap's RC scope and don't build ahead
  of it.
- Tests: `pytest` (per-layer suites under `tests/<layer>` as RCs land).
  Every RC's exit-gate commands must pass before it's done.
- When a domain term is added or changed, update `CONTEXT.md` in the same
  change. Glossary only — no implementation details there.
- Offer an ADR only for hard-to-reverse, surprising, genuine-trade-off
  decisions.
