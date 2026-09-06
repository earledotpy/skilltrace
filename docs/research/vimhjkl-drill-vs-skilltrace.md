# vimhjkl and drill compared with SkillTrace

**Research date:** 2026-09-03  
**Scope:** `S-Sigdel/vimhjkl` at `501762feecd0aa1c2f04089ba2f94177159b730e`
and `rr-/drill` at `a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0`. SkillTrace
comparisons cite repository `HEAD` at
`61f54164a50ed76b2481f270cb6abc2841e26265`.

**Method:** Source code, tests, and first-party README files were read from
the pinned commits only. Citations use
`owner/repo@full-commit:path:Lx-Ly`; the links resolve to the same commit.
The SkillTrace comparison uses its glossary, ADRs, and roadmap, not inferred
behavior from generated artifacts.

## Executive comparison

Both projects make correctness drive a practice schedule. `vimhjkl` is a
procedural-skill trainer: it launches real Vim, grades the resulting buffer,
cursor, register, command, and efficiency, then mutates Leitner progress.
`drill` is a deck/card SRS: the learner answers a card, the answer is marked
correct or incorrect, and the card's due date is recomputed. Neither inspected
implementation has SkillTrace's separate immutable evidence record, acceptance
authority, eligibility calculation, and explicit learner-only pass/mastery
assertions.

The important distinction is not “machine grading versus human grading.”
SkillTrace permits objective gates, but a green gate only accepts evidence; it
does not pass or master a node. `pass` and `master` remain explicit learner
acts, while later review is retention evidence rather than an automatic
demotion.

## 1. Challenge verification and authority

### vimhjkl

The challenge model is data-driven: a challenge carries starting and goal
buffers, optional cursor target/waypoint, optional yank target, and an optimal
solution/why explanation
([`challenge.py:L82-L113`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/challenge.py#L82-L113)).
`run_attempt` starts Vim interactively for a learner or headlessly for
playback, then reads the resulting buffer, cursor, register, command line,
save status, and keystrokes
([`grader.py:L311-L327`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/grader.py#L311-L327),
[`grader.py:L403-L422`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/grader.py#L403-L422)).
Scoring is objective: cursor challenges require the target and unchanged
buffer; yank challenges require the expected register bytes; buffer challenges
require the goal buffer, saving, and (where configured) an Ex command
([`grader.py:L429-L500`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/grader.py#L429-L500)).
Correctness plus an efficiency floor is called a passed outcome for the
trainer's purposes
([`engine.py:L338-L348`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/engine.py#L338-L348)).

That is strong challenge verification, but it is also an automatic progress
authority: the session records the graded outcome and updates player progress
after the attempt
([`engine.py:L488-L545`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/engine.py#L488-L545)).
There is no separate evidence submission, immutable acceptance record, or
human-only pass/master command in the inspected flow.

### drill

Review asks for a non-empty answer and compares it case-insensitively with the
card's answer aliases. A mismatch is shown to the learner with choices to mark
it incorrect, mark it correct without an alias, or mark it correct and append
an alias
([`cmd/review.py:L37-L85`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/review.py#L37-L85)).
The result is stored as `UserAnswer.is_correct`; correct answers update the
due date and incorrect cards are inserted for another pass in the same review
session
([`cmd/review.py:L87-L120`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/review.py#L87-L120)).
The manual override is useful CLI ergonomics, but it is not an evidence
authority model: the learner labels a card response, rather than submitting
an artifact against a rubric whose acceptance is frozen independently of
progress.

### SkillTrace comparison

SkillTrace defines pass eligibility as accepted, non-superseded evidence
meeting every required artifact minimum; eligibility is derived on demand.
Passing is an explicit learner command and is refused when eligibility or hard
prerequisites are absent
([`CONTEXT.md:L118-L131`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/CONTEXT.md#L118-L131)).
Acceptance has exactly two authorities: an objective gate or the learner's
explicit manual review; AI can add commentary but cannot accept evidence
([`CONTEXT.md:L141-L164`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/CONTEXT.md#L141-L164)).
ADR 0003 freezes the verdict, authority, and artifact hash at submission and
requires a new superseding record for correction
([`docs/adr/0003-acceptance-frozen-at-submission.md:L28-L44`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/docs/adr/0003-acceptance-frozen-at-submission.md#L28-L44)).

**Implication:** vimhjkl's real-world verification is a good gate
implementation pattern, and drill's explicit answer correction is a good
low-friction interaction pattern, but neither should be allowed to collapse
SkillTrace evidence acceptance into an automatic pass/master transition.

## 2. Unlock and mastery rules

### vimhjkl

The trainer exposes belt progression, but its actual new-skill unlock is a
difficulty-tier gate. A tier is considered mastered when at least 80% of its
skills (with at most one straggler) have reached box 4; the gate then rises
from difficulty 2 toward 5
([`engine.py:L260-L332`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/engine.py#L260-L332)).
The progress record is a mutable JSON entry with box, seen/pass/fail counts,
ease, timestamps, and last result. A correct result promotes or holds the box
based on efficiency; a miss demotes (with a one-miss grace at the top box)
([`store.py:L121-L180`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/store.py#L121-L180)).
This makes unlock and “mastery” operational scoring rules, not graph
eligibility backed by an evidence ledger.

### drill

`drill` has no prerequisite graph or node mastery transition in the inspected
implementation. Studying activates a card, sets its activation date, and
computes its first due date
([`cmd/study.py:L29-L31`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/study.py#L29-L31)).
Its durable abstraction is a deck containing cards, tags, activation, due
date, and answer history
([`db.py:L45-L101`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/db.py#L45-L101)).

### SkillTrace comparison

SkillTrace's five states are `locked -> available -> active -> passed ->
mastered`; readiness (`locked`/`available`) is derived, while
`active`/`passed`/`mastered` are asserted progress
([`CONTEXT.md:L30-L49`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/CONTEXT.md#L30-L49)).
Hard prerequisites are never overridden, and mastery requires a satisfactory
post-pass review on a later day before the learner explicitly masters the
node
([`CONTEXT.md:L127-L139`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/CONTEXT.md#L127-L139)).

**Implication:** vimhjkl's tier gate is a useful pattern for introducing
difficulty gradually, but SkillTrace must retain graph edges as the sole
unlock source and evidence/eligibility as separate from assertion. Drill's
deck activation is analogous to starting study, not to passing a node.

## 3. Review scheduling

### vimhjkl

Normal Leitner boxes use intervals of 0 seconds, 1 minute, 10 minutes, 1 hour,
and 8 hours, scaled by an ease multiplier. Once a skill is box-maxed and has
at least 25 successful repetitions, it enters maintenance beginning at one
day, doubling in stages up to a 30-day cap
([`engine.py:L33-L76`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/engine.py#L33-L76)).
A later miss lowers the box and therefore removes the skill from maintenance;
the tests explicitly cover due selection, blending new and old work, the
maintenance schedule, and efficiency-based promotion/demotion
([`tests/test_engine.py:L1-L149`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/tests/test_engine.py#L1-L149)).

### drill

The scheduler uses a fixed ladder from immediate review through 1 hour, 3
hours, 8 hours, 1 day, 3 days, 7 days, 14 days, 30 days, 60 days, and 120
days. It walks the full answer history, increments the bucket for correct
answers, decrements it for incorrect answers, and anchors the next due date
to the latest answer
([`scheduler.py:L6-L40`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/scheduler.py#L6-L40)).
Due cards are selected by active status and due date, then shuffled for a
review session
([`scheduler.py:L43-L68`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/scheduler.py#L43-L68)).

### SkillTrace comparison

SkillTrace schedules reviews as retention checks on passed/mastered nodes;
overdue reviews warn and reorder recommendations but do not block a
human-initiated action
([`docs/skilltrace-application-roadmap.md:L81-L84`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/docs/skilltrace-application-roadmap.md#L81-L84),
[`CONTEXT.md:L244-L268`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/CONTEXT.md#L244-L268)).
Review is therefore advisory retention evidence, not an automatic state
demotion; this preserves the hard boundary that asserted progress never moves
backward.

## 4. CLI ergonomics

`vimhjkl` provides an interactive lesson loop around real Vim and a separate
review path. Its session API injects presentation and result-review callbacks;
the presentation can quit before launch, while retry does not commit mastery
and next/quit commit the graded attempt
([`engine.py:L488-L545`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/engine.py#L488-L545)).
The CLI also has explicit drill, practice, blind, grind, review, and list
surfaces
([`cli.py:L1-L172`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/cli.py#L1-L172),
[`cli.py:L220-L340`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/cli.py#L220-L340)).

`drill` favors composable commands: `study`/`learn` accept a deck, count, and
direct/reversed/mixed mode
([`cmd/study.py:L34-L50`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/study.py#L34-L50)),
while `review` adds a maximum count and the same mode choice
([`cmd/review.py:L100-L120`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/review.py#L100-L120)).
The README explicitly targets a CLI usable through tmux/SSH and documents
multiple decks, JSON import/export, and HTML reports
([`README.md:L3-L12`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/README.md#L3-L12)).

SkillTrace's CLI ergonomics are intentionally explanation- and safety-oriented:
the roadmap centers “what evidence proves progress?”, “what review or
remediation is due?”, and “can this node be passed or mastered safely?”
([`docs/skilltrace-application-roadmap.md:L15-L39`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/docs/skilltrace-application-roadmap.md#L15-L39)).
The transferable lesson is to keep vimhjkl's explicit drill modes and drill's
small command grammar, while making every state-changing authority visible in
the command UX.

## 5. Persistence, export, and reporting

`vimhjkl` deliberately separates bundled curriculum (`skills.json`) from
player progress (`progress.json`), choosing a writable repo-root path in a
source checkout and an XDG data path when installed
([`store.py:L1-L19`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/store.py#L1-L19)).
Progress is JSON and writes are atomic through a temporary file followed by
replacement
([`store.py:L150-L180`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/store.py#L150-L180)).
The inspected CLI is oriented toward live progress/listing rather than a
separate export/report command.

`drill` stores decks, cards, tags, and answer history in SQLite under the XDG
data directory
([`db.py:L1-L40`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/db.py#L1-L40),
[`db.py:L45-L101`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/db.py#L45-L101)).
Its JSON export includes deck metadata, tags, cards, activation data, and
answer history, and can write either a named file or standard output
([`cmd/export.py:L20-L48`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/export.py#L20-L48),
[`cmd/export.py:L51-L87`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/export.py#L51-L87)).
The stats command derives HTML/JSON history, active/inactive counts, and
correct/incorrect totals from SQLite answer and activation history
([`cmd/stats.py:L38-L53`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/stats.py#L38-L53),
[`cmd/stats.py:L81-L120`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/stats.py#L81-L120)).

SkillTrace is stricter about authority and source-of-truth boundaries:
Markdown/YAML curriculum and progress are separate, exports/indexes are
disposable, and every mutating command appends an audit event
([`docs/adr/0001-separate-progress-store.md:L17-L24`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/docs/adr/0001-separate-progress-store.md#L17-L24),
[`CONTEXT.md:L311-L323`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/CONTEXT.md#L311-L323)).
Drill's export/reporting surface is a useful portability model, but an
equivalent SkillTrace export must remain a derived view and must never be read
back to compute learner state.

## 6. Tests and confidence

`vimhjkl` includes an executable, no-Vim-needed engine test script covering
new-skill difficulty gating, due ordering, blending new and old work,
maintenance scheduling, efficiency thresholds, grace demotion, and box bounds
([`tests/test_engine.py:L1-L149`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/tests/test_engine.py#L1-L149)).
The pinned `vimhjkl` tree also contains separate grader, i18n, and TUI test
modules. The pinned `drill` tree contains application modules and command
implementations but no repository-level test module; the scheduler and command
code are therefore the primary executable specification for this snapshot
([`vimhjkl` tree`](https://github.com/S-Sigdel/vimhjkl/tree/501762feecd0aa1c2f04089ba2f94177159b730e),
[`drill` tree`](https://github.com/rr-/drill/tree/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0)).

For SkillTrace, the key test obligation is different: tests must prove that
objective verification and review bookkeeping cannot invoke `pass_node` or
`master_node`, that evidence acceptance remains immutable, and that derived
eligibility cannot be mistaken for asserted progress. The hard-boundary ADR
makes those automation restrictions engine invariants rather than editable
policy defaults
([`docs/adr/0004-hard-boundaries-are-engine-constants.md:L28-L39`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/docs/adr/0004-hard-boundaries-are-engine-constants.md#L28-L39)).

## Design conclusions for SkillTrace

1. **Reuse verification seams, not authority semantics.** Real-Vim result
   inspection and deterministic objective gates are strong evidence producers.
   Their result must enter an immutable evidence record; it must not directly
   flip `passed` or `mastered`.
2. **Keep unlocks graph-derived.** Difficulty tiers and belts can improve
   recommendations or pacing, but they cannot replace hard prerequisite edges
   or create a second source of truth for readiness.
3. **Keep review advisory and append-only.** Leitner/SRS intervals are useful
   retention policy inputs. A failed review should create review evidence and
   warnings/remediation pressure, not demote asserted progress.
4. **Adopt the CLI strengths with explicit verbs.** Interactive drill modes,
   bounded review counts, standard-output export, and human-readable reports
   are compatible with SkillTrace if the command output distinguishes
   eligibility, acceptance, and assertion.

## Additive features worth considering

These are additive because they improve evidence capture, scheduling, or
observability without granting an automated process authority over
`passed`/`mastered`:

- **Interactive challenge adapters.** A node could declare a reproducible
  challenge runner whose observed result becomes an objective-gate evidence
  submission. `vimhjkl` demonstrates the useful seam: launch the real tool,
  inspect the post-action state, and grade deterministic properties
  ([`vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/grader.py:L311-L327`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/grader.py#L311-L327)).
- **Named practice modes and bounded queues.** Expose focused, review, blind,
  or mixed modes plus a maximum item count, borrowing the explicit vimhjkl
  surfaces and drill's `--count`/mode grammar
  ([`vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/cli.py:L1-L172`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/cli.py#L1-L172);
  [`drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/cmd/review.py:L100-L120`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/review.py#L100-L120)).
- **Portable derived reports.** Provide JSON-to-stdout export and
  human-readable/HTML reporting as views over Markdown/YAML truth, not as
  engine inputs. Drill's export shape and stats derivation are concrete
  portability/reporting precedents
  ([`drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/cmd/export.py:L20-L48`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/export.py#L20-L48);
  [`drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/cmd/stats.py:L81-L120`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/stats.py#L81-L120)).
- **Policy-pluggable retention intervals.** Leitner/SRS ladders can seed
  review cadence and recommendation priority while preserving SkillTrace's
  permanent asserted mastery and advisory-only overdue behavior
  ([`vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/engine.py:L33-L76`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/engine.py#L33-L76);
  [`CONTEXT.md:L127-L139`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/CONTEXT.md#L127-L139)).
- **Atomic progress writes and explicit answer correction UX.** Keep
  SkillTrace's append-only records, but make correction and retry flows as
  low-friction as drill's correct/incorrect/alias choices and vimhjkl's
  retry-without-commit loop
  ([`drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/cmd/review.py:L37-L120`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/review.py#L37-L120);
  [`vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/engine.py:L488-L545`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/engine.py#L488-L545)).

## Open questions for SkillTrace

1. **What is the portable challenge contract?** Should an objective gate
   return only accepted/rejected, or also structured observations such as
   efficiency, cursor position, or captured output? `vimhjkl` grades several
   post-action dimensions and an efficiency floor
   ([`vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/grader.py:L429-L500`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/grader.py#L429-L500);
   [`vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/engine.py:L338-L348`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/engine.py#L338-L348)), while SkillTrace freezes the verdict, authority, and artifact hash
   ([`docs/adr/0003-acceptance-frozen-at-submission.md:L28-L44`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/docs/adr/0003-acceptance-frozen-at-submission.md#L28-L44)).
2. **Where do interactive runners execute?** Real-tool verification raises
   questions about timeouts, side effects, dependency availability, captured
   artifacts, and reproducibility. The current comparison establishes the
   grading seam, but not a safe execution policy; this needs an explicit
   gate contract rather than an implicit subprocess convention.
3. **How should retention schedules map to nodes and evidence?** Drill anchors
   due dates to answer history and vimhjkl changes boxes on efficiency and
   misses ([`drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/scheduler.py:L6-L68`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/scheduler.py#L6-L68);
   [`vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/store.py:L121-L180`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/store.py#L121-L180)). SkillTrace must decide whether a review schedules the node, a specific artifact spec, or an evidence/review record, while keeping overdue status advisory.
4. **What does a useful export promise?** Drill exports answer history and
   activation state from SQLite ([`drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/cmd/export.py:L51-L87`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/export.py#L51-L87)), but SkillTrace exports are disposable and never read back
   ([`docs/adr/0001-separate-progress-store.md:L17-L24`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/docs/adr/0001-separate-progress-store.md#L17-L24)). The open design choice is which stable, reviewable fields external consumers need without accidentally creating a second source of truth.
5. **Which test boundary proves authority separation?** vimhjkl's tests
   thoroughly exercise scheduling and box transitions
   ([`vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:tests/test_engine.py:L1-L149`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/tests/test_engine.py#L1-L149)). SkillTrace additionally needs regression tests that objective verification, review scheduling, sync, and exports cannot invoke `pass_node`/`master_node`, mutate immutable evidence, or demote asserted progress, as required by the hard-boundary decision
   ([`docs/adr/0004-hard-boundaries-are-engine-constants.md:L28-L39`](https://github.com/earledotpy/skilltrace/blob/61f54164a50ed76b2481f270cb6abc2841e26265/docs/adr/0004-hard-boundaries-are-engine-constants.md#L28-L39)).
