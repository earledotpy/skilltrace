# R-Provenance (POST_V2 map #191, issue #194) — additive findings note

Decisions only; no engine code changed. Slot-table decision is G-Slots' call.

## 1. Gate-run receipt — minimal fields + guardrails

Minimal immutable fields on a new `EvidenceRecord` (optional; Q1, High impact,
Low reversibility — hard to unwind once records exist):

- normalized command identity; declared root-relative inputs; available
  runner/tool version; exit class (not raw code only); hashes of retained
  outputs; artifact hash (already frozen today).
  (`docs/research/evidence-provenance-and-operational-contracts.md:56`;
  `docs/research/ten-repository-additive-adoption-roadmap.md:112-129`)
- Exclude by default: secrets, arbitrary environment values, unbounded logs.
  (`...operational-contracts.md:56`; Q9 tiers at `:64`: summary/hash default,
  opt-in bounded sanitized excerpt, explicit local attachment.)

Guardrails:

- Receipt context never passes/masters; exit code decides the submitted
  record verdict only. (`...roadmap.md:130-135`; ADR 0003)
- Unrunnable gate = no judgment, no record (exit 1, nothing written).
  (`src/skilltrace/evidence/submission.py:185-195`; planner verdict at `:177-199`,
  record build at `:201-216`; schema `manual`/`objective` only,
  `src/skilltrace/evidence/gates.py:24-115`)
- Diagnostic failure is not verdict failure; test unrunnable stays no-judgment.
  (`...operational-contracts.md:64`)
- Precedent is bounded: vimhjkl grades observable final state + efficiency
  (`S-Sigdel/vimhjkl@501762f:src/vimhjkl/grader.py:429-500`; fixture/learner
  separation at `build/generate.py:34-102`); Engram durable on-disk receipts
  (`nagisanzenin/engram@0590eb8:README.md:18-20`). Do NOT import in-toto's full
  Link/provenance validator (`in-toto/attestation@2dcd055:link.pb.go:26-35`,
  `provenance.go:14-137`) — take the subject+digest+predicate-type discipline
  (`statement.go:15-57`) in miniature only.
- Metrics hygiene (near-term-1): keep v1.6 coverage labeled
  **required-spec presence coverage** (`derive.py:347-393`); any pass-readiness
  metric gets a distinct name + explicit denominator, never silent relabeling.
  (`...roadmap.md:58-83`; `...operational-contracts.md:63`;
  `src/skilltrace/evidence/submission.py:110-126`)

## 2. Graph-impact diagnostic — report shape + guardrails

Read-only, optional, pre-curriculum-release report (Q5, Medium/Medium):

- newly locked/unlocked *derived* nodes; recommendation-list changes;
  dangling evidence/spec references; no-op edges (active edges that unlock
  nothing / parked-edge hygiene).
  (`...operational-contracts.md:60`)
- Guardrails: relationships read from `graph/edges.yaml` only; asserted
  `passed`/`mastered` treated as immutable; never writes state, never blocks
  human action. (Same line; roadmap decision 12.)
- Seams it composes without changing: `check_graph` already reports dup IDs,
  all-edge endpoints, active hard-cycle, dangling progress, advisory soft-cycle
  (`src/skilltrace/graph/validation.py:91-146,124-185`); readiness derives from
  active hard prereqs, skips asserted (`readiness.py:47-115`); `recommend()`
  is pure, ranks `available`/`active` only, ties by node id
  (`src/skilltrace/graph/recommendation.py:204-276`), with locked-prereq
  explainer `_locked_candidates` (`:169-201`).

## 3. Slot recommendation (advisory to G-Slots)

- Receipt contract: earns POST_V2 (schema definition + frozen-record extension
  of `plan_submit`; defer the general runner until a concrete seed artifact
  needs it, per roadmap §3). Rationale: Low reversibility — freezing the
  schema before reproducible-gate records exist is the value; Beyond loses it.
- Impact diagnostic: earns POST_V2 as the read-only companion in the **same
  slot** — one combined provenance/diagnostics slot, not two. Rationale: both
  are additive metadata/views over the same seams (submission + validation +
  recommend), neither touches asserted progress or `edges.yaml` authority;
  a second slot buys little (Medium reversibility, no migration risk).
- Beyond: full runner, scheduler/queue, plugins/sync, AI authority. Explicitly
  avoided (`...roadmap.md:203-213`; Q2–Q4 guardrails at `:57-59`).

## Reversibility summary

- Receipt schema: **Low** — records are immutable; wrong fields persist.
  Decide small + optional now, extend by new optional fields only.
- Diagnostic: **Medium** — read-only output; shape can evolve without
  migrating learner state.
- Metric names: **High** — renaming is cheap; keep presence vs eligibility
  distinct from the start.
