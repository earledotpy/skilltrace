# v3 single-learner validation — observation report

**Ticket:** [T-ValidationExecution — run the moderated usability and accessibility contract](https://github.com/earledotpy/skilltrace/issues/344) (wayfinder map #327)
**Protocol:** `docs/validation/v3-usability-runbook.md` (implements [G-ValidationContract — define moderated usability and accessibility validation](https://github.com/earledotpy/skilltrace/issues/339), re-scoped by [G-SingleLearnerValidation — re-scope the validation gate to single-learner structured self-evaluation](https://github.com/earledotpy/skilltrace/issues/347)).
**Consumers:** this report is the *evidence* for [G-FinalValidationVerdict — decide the final product direction from observed evidence](https://github.com/earledotpy/skilltrace/issues/345) — it is not the verdict. Insufficient evidence is recorded explicitly; it is never a pass.

**Status:** EVIDENCE COMPLETE — the learner confirmed this report finished on 2026-11-07 and settled the scope question it left open: **the pointer (mouse) pass is sufficient evidence for the learner's needs — they are the primary user — and the accessibility passes are deferred to a later effort** (recorded in wayfinder map #327, Out of scope). **One of three passes run: the pointer (mouse) pass, both prototypes, complete.** The keyboard-only and screen-reader passes were **not run, by the learner's decision** (stated reason: the prototype does not have enough functionality for a keyboard pass). They are recorded as not run, not as passed: deferral is a scope decision, not an accessibility result. Evidence tags: **O** = observed learner outcome/quote, **E** = evaluator-run or evaluator judgment, **L** = prototype limitation. The learner has reviewed this report; the comprehension classes and **O**-finding severities remain **evaluator judgments**, not observed facts.

---

## 1. Fixture reset procedure (as executed)

| Item | Record |
|------|--------|
| Prototype files + integrity (path, mtime/hash) | `p-core-journey.html`: sha256 `7b2948eb2f0c0420f343f2dc0d79df865ee70d7a8e42ccc2335fe3d5c2828f09`, 32,625 bytes. `p-operations-workspace.html`: sha256 `0a885f295acad3db40b14028e0a5a3ace33cc25c4a548ebbb5fcdcf3f318fb62`, 11,132 bytes. Hashed from the uploaded copies. The learner's own copies under `C:\skilltrace\prototype` were **not** hashed, so it is **unconfirmed** that the learner ran these exact files. |
| Reset method used per mode | **Learner pass (pointer):** F5 reload, then the task's setup button (Guided: the named walkthrough button; Operations: Seeded / Limited fixture button). **E (agent replay):** unchanged from the earlier draft: fresh clone of the page's `FIXTURE.cold` / `FIXTURE.active` through the page's own reducer (Node 22); Operations via fresh headless Chromium load per state. |
| Baseline checks performed before each scenario | Instructed for every task (companion §4 step 2). The learner reported no starting-line mismatch on any task. Only O8 had its starting line explicitly confirmed in the learner's answer (label read *limited*, 3 nodes: 1 available, 2 locked). All other baseline checks are **instructed but not individually evidenced**. |
| Any scenario voided for dirty state | None. |
| Fixture date pinned | 2026-11-17 (Guided) / n/a (Operations) |

## 2. Learner profile, pass order and method

| Field | Record |
|-------|--------|
| Learner | The repo owner — single learner |
| Prior SkillTrace exposure | Inherent. Noted in comprehension cells (L9); never mistaken for comprehension. |
| Passes run | **Pointer: complete** (Guided G1–G9, then Operations O1–O8 and O1 in Draft B). **Keyboard-only: not run. Screen-reader (NVDA + Firefox): not run.** Learner decision, 2026-11-07, settled the same day as a scope decision: the pointer pass is the evidence base for the verdict; the accessibility passes are a later effort. |
| Order in the pointer pass | Guided G1→G9, then Operations (Draft A, Seeded: O1–O7; Limited: O8; Draft B, Seeded: O1). **O9 was not run.** |
| Dates | Pointer pass conducted in a chat-moderated session, completed 2026-11-07. Agent mechanical checks: 2026-10-21. |

Hats: moderator: agent (via chat) / evaluator: agent / accessibility checker: agent (automated axe) plus the learner (manual narrow-window and zoom observations only).

**Method deviations (affect how much weight the observations carry):**

- **M1.** Moderation was by text chat, not live. The learner filled the answer form after each task; no audio/screen recording is referenced. "Time" is the learner's self-timed stopwatch.
- **M2.** Several forms were incomplete or ambiguous when first submitted (G1, G2 outcome, G3, G7, O1, O8). The agent asked follow-up questions after the task, and the learner answered **from memory**. Those answers are post-hoc recall and are marked "(recall)" below.
- **M3.** The learner often did not compare "before/after" Current facts (G1, G6, G8). That is recorded as "not checked", not as "nothing changed".
- **M4.** O9 was skipped and the keyboard and screen-reader passes were not run (see above).

## 3. Scenario results (raw rows — one per pass × task)

### 3.1 Guided (`p-core-journey.html`) — pointer pass

Outcome key: *done* = finished unaided; *done+hint(N)* = finished after opening the walkthrough ladder to step N. CLI vocab was "no" for every task unless stated. Comprehension classes are **E, provisional**.

| Pass | Task | Reset used | Outcome | Time (s) | Errors | Recovery | CLI vocab? | Comprehension (verbatim → class) | A11y defects |
|---|------|-----------|---------|----------|--------|----------|------------|----------------------------------|--------------|
| pointer | G1 | F5 + Cold start & discovery | done | 47 | 0 | none | n | Pressed Start studying; message "Session started… One explicit Session is now open with its first SessionWork." Recorded time read 20 min; learner did **not register** whether that was expected. Expectation (recall): "I expected it would point me to the site where I am to get started on the material." → **partial** | none |
| pointer | G2 | F5 + Normal active study | done | 31 | 0 | none | n | "I could tell a session was open, due to the open Session tag." Pressed Resume and Log work here; timeline showed "25 min-filtering rows and selecting columns". Task asked for 30; learner did not comment on 25 vs 30 (**L8**). → **correct** (for what was asked) | none; annoyance: SkillNode shown by raw id `data.pandas.dataframe_basics_01` rather than a readable title |
| pointer | G3 | F5 + Blocked work & Blocker | done (partly **L**) | 71 | 1 refusal: Create Blocker → "a blocker was already open and that another is allowed but it might duplicate" (**L8**; not a learner error) | none needed | n | "Log blocked is stops you progressing I think and Create Blocker is for when you feel stuck at a point in study." Log blocked work message (recall): "This is one blocked SessionWork item, not a Blocker. Nothing else changed automatically."; Recorded time unchanged; timeline "10 min blocked work". Open-Blocker count: "I think… the same." After Close: work preserved, Blocker remains, node active, Session completed. Did not notice the pre-existing Blocker before starting. → **partial** | none |
| pointer | G4 | F5 + Evidence & pass | done+hint(3) | 77 | 0 | hint step 3 | n | "'Submit evidence' and 'pass' felt more like a check or gate decision than two separate ones." Quoted all three messages (gate ran and passed; "pass eligibility is now true"; "Passing is a separate explicit choice and may schedule Reviews at +1, +3, and +7 days."; "Reviews are scheduled for 2026-11-18, 2026-11-20, and 2026-11-24."). Looked hard at the Review area after pass: "I did not see any discernible change." Session still open. → **partial** | Difficulty locating "not pass eligible" intuitively; "quick status of the SkillNode… not intuitively placed for a quick scan." |
| pointer | G5 | F5 + Safe Session close | done | 97 | 0 | none | n | Pressed Log work here (+25 → 70 min), then Close. Message: work preserved, Blocker remains, SkillNode still active. "I think closing did not change the Evidence, as in nothing was accepted as evidence." Clear when something was saved. → **correct** | none |
| pointer | G6 | F5 + Refusal & recovery | done+hint(9) | 161 | Stale confirmation **not noticed** ("I missed that part") | opened walkthrough at step 3, then used steps 6–9 | n | Refusal read as "the gate ran and fail and could not accept a honest evidence record"; "I think the submit a corrected evidence it will supersede the previous evidence." Both submissions visible in the Session timeline. Ended passed. "There was considerable steps… I did not understand it all what was going on." → **partial** | none |
| pointer | G7 | F5 + Review completion | done (evidence weak) | 45 | 0 | none | n | The message quoted was the **Close Session** message, not a review-completion message (clarified: recall). Looked at the Review card under Distinct paths; "I did not see what was overdue in the sense of a SkillNode." "I did not observe how this review touch my session." Session state read after Close: completed. → **not assessable** | none |
| pointer | G8 | F5 + Failure & empty recovery | done+hint(4) | 180 | 0 | hint steps 1–4 | n | "I wasn't initially sure what each button was trying to test." Refusals read as "a single session can only run, that current session cannot close and the gate was unrunable"; "Operational failure" was clear. Did not check what was left behind ("I was more concentrated on the message box"). After the honest close, "all work is still intact." → **correct** on messages, state check **not done** | none |
| pointer | G9 | none | expectation probe (not scored) | 92 | — | — | n | Looked at Guided walkthroughs, Current facts, Distinct paths. Expected: "only after the node is pass eligible that it can then be judged mastered or not." Found nothing on mastery (**L1**). | none |
| — | G1–G9 | — | *keyboard pass: **not run*** | | | | | | |
| — | G1–G9 | — | *screen-reader pass: **not run*** | | | | | | |

**Post-G9 comprehension questions (pointer pass, verbatim → class, E provisional):**

| Q | Learner answer | Class |
|---|----------------|-------|
| 1. Passing vs mastering | "I think the difference is that pass allows you to review to see if you have mastered the skill or not." | incorrect (mastery is a separate, deliberate act, not a review) |
| 2. Written down permanently? | "I believe the session is saved as a file ses.snapshot.001." | partial (names a record; no reasoning on permanence) |
| 3. What happened to the original when corrected? | "You need to submit new evidence first before something can be corrected." | incorrect. It does not state that the original is kept and marked superseded. Compare the in-task wording in G6 ("it will supersede the previous evidence"). |
| 4. What closing does / does not do | "I think it saves your work but it does not resolve a pass or clear blockers or reviews." | correct |
| 5. What makes a node locked | "Something to do with not meeting the prerequisites of opening the node because insufficient evidence has been presented." | partial |
| 6. Refusal: what was refused, what state left | "The evidence was insufficient and it would not pass the gate. Not really sure on this one." | partial (learner flagged uncertainty) |

**E — mechanical replay of the prototype's own logic (not a learner pass; not counted toward §4).** Unchanged from the earlier draft; summarised: G1 start adds an unlogged 20 min (F4); G2 adds 25, not 30 (F3); G3 Create Blocker refused as duplicate and the walkthrough resolves the pre-existing Blocker (F2); G4 pass schedules two new Reviews though three dates are listed (F5); G5 close leaves Blocker open, node active, no evidence; G6 refusals write nothing, correction supersedes, stale confirm refused, final pass succeeds; G7 review completes without touching Session or progress; G8 refusals and operational failure create no records; G9 no mastery action exists (L1).

**How the learner observations compare with the replay:** G1, G2, G3, G5 and G8 learner observations match the replay (20 min recorded on start; 25 min added; duplicate Blocker refusal; close preserves work, Blocker open). The G4 "no discernible change" in the Review area is consistent with the replay's finding that the Reviews branch changes only as a count (4→6), not as a visible list (see F12/F16).

### 3.2 Operations (`p-operations-workspace.html`) — pointer pass

| Pass | Task | Variant | Fixture | Outcome | Time (s) | Errors | Recovery | CLI vocab? | Comprehension (verbatim → class) | A11y defects |
|---|------|---------|---------|---------|----------|--------|----------|------------|----------------------------------|--------------|
| pointer | O1 | A | seeded | done | 96 | 0 | none | n | Answer came from the heading "Operations workspace" ("inspection space for facts about where the learner state is currently is"). Recall: "It tells you at a glace what skillnodes are available, which are locked, how many session logged, the evidence records recorded and reviews recorded." → **correct** | Minor visual: "the 'Review records' panel is not on the same row as the other 4 panels" |
| pointer | O2 | A | seeded | done (part 2 unanswered) | 43 | 0 | none | n | "Yes the agents.agent_fundamentals_01 is available to start. The pass is learner-initiated for pass status. I think once the evidence is recorded and passed, this will open 10 other nodes downstream." Could not tell what evidence it wants: unsure whether the "Evidence" field "is the amount of evidence I need to record or the amount of evidence has been recorded." → **partial** | Ambiguous "Evidence" label under Selected SkillNode |
| pointer | O3 | A | seeded | could not answer (**L4**) | 41 | 0 | none | n | "There are two points that have 'Evidence and 'Records in the ui and both only show a numerical value… Very uncertain what this was asking for." → **not assessable (L4)** | "A more clearer definition on where I can review the evidence." |
| pointer | O4 | A | seeded | could not answer (**L4**) | 20 | 0 | none | n | "Other than the 'Review records' panel (which states a numerical value of three), I am not seeing any indications of where the reivews are or where its reporting which are overdue." → **not assessable (L4)** | — |
| pointer | O5 | A | seeded | done | 56 | 0 | none | n | "Nothing I could see to click on." Read the Selected SkillNode card (readiness, unlocks, evidence, pass status). Believed "derived facts only": "empty analytics explain their derivation and is linked to the engine view." → **correct** (caption-level only, **L4**) | none |
| pointer | O6 | A | seeded | no (**L4**) | 23 | Portfolio menu item did nothing (not a learner error) | none | n | "I was unable to answer the Portfolio question because when I click on the menu name, it did not have an associated link." Unsure what the task asked. → **not assessable (L4)** | Menu item with no action |
| pointer | O7 | A | seeded | no (**L4**) | 45 | Health menu item opened nothing | none | n | "I cannot make a judgement about 'health' being a user score because the current prototype does not have a interface linked to the Health button." → **not assessable (L4)** | "I was expecting to see a seeded Health section" |
| pointer | O8 | A | limited (confirmed: label *limited*, 3 nodes, 1 available, 2 locked) | done | 31 | 0 | none | n | "When I seen a zero in 'Evidence records' or 'Review records' it just tells me that I haven't progressed anywhere on the nodes. I have not noticed anything that different than the seeded fixture." Did **not notice** the stale "Evidence: 2 records" in the inspector (F8). → **partial** | Raw SkillNode id again |
| pointer | O9 | — | — | **not run** | | | | | | |
| pointer | O1 | B | seeded | done | 51 | 0 | none | n (logged as no; learner left the field blank) | "The pane that is labelled 'Graph'… 100 nodes with 49 available and 51 locked. Page B lets you orientate yourself better as its more direct with what each pane is suppose to convey." → **correct** | none |
| — | O1–O9 (+ O1 in B) | A/B | seeded/limited | *keyboard pass: **not run*** | | | | | | |
| — | O1–O9 (+ O1 in B) | A/B | seeded/limited | *screen-reader pass: **not run*** | | | | | | |

A-vs-B comparison (O1): A 96 s, B 51 s; the learner preferred B (single observation, one learner; prior exposure and ordering, A before B, may bias the time).

## 4. Raw measurements vs thresholds (computed from §3)

Computed on the **pointer pass only**. The runbook's list of "critical learner actions" was not available when this draft was assembled, so counts below are raw, over all scored tasks. Every threshold is marked **insufficient evidence**, not pass, because the contract needs all passes.

| Measure | Threshold (contract) | Observed (pointer pass only) | Pass? |
|---------|----------------------|------------------------------|-------|
| First-attempt completion, critical learner actions | ≥80% | Guided G1–G8 finished unaided: 5/8 (G1, G2, G3, G5, G7); with hint: G4, G6, G8. Operations O1–O8 plus O1-B finished: 5/9; the other four (O3, O4, O6, O7) could not be done because destinations are stubs (**L4**). Excluding L4: 5/5. | **Insufficient evidence** |
| Recovery after refusal/failure | ≥90% | Recovery needed in G6 and G8: both recovered **with hints** (G6 steps 3→9; G8 steps 1–4); 0/2 unaided. G3's refusal needed no recovery (**L8**). | **Insufficient evidence** |
| Every critical action successful in every pass | 100% | One pass only. Within it, G4, G6 and G8 needed hints and the stale-confirmation step in G6 was missed. | **Insufficient evidence** (not met in pointer pass) |
| Critical safety / domain-boundary violations | 0 | None observed by the learner in the pointer pass; none in the agent replay (E) | **Insufficient evidence** (only one of three passes) |
| Refusals recoverable without CLI vocabulary | all recorded cases | G3, G6, G8: CLI vocabulary needed = **no** in all three | **Insufficient evidence** (one pass), but no counter-example |

Critical actions that failed: none outright. Actions that needed hints: G4 (pass), G6 (refusal recovery, stale confirmation missed), G8 (deliberate refusals).

## 5. Accessibility findings

### 5.1 Automated (per prototype)

Tool: axe-core 4.14.0, headless Chromium 156 (Playwright), rule sets wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa, best-practice. "200%" was emulated with a 640×400 viewport. Operations scanned in A-seeded, B-seeded, A-limited. Colour-contrast ran in a real browser and reported no violations.

| Prototype | Tool + version | Viewport/zoom | Violations (full list, with rule IDs) |
|-----------|----------------|---------------|----------------------------------------|
| p-core-journey | axe-core 4.14.0 | 100% / 200% / 320px | Same at all three: `region` [moderate] ×1 — `.throwaway` banner outside any landmark. No other axe violations. Reflow at 320px: no horizontal scroll (320 = 320). |
| p-operations-workspace | axe-core 4.14.0 | 100% / 200% / 320px | Same at all three, all states: `region` [moderate] ×2 — `.banner` and fixed `.switch` variant bar outside landmarks. No other axe violations. **Not caught by axe (measured separately, E):** at 320px, A-seeded scrolls horizontally (scrollWidth 353 > 320; `.pill` and "Inspect →" overflow) and B-seeded to 475 px. |

### 5.2 Manual walkthrough matrix

Only the narrow-window and zoom checks were walked by the learner (pointer pass). Keyboard, focus-with-keyboard, screen-reader and touch checks were **not walked**.

| Check | Guided states walked | Operations states walked | Pass/Fail | Defect description (severity) |
|-------|----------------------|--------------------------|-----------|-------------------------------|
| Keyboard-only operation | not walked (pass not run) | not walked (pass not run) | not run | E (code read, unchanged): all actions are native `<button>`s; Guided re-renders buttons on every dispatch and moves focus to the result box; Operations sidebar nav only toggles a class (F9). |
| Focus behaviour | not walked | not walked | not run | E (code read): `:focus-visible` outlines defined on both; Guided `#result` is `role=status`, `aria-live=polite` and focused, possible double announcement (F11, unverified). |
| Screen reader | not walked | not walked | not run | E (code read, unverified): dangling `aria-labelledby="study-heading"`; inert mode control and top-nav; Operations A/B switcher has only an `aria-label`. |
| Contrast | n/a (automated) | n/a (automated) | axe: no violations | E automated only; muted text and focus colours not manually sampled. |
| 200% zoom / reflow (learner, pointer pass) | Guided: learner reported nothing cut off, squashed, overlapping or unreachable; no sideways scroll; main Today-card button reachable; all readable (480 px, 320 px and 200%: learner's answers were given as one set and are recorded as applying to all three) | Operations, Drafts A and B: learner reported nothing cut off or unreachable; **no sideways scroll**; all menu items and links reachable; nothing too small; all readable (same single set of answers) | Guided **Pass** (learner O + E automated agree). Operations: **conflicting evidence, unresolved** | **Conflict.** The agent's scripted measure (E) found horizontal overflow on Operations at 320 px (A: 353 px, B: 475 px, SC 1.4.10). The learner (O) saw no sideways scroll at 320 px in Chrome device mode. Possible causes: device-mode width not exactly 320 CSS px, a scrollbar not noticed, or headless-vs-desktop rendering difference. Needs a re-measure on the learner's machine. F7 stays open as **disputed**, not resolved. |
| Reduced motion | not walked | not walked | not run | E (code read): Guided declares `prefers-reduced-motion`; Operations declares none (no animation). |
| Touch | not walked | not walked | not run | E (code read): Guided buttons `min-height:44px`; Operations Inspect links, nav buttons and fixture toggles have no minimum target size. Learner (mouse): "Nothing felt too small", which is not a touch test. |
| Narrow window (480/320 px) | learner pass: no problems | learner pass: no problems (conflicts with E at 320, see Reflow) | Guided pass; Operations unresolved | See above |
| Graph nonvisual equivalent | — | not walked | not run / **L** | The Operations "graph" is a four-row list with no edges (L3). |

**Mandatory accessibility gate:** **not determinable / not passed.** Keyboard, focus, screen-reader and touch criteria were not walked, and the Operations 320 px reflow result is disputed. Insufficient evidence, not pass.

**Scope decision recorded afterwards (learner, 2026-11-07):** the gate is **deferred, not waived and not passed**. The pointer pass is sufficient for the learner's needs as the primary user, so the un-walked criteria leave this map's validation gate and return later as a separate accessibility effort (map #327, Out of scope). Nothing above changes status: the only accessibility criteria with evidence behind them are automated axe, colour contrast, and the learner's own narrow-window and zoom observations.

## 6. Findings register (critical / major / minor — no scores)

"Domain-contract link" refers to the claim IDs in §9. **E** = evaluator judgment from code/scripts. **O** = observed from the learner's pointer pass. Severity on **O** findings is the evaluator's, provisional.

| # | Class | Description | Evidence (pass, task, quote/screenshot) | Domain-contract link |
|---|-------|-------------|------------------------------------------------|----------------------|
| F1 | major (E) | Operations Draft B ignores the fixture toggle: switching to "Limited" updates only the label; B still shows "100 nodes", "49 available · 51 locked", "12 records", "3 records". | Scripted run; `sections()` hardcodes values. **Not exercised by the learner** (O8 was done in Draft A only). | C20 (O8), C13 |
| F2 | major (E, partly O) | Guided G3 is internally inconsistent: an open Blocker already exists in ACTIVE, so "Create Blocker" yields a duplicate warning and creates nothing. | Replay G3. Learner O (G3): Create Blocker "said that a blocker was already open and that another is allowed but it might duplicate"; learner did not notice the pre-existing Blocker beforehand. | C03 |
| F3 | minor (E, O) | G2 asks for 30 minutes but "Log work here" always adds 25. | Replay; learner O: timeline entry "25 min". Learner did not comment. | C02 |
| F4 | major (E, partly O) | G1: "Start studying" silently creates a 20-minute SessionWork. | Replay G1; learner O: Recorded time read 20 min after Start, not registered as unexpected. The learner's reaction is unknown, which does not refute the finding. | C01, C26 |
| F5 | minor (E) | Pass message lists Reviews 11-18/11-20/11-24 but the 11-24 Review already exists, so only two are created. | Replay G4. | C04 |
| F6 | minor (E) | "Recorded time" excludes blocked work minutes although the timeline shows the item. | Replay G3; learner O: recorded time did not change after Log blocked work; timeline showed "10 min blocked work". | C03 |
| F7 | major (E), **disputed** | Operations at 320px scrolls horizontally in both drafts. | Scripted measure (353 / 475 px). **Conflicts with learner O** (no sideways scroll seen in device mode). See §5.2. | C24, C23 |
| F8 | major (E) | Operations Limited fixture, Draft A: summary cards show 0 evidence while the inspector still says "Evidence: 2 records". | Scripted run. Learner O (O8): did **not notice** the contradiction. | C20 |
| F9 | minor→major (E, O) | Operations nav and "Inspect/Explore/Open →" links are stubs; O3–O7 cannot be answered. | Source read. **Learner O:** O3, O4 unanswerable; O6 "the menu name… did not have an associated link"; O7 "no interface linked to the Health button". | C15–C19 |
| F10 | minor (E) | axe `region`: scaffolding banners and variant switcher outside landmarks. | §5.1. | C23 |
| F11 | minor (E, unverified) | Guided result box is `aria-live` and also focused; dangling `aria-labelledby`. | Source read; screen-reader pass not run. | C26 |
| F12 | note | Companion text vs file mismatches (Seeded/Limited buttons appear in both drafts; Reviews shown as an id list in Guided). | Source read. Learner O (G4/G7): could not see which review or what changed in the Review area. | — |
| F13 | minor (O) | SkillNodes are shown by raw ids (`data.pandas.dataframe_basics_01`, `agents.agent_fundamentals_01`) rather than readable titles. | Learner annoyance in G2 and O8. | C12, C22 |
| F14 | major (O) | Stale confirmation in G6 was **not noticed** by the learner. | G6: "I missed that part." | C08 |
| F15 | major (O) | G6 and G8 needed heavy hint use (steps 3→9 and 1–4) and the learner reported not understanding "what was going on". Recovery from refusals was not unaided. | G6: "considerable steps… I did not understand it all"; G8: "I wasn't initially sure what each button was trying to test." | C06, C10 |
| F16 | major (O) | After passing (G4) and completing the review (G7), the learner could not see any change in the Review area or which review was overdue. | G4: "I did not see any discernible change." G7: "I did not see what was overdue in the sense of a SkillNode." | C04, C09 |
| F17 | major (O) | The "Evidence" figure under the Selected SkillNode is ambiguous: needed vs recorded. The learner could not see what evidence a node wants before starting. | O2: "not sure if its the amount of evidence I need to record or the amount of evidence has been recorded." | C14 |
| F18 | major (O) | Learner perceived "submit evidence" and "pass" as one gate decision, although the messages describe pass as "a separate explicit choice". | G4 comprehension. | C04 |
| F19 | minor (O) | "Not pass eligible" and the SkillNode quick status are hard to find at a glance. | G4: "trying to find the 'not pass eligible' intuitively"; "not intuitively placed for a quick scan." | C12, C26 |
| F20 | minor (O) | Operations home: the Review records panel sits on a different row from the other four panels. | O1-A annoyance. | C13 |
| F21 | note (O) | Orientation: Draft B faster (51 s) and preferred over A (96 s) for O1. | O1 A/B. | C13 |

No critical findings. A critical finding requires a domain-boundary or safety violation observed in a pass; none was observed.

## 7. Distinction ledger

- **Observed learner outcomes** (behaviour, times, errors, verbatim quotes): §3–§4, pointer pass only.
- **Evaluator judgments** (classification, severity, comprehension scoring): §5–§6, marked **E**; comprehension classes and **O**-finding severities are provisional pending the learner's review.
- **Prototype limitations** (asset cannot evidence the claim): §8, marked **L**, never counted as pass or fail of the product claim.
- **Recall vs in-task:** statements marked "(recall)" or reconstructed after follow-up questions are weaker than in-task notes (M2).

## 8. Prototype limitations and gaps in this run

| # | Limitation | Contract claim left untested | Effect on matrix |
|---|-----------|------------------------------|------------------|
| L1 | No mastery action in the Guided page (by design, G9). | C11 | Expectation probe only. |
| L2 | No "could not compute" state in the Operations page (by design, O9). **O9 was also not run.** | C21 | Untested. |
| L3 | The Operations "graph" is a four-row list; no edges or dependency inspection. | C25; part of C14 | Cannot be fully evidenced. |
| L4 | Operations destinations (Evidence, Reviews, Analytics, Portfolio, Health) are stubs. **Confirmed by the learner:** O3, O4, O6, O7 could not be completed. | C15–C19 | O3/O4/O6/O7 not assessable; O5 caption-level only. |
| L5 | Operations Draft B ignores the Limited fixture (F1). O8 was done in Draft A only. | C20 in B | O8 evidence valid for Draft A only (and A has F8). |
| L6 | No omnibar in either prototype. | C27 | Untested. |
| L7 | In-memory reducer, fixed timestamps and ids; "server changed" is a scripted button. | C08 (partly), C10 | Behaviour demonstrated, not independently produced. |
| L8 | G2 cannot record exactly 30 minutes; G3's Create Blocker is blocked as duplicate in ACTIVE. | C02, C03 | Learner outcomes on those literal steps classed **L**. |
| L9 | Single learner has prior exposure to SkillTrace; cold-start claims (C01, C13) are biased toward success. | C01, C12, C13 | Noted. |
| G-1 | **Keyboard-only and screen-reader passes not run** (learner decision, 2026-11-07; stated reason: prototype lacks functionality for keyboard use). Settled the same day: the pointer pass is sufficient for the learner's needs; accessibility validation deferred to a later effort (map #327, Out of scope). | C23, C25, C26, mandatory a11y gate | These claims carry **no accessibility evidence** — deferred, never passed. The verdict ticket dispositions them as deferred rather than judging pass/fail on absent evidence. |
| G-2 | Method deviations M1–M4 (chat moderation, recall answers, unchecked state, O9 skipped). | all | Lowers weight of observations. |

## 9. Claim-by-claim matrix (input to G-FinalValidationVerdict)

Disposition stays **blank** until the verdict ticket fills it: accept / revise / reject / **insufficient evidence**. "Threshold result" is the evaluator's view. **E-replay** = the agent confirmed the prototype's logic; **O-pointer** = observed in the learner's pointer pass.

| Claim ID | Requirement (source ticket) | Scenario(s) | Measurement | Threshold result | Evidence ref (§) | Disposition (verdict ticket) |
|----------|-----------------------------|-------------|-------------|------------------|------------------|------------------------------|
| C01 | Cold start & discovery completes without CLI vocabulary (G-CoreWorkflows) | G1 | first-attempt, errors, recovery | Insufficient evidence (one pass). O-pointer: done unaided in 47 s, no CLI vocabulary; F4 side effect seen but unremarked; L9 bias. | §3.1, F4, L9 | |
| C02 | Session resume / log work without second Session (G-CoreWorkflows) | G2, G8 | first-attempt, refusal | Insufficient evidence. O-pointer: G2 done; G8 second-Session refusal understood with hint; F3, L8. | §3.1, F3 | |
| C03 | Blocked work ≠ Blocker; Blocker persists across close (G-DomainContract) | G3, G5 | comprehension, outcome | Insufficient evidence. O-pointer: difference understood in own words and from the message; Blocker persists after close (G3, G5); Create Blocker refused as duplicate (F2, L8). | §3.1, F2, F6 | |
| C04 | Evidence → eligibility → pass distinct and learner-initiated (G-DomainContract) | G4 | comprehension, outcome | Insufficient evidence. O-pointer: needed hint 3; learner experienced evidence and pass as one gate decision (F18); no visible Review change (F16). | §3.1, F5, F16, F18 | |
| C05 | Safe Session close implies nothing (G-CoreWorkflows) | G5 | comprehension | Insufficient evidence. O-pointer: learner stated closing did not change evidence; Q4 answer correct. | §3.1 | |
| C06 | Refusal is safe, recoverable, leaves correct state (G-DomainContract) | G6 | recovery ≥90%, verbatim | Insufficient evidence. O-pointer: recovered only with hints to step 9; learner did not check state after refusals (M3); F15. | §3.1, F15 | |
| C07 | Correction supersedes; original never edited/deleted (G-DomainContract) | G6 | comprehension | Insufficient evidence. O-pointer: in-task "supersede" wording, but Q3 post-G9 answer incorrect. | §3.1 | |
| C08 | Stale confirmation refuses without writing (G-DomainContract) | G6, G8 | outcome | Insufficient evidence. O-pointer: stale confirmation **missed** (F14). | §3.1, F14, L7 | |
| C09 | Review completion independent of Session; no demotion (G-DomainContract) | G7 | comprehension, outcome | Insufficient evidence. O-pointer: weak: review-completion message not captured; learner could not see what was overdue (F16). | §3.1, F16 | |
| C10 | Refusals/operational failures create no records (G-DomainContract) | G8 | outcome, comprehension | Insufficient evidence. O-pointer: "Operational failure" message clear; state not checked (M3). | §3.1 | |
| C11 | Mastery is separate, deliberate, two-step (G-CoreWorkflows) | G9 (**L**) | expectation probe | Insufficient evidence; Q1 answer conflated passing and mastering. | L1 | |
| C12 | Guided navigation is task-led and predictable (G-InformationArchitecture) | G1–G8 | errors, comprehension | Insufficient evidence. O-pointer: 0 errors outside refusals; hints needed in G4, G6, G8; F13, F19. | §6 F13, F19 | |
| C13 | Operations home orientation in ≤1 glance (P-OperationsWorkspace hybrid) | O1 A/B | time, comprehension | Insufficient evidence. O-pointer: A 96 s, B 51 s; both answered correctly; B preferred; F1, F20, L9. | F1, F20, F21 | |
| C14 | Graph readiness/evidence inspectable (G-OperationsSurfaces) | O2 | outcome | Insufficient evidence. O-pointer: availability found; evidence wanted not determinable (F17, L3, L4). | F17, L3, L4 | |
| C15 | Evidence Vault inspectable; immutability legible (G-OperationsSurfaces) | O3 | outcome, comprehension | Insufficient evidence; asset cannot evidence (stub). O-pointer: unanswerable. | F9, L4 | |
| C16 | Retention/Reviews inspectable (G-OperationsSurfaces) | O4 | outcome | Insufficient evidence; asset cannot evidence. O-pointer: unanswerable. | F9, L4 | |
| C17 | Analytics show derivations, no fake telemetry (G-OperationsSurfaces) | O5 | comprehension | Insufficient evidence; caption-level only. O-pointer: learner believed the "derived facts" claim. | L4 | |
| C18 | Portfolio export honest and redacted (G-OperationsSurfaces) | O6 | comprehension | Insufficient evidence; stub, menu item inert. | F9, L4 | |
| C19 | Health is ordinary capability, not a score (P-OperationsWorkspace) | O7 | comprehension | Insufficient evidence; no health view exists. | F9, L4 | |
| C20 | Empty/limited states truthful, no zeroes-as-truth (G-OperationsSurfaces) | O8 | outcome, comprehension | Insufficient evidence. E: fails as built in Draft B (F1) and partly in A (F8). O-pointer: Draft A only; learner read zeros as "haven't progressed", did not notice F8. | F1, F8, L5 | |
| C21 | Could-not-compute surfaced honestly (G-ValidationContract) | O9 (**L**) | expectation probe | **Not run**; no evidence. | L2 | |
| C22 | Dark dense system readable; status never colour-only (G-VisualSystem) | all | a11y §5 | Partial: axe contrast clean; status pills carry text; learner reported everything readable at narrow/zoom. Not manually sampled for contrast. | §5.1, §5.2 | |
| C23 | WCAG 2.2 AA mandatory criteria (G-AccessibilityContract) | §5 matrix | mandatory gate | Insufficient evidence; keyboard/SR/touch not walked; Operations reflow disputed. | §5, F7 | |
| C24 | Narrow-window degradation keeps critical actions (G-AccessibilityContract) | §11 narrow | walkthrough | Guided: learner and automation agree (no overflow). Operations: learner saw no problem; scripted measure shows overflow at 320 px, **unresolved**. | §5.2, F7 | |
| C25 | Graph nonvisual equivalent complete (G-AccessibilityContract) | §11 graph | SR + keyboard | **Not run** (screen-reader pass not run; L3). | L3, G-1 | |
| C26 | Interaction budget: explicit actions, focus on outcome (G-InteractionModel) | all | errors, focus checks | Insufficient evidence. O-pointer: state changes were usually read from the message box; focus not tested (keyboard pass not run); F4, F11, F19. | F4, F11, F19 | |
| C27 | Omnibar as accelerator, navigation-only (G-InteractionModel) | record coverage | errors | Not covered: no omnibar in either prototype (L6). | L6 | |

## 10. Verdict readiness statement (filled by evaluator)

- All contract scenarios executed? **No.** Run: pointer pass, Guided G1–G9 and Operations O1–O8 plus O1-B. **Not run:** keyboard-only pass, screen-reader pass, O9, touch, reduced-motion, focus checks.
- Thresholds table (§4) complete? Computed for the pointer pass only; all rows insufficient evidence.
- Mandatory accessibility gate result (§5.2)? **Not passed / not determinable — and now deferred by the learner's scope decision** (see §5.2, G-1). Operations 320 px reflow stays disputed between the learner (no sideways scroll) and the scripted measure (overflow).
- Remaining insufficient-evidence claims for the verdict ticket: **C01–C26 all** (C22 and C24 partial; C21, C25 not run; C27 not covered).
- Strongest learner-observed concerns for the verdict ticket: F14 (stale confirmation missed), F15 (heavy hint use in G6/G8), F16 (no visible Review change or overdue list), F17 (ambiguous Evidence field), F18 (evidence and pass perceived as one decision), F13 (raw ids). Operations stub destinations (F9/L4) made O3, O4, O6, O7 unassessable.
- Sufficiency is no longer open: the learner decided on 2026-11-07 that **one pointer pass is sufficient** for what they need as the primary user, and that accessibility is deferred to a later effort. This report is therefore the complete evidence base for [G-FinalValidationVerdict — decide the final product direction from observed evidence](https://github.com/earledotpy/skilltrace/issues/345).
- Where the evaluator's outstanding wishes now stand: the learner's review of the provisional comprehension classes (§3.1) — **done, 2026-11-07**; re-measuring the disputed Operations 320 px reflow (F7) on the learner's machine — **not done, transfers to the deferred accessibility effort**; the learner's own prototype file hashes (§1) — **not provided, stays an unconfirmed limit of this run**.

---
*Evidence file for wayfinder map #327; the engine never reads it. The decision lives in G-FinalValidationVerdict's ticket; this report is its evidence.*
