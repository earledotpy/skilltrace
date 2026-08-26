# Spec — Tier 2 FSRS retention analytics

**Status:** locked hand-off (map #86) — no open product or architecture
decisions block the Tier 2 build.
**Target:** a Tier 2 RC shipping between v0.9.0-rc1 and v1.0.0-rc1 (per
`docs/skilltrace-application-roadmap.md:596-611` v2.0 reservation: this spec
promotes the deferred "retention/confidence modeling as a derived overlay"
into a concrete, shippable RC whose scope is narrower than v2.0's adaptive
sequencing goals).
**Map:** [#86 Map — Tier 2 FSRS retention analytics (wayfinder map)](https://github.com/earledotpy/skilltrace/issues/86)
**Decisions:** [R-Survey #87](https://github.com/earledotpy/skilltrace/issues/87) · [G-Authority #88](https://github.com/earledotpy/skilltrace/issues/88) · [G-Rating #89](https://github.com/earledotpy/skilltrace/issues/89) · [G-Storage #90](https://github.com/earledotpy/skilltrace/issues/90) · [G-Surfaces #91](https://github.com/earledotpy/skilltrace/issues/91) · [T-Clock #92](https://github.com/earledotpy/skilltrace/issues/92) · [T-Exit #93](https://github.com/earledotpy/skilltrace/issues/93).
**Algorithm survey:** [`research/fsrs-algorithm-survey.md`](https://github.com/earledotpy/skilltrace/blob/research/fsrs-algorithm-survey/research/fsrs-algorithm-survey.md) on branch `research/fsrs-algorithm-survey` (commit `1b6ac38`).
**Standing rule:** all terms per `CONTEXT.md`; safety rules in
`AGENTS.md` are unchanged and binding — this spec never relaxes them.

> Hand-off gate (from map `Destination`): a builder can implement Tier 2
> without reopening a product or architecture question. This doc satisfies
> that gate; the build plan is the seven exit-gate commands and the
> five-assertion safety suite, sliced by the existing test-layer split.

---

## 0. Scope and what is explicitly out of scope

In scope for this RC:

- The retention model's *derivation*, surfaces, and policy seed.
- One new read-only CLI surface (`retention status`).
- Two existing CLI surfaces edited to host the model (`report reviews`
  header rename; `suggest reviews` two-section expansion with an
  appended count-based `next`-side warning line for below-threshold
  nodes).
- One new disposable SQLite analytics table.
- A new `policy/retention_model.yaml` seed document and its entry in
  the `validate policy` umbrella.

Explicitly **out of scope** (per map `Out of scope`):

- v1.5 general event-log analytics (study velocity, blockers by domain,
  review completion, evidence coverage) — separate effort.
- Tier 1 dashboard widgets for retention (Serve renders health strip
  only per `docs/spec-tier1-serve.md:94`). Tier 2 ships a count-based
  `next` warning line and the `retention status` read surface; *no*
  retention card in Serve for this RC. A future Tier 2+ RC can wire
  retention into the existing daily views — recorded as a
  "future: serve widgets" upgrade path, **not** as a hook in this RC.
- Elo / BKT mastery modeling (mastery is permanent in v1 per decision
  8; no replacement here).
- Any change to pass/mastery law or to the `Review.outcome` enum
  (`satisfactory | unsatisfactory` exactly).
- Wiring the dormant `review_due: 2.0` key in
  `policy/recommendation.yaml`. It is recorded here as
  known-unwired and is a separate cleanup.

---

## 1. The model — exponential decay, pure derivation

### 1.1 Family and inputs

**Family: exponential decay (half-life).** Per G-Rating and the algorithm
survey, Tier 2 ships exponential decay; FSRS-4.5 via `py-fsrs` is the
documented future upgrade path (AGPL `anki-sm-2` is explicitly avoided).

**Inputs (per node):**

- A `today: datetime.date` (mandatory; see §6.1 clock injection).
- The node's review history from `execution/reviews.yaml`: list of
  `Review` records with `status`, `scheduled_for`, `completed_at`,
  `outcome`, `cancelled_at`. Only `status == "completed"` records feed
  the model.
- The node's pass date (read from `graph/state.yaml` `progress.<id>.transitions.passed`).
- The policy seed: `default_half_life_days`, `satisfactory_growth_factor`,
  `unsatisfactory_reduction_factor`, `attention_threshold`.

### 1.2 The math

The model is the policy seed's exponential decay with multiplicative
updates. All values are recomputed at read time; nothing is persisted.

- **Anchor.** Per G-Rating: anchor on the last *completed* review, or
  on the pass date if no post-pass completion exists (e.g. only-cancelled
  reviews after pass). The anchor date is `anchor_at`; the anchor kind
  is one of `last_completed_review` or `pass`.
- **Half-life.** Starts at `default_half_life_days` (7.0). Each
  completed satisfactory review multiplies the current half-life by
  `satisfactory_growth_factor` (×2.0). Each completed unsatisfactory
  review multiplies the current half-life by `unsatisfactory_reduction_factor`
  (×0.5). The half-life is never reset to default and never demotes
  asserted progress. Multipliers are delay-blind (G-Rating D3): a late
  but satisfactory review does not earn extra growth; an early one does
  not earn less.
- **Retention confidence.** `R(t) = 0.5^(t / h)` where `t = (today - anchor_at).days`
  (in days) and `h` is the current half-life after multipliers have
  been applied in review-history order from the anchor. `R(t) = 1.0`
  at `t = 0`, `0.5` at `t = h`, `0.25` at `t = 2h`. Cancelled reviews
  contribute nothing; they do not anchor, do not multiply, and do not
  short-circuit a pass-date fallback.
- **Suggested next review.** A retention suggestion is due when either
  `R(t) < attention_threshold` (i.e. roughly a half-life has elapsed
  since the last contact) **or** the suggested date has arrived (see
  below). The suggested date is `anchor_at + h` after the *last
  multiplier-applying review*, or the pass date at the default
  half-life when the pass-date fallback anchor applies.

### 1.3 Storage — pure derivation (G-Storage)

The engine **never persists** memory state. No `state/retention.yaml`,
no per-node cache, no `Review`-record augmentation, no fields on
`graph/state.yaml`. Every read recomputes from the inputs above. The
engine never reads `data/skilltrace.db`.

The disposable SQLite mirror gains one derived table
(`retention_memory`; see §5.2) as an explicit charter exception
alongside `nodes.state`, computed during the mirror's existing
rebuild pass. The table is disposable output, never read back.

### 1.4 Authority — advisory only (G-Authority)

The retention model emits *suggestions* and *warnings*, never writes.
No `Review` record is created, moved, or cancelled by the model.
Auto-schedule-on-pass remains the *only* sanctioned automation
(`policy/automation_boundary.yaml`); the model introduces no second
automation. Coverage includes mastered nodes and post-ladder nodes —
precisely where automation has stopped by law but forgetting continues.

---

## 2. CLI surfaces

Three surfaces. The first two are edits to existing commands; the
third is one new read-only command.

### 2.1 `skilltrace report reviews` — calendar truth, header rename only

**No model-derived columns** are added. The "Retention & Mastery
Health" header is renamed to a calendar-truth phrasing (e.g.
"Scheduled Reviews") so calendar truth no longer wears the retention
model's name. Overdue urgency already renders as "N days overdue";
nothing else moves. The mastery-promotion candidate list stays
calendar-driven (a satisfactory review on a passed node is the
existing input; the model is not in that path).

### 2.2 `skilltrace suggest reviews` — the model's primary voice, two sections

`suggest reviews` becomes the model's primary voice. It renders two
sections, in this order:

1. **Calendar-due** — existing behavior over real `Review` records,
   unchanged. Scheduled reviews at or past their `scheduled_for`,
   oldest first, with the existing cadence grace-day phrase. Always
   rendered first; the section header is present iff there is at
   least one such review.
2. **Retention suggestions** — derived from the model, not from any
   record. For every passed or mastered node whose **Retention
   confidence** is below `attention_threshold` or whose suggestion
   date has arrived, render the node id, the current confidence
   (e.g. "confidence 0.42"), the suggested date, and a closing pointer
   to the manual `review schedule` command. The section is sorted
   ascending by confidence (lowest first = most urgent). The empty
   case renders a calm "nothing fading" line.

The two sections are visually distinct blocks; the calendar-due list
is never reordered by retention pressure (G-Authority / T-Exit §5).
The command remains `READ_ONLY`, never emits records, never exits
nonzero on seed.

**`next`-side warning line.** When the threshold-gated retention
section contains one or more suggestions, `suggest reviews` also
appends a single count-based advisory line that downstream surfaces
(notably `next` and the Tier 1 home pressure strip) can pick up
verbatim. The line is text, not a numeric score, and exists so the
existing pattern of "N retention suggestions due — `skilltrace
suggest reviews`" surfaces without inventing a new recommendation
weight (per G-Authority's deferred-weights landing in G-Surfaces D8).

### 2.3 `skilltrace retention status [--node-id]` — new read-only command

One new command. `READ_ONLY`. Derives the full memory-state picture
across all passed/mastered nodes, or one node if `--node-id` is
supplied. For each row, it prints:

- the node id and title,
- the anchor kind (`last_completed_review` or `pass`) and anchor date,
- the current half-life (days),
- the current **Retention confidence** (0–1, formatted),
- the suggested next review date,
- a `BELOW THRESHOLD` marker when the node is below
  `attention_threshold`.

No `refresh` (nothing to refresh under pure derivation). No `config`
(the policy file is directly readable). `--node-id` accepts a
single id; unknown ids exit non-zero with a clear message.

### 2.4 Registration

`retention status` is registered in `src/skilltrace/commands/` as a
new module and wired through the existing `Registry.register(…)`
pattern (`src/skilltrace/cli.py:68`); kind `READ_ONLY`; no audit
event. The module is the home of the pure derivation function and
the `today` arg (see §6.1) so the CLI layer is the only
`datetime.date.today()` call site.

---

## 3. Policy seed

### 3.1 New file: `policy/retention_model.yaml`

```yaml
retention_model_policy:
  id: policy.retention.default_v0_9
  status: active
  title: Retention model
  description: >
    Advisory-only retention overlay. The model derives per-node
    confidence and suggestion dates from the review history and the
    decay parameters below; it never writes. Cancelled reviews feed
    nothing. The model may warn and reorder recommendations on its
    own surfaces, never block a human command, and never move
    asserted progress.
  model: exponential_decay
  default_half_life_days: 7
  satisfactory_growth_factor: 2.0
  unsatisfactory_reduction_factor: 0.5
  attention_threshold: 0.5
  created_at: 2026-08-26
  updated_at: 2026-08-26
```

The numeric seed is locked: `h = 7`, `×2.0 / ÷0.5`, `attention_threshold = 0.5`.
These are policy *values* (G-Surfaces D4), not engine constants. No
enabled kill-switch — `status: active` covers it, matching the
sibling seeds. No cross-file dependencies.

### 3.2 `validate policy` integration

Add `retention_model.yaml` to `POLICY_FILES` in
`src/skilltrace/policy/loading.py:18`, mapping the filename to
`retention_model_policy` (its top-level key). The existing umbrella
`validate policy` command gains the file and the value-range
checks below. **No new sub-target** is added; the new file rides
the umbrella per G-Surfaces D5 and T-Exit.

Value-range checks (each is a hard error on load, non-zero exit):

- `default_half_life_days`: `0 < h <= 365` (days).
- `satisfactory_growth_factor`: `> 1`.
- `unsatisfactory_reduction_factor`: `0 < factor < 1`.
- `attention_threshold`: `0 < threshold < 1`.

Bad values exit non-zero with a precise message naming the field.
The boundary-disagreement check is unchanged; this file is not a
boundary file (the engine has no forbidden action here).

---

## 4. Glossary

Two terms are introduced in `CONTEXT.md` (already landed with
G-Storage and G-Surfaces, included here for spec completeness):

- **Memory state** (added by G-Storage) — the retention model's
  derived picture of how well a passed or mastered node is
  currently retained. It exists only at read time: recomputed from
  review history and policy values, never stored, and never written
  by the engine on the learner's behalf. The core quantity it
  exposes is **Retention confidence**.

- **Retention confidence** (added by G-Surfaces D6) — the retention
  model's derived, 0–1 measure of how well a passed or mastered
  node is currently retained, where 1 means freshly reviewed and
  0 means fully faded. It is recomputed at read time from review
  history and policy seed values (the decay model's half-life and
  multipliers), never stored, and never written by the engine on
  the learner's behalf. A node falls below the policy
  `attention_threshold` when roughly a half-life has elapsed since
  its last contact, at which point a retention suggestion is due.

- **Retention suggestion** (already in `CONTEXT.md` per G-Authority)
  — a derived, never-stored recommended date for the next
  retention check on a passed or mastered node, produced by the
  retention model and recomputed from review history and the
  current date at read time whenever the node's
  **Retention confidence** is below the policy
  `attention_threshold`.

No new outcome values; no `ReviewOutcome` term; no CamelCase
`MemoryState` / `RetentionConfidence`. The existing
`satisfactory | unsatisfactory` enum is unchanged.

---

## 5. The disposable SQLite mirror

### 5.1 Charter exception

Per G-Storage: the SQLite mirror's "no derived or joined tables"
rule is amended to admit **one** retention table alongside the
existing `nodes.state` exception. The engine still never reads
`data/skilltrace.db`; the table is computed during the mirror's
rebuild pass and is disposable output.

The relevant docstring at `src/skilltrace/sqlite_export.py:1-7` is
amended to record the exception.

### 5.2 `retention_memory` table

Columns (in order; identical to the in-process derivation's field
names where natural):

- `node_id` (TEXT, primary key with `computed_at` would be wrong —
  this is a *snapshot*, not a history; one row per node per
  rebuild).
- `asserted_state` (TEXT) — the node's progress-store state at
  computation time (`passed` or `mastered`; nodes in other states
  are not in this table).
- `anchor_kind` (TEXT) — `last_completed_review` or `pass`.
- `anchored_at` (TEXT, ISO date).
- `half_life_days` (REAL).
- `confidence` (REAL, 0–1).
- `suggested_next_review` (TEXT, ISO date).
- `computed_at` (TEXT, ISO datetime at rebuild).

Rows: one per passed or mastered node at the time of the mirror's
rebuild. The table is rebuilt whole each `skilltrace export sqlite`
run, exactly like the other tables in the mirror.

### 5.3 Engine-never-reads guarantee

This table widens the existing engine-never-reads-the-DB invariant
by exactly one artifact. The T-Exit safety assertion (safety gate
#3) pins the literal-string grep of `src/**/*.py` for
`sqlite3.connect` and `data/skilltrace.db`, whitelisting only
`src/skilltrace/export/sqlite_export.py`. The retention module
imports nothing from `sqlite3` and references no db path.

---

## 6. Testing (per T-Clock)

### 6.1 Clock injection

The pure derivation function(s) computing `confidence`, `half_life`,
`suggested_next_review` (and any helper that reads the wall clock)
take `today: datetime.date` as a **required** keyword argument. The
CLI layer — the `retention status` handler, the `suggest reviews`
handler, and the `next`-side warning emission — is the only place
that calls `datetime.date.today()`. No module-level clock, no
default-to-now, no `monkeypatch` of stdlib `date`.

`datetime.now()` does not appear in the derivation core.

### 6.2 Fixtures

Tests use the existing `_write_yaml(root, relpath, doc)` helper
(see `tests/policy/conftest.py:127` and the call sites in
`tests/cli/test_report_command.py`, `tests/cli/test_today_command.py`,
`tests/policy/test_suggest_commands.py`). No new `tests/fixtures/`
directory. No checked-in YAML fixture for the retention history.
Test cases are short enough that a generator would obscure more
than it abbreviates; a checked-in fixture would be a second
source of truth whose drift from the policy seed wouldn't be
caught.

### 6.3 Unit layer — `tests/policy/test_retention_model.py` (new)

Calls the pure derivation function directly with a frozen `today`
and hand-built review histories. Pins the exact values computable
from the `h = 7, ×2.0, ÷0.5, threshold = 0.5` seed:

- `t = 0` (anchor day, just completed) → `confidence = 1.0`,
  `half_life = 14.0` (after one growth from the default 7.0),
  `suggested_next_review = anchor + 14 days`.
- `t = h/2` (3.5 days) → `confidence = 0.5^(3.5/7) ≈ 0.70710678…`,
  asserted with `pytest.approx` at `1e-9`.
- `t = h` (7 days) → `confidence = 0.5`.
- `t = 2h` (14 days) → `confidence = 0.25`.
- Unsatisfactory: `half_life` multiplied by `0.5` (not reset, not
  demoted) and `confidence` recomputed from the reduced half-life.
- Cancelled-only fallback: a node whose only post-pass review was
  cancelled anchors on the pass date at the default half-life; no
  completed-review record enters the math.
- Empty case: a passed node with zero completed reviews returns
  `confidence = 0.5^(t/7)` from the pass date at the default
  half-life.
- Below-`attention_threshold` gating: a node whose confidence
  drops below `0.5` reports `below_threshold = True`.

This file is the executable spec for the formula and the policy
seed.

### 6.4 Command-output layer

Two test files, extending the existing patterns
(in-process `cli.run(...)`, disposable repo seeded with the
policy file, event-log read-only assertion):

- Additions to `tests/policy/test_suggest_commands.py`: drive
  `cli.run("suggest reviews", root)` against a disposable repo;
  assert exit 0 and that the *section* "Retention suggestions"
  appears when at least one node is below threshold or has a
  suggestion date at or before `today`. Empty case: the
  "nothing fading" line. Assert the count-based warning line is
  emitted when the section is non-empty.
- New `tests/cli/test_retention_status_command.py`: drive
  `cli.run("retention status", root)`; assert exit 0 and that
  one row per passed/mastered node renders, with the documented
  columns present. With `--node-id` of a passed node, assert a
  single-row output.

The command-output layer asserts *presence / section* — not exact
rendered text. The formatting is the surface's own concern, and
pinning it would make cosmetic edits expensive.

### 6.5 Coverage matrix

| Behaviour                                | Unit | Command output |
| ---------------------------------------- | ---- | -------------- |
| `R(t) = 0.5^(t/h)` at t = 0, h/2, h, 2h  | yes  | —              |
| Suggestion-date arithmetic               | yes  | presence in `suggest reviews` |
| Unsatisfactory multiplicative reduction  | yes  | —              |
| Cancelled-only → pass-date fallback      | yes  | —              |
| Empty / no completed reviews             | yes  | "nothing fading" line in `suggest reviews` |
| Below-`attention_threshold` gating       | yes  | count-based `next` warning line |
| `retention status` per-node rendering    | —    | presence of columns + one row per passed/mastered node |
| `retention status --node-id`             | —    | single-row output |

---

## 7. Exit gates (per T-Exit — verbatim)

The Tier 2 RC's release block is **seven commands + five safety
assertions + two doc gates**. This block is what the safety-gate
doc check in `tests/release/` pins verbatim, and is the only
exit-gate definition for this RC.

### 7.1 Functional gates (commands the release runs)

```bash
pytest tests/policy
skilltrace validate policy
skilltrace retention status
skilltrace suggest reviews
skilltrace report reviews
skilltrace export sqlite
skilltrace health
```

- `pytest tests/policy` is the only layer that gains code in this
  RC; the other layers' suites are unchanged and not part of this
  gate.
- `skilltrace validate policy` is the umbrella;
  `policy/retention_model.yaml` joins the existing
  `policy/*.yaml` iteration in the policy loader (no new
  sub-target). The value-range assertions in §3.2 are enforced
  here.
- `retention status`, `suggest reviews`, `report reviews` exit 0
  on seed. The two-section model voice is verified in
  `tests/cli/test_suggest_reviews.py` and
  `tests/cli/test_report_reviews.py` per §6.4 (presence/section
  only, not exact text).
- `skilltrace export sqlite` exits 0 and produces the
  `retention_memory` table; a separate assertion (safety gate
  #3) pins the engine never reads that table.
- `skilltrace health` stays in the gate because a new read-only
  surface grew; the health check would catch any new read
  surface that misbehaves on seed.

### 7.2 Safety assertions (precise diffs the suite must produce on regression)

All five live in `tests/release/test_tier2_safety_gates.py` and
fail with the exact violated invariant, not a generic "safety
check failed".

1. **Schema frozen: `execution/reviews.yaml`** — load the seed
   file, compare the set of top-level keys and per-record keys
   against the v1.0 snapshot stored at
   `tests/release/snapshots/reviews_v1_0.yaml`. Diff is the
   failure message. Protects G-Authority's "advisory-only, no
   persisted fields" decision from a regression that quietly
   grows the schema.
2. **Schema frozen: `graph/state.yaml`** — same shape as (1)
   against `tests/release/snapshots/state_v1_0.yaml`. Protects
   G-Storage's "memory state is never stored" decision at the
   store level.
3. **Engine never reads `data/skilltrace.db`** —
   `Path.glob("src/**/*.py")` is collected; each file is scanned
   for the literal string `sqlite3.connect` and
   `data/skilltrace.db`. A hit is a failure printing the
   `file:line`. The exception is the export module, whitelisted
   by path (`src/skilltrace/export/sqlite_export.py`); G-Storage
   already named the export as the sole allowed writer.
4. **No automated pass/master/delete path** — scan `src/**` and
   `tests/**` for any code path that issues a `pass`, `master`,
   or `delete_record` command without an explicit `--i-am-sure`
   (or equivalent) learner flag. Concretely: the literal
   substring `"pass"` paired with `subprocess.run` in the same
   function is flagged. Acceptance test: no false positives in
   the seed harness and the read-only commands. This is the
   hard-boundary guard from
   `policy/automation_boundary.yaml`, pinned at the release
   layer so a future test helper that tries to shortcut a pass
   fails the RC.
5. **No ordering override from retention pressure** — assert
   that the output of `suggest reviews` sorts calendar-due
   first; the threshold-gated retention section appears as its
   own block and does not reorder the calendar-due list. Per
   T-Clock, the assertion is structural (section headers
   present, ordering of block indices), not on the exact text.
   This is G-Authority's "may warn and reorder recommendations
   in principle" decision, narrowed to "warns, does not reorder
   the calendar block" for the first RC.

### 7.3 Doc gates

Two checks, each a one-line pytest in `tests/release/`:

- `docs/spec-tier2-retention-analytics.md` exists and the
  `## Exit gates` section matches the block in §7.1–7.2
  verbatim.
- `CONTEXT.md` contains the `Retention confidence` term (added
  by G-Surfaces) and the `Memory state` term (added by
  G-Storage).

These are the only doc gates; the other Tier 2 docs
(`policy/retention_model.yaml` itself, the schema snapshot) are
checked by their respective layer tests.

### 7.4 Canonical safety-gate shape

The five-assertion set above is the canonical safety-gate shape
for this RC. Future RCs inherit the pattern
(`tests/release/test_<tier>_safety_gates.py` + two schema
snapshots) — implicit, noted but not created here.

---

## 8. Known-unwired / future upgrade paths

These are recorded so future efforts don't re-derive them; they
are **not** hooks in this RC. Tier 2 ships with no
retention-related hook into Serve (see §0) and no replacement
for the dormant `review_due: 2.0` weight.

- **Future: serve widgets.** Tier 1 Serve renders the health
  strip only (`docs/spec-tier1-serve.md:94`). A future Tier 2+
  RC may add a retention card to the daily views using the same
  `JoinedView` lenient pattern. Recorded as a follow-on
  upgrade, not a hook in this spec.
- **Future: next-score integration.** The `next`-side warning
  line in §2.2 is text. A future RC may fold a count or
  confidence-derived signal into the existing
  `policy/recommendation.yaml` factor weights — only after
  there is real recommendation traffic to tune against.
- **Future: wire `review_due`.** `policy/recommendation.yaml`
  currently carries a dormant `review_due: 2.0` weight. This
  spec does not wire it; removal or activation is its own
  cleanup. Out of scope here.
- **Future: FSRS-4.5 upgrade.** The algorithm survey
  (`research/fsrs-algorithm-survey.md`) recommends
  exponential decay for Tier 2 with `py-fsrs` (FSRS-4.5,
  MIT) as the future upgrade path. Promotion requires
  storing per-card state (breaking the pure-derivation
  guarantee of §1.3) and adopting the four-grade rating
  set; both are downstream decisions. The exponential-decay
  test suite and policy seed are the seam.

---

## 9. Invariants and constraints preserved

- Hard boundaries per `AGENTS.md` (Safety rules) and
  `docs/SAFETY_BOUNDARIES.md` are unchanged. `pass_node`,
  `master_node`, `delete_record` remain manual-only; asserted
  progress never moves backward; AI review is never an
  acceptance authority. The retention model is advisory-only
  (§1.4) and never writes.
- The engine never reads `data/skilltrace.db` (T-Exit safety
  gate #3; the `retention_memory` table widens the disposable
  mirror, not the engine's read path).
- The `Review.outcome` enum stays exactly
  `satisfactory | unsatisfactory`. No new outcome values; no
  `ReviewOutcome` term. The binary-native input is the
  exponential-decay family's native shape.
- v1's five layers (`docs/adr/0002-cut-interface-layer-from-v1.md`)
  are preserved. Tier 2 adds code in the `execution`, `policy`,
  and `release` layers only — no new layer, no revived
  `interface/` scaffold.
- Mastery is permanent (decision 8 / `CONTEXT.md:46`). The
  retention model never demotes; unsatisfactory reviews
  reduce half-life, never reset it, never change asserted
  progress.
- `policy/automation_boundary.yaml` is unchanged. The model
  is not an automation; it emits suggestions. The boundary
  check at `src/skilltrace/policy/validation.py:44` continues
  to mirror the engine constants with no churn from Tier 2.
- `docs/curriculum-authoring.md` is not affected: Tier 2 is
  not seed-data work; it is engine surface work that the
  existing seed graph (81 nodes, 124 edges, 29 verified
  resources per AGENTS.md "Current phase") operates on
  unchanged.

---

## 10. Acceptance — this map is done when

- [x] All seven wayfinder tickets on map #86 are closed
      (R-Survey, G-Authority, G-Rating, G-Storage, G-Surfaces,
      T-Clock, T-Exit, **T-Spec #94 — this spec**).
- [ ] `docs/spec-tier2-retention-analytics.md` (this file) is
      referenced from #86's `## Decisions so far`.
- [ ] No product or architecture decision remains that would
      block the seven-command + five-assertion exit gate in §7.
- [ ] Map `## Not yet specified` is empty; `## Out of scope`
      records the four ruled-out patches in §0 and §8.
- [ ] On a fresh clone, `pytest tests/policy` and the six
      `skilltrace …` commands in §7.1 exit 0 on the shipped
      seed; `tests/release/test_tier2_safety_gates.py` passes
      its five assertions; the two `tests/release/` doc checks
      pass.

---

## References

`CONTEXT.md` (especially **Memory state**, **Retention confidence**,
**Retention suggestion**, **Review**, **Hard boundary**, **Advisory
policy**, **Mastery is permanent**); `AGENTS.md` (Safety rules;
Current phase); `docs/skilltrace-application-roadmap.md` (v1 design
decisions 1, 3, 4, 7, 8, 11, 12, 16, 19, 20); `docs/adr/0001` … `0005`;
`docs/spec-tier1-serve.md:94` (Tier 1 daily loop; out of scope
for retention widgets); `src/skilltrace/policy/loading.py:18`
`POLICY_FILES`; `src/skilltrace/policy/validation.py:30`
`load_and_validate_policy`; `src/skilltrace/dispatch.py:116`
registry + sole-caller invariant; `src/skilltrace/automation.py:12`
`FORBIDDEN_ACTIONS`; `src/skilltrace/sqlite_export.py:1-7`
disposable-mirror charter; `src/skilltrace/commands/suggest.py:135`
existing `suggest reviews`; `src/skilltrace/commands/report.py:261`
existing `report reviews`; `tests/policy/conftest.py:127`
`_write_yaml`; `tests/cli/test_report_command.py`,
`tests/cli/test_today_command.py`,
`tests/policy/test_suggest_commands.py`; `policy/automation_boundary.yaml`
allowed/forbidden actions; `policy/recommendation.yaml`
dormant `review_due: 2.0`; `policy/review_cadence.yaml`
post-pass 1/3/7 ladder (model default half-life matches the
third interval as a *seed* value, not a derivation).
