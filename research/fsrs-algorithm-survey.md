# FSRS Algorithm Survey for Tier 2 Retention Analytics

Research findings for SkillTrace's Tier 2 retention analytics feature. This
document surveys the spaced-repetition algorithm landscape and evaluates each
option against SkillTrace's constraints.

## SkillTrace constraints

- Binary review outcomes only: `satisfactory` / `unsatisfactory`
- Sparse history: ~3-5 reviews per node, ~81 nodes total
- Fixed 1/3/7-day review scheduling after pass; manual only after mastery
- Mastery is permanent and never demotes
- Reviews are on passed/mastered nodes only (retention, not learning)
- Single learner, local-first, CLI-first
- Review fields: id, node_id, status (scheduled/completed/cancelled),
  scheduled_for, created_at, completed_at, outcome, result_summary,
  cancelled_at, cancel_reason

---

## 1. FSRS-5 / FSRS-4.5

### Algorithm overview

FSRS (Free Spaced Repetition Scheduler) uses a three-component memory model:
**Difficulty** (D, 1-10), **Stability** (S, days until R=90%), and
**Retrievability** (R, current recall probability). It models the forgetting
curve as a power function and computes optimal intervals from predicted
retrievability at the desired retention threshold.

### Review-log inputs

| Input | FSRS-4.5 | FSRS-5 |
|-------|----------|--------|
| Rating granularity | 4 grades: Again(1), Hard(2), Good(3), Easy(4) | Same |
| Timestamps | Required: review datetime, scheduled datetime | Same + same-day review support |
| Review count per card | Works from first review; optimizes better with 16+ reviews | Same |
| Card state | Stability, difficulty, reps, lapses, learning state | Same + short-term memory state |

### How they handle binary outcomes

FSRS is designed for 4-grade ratings. Binary satisfactory/unsatisfactory maps
to a **2-out-of-4** subset:
- `satisfactory` -> `Good` (rating 3)
- `unsatisfactory` -> `Again` (rating 1)

This discards the Hard/Easy distinction, which means:
- No difficulty gradient between "barely remembered" and "easy recall"
- Stability increments are less granular (Hard gives smaller S increase than
  Good; Easy gives larger)
- The optimizer has fewer signal points to work with

FSRS does work with binary inputs — the algorithm degrades gracefully to
approximately SM-2-level accuracy when only Again/Good are used, because the
core stability update function still operates on the rating axis.

### Cold-start behavior

- **FSRS-4.5**: Initial stability `S_0(G)` is looked up from the first rating
  (4 parameters: w[0]-w[3]). No prior reviews needed for a single card's
  first scheduling decision.
- **Parameter optimization**: Anki's integration requires 400+ reviews for full
  optimization of all 17 parameters, but pretrain (optimizing only the first 4
  parameters) works with as few as 16 reviews. Default parameters trained on
  700M+ reviews work well out of the box.
- **Practical minimum**: With SkillTrace's ~81 nodes × ~3-5 reviews = ~240-405
  total reviews, full optimization is marginal. Default parameters would be the
  safe choice.

### py-fsrs Python library

- **Package**: `fsrs` on PyPI (version 6.3.2 as of Aug 2026)
- **License**: MIT
- **Maturity**: 474 GitHub stars, 122 commits, actively maintained (last release
  Aug 9, 2026), two maintainers (Jarrett Ye, joshdavham)
- **Python**: Requires 3.10+
- **Capabilities**: Scheduler, Card, Rating, ReviewLog, Optimizer (optional
  extra via `pip install "fsrs[optimizer]"`)
- **Operates without stored memory state?** No — FSRS requires per-card state
  (stability, difficulty, reps, lapses, learning state). These must be stored
  between reviews. The py-fsrs Card object serializes to/from JSON.
- **Relevance to SkillTrace**: The library could be a direct dependency, but
  SkillTrace would need to store FSRS card state alongside review records.
  This introduces a new stateful component that must persist across CLI runs.

### FSRS-5 vs FSRS-4.5

FSRS-5 adds short-term memory modeling (same-day review formulas) and has 19
parameters vs 17. The accuracy improvement over FSRS-4.5 is marginal (~1-2%
better log loss). Since SkillTrace reviews are multi-day (1/3/7 day cadence),
same-day review handling is irrelevant. **FSRS-4.5 is sufficient.**

---

## 2. SM-2 (Anki's Legacy Algorithm)

### Algorithm overview

SM-2 (SuperMemo 2, 1987) adjusts an "easiness factor" (EF, minimum 1.3) and
computes the next interval as `previous_interval × EF`. On the first review,
the interval is 1 day; subsequent intervals grow by the EF multiplier.

### Review-log inputs

| Input | Details |
|-------|---------|
| Rating | 0-5 scale (0=blackout, 5=perfect). Anki maps to Again(1)/Hard(2)/Good(3)/Easy(4) |
| Repetitions | Count of consecutive successful reviews |
| Previous EF | Current easiness factor |
| Previous interval | Current interval in days |

### How it handles binary outcomes

SM-2's original scale is 0-5, but Anki's adaptation maps it to 4 grades.
Binary maps naturally:
- `satisfactory` -> Good (quality 3-4 in original scale)
- `unsatisfactory` -> Again (quality 0-2)

The EF update formula `EF' = EF + (0.1 - (5-q) × (0.08 + (5-q) × 0.02))`
adjusts based on quality, so binary outcomes produce coarser EF adjustments
than the full scale.

### Cold-start behavior

- First review: interval = 1 day, EF = 2.5 (default)
- No optimization needed — SM-2 uses fixed heuristics, not trained parameters
- Works immediately with zero review history

### Python implementations

| Package | License | Notes |
|---------|---------|-------|
| `sm-2` (open-spaced-repetition) | MIT | Clean, modern. Python 3.10+. v0.3.0 (Dec 2024) |
| `anki-sm-2` (open-spaced-repetition) | AGPL-3.0 | Anki's specific SM-2 variant. **License incompatible with permissive use** |
| `supermemo2` | MIT | Alternative implementation |

### Limitations vs FSRS

- ~81% worse log loss than FSRS-4.5 on benchmarks
- No difficulty modeling — all items share the same EF dynamics
- "Ease hell" problem: EF can ratchet down irreversibly with difficult items
- No retrievability prediction — cannot answer "what is the current recall
  probability?"

---

## 3. Exponential Decay Heuristic

### Algorithm overview

A simple model: each item has a half-life `h` (configurable, default ~7 days).
After a satisfactory review, the half-life is multiplied by a factor (e.g.,
1.5-2.0). After an unsatisfactory review, it is reset or reduced (e.g.,
divided by 2). Retrievability at time `t` since last review is:

```
R(t) = 0.5^(t / h)
```

The next review is scheduled when `R(t)` drops to a threshold (e.g., 0.8).

### Input requirements

| Input | Details |
|-------|---------|
| Outcome | Binary: satisfactory / unsatisfactory |
| Timestamp | Last review time |
| Half-life | Per-item, updated after each review |

### Binary sufficiency

**Fully sufficient.** This model was designed for binary outcomes. The original
Ebbinghaus forgetting curve and Duolingo's half-life regression both operate
on binary recall data (Settles & Meeder, 2016, PNAS).

### Advantages for SkillTrace

- Minimal state: only half-life and last-review timestamp per node
- No external library dependency
- Trivially cold-starts: assign default half-life on first pass
- Binary outcomes are the native input, not a degraded mapping
- Easy to explain in reports ("this skill fades with a 7-day half-life")

### Disadvantages

- No difficulty modeling — all nodes share the same decay dynamics
- No per-learner personalization (no optimization)
- Fixed growth factor doesn't adapt to individual patterns
- Less accurate than FSRS on benchmarks (no published comparisons exist for
  this simplified model, but it lacks the DSR model's expressiveness)

---

## 4. Binary-to-Rating Mapping

### Mapping strategies

| Algorithm | Satisfactory maps to | Unsatisfactory maps to | What's lost |
|-----------|---------------------|----------------------|-------------|
| FSRS-4.5 | Good (3) | Again (1) | Hard/Easy granularity — ~10-15% less precise stability updates |
| FSRS-4.5 (alt) | Good (3) | Hard (2) | Again triggers lapse state; using Hard avoids lapse but misrepresents failure |
| SM-2 | Quality 4 | Quality 1 | Full 0-5 scale — EF adjustments coarser |
| Exponential decay | half-life × growth | half-life / reduction | Nothing — binary is the native input |

### Heuristics for mapping binary to 4-grade

If FSRS's 4-grade granularity is desired from binary data, possible heuristics:

1. **Fixed mapping** (recommended): Satisfactory=Good, Unsatisfactory=Again.
   Simple, honest, no information fabrication.

2. **Retrievability-based**: Map based on R at review time. If R was high
   (reviewed early) and satisfactory -> Easy; if R was low (overdue) and
   satisfactory -> Good. This extracts timing signal from the binary outcome.
   Requires storing the scheduled-vs-actual review gap.

3. **Response-time proxy**: If review time is recorded, fast satisfactory ->
   Easy, slow satisfactory -> Good. Not applicable to SkillTrace (no response
   time captured).

4. **History-based**: After several satisfactory reviews in a row, promote to
   Easy. After a recent failure followed by satisfactory, keep as Good.
   Requires per-node state tracking.

### Recommendation

For Tier 2, **fixed mapping (Good/Again) is sufficient.** The timing-based
heuristic (option 2) is the only one that extracts real signal without
fabricating information, and it adds complexity. If SkillTrace later captures
response time or confidence scores, the mapping can be refined.

---

## 5. Overdue and Cancelled Review Handling

### How each algorithm treats delayed reviews

| Algorithm | Overdue treatment |
|-----------|------------------|
| FSRS | Models retrievability decay. A successful review when R is low (overdue) produces a larger stability increase than one at R=0.9. The increase converges to an upper bound — reviewing months late doesn't give infinite credit. |
| SM-2 | Uses a linear bonus: `interval × (delay_days / scheduled_days)`. Can grow without bound for very overdue items. |
| Exponential decay | Naturally handled — R(t) is computed from actual elapsed time, so overdue reviews see lower R and schedule the next review accordingly. |

### Cancelled reviews

No standard algorithm handles cancelled reviews — they are an SkillTrace-specific concept.

**FSRS/SM-2**: Both expect a rating for every review. A cancelled review
provides no rating, so it should be **excluded from the algorithm's input
entirely.** It is historical noise: the learner decided not to assess, which
is different from failing.

**Exponential decay**: Same — cancelled reviews contribute nothing. The
half-life remains unchanged.

### SkillTrace integration approach

- **Cancelled reviews**: Skip them in scheduling calculations. They are
  audit history only.
- **Overdue reviews**: FSRS naturally accounts for delay via retrievability.
  Exponential decay does the same via R(t). SM-2's linear bonus is less
  principled.
- **Scheduled vs completed gap**: Store both `scheduled_for` and
  `completed_at`. The gap is the "delay" that FSRS and exponential decay
  use to compute R at review time.

---

## 6. Comparison Table

| Criterion | FSRS-4.5 | SM-2 | Exponential Decay |
|-----------|----------|------|-------------------|
| Accuracy (vs SM-2) | ~81% better log loss | Baseline | Unknown (simpler model) |
| Rating input | 4-grade (Again/Hard/Good/Easy) | 0-5 or 4-grade | Binary only |
| Binary compatibility | Degrades gracefully | Works | Native |
| Cold-start | Default params from day 1 | Always works | Default half-life |
| Per-card state | S, D, reps, lapses, learning state | EF, interval, reps | Half-life, last review |
| State storage required | Yes (serialized Card object) | Yes (EF, interval) | Minimal (2 values) |
| Parameter optimization | Yes (17 params, needs 400+ reviews) | No (fixed heuristics) | No (fixed heuristics) |
| Python library | `fsrs` (MIT, v6.3.2, mature) | `sm-2` (MIT, v0.3.0) | None needed |
| Library maturity | High (474★, actively maintained) | Low (6★, early) | N/A |
| Retrievability prediction | Yes (core feature) | No | Yes (R(t) = 0.5^(t/h)) |
| Overdue handling | Bounded stability increase | Linear (unbounded) | Natural via R(t) |
| Complexity | High (DSR model, 17 params) | Low | Very low |
| SkillTrace fit | Good but heavy | Adequate | Best fit for constraints |

---

## 7. Recommendation

### Tier 2 initial implementation: Exponential Decay

**Rationale:**

1. **Binary-native**: SkillTrace's `satisfactory`/`unsatisfactory` is the
   direct input. No mapping loss, no approximation.

2. **Minimal state**: Only two values per node (half-life, last review time).
   Fits naturally into SkillTrace's YAML-based state store without
   introducing a new serialized object format.

3. **Zero dependencies**: No external library. The algorithm is ~20 lines of
   Python.

4. **Transparent**: The half-life concept is explainable in reports and
   advisory output ("This skill's retention half-life is 12 days").

5. **Cold-start friendly**: Assign a default half-life (e.g., 7 days matching
   the current 1/3/7-day schedule) on pass. First review refines it.

6. **Overdue handling**: Naturally accounts for delayed reviews via R(t).

### Future upgrade path: FSRS-4.5

If SkillTrace later captures richer signal (confidence grades, response time,
or multiple review types), FSRS-4.5 via `py-fsrs` is the natural upgrade:

- Same DSR model, same concepts (stability, retrievability)
- The exponential decay model's half-life is analogous to FSRS's stability
- Migration: map each node's current half-life to an initial FSRS stability
  estimate, then let FSRS take over

The `py-fsrs` library (MIT, mature, actively maintained) is the right choice
when that upgrade happens. The `sm-2` library is an alternative but provides
less accuracy and no retrievability prediction.

### What to watch

- FSRS-4.5's default parameters are trained on millions of flashcard reviews.
  SkillTrace's "reviews" are qualitatively different (skill verification,
  not flashcard recall). The defaults may not transfer well. If FSRS is
  adopted, a SkillTrace-specific optimization pass would be valuable once
  enough history accumulates.
- The `anki-sm-2` package is AGPL-3.0 licensed — avoid it.
- FSRS-5/6 add same-day review modeling, which is irrelevant for SkillTrace's
  multi-day cadence. FSRS-4.5 is sufficient.

---

## References

- [FSRS Algorithm (open-spaced-repetition)](https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler)
- [py-fsrs Python package](https://github.com/open-spaced-repetition/py-fsrs) — MIT license
- [sm-2 Python package](https://github.com/open-spaced-repetition/sm-2) — MIT license
- [FSRS-4.5/5/6 Wiki](https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm)
- [Enhancing Human Learning via Spaced Repetition Optimization (Settles & Meeder, 2016, PNAS)](https://www.pnas.org/doi/10.1073/pnas.1815156116)
- [SRS Benchmark](https://github.com/open-spaced-repetition/srs-benchmark)
- [Anki FSRS FAQ](https://faqs.ankiweb.net/frequently-asked-questions-about-fsrs.html)
- [FSRS technical explanation (Expertium)](https://expertium.github.io/Algorithm.html)
