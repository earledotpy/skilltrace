# v3 single-learner validation runbook

**Ticket:** [T-ValidationExecution — run the moderated usability and accessibility contract](https://github.com/earledotpy/skilltrace/issues/344) (wayfinder map #327)
**Contract:** [G-ValidationContract — define moderated usability and accessibility validation](https://github.com/earledotpy/skilltrace/issues/339), re-scoped by [G-SingleLearnerValidation — re-scope the validation gate to single-learner structured self-evaluation](https://github.com/earledotpy/skilltrace/issues/347) — this runbook operationalises it; where the two differ, the re-scope wins.
**Feeds:** [G-FinalValidationVerdict — decide the final product direction from observed evidence](https://github.com/earledotpy/skilltrace/issues/345) via `docs/validation/v3-observation-report.md`.
**Status:** single-learner self-evaluation. One learner wears every hat (moderator, evaluator, accessibility checker) and records which hat produced each entry. HITL — this document is not the evidence; the filled observation report is.

Assets under test (throwaway decision aids, in-memory, no engine writes):

- `prototype/p-core-journey.html` — Guided study loop. Pinned route fixture dated **2026-11-17**, real `data.pandas.dataframe_basics_01` node, real ArtifactSpec `spec.data.pandas.dataframe_basics`, shipped cold-start counts (100 nodes, 49 available / 51 locked).
- `prototype/p-operations-workspace.html` — Operations capabilities with an A/B variant switcher and seeded/limited fixture toggle.

Known constraints inherited from the prototype resolutions (recorded, not re-litigated here): mastery's two-step confirmation has no Guided prototype surface; the Operations prototype renders no per-capability detail views, its nav is client-side buttons rather than links, and it shows no could-not-compute state. See §14 — these become *prototype limitations* in the report, never silent passes.

---

## 1. Roles (hats worn by the one learner)

- **Moderator** — runs the script, keeps time, never rescues before the recovery measure is recorded, logs probes only after task completion.
- **Evaluator** — records the authoritative learner-visible result for each scenario and whether the learner could recover without CLI vocabulary.
- **Accessibility checker** — owns §11.

Preference, compliments, or prior tool familiarity are never acceptance signals.

## 2. Setup

- Two evergreen browser windows (or profiles), each opening one prototype file directly by path. No server required.
- Browser devtools with axe-core (axe DevTools extension or Lighthouse) for the automated pass; run against the file URL at 100%, 200% zoom, and a 320 px-wide responsive viewport.
- Screen reader for the SR pass (NVDA + Firefox or VoiceOver + Safari — record which).
- Viewport presets: desktop (≥1280 px), narrow (≤480 px, plus 320 px reflow spot-check).
- Recording: screen capture or notes, stopwatch per task.
- Between passes: close all tabs and reopen the prototype files fresh (state is a page-lifetime JS variable; a reload is a full reset).

## 3. The learner

One learner — the repo owner, the only actual SkillTrace learner — runs every pass. Prior SkillTrace exposure is inherent and recorded; it is never mistaken for comprehension, so comprehension probes are still answered verbatim and classified against the domain contract.

The learner runs three passes over the task set:

- **Pointer pass** — ordinary mouse + keyboard.
- **Keyboard-only pass** — no pointer for the whole pass; record any moment a pointer is reached for.
- **Screen-reader pass** — SR used for at least the representative states in §11 (NVDA/Firefox or VoiceOver/Safari — record which).

## 4. Pass order and fixture assignment

Within-learner, counterbalanced across the two prototypes: the pointer pass runs Guided first then Operations; the keyboard-only and screen-reader passes run Operations first then Guided, so no single confound (pointer vs keyboard-only vs screen-reader) tracks one mode.

| Pass | Order 1 | Order 2 |
|------|---------|---------|
| Pointer | Guided | Operations |
| Keyboard-only | Operations | Guided |
| Screen-reader | Operations | Guided |

Cross-participant counterbalance (half a cohort Guided-first, half Operations-first) is **insufficient evidence / deferred** — there is no cohort. Recorded, never fabricated.

Equivalent fixture states per mode — the modes never share a mutated state:

- **Guided** runs on the pinned **active** fixture (`RESET_ACTIVE`: open Session `ses.snapshot.001`, one work item, open Blocker `blk.snapshot.001`, overdue Review `rvw.snapshot.001`); the cold fixture (`RESET_COLD`) is reserved for cold-start/empty tasks.
- **Operations** runs on the **seeded** fixture (100 nodes, 49 available, 51 locked, 8 sessions, 12 evidence records, 3 reviews — same richness band as Guided's active state); the **limited** fixture (3 nodes, 1 available, 0 evidence) is reserved for empty/limited-data tasks.

Because Guided mutates in-memory state and Operations has no write actions, each pass's second mode still starts from an untouched fixture — only a reload is needed between modes.

## 5. Fixture reset procedure (per scenario, per pass)

**Guided — hard reset between passes:** reload the file. Verify the result panel reads *"Prototype ready"* and the state table matches the expected baseline for the fixture in use.

**Guided — soft reset between scenarios:** click the scenario button (it dispatches the scenario's own reset: `RESET_COLD` or `RESET_ACTIVE`) *or* press **Reset active fixture** / **Reset cold fixture** in Free play. Verify:

- Active baseline: Session `ses.snapshot.001 · open`, node `active`, 45 recorded minutes, 1 open Blocker, 0 accepted records, pass eligibility `false`, today `2026-11-17`, one overdue Review (`rvw.snapshot.001`).
- Cold baseline: no Session, node `available`, no work/records/Blockers, pass eligibility `false`, same four Review rows (one overdue), counts 49 available / 51 locked.

**Operations — reset:** reload the file, then set the fixture toggle (**Seeded fixture** / **Limited fixture**) and confirm the header state label (`seeded` / `limited`) and the count cards match: seeded → 100/49/51, 8 sessions, 12 evidence, 3 reviews; limited → 3 nodes, 1 available, 2 locked, 1 session, 0 evidence, 0 reviews.

Record in the report §1 that every scenario row names the reset used and that its baseline check passed *before* the learner acted. A scenario started from a dirty state is void and rerun.

## 6. Session script

1. **Orientation (5 min).** State the think-aloud rule ("say what you're trying, expecting, and noticing") and hold to it; this tests the prototype, not the learner; no CLI vocabulary is needed or expected.
2. **Task performance (think-aloud).** Read the task goal verbatim (§7/§8), start the stopwatch, stay silent. On visible struggle note time/errors and may, **after** the recovery measurement point, use the hint ladder in order (§7.3) — hints are recorded as errors-with-assist.
3. **Probes after task completion only.** Use the comprehension probe bank (§7.4); never probe mid-task.
4. **Retrospective (10 min).** What confused, what was trusted, what would be feared doing wrong; accessibility comfort (keyboard/SR passes: where the experience broke); final open comments.

Same script and task order within each prototype for every pass; only the across-mode order counterbalances (see §4).

## 7. Task script — Guided (`p-core-journey.html`)

### 7.1 Driving rule

The learner drives **free play** with the task goal as the prompt; the "Guided walkthroughs" panel is held scaffolding only — ignore it, and treat its step list as the hint ladder if free play fails. Scenario buttons are used for resets (§5), not to reveal steps. This keeps time-to-completion and first-attempt measures meaningful.

### 7.2 Tasks (map to the 8 built-in scenarios)

| # | Task goal (read verbatim) | Prototype scenario | Reset | Critical action(s) |
|---|---------------------------|--------------------|-------|--------------------|
| G1 | "You've never opened this before. Find what you should study first and begin — without changing anything you don't mean to." | Cold start & discovery | `RESET_COLD` | inspect, start Session |
| G2 | "Your Session is already open. Pick up where you left off and record 30 more minutes of work on this node." | Normal active study | `RESET_ACTIVE` | resume, log work |
| G3 | "You're stuck on groupby and don't want to lose that. Make the stuckness visible, and make sure it stays visible even if you close the Session." | Blocked work & Blocker | `RESET_ACTIVE` | log blocked work, create Blocker, resolve Blocker |
| G4 | "Your solution script passed your own check — submit it as evidence and become eligible to pass; then pass." | Evidence & pass | `RESET_ACTIVE` | submit evidence, open pass confirmation, confirm pass |
| G5 | "You're done for today. Close the Session — and be clear what closing does *not* do." | Safe Session close | `RESET_ACTIVE` | log work, close Session |
| G6 | "You try to pass, but the system refuses. Recover: correct what was rejected, notice a stale confirmation when truth changes, and pass when genuinely eligible." | Refusal & recovery | `RESET_ACTIVE` | refusal handling, correction, pass |
| G7 | "A review you were meant to do earlier is overdue. Do it — it must not disturb your Session or your progress." | Review completion | `RESET_ACTIVE` | complete Review |
| G8 | "Deliberately do three wrong things: start a second Session, close in the future, and submit to a gate that can't run. Then close the Session honestly." | Failure & empty recovery | `RESET_ACTIVE` | refusals, operational failure, honest close |
| G9* | "Mastery is a separate, deliberate act after passing. Show how you would master this node." | **No prototype surface** | — | master (two-step) |

G9 is run as an **unaided intent probe only**: no buttons exist, so record what the learner expects to do and what they find instead. Never fake a mastery action. (Prototype limitation, §14.)

### 7.3 Hint ladder (free play failures, in order; each level logged)

1. Restate the goal. 2. Name the region of the page (focus panel / branches / free play). 3. Name the control. 4. Demonstrate. Recovery-without-hint vs recovery-with-level-N is the recovery measure.

### 7.4 Comprehension probe bank (after tasks; record verbatim)

- "What is the difference between what you just did to *pass* vs *master*?"
- "Did anything you saw get written down permanently? How do you know?"
- "If you corrected something earlier, what happened to the original?"
- "What does closing the Session do — and not do?"
- "What makes a node locked, and what would change that?"
- "You saw a refusal. What did it refuse, and what state did it leave behind?"
- CLI-vocabulary check: after any failure, could the learner recover without knowing a command name? (yes/no + evidence quote)

## 8. Task script — Operations (`p-operations-workspace.html`)

Variant handling: the structure verdict favours **A's persistent chrome with B's capability-directory home** (see P-OperationsWorkspace). Run capability tasks in **variant A** first; repeat the landing tasks in **variant B** to evidence the directory-home claim; record per-variant results separately (switcher: bottom bar or ←/→ keys).

| # | Task goal (read verbatim) | Capability | Fixture | Critical action(s) |
|---|---------------------------|------------|---------|--------------------|
| O1 | "Land here cold: what is the state of this learner's graph in one glance?" | Home (directory) | seeded | orient, read counts |
| O2 | "Find out whether `agents.agent_fundamentals_01` can be started, and what evidence it wants." | Graph → node readiness | seeded | inspect readiness |
| O3 | "Find the most recent evidence record and describe its status." | Evidence Vault | seeded | inspect evidence |
| O4 | "Which reviews are due, and which are overdue?" | Reviews | seeded | inspect reviews/retention |
| O5 | "What can analytics tell you — and how would you know it isn't invented?" | Analytics | seeded | inspect derivations |
| O6 | "Prepare a portfolio export view; say what it does and doesn't claim." | Portfolio | seeded | inspect export |
| O7 | "Is this repository healthy? Where would you look?" | Health | seeded | inspect diagnostics |
| O8 | "Same landing, but the learner has almost no history — what does the product tell you?" | Home + at least Graph/Evidence | **limited** | truthful empty states |
| O9* | "A number the product can't compute — where does that appear?" | any | seeded | **no surface exists** (§14) — record expectation + absence |

O9 is an expectation probe only; absence is recorded as a prototype limitation, never a pass.

## 9. State-variant coverage matrix

The contract requires empty, limited-data, could-not-compute, operational-failure, stale, and narrow-window variants plus representative accessibility states. Coverage below is per pass; every *critical path* task (G1–G8, O1–O7) runs in every pass.

| Variant | Where exercised | Minimum coverage |
|---------|-----------------|------------------|
| Empty / cold start | G1 (cold fixture) | every pass |
| Limited data | O8 (limited fixture) | every pass |
| Operational failure | G8 gate-unrunnable step | every pass |
| Stale / SERVER_CHANGED | G6 stale-confirmation step; G8 honest close | every pass |
| Refusal & recovery | G6 | every pass |
| Could-not-compute | O9 probe | every pass (expectation + recorded absence) |
| Narrow window (≤480 px) | one Guided block + one Operations block per pass, see §11 | every pass |
| Mastery absent | G9 probe | every pass |

## 10. Measures and recording

One row per pass × scenario, into the observation report §3:

- **Outcome:** completed / completed-with-hint / failed (+ verbatim slip).
- **Time (s)** from goal read to learner-declared done.
- **Errors:** count + description (wrong control, wrong mental model, dead end, CLI-vocabulary guess).
- **Recovery:** none needed / self-recovered / recovered at hint level N; and whether recovery needed CLI vocabulary (yes/no).
- **Comprehension:** probe answers verbatim (§7.4), classified correct / partial / incorrect against the domain contract.
- **Accessibility defects:** observable breakage during the task (focus loss, unnamed control, contrast, reflow, SR announcement failure) + severity.

**Thresholds (from the contract, as re-scoped):** critical learner actions ≥80% first-attempt completion; ≥90% recovery after refusal/failure; *every* critical action successful in *every* pass before acceptance; **zero** critical safety or domain-boundary violations. Accessibility is a mandatory gate: every mandatory criterion passes or acceptance is blocked. The cross-participant reading of "every participant" is insufficient evidence / deferred (there is no cohort) — recorded explicitly, never a pass.

## 11. Accessibility checks

### Automated (per prototype, record tool + version + full violation list)

axe-core/Lighthouse at 100% zoom, 200% zoom, and 320 px viewport: semantic structure, accessible names, contrast, reflow. Any violation is a finding (classified §12), not auto-dismissed.

### Manual walkthrough matrix (per prototype unless noted)

Walk representative states: cold start, active Session (Guided), a refusal result, an empty/limited state (Operations), and a detail view.

| Check | Method | Pass criteria |
|-------|--------|---------------|
| Keyboard-only operation | Whole pass, keyboard-only pass + checker spot-check | every action reachable, logical order, no trap except modal with Escape + close |
| Focus behaviour | Tab/activate through tasks | visible focus, focus lands on outcome/result panel after actions |
| Screen reader | SR pass + checker pass | landmarks/headings navigate; status changes announced (`aria-live`); counts and states readable |
| Contrast | axe + spot-check of tokens | WCAG 2.2 AA for text, controls, focus, status graphics; status never colour-only |
| 200% zoom / reflow | Zoom each representative state | content and actions usable; horizontal scroll only for true 2-D data |
| Reduced motion | OS/ emulation | nonessential animation removed; nothing motion-dependent |
| Touch | Emulated touch or device | targets ≥44×44 where feasible; no hover/drag-only essentials |
| Narrow window | 480 px + 320 px | Today, Active Session, SkillNode detail, Blockers, Evidence, pass/master/close still available; complex views disclose to lists |
| Graph equivalence | Keyboard + SR on Operations graph | complete nonvisual equivalent: nodes/edges named, states, prereq context, same actions |

## 12. Findings classification

- **Critical:** unsafe action possible, hidden/fabricated domain state, inaccessible essential path, any SkillTrace boundary violation (automated pass/master, demotion, override, AI acceptance).
- **Major:** materially impairs completion, comprehension, recovery, or required inspection.
- **Minor:** recorded, does not block completion.

No aggregation into a score. Counts + full descriptions go to report §6.

## 13. Decision rules (restated for the verdict ticket)

- **Accept** only when all critical learner paths, required Operations inspection paths, domain-boundary checks, and mandatory accessibility gates pass.
- **Revise** when failures are recoverable, the domain model is safe, and a concrete prototype follow-up can test the repair.
- **Reject** when the core study loop, canonical domain contract, or accessibility model is unsafe, fundamentally unclear, or cannot meet the required interaction behaviour without a new product direction.

## 14. Known prototype limitations (pre-seeded; extend during sessions)

Recorded so the evaluator judges the *journey*, not the scaffolding — and so none of these is silently counted as a pass:

1. **Mastery** has no Guided surface (G9 records expectation only).
2. **Operations per-capability detail views** are not rendered (nav reaches headings/anchors); owned by G-OperationsSurfaces contract, not evidenced here.
3. **Operations nav is client-side buttons**, not links — URL-addressability is an IA contract, not demonstrated by this asset.
4. **No could-not-compute state** in the Operations asset (O9 records expectation + absence).
5. **No live timer / no client mutation** — server-rendered target shown as discrete fresh-page outcomes; all failures, receipts, outcomes are fixture-based.
6. **Copy is prototype copy**, not final product copy.
7. **A/B switcher chrome** (bottom bar, arrow keys) is scaffolding, not a product surface.

A limitation that leaves a contract-required claim untested ⇒ **insufficient evidence** in the matrix, explicitly.

## 15. After the sessions

1. Fill `docs/validation/v3-observation-report.md` completely (fixture procedure as executed, learner profile, pass order, scenario results, raw measurements, a11y findings, findings register).
2. Keep the three-way distinction intact: observed learner outcomes | evaluator judgments | prototype limitations.
3. Post the report (or link) as the resolution comment on **T-ValidationExecution** and close it — that unblocks **G-FinalValidationVerdict**, which produces the claim-by-claim accept/revise/reject matrix for **G-ProductHandoff**.
4. Do not carry thresholds, verdicts, or spec edits anywhere else: a decision lives in its ticket; the map only indexes its gist.

