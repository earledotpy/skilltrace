# Spec — v2.1 Adaptive sequencing + retention overlay (FSRS-closeness)

**Status:** implemented (2026-09-08) — decisions D-Surface through D-Gates
locked; formulas T-Personalization, T-Weights, T-AgentInput, T-Rendering,
T-Storage-guard filled below (§1, §2, §3, §6).
**Target:** v2.1, slot 1 of `docs/POST_V2_ROADMAP.md:55` — carried fixed from
POST_V1 verbatim: adaptive sequencing + retention overlay (FSRS), binds to the
v1.6 event log + v1.5 retention model, advisory-only.
**Map:** in-session wayfinder (no GitHub map yet per Q1). Candidate tickets:
T-Personalization, T-Weights, T-AgentInput, T-Rendering, T-Storage-guard,
T-Spec. Prior map #191 closed; v2.1 hands off slot-row only.
**Standing rule:** all terms per `CONTEXT.md`; safety rules in `AGENTS.md`
are unchanged and binding — this spec never relaxes them.

> Hand-off gate: a builder can implement v2.1 without reopening a product or
> architecture question. This doc satisfies that gate — the stubs in §1–§3
> are filled here (their ticket decisions) and the §7 gate runs green.

---

## 0. Scope and what is explicitly out of scope

In scope for v2.1:

- The retention overlay upgrade: tuned exponential-decay, as FSRS-close as
  pure derivation allows — per-node half-life derived from review history +
  v1.6 analytics, delay-aware multipliers on the binary outcome, nothing
  persisted (D-FSRS, D-Storage/Q7, D-Grades/Q11).
- The adaptive-sequencing signal: an advisory ordering consumed by `next` /
  `today` as factor weights + reason strings (D-Surface/Q3, D-Weights/Q8).
- Day-one inputs: retention confidence + all four v1.6 themes (velocity,
  blockers-by-domain, review completion, evidence coverage) + Phase 3/4
  agent recs as opaque advisory input (D-Inputs/Q5, D-AgentInput/Q9,
  D-EventLog/Q10).
- Suggestions, never auto-writes: retention suggestions and sequence hints
  are words, not writes (D-Advisory/Q4).
- Policy seeds only: `policy/retention_model.yaml` deltas +
  `policy/recommendation.yaml` new weights as seed values, wired through
  `validate policy` (D-Weights).
- Mirror reuse: `retention_memory` stays disposable, engine-never-reads
  (D-Gates/Q12).

Explicitly **out of scope**:

- Real FSRS-4.5 via `py-fsrs` with stored stability/difficulty — the
  explicit rejected-alternative. Re-opens only if the pure-derivation
  invariant (`CONTEXT.md` Memory state, G-Storage) is revised.
- Any change to `Review.outcome` (`satisfactory | unsatisfactory` stays
  closed), to pass/mastery law, or to the five layers.
- Auto-pass / auto-master / auto-schedule (beyond the existing
  pass-ladder), LLM-graded evidence, cloud sync, Elo/BKT mastery,
  generative tutoring (hard boundaries + POST_V2 Beyond list).
- Full gate-runner / scheduler-queue (v2.2's problem).
- Reordering the `suggest reviews` calendar-due block (Tier 2 safety gate
  preserved); sequencing re-ranks `next`/`today` only.

---

## 1. The model — tuned decay, derived personalization (T-Personalization)

Locked:

- Family stays exponential decay `R(t) = 0.5^(t / h)` (Tier 2 math,
  `src/skilltrace/policy/retention_model.py:18-22`).
- Pure derivation: every read recomputes from review history + policy seed
  + derived analytics; `today: datetime.date` required keyword; CLI layer is
  the only wall-clock call site (T-Clock pattern). No `state/retention.yaml`,
  no per-node cache, no `Review`-record augmentation, no new fields on
  `graph/state.yaml` (D-Storage).
- Binary outcome stays closed; closeness comes from delay-aware multipliers
  and per-node/per-domain half-life, never new grades (D-Grades).
- Event-log binding is analytics-read for ordering only; state computation
  untouched; loss of log loses signal, never state (D-EventLog).

Filled (T-Personalization) — realized in `src/skilltrace/policy/retention_model.py`:

**Per-node half-life derivation.** For one passed/mastered node:

1. `completed` = the node's reviews with `status: completed`, sorted by
   `(created_at, id)` (oldest first, deterministic); cancelled reviews
   never enter this list.
2. `base_scale = domain_half_life_scales[prefix(node.id)]` (default 1.0;
   `prefix` = first two dot segments, e.g. `math.arithmetic` from
   `math.arithmetic.order_operations_01`), `× incomplete_evidence_scale`
   when the node is in the derived evidence-gap set, `× low_velocity_scale`
   when its domain's session count is below `min_domain_sessions`. All
   three fold multiplicatively and default to no-op.
3. Start `h = clamp(default_half_life_days × base_scale)` with anchor =
   none. For each completed review in order: anchor = its completed date,
   `h = clamp(h × multiplier(review))` where clamp is
   `[min_half_life_days, max_half_life_days]`.
4. Anchor selection (G-Rating D2, carried from Tier 2): any completion →
   kind `last_completed_review`; else a parseable pass transition → kind
   `pass`, `h = clamp(default × base_scale)`; else the degenerate
   never-passed case anchors on `today` so callers render a sane picture.
5. `R(t) = 0.5^(t / h)` with `t = (today − anchor)` in fractional days;
   `suggested_next_review = anchor + int(h)` days;
   `below_threshold = R(t) < attention_threshold` **or**
   `suggested_next_review <= today`.

**Delay-aware multiplier table** (seed
`policy/retention_model.yaml`, `delay_aware_multipliers`). The bucket
comes from `delay = (completed_at − scheduled_for).days` (0 when either
date is missing/unparseable → `on_time`), with `w = on_time_window_days`
(seed: 2):

| bucket   | condition        | satisfactory | unsatisfactory |
| -------- | ---------------- | ------------ | -------------- |
| early    | `delay < −w`     | 1.0          | 0.6            |
| on_time  | `−w ≤ delay ≤ w` | 2.0          | 0.5            |
| late     | `delay > w`      | 1.5          | 0.4            |

When the table is absent, the flat `satisfactory_growth_factor` (2.0) /
`unsatisfactory_reduction_factor` (0.5) fallback applies — on-time is its
strict superset, so Tier 2 behavior is reproduced exactly. Unknown
outcomes multiply by 1.0 (the binary enum is closed).

**Worked examples** (executed as `pytest.approx` assertions in
`tests/policy/test_retention_model.py`; seed h₀ = 7):

- `t = 0` after one on-time satisfactory review: `h = 7 × 2.0 = 14` →
  `R = 1.0`, suggested = anchor + 14 d.
- `t = h` at the default 7: `R = 0.5` — exactly the threshold, not below.
- `t = 2h` at the default 7: `R = 0.25` — below threshold, suggestion due.
- Delay buckets, one review over h₀ = 7: on-time satisfactory → h = 14;
  early satisfactory (delay −3) → ×1.0, h stays 7; late unsatisfactory
  (delay +3) → ×0.4, h = 2.8.
- An unsatisfactory review halves (flat/on-time 0.5) and a later
  satisfactory one multiplies back up from the reduced `h`; the anchor
  moves to the newer completion and confidence is recomputed from it,
  never reset to 1.

**Fallbacks (Tier 2, unchanged):** cancelled-only history and empty
history both anchor on the pass date at `default_half_life_days ×
base_scale`; the multiplier loop simply never runs.

---

## 2. CLI surfaces (T-Rendering)

Locked shape (D-Surface, D-Weights):

- `suggest reviews` keeps two sections in order — calendar-due first
  (never reordered), retention suggestions second (confidence-ascending).
  Empty case renders the calm "nothing fading" line. `READ_ONLY`.
- `next` / `today` consume the new advisory weights and render reason
  strings (Mentor cards). Locked appendix unchanged.
- `retention status [--node-id]` stays the full memory-state read surface;
  new columns (if any) named by T-Rendering.
- Agent recs enter as opaque advisory input: missing/unreadable →
  warn-and-ignore, calendar section still renders (D-AgentInput).

Filled (T-Rendering):

- `suggest reviews` (READ_ONLY) always renders the retention section
  header (`suggest reviews: Retention suggestions` + underline), even on
  runs where the calendar-due header was skipped. Per below-threshold
  node, confidence-ascending (most urgent first):
  `suggest reviews: {node_id} — confidence {R:.4f}, suggested {YYYY-MM-DD} (`review schedule` to make it real).`
  Empty case (calm line): `suggest reviews: nothing fading — no
  retention suggestions right now.` Non-empty case appends exactly one
  count-based warning line for downstream surfaces:
  `suggest reviews: {n} retention suggestion(s) due — `review schedule <node> --date <YYYY-MM-DD>` to schedule a check.`
  Missing retention seed = soft pass: calendar section renders, retention
  section is omitted without error.
- `next` / `today` share the derivation (`prereq_retention_urgency` +
  `load_agent_recommendations` folded into `recommend`) and render two
  new reason clauses on the Mentor cards, joined with `; ` like the
  existing ones: retention urgency →
  `{count} prerequisite review(s) fading below retention (+{retention_urgency} policy boost)`
  (singular/plural noun); agent signal →
  `agent signal (+{agent_signal} policy boost)`.
  Score contributions ride the same weights; the locked appendix and all
  pre-existing clauses are unchanged.
- `retention status [--node-id]`: **no new columns** — the v2.1 fields
  (`half_life`, `confidence`, `suggested_next`) were already Tier 2's
  line. Output per node stays two lines: heading
  `{title} ({node_id})  state={state}  domain={two-segment prefix}  anchor={kind}@{iso}`
  then `half_life={h:g}d  confidence={R:.4f}  suggested_next={iso}` with
  ` BELOW THRESHOLD` appended when flagged. `--node-id` on an unknown id
  fails (exit 1); on a passed/mastered id filters to that node; on a
  non-retained id prints the "not passed or mastered" notice (exit 0);
  with no retained nodes at all it prints the "nothing to derive" line.
- Agent-input warnings never suppress cards or the calendar section:
  a missing `data/agent_recommendations.yaml` is silent; an unreadable or
  malformed file prints warn-and-ignore lines prefixed with the command
  name (`next: …` / `today: …`) and the command proceeds with the factor
  stood down.

---

## 3. Policy seeds (T-Weights, T-AgentInput)

Locked:

- Numeric seeds are policy *values*, not engine constants. No kill-switch
  beyond `status: active`.
- `review_due: 2.0` dormant weight in `policy/recommendation.yaml:18` is
  wired or superseded by named successors in this slot (no second dormant
  key left behind).
- Agent-input schema is opaque, advisory, validated leniently.

Filled (T-Weights):

- `policy/recommendation.yaml` bumps to `policy.recommendation.default_v0_7`:
  the dormant `review_due` weight is **removed** (superseded, not wired) and
  two named successors land in `factor_weights`:
  - `retention_urgency: 2.0` — multiplied by the candidate's count of
    below-threshold active hard-prerequisite sources
    (`prereq_retention_urgency`); zero when none, so the factor stands down.
  - `agent_signal: 1.5` — flat contribution when the node carries an agent
    recommendation.
- `validate policy` (`src/skilltrace/policy/validation.py::
  _recommendation_weight_checks`) enforces, as hard errors (non-zero exit,
  message naming the field, printed under `validate policy: FAILED`):
  `review_due` present → "'review_due' is retired — use
  'retention_urgency'; no dormant key may survive (D-Weights).";
  `retention_urgency` missing → "missing required factor weight
  'retention_urgency' (v2.1 sequencing)."; every factor weight must be a
  finite number (bools and NaN rejected).
- `policy/retention_model.yaml` bumps to `policy.retention.default_v1_0`:
  adds `delay_aware_multipliers` (the §1 table), `on_time_window_days: 2`,
  `domain_half_life_scales: {}` (empty = no-op), `low_velocity_scale: 0.9`,
  `incomplete_evidence_scale: 0.85`, `min_half_life_days: 1`,
  `max_half_life_days: 365`. Value ranges (`_retention_value_ranges`),
  hard errors likewise: `default_half_life_days ∈ (0, 365]`; flat
  multipliers optional but growth > 1 and reduction ∈ (0, 1) when present;
  `attention_threshold ∈ (0, 1)`; `on_time_window_days` a non-negative
  integer; each delay bucket a mapping with both outcome cells > 0;
  domain scales > 0; both analytics scales ∈ (0, 1]; `min_half_life_days ≥ 1`
  and `max_half_life_days ≥ min_half_life_days`.
- `retention_seed_from_doc` materializes the typed seed and trusts the
  validator as the contract; missing v2.1 keys fall back to no-ops
  (Tier 2 callers unchanged).

Filled (T-AgentInput):

- **Path:** `data/agent_recommendations.yaml` (repo-relative;
  `AGENT_RECS_RELPATH` in `src/skilltrace/policy/agent_input.py`).
- **Schema (deliberately lenient):** top-level key
  `agent_recommendations` → list of mappings with `node_id: str` (required,
  else the entry is skipped with a warning) and `priority: number`
  (optional, default 0.5; non-numeric defaults; negative clamps the entry
  out with a warning). Everything else in an entry is opaque and ignored —
  unknown node IDs simply receive no boost downstream.
- **Warn-and-ignore paths:** missing file → silent empty (the most common
  day-one case); YAML/OSError on read → empty plus one
  "agent recommendations unreadable — ignored: …" warning; non-mapping
  document or missing top-level key → empty plus one warning; per-entry
  defects → entry skipped, one warning each, other entries still load.
  Consumers (`derive_next`, `today`) print warnings prefixed with the
  command name and proceed with the factor stood down; the calendar/cards
  always render. The engine never writes this file.

---

## 4. The disposable SQLite mirror

- `retention_memory` stays the one derived-table exception alongside
  `nodes.state` (Tier 2 charter). Rebuilt whole each `export sqlite`;
  engine never reads `data/skilltrace.db` (safety gate pins the
  `sqlite3.connect` / `data/skilltrace.db` grep with the export-module
  whitelist).
- Analytics themes are NOT mirrored as new tables in v2.1 unless
  T-Personalization proves the ordering formula needs them — default: no new
  tables.

---

## 5. Glossary

No new terms (D-Terms/Q6):

- **Sequencing** — derived recommendation ordering (prose only, not a
  `CONTEXT.md` term unless T-Spec proves a glossary gap).
- **Retention overlay** — the existing Memory state / Retention confidence /
  Retention suggestion triple, upgraded. No new CamelCase types.

If T-Spec finds a genuine gap, terms land in `CONTEXT.md` in the same change
(per `AGENTS.md` working conventions).

---

## 6. Testing (mirrors Tier 2 §6 + v1.6 T-TestArch)

- Clock injection everywhere derived (`today` required kwarg; no
  module-level clock; no `datetime.now()` in derivation cores).
- Unit layer: pure-derivation tests with frozen `today` pinning `R(t)` at
  `t = 0, h/2, h, 2h`, delay-aware multipliers, unsatisfactory reduction,
  cancelled-only fallback, below-threshold gating (T-Personalization's
  worked examples are the executable spec).
- Command-output layer: presence/section assertions (never exact text) for
  `suggest reviews` two-section order, `next` weight reasons, `retention
  status` columns, empty-case lines, count-based warning line.
- Safety layer (T-Storage-guard): schema-frozen `execution/reviews.yaml` +
  `graph/state.yaml` snapshots; engine-never-reads-DB grep; no
  auto-pass/master/delete path scan; calendar-order-frozen assertion;
  binary-enum-frozen assertion.

Filled (T-Storage-guard) — where each layer lives:

- Unit: `tests/policy/test_retention_model.py` (R(t) anchors
  `t = 0, h, 2h` and post-growth, all three delay buckets, base-scale
  folding, unsatisfactory reduction, cancelled-only + empty fallbacks,
  `today`-is-the-only-clock), `tests/graph/test_recommendation.py`
  (urgency/agent boost + reason strings, stand-down defaults, score
  arithmetic), `tests/policy/test_agent_input.py` (lenient decoding and
  every warn-and-ignore path).
- Command-output: `tests/policy/test_suggest_commands.py` (two-section
  order, empty-case lines, count-based warning line),
  `tests/policy/test_next_policy_weights.py` (urgency reordering through
  the CLI), `tests/cli/test_retention_status_command.py`.
- Policy validation: `tests/policy/test_validate_policy.py` (retention
  value ranges incl. delay table, retired/required factor weights,
  non-numeric weight rejection).
- Safety: `tests/release/test_v21_safety_gates.py` — schema-frozen
  snapshots `tests/release/snapshots/reviews_v2_1.yaml` and
  `tests/release/snapshots/state_v2_1.yaml`; engine-never-reads-DB grep
  with the export module whitelisted; no automated pass/master/delete
  path; `suggest reviews` calendar block order frozen (sequencing never
  re-ranks it); `Review.outcome` binary enum frozen.
- Doc: `tests/release/test_v21_doc_gates.py` — spec §7 command list and
  `CONTEXT.md` glossary terms.

---

## 7. Exit gates

Functional (mirror Tier 2 per D-Gates/Q12):

```bash
pytest tests/policy
skilltrace validate policy
skilltrace retention status
skilltrace suggest reviews
skilltrace next --minutes 60
skilltrace today
skilltrace export sqlite
skilltrace health
```

Safety (five + two, Tier 2 shape):

1. Schema frozen: `execution/reviews.yaml` vs snapshot.
2. Schema frozen: `graph/state.yaml` vs snapshot.
3. Engine never reads `data/skilltrace.db` (export module whitelisted).
4. No automated pass/master/delete path.
5. No ordering override in `suggest reviews` calendar block (sequencing
   re-ranks `next`/`today` only).
6. Doc gate: this spec exists and §7 matches verbatim.
7. Doc gate: `CONTEXT.md` still carries Memory state / Retention confidence
   (/ Retention suggestion if touched).

---

## 8. Invariants and constraints preserved

- Hard boundaries (`AGENTS.md`): `pass_node` / `master_node` /
  `delete_record` manual-only; asserted progress never moves backward; AI
  review never an acceptance authority.
- Advisory-only overlay: warns and reorders, never blocks, never writes
  `Review` records, never demotes.
- Pure derivation; files are truth; exports disposable and never read back;
  event log audit-only.
- Five layers (ADR 0002); no new layer; no Phase 4/5 seed-graph work in
  this slot (engine-only per map #191 owner notes).

---

## 9. Acceptance — this outline is done when

- [x] In-session decisions D-Surface through D-Gates + D-Storage recorded.
- [x] T-Personalization, T-Weights, T-AgentInput, T-Rendering,
      T-Storage-guard close and their stubs (§1, §2, §3, §6) are filled
      verbatim.
- [x] No product or architecture decision remains blocking the §7 gate.
- [x] Fresh-clone run of the §7 functional gates exits 0 on seed; safety
      + doc gates green.

---

## References

`CONTEXT.md` (Memory state, Retention confidence, Retention suggestion,
Review, Hard boundary, Advisory policy, Event log, Serve);
`docs/POST_V2_ROADMAP.md:55` (v2.1 slot row);
`docs/POST_V1_ROADMAP.md:58` (verbatim source);
`docs/spec-tier2-retention-analytics.md` (Tier 2 math, surfaces, gates —
this spec's template);
`docs/spec-v1.6-event-log-analytics.md` (four themes, `derive.py` framework);
`src/skilltrace/policy/retention_model.py`,
`src/skilltrace/analytics/derive.py`,
`src/skilltrace/graph/recommendation.py`,
`src/skilltrace/commands/recommend.py`,
`src/skilltrace/commands/suggest.py`;
`policy/retention_model.yaml`, `policy/recommendation.yaml`,
`policy/analytics.yaml`; map #191 (POST_V2 trail).
