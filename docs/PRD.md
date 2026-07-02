# SkillTrace v1 — Product Requirements

Status: accepted (v0.2). Terms per `CONTEXT.md`; decisions per
`docs/skilltrace-application-roadmap.md` and `docs/adr/`.

## Problem

A self-directed learner working through a multi-year AI curriculum has no
trustworthy answer to "what should I study next, and is my progress real?"
Todo lists don't model prerequisites; LMS platforms own your data, assume a
cohort, and grade with checkboxes; spreadsheets rot. The learner needs a
tool that models skills as a dependency graph, demands evidence before
progress is claimed, and survives years of daily use without a server.

## Product definition

SkillTrace v1 is a **local-first, CLI-first, single-learner learning
engine**. It is explicitly *not* an LMS, an AI tutor, a mastery-prediction
model, a badge platform, or a content library. The engine is
curriculum-agnostic; the learner's AI Learning Roadmap enters only as seed
data (nodes, edges, resources) and policy values.

One git repository = one learner's curriculum + progress. No accounts, no
server, no internet dependency for any core operation.

## Users

Exactly one: the learner-operator. They are technical (comfortable with a
terminal, git, and YAML), studying daily in sessions of 15–120 minutes, and
they are also the tool's administrator and curriculum editor.

## Goals (v1)

The product is done when, on their own machine, the learner can reliably
answer:

1. **What should I study next?** — `skilltrace next` recommends nodes that
   are prerequisite-safe, policy-weighted, and sized to available minutes.
2. **Why that node?** — every recommendation carries a stated reason,
   including policy effects.
3. **What evidence proves progress?** — every passed node has accepted
   evidence behind it, traceable to a gate and an acceptance authority.
4. **What happens if I fail?** — failed attempts and blockers are recorded,
   activate remediation pressure, and never silently alter progress.
5. **What review or remediation is due?** — reviews auto-schedule on pass;
   due and overdue work is visible daily.
6. **Can this node be passed or mastered safely?** — eligibility is
   computable on demand and enforced by the explicit pass/master commands.

## Non-goals (v1)

- No web UI, dashboard, or HTML reports (backlog v1.4).
- No automated web verification of resources (backlog v1.1).
- No adaptive sequencing, Elo/BKT mastery modeling, or analytics beyond
  basic reports (backlog v1.5/v2.0).
- No AI grading authority of any kind — AI review is advisory commentary
  only, forever bounded by the hard boundaries.
- No multi-user, sync, or hosting features. Fork, don't share.
- No curriculum content beyond the Phase 0–1 seed graph.

## Functional requirements

**Graph** — nodes as markdown curriculum files; relationships solely in
`edges.yaml` (`hard_prerequisite` locks, `soft_prerequisite` warns,
`remediation` applies advisory pressure); learner state in a separate
progress store; five node states with derived readiness and asserted
progress; validation catches duplicate/dangling IDs and hard-prerequisite
cycles.

**Evidence** — artifact specs and validation gates per node; attempts and
evidence records append-only with supersession; pass eligibility derived
from accepted evidence satisfying a closing gate; acceptance authority is an
objective gate or learner manual review.

**Execution** — sessions (one open at a time) containing per-node work
items; blockers, remediation actions, reviews; every mutating command
appends one audit event.

**Policy** — hard boundaries refuse (no automated pass/master/delete, no
hard-prerequisite override, no AI authority); advisory policies warn and
reorder (workload, review cadence, remediation pressure, track weights).
All thresholds and weights are seed values.

**Resources** — per-node learning resources with cost/license/verification
metadata; zero coupling to node state; staleness derived from
`last_verified` against a policy window.

**Interface** — one installable `skilltrace` CLI; readable daily views
(`today`, `next`, `node`, reports); Markdown and SQLite exports plus backups
as disposable derived artifacts.

## Constraints & quality requirements

- **Local-first:** every v1 command works with no network access.
- **Files are truth:** all state in human-readable Markdown/YAML, diffable
  and hand-recoverable via git; exports never read back.
- **Windows-first, cross-platform Python:** primary target is the learner's
  Windows machine; nothing platform-exotic.
- **Auditability:** any data change without a matching event is by
  definition a hand edit.
- **Longevity over features:** schema v1 freezes at v1.0; additions must be
  backward-compatible or carry migrations.

## Acceptance (v1.0)

A fresh clone can: install; validate all layers; recommend; start a session
and record work; submit evidence; check eligibility; pass with an explicit
command; schedule and complete a review; master with an explicit command;
export and back up — all offline, with every hard boundary enforced and all
exit-gate tests green. Full criteria: roadmap §v1.0.0.
