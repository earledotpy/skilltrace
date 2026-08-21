# SkillTrace

SkillTrace is a local-first, CLI-first, single-learner learning engine: a skill
graph with evidence-gated progress. It operates a personal study curriculum, but
the engine is curriculum-agnostic — curriculum protocols enter only as seed data
and policy values, never as engine code.

It answers questions like "What should I study next?", "Why that node?", "What
evidence proves progress?", and "Can this node be passed safely?" — from Markdown
and YAML files on disk, with no network access.

## Install

```bash
pip install -e .
```

Python ≥ 3.14; the only runtime dependency is PyYAML. Installing exposes the
`skilltrace` console script (equivalently, `python -m skilltrace`).

## Commands

A single `skilltrace` entry point dispatches subcommands. The dispatcher owns the
two cross-cutting rules: every mutating command appends exactly one audit event,
and forbidden automation is refused before it runs.

Graph:

```bash
skilltrace validate graph                              # nodes, edges, cycles
skilltrace sync                                        # recompute locked/available readiness
skilltrace next --minutes 60 --limit 5 --show-locked   # recommend prerequisite-safe nodes
```

Evidence:

```bash
skilltrace validate evidence                           # specs, gates, records, attempts
skilltrace evidence submit <node_id> --location <path> --accept
skilltrace attempt record <node_id> --outcome passed
skilltrace eligibility <node_id>                       # is the node pass-eligible, and why
skilltrace pass <node_id>                              # explicit learner pass assertion
```

## Layers

Five layers: **graph**, **evidence**, **execution**, **policy**, **release**. The
scaffold's original interface layer was cut from v1 (see `docs/adr/`).

- `graph/` — node markdown (curriculum) + `edges.yaml` + the progress store
- `evidence/` — artifact specs, gates, attempts, evidence records
- `execution/` — sessions, work, blockers, remediation, reviews, the audit event log
- `policy/` — hard-boundary and advisory policy values (seed data)
- `release/` — release manifest, tests, criteria

## Safety boundaries

- Passing and mastering are explicit learner commands; nothing else — no gate,
  sync, or AI — flips those states.
- AI review is never an acceptance authority; it may only attach advisory
  commentary to evidence.
- Asserted progress (`active`/`passed`/`mastered`) never moves backward.
- Evidence records are immutable — a correction supersedes, never edits or deletes.
- Markdown/YAML files are the only source of truth; SQLite/Markdown exports and
  backups are disposable and never read back by the engine.

## Status

Local-first and in active development. See
`docs/skilltrace-application-roadmap.md` for the per-release-candidate plan and
its exit gates, `docs/adr/` for structural decisions, and `CONTEXT.md` for the
ubiquitous language. It is not an LMS: no cloud sync, badges, analytics,
automatic mastery, or automatic state mutation.
