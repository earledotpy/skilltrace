# v3 single-learner validation — observation report

**Ticket:** [T-ValidationExecution — run the moderated usability and accessibility contract](https://github.com/earledotpy/skilltrace/issues/344) (wayfinder map #327)
**Protocol:** `docs/validation/v3-usability-runbook.md` (implements [G-ValidationContract — define moderated usability and accessibility validation](https://github.com/earledotpy/skilltrace/issues/339), re-scoped by [G-SingleLearnerValidation — re-scope the validation gate to single-learner structured self-evaluation](https://github.com/earledotpy/skilltrace/issues/347)).
**Consumers:** this report is the *evidence* for [G-FinalValidationVerdict — decide the final product direction from observed evidence](https://github.com/earledotpy/skilltrace/issues/345) — it is not the verdict. Insufficient evidence is recorded explicitly; it is never a pass.

**Status:** PARTIALLY FILLED (2026-10-21, agent-prepared). **No learner passes (mouse / keyboard / screen-reader) have been run yet.** Everything in §3 that depends on a human (outcome, time, errors, recovery, verbatim comprehension) is intentionally blank — it must come from the learner's answer forms, and was not invented. What *is* filled was produced by the agent and is marked **E** (evaluator-run) or **L** (prototype limitation). Nothing agent-run is an observed learner outcome (**O**).

---

## 1. Fixture reset procedure (as executed)

| Item | Record |
|------|--------|
| Prototype files + integrity (path, mtime/hash) | `p-core-journey.html`: sha256 `7b2948eb2f0c0420f343f2dc0d79df865ee70d7a8e42ccc2335fe3d5c2828f09`, 32,625 bytes. `p-operations-workspace.html`: sha256 `0a885f295acad3db40b14028e0a5a3ace33cc25c4a548ebbb5fcdcf3f318fb62`, 11,132 bytes. Hashed from the uploaded copies (upload mtime 2026-10-21 00:33 MDT, not the original file mtime). The learner's own copies under `C:\skilltrace\prototype` were **not** hashed — confirm they match before the learner passes. |
| Reset method used per mode (reload / scenario reset / fixture toggle) | **Learner passes:** not yet run. **E (agent replay):** Guided — fresh clone of the page's own `FIXTURE.cold` / `FIXTURE.active` per scenario, using the page's actual reducer (extracted from the file, run in Node 22). Operations — fresh headless Chromium page load per state; fixture toggle and A/B switch clicked via DOM. |
| Baseline checks performed before each scenario (per runbook §5) — pass/fail | **E:** Guided starting lines match the companion's COLD/ACTIVE descriptions by construction of the fixtures (COLD: no session, `available`, 0 min, 0 blockers, 4 reviews incl. 1 overdue; ACTIVE: `ses.snapshot.001` open, `active`, 45 min, 1 open Blocker, 1 overdue review). Learner pre-scenario baseline checks: not yet run. |
| Any scenario voided for dirty state (which, why, rerun?) | None (no learner scenarios run). |
| Fixture date pinned | 2026-11-17 (Guided) / n/a (Operations) |

## 2. Learner profile and pass order

| Field | Record |
|-------|--------|
| Learner | (the repo owner — single learner) |
| Prior SkillTrace exposure | (inherent; noted in the comprehension column, never mistaken for comprehension) |
| Passes run | **None yet.** Planned: pointer / keyboard-only / screen-reader (NVDA + Firefox) |
| Order per pass | Planned per companion §7: Pass 1 Guided→Operations; Passes 2 and 3 Operations→Guided |
| Dates | Agent-run mechanical checks: 2026-10-21. Learner passes: pending |

Hats worn (one person): moderator: pending / evaluator: agent (mechanical checks only) / accessibility checker: agent (automated axe only; manual checks pending)

## 3. Scenario results (raw rows — one per pass × task)

**Not filled — requires the learner's answer forms.** Columns per runbook §10: task (G1–G9, O1–O9), variant (A/B), fixture, outcome, time (s), errors (count + verbatim), recovery (none / self / hint level N; CLI vocabulary needed? y/n), comprehension (verbatim + correct/partial/incorrect), a11y defects (description + severity).

### 3.1 Guided (`p-core-journey.html`)

| Pass | Task | Reset used | Outcome | Time (s) | Errors | Recovery | CLI vocab? | Comprehension (verbatim → class) | A11y defects |
|---|------|-----------|---------|----------|--------|----------|------------|----------------------------------|--------------|
| — | G1–G9 | — | *awaiting learner (pointer pass)* | | | | | | |
| — | G1–G9 | — | *awaiting learner (keyboard pass)* | | | | | | |
| — | G1–G9 | — | *awaiting learner (screen-reader pass)* | | | | | | |

**E — mechanical replay of the prototype's own logic (NOT a learner pass; not counted toward §4).** Each walkthrough's step list was replayed through the page's reducer. Purpose: confirm the prototype *can* produce the outcomes the tasks assume, so a learner failure can be attributed correctly.

| Task | Replay result |
|------|---------------|
| G1 | START → "Session started" (success). **Side effect:** starting creates 20 min of SessionWork ("first focused pass") that the learner never logged. RESUME → "Session resumed", no change. LOG_WORK → 45 min total. |
| G2 | RESUME no-op; LOG_WORK adds **25** min (45→70), not the 30 min the task card asks for. The prototype cannot record exactly 30. |
| G3 | LOG_BLOCKED → "Blocked work recorded" (warning); recorded minutes stay 45 (blocked minutes not in "Recorded time"). CREATE_BLOCKER → **"Possible duplicate Blocker"** and nothing is created, because the ACTIVE fixture already has an open Blocker. RESOLVE_BLOCKER (3rd step) resolves that **pre-existing** Blocker — which contradicts the task goal that stuckness "stays visible". |
| G4 | SUBMIT_EVIDENCE → accepted, eligible; PASS_PANEL → opens; CONFIRM_PASS → node `passed`; reviews 4→6 (only 2 added because the 11-24 review already exists in the fixture, although the success message lists three dates). Session stays open. |
| G5 | LOG_WORK → 70 min; CLOSE → Session `completed`, Blocker still `open`, node still `active`, no evidence, not passed. Matches the safe-close claim. |
| G6 | Pass refused when ineligible (no write) → rejected record → correction supersedes it (original kept, marked superseded) → panel opens → SERVER_CHANGED supersedes the live record → CONFIRM_PASS **refused, node stays `active`, nothing written** → second correction → pass succeeds. Matches claims C06–C08. |
| G7 | COMPLETE_REVIEW → review completed; node `active`, Session `open`, no demotion; CLOSE then works normally. Matches C09. |
| G8 | START_SECOND refused; CLOSE_FUTURE refused; GATE_UNRUNNABLE → "Operational failure — no EvidenceRecord", records unchanged (none); CLOSE_STALE → Session `completed`, work intact (45 min). Matches C10. |
| G9 | No mastery action exists anywhere in the page (verified by reading the action list). Expected by design (**L**). |

### 3.2 Operations (`p-operations-workspace.html`)

| Pass | Task | Variant | Fixture | Outcome | Time (s) | Errors | Recovery | CLI vocab? | Comprehension (verbatim → class) | A11y defects |
|---|------|---------|---------|---------|----------|--------|----------|------------|----------------------------------|--------------|
| — | O1–O9 (+ O1 in B) | A/B | seeded/limited | *awaiting learner (pointer pass)* | | | | | | |
| — | O1–O9 (+ O1 in B) | A/B | seeded/limited | *awaiting learner (keyboard pass)* | | | | | | |
| — | O1–O9 (+ O1 in B) | A/B | seeded/limited | *awaiting learner (screen-reader pass)* | | | | | | |

## 4. Raw measurements vs thresholds (computed from §3)

Not computable: §3 has zero learner rows. Marked **insufficient evidence**, not pass.

| Measure | Threshold (contract) | Observed | Pass? |
|---------|----------------------|----------|-------|
| First-attempt completion, critical learner actions | ≥80% | no learner data | **Insufficient evidence** |
| Recovery after refusal/failure | ≥90% | no learner data | **Insufficient evidence** |
| Every critical action successful in every pass | 100% | no learner data | **Insufficient evidence** |
| Critical safety / domain-boundary violations | 0 | none seen in the agent replay (E); none observed from a learner | **Insufficient evidence** (replay is not a learner observation) |
| Refusals recoverable without CLI vocabulary | all recorded cases | no learner data | **Insufficient evidence** |

Critical actions that failed in any pass: none recorded (no passes run). **E note:** G2 and G3 as written cannot be completed exactly by the prototype (see §3.1 replay and §6 F2, F3); a learner may fail them for prototype reasons, which must be classed as **L**, not product failure.

## 5. Accessibility findings

### 5.1 Automated (per prototype)

Tool: axe-core 4.14.0, headless Chromium 156 (Playwright), rule sets wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa, best-practice. "200%" was emulated with a 640×400 viewport (equivalent to 200% of 1280×800), not true browser zoom. Operations scanned in A-seeded, B-seeded, A-limited. Colour-contrast ran in a real browser and reported no violations.

| Prototype | Tool + version | Viewport/zoom | Violations (full list, with rule IDs) |
|-----------|----------------|---------------|----------------------------------------|
| p-core-journey | axe-core 4.14.0 | 100% / 200% / 320px | Same at all three: `region` [moderate] ×1 — `.throwaway` banner is outside any landmark. No other axe violations. Reflow check at 320px: no horizontal scroll (320 = 320). |
| p-operations-workspace | axe-core 4.14.0 | 100% / 200% / 320px | Same at all three, all states: `region` [moderate] ×2 — `.banner` and the fixed `.switch` variant bar are outside any landmark. No other axe violations. **Not caught by axe (measured separately):** at 320px, A-seeded scrolls horizontally (scrollWidth 353 > 320; the `.pill` and "Inspect →" link in table rows overflow) and B-seeded scrolls to 475 px. This fails WCAG 2.2 SC 1.4.10 Reflow (E). |

Both `region` hits are on prototype scaffolding (banners / variant switcher), not on the proposed product UI — judged low-impact (E).

### 5.2 Manual walkthrough matrix (rows = checks from runbook §11; record per representative state)

Manual checks have not been walked by a human. Only items the agent could determine from code or automation are noted, marked **E**. Pass/Fail stays blank where a human check is required.

| Check | Guided states walked | Operations states walked | Pass/Fail | Defect description (severity) |
|-------|----------------------|--------------------------|-----------|-------------------------------|
| Keyboard-only operation | not walked | not walked | pending | E (code read): all actions are native `<button>`s. Guided: `render()` rebuilds the free-play and focus-action buttons on every dispatch, so focus on a clicked button is lost; the code moves focus to the result box instead (by design, but verify by keyboard). Operations: the sidebar "nav" buttons in A only toggle a class — they do not change content (see §8). |
| Focus behaviour | not walked | not walked | pending | E (code read): visible `:focus-visible` outlines (3px) defined on both. Guided: `#result` has `role=status`, `aria-live=polite` **and** receives programmatic focus — likely to double-announce in a screen reader; verify in NVDA (minor, unverified). |
| Screen reader | not walked | not walked | pending | E (code read, unverified): Guided `<section aria-labelledby="study-heading">` references an id that does not exist (minor). The "Guided / Operations" mode control and top-nav links are inert `<span>`/`href="#"` items. Operations has no heading for the A/B switcher bar content beyond `aria-label`. |
| Contrast | n/a (automated) | n/a (automated) | axe: no contrast violations, both pages | — (E, automated only; muted text and focus colours not manually sampled) |
| 200% zoom / reflow | emulated 640×400: axe clean | emulated 640×400: axe clean | **Operations Fail at 320px (E)**; Guided Pass at 320px | Operations: horizontal scroll at 320px in A (353px) and B (475px) — major (WCAG 1.4.10). True browser 200% zoom not walked. |
| Reduced motion | not walked | not walked | pending | E (code read): Guided declares `prefers-reduced-motion` reset; Operations declares none (but has no animation). |
| Touch | not walked | not walked | pending | E (code read): Guided buttons `min-height:44px`; Operations "Inspect →" links, nav buttons and fixture toggles have no minimum target size (6px×10px padding on toggles). Likely sub-44px; target-size AA (24px) not measured. |
| Narrow window (480/320 px) | 320px scanned (see §5.1) | 320px scanned (see §5.1) | Guided pass / Operations fail (E) | See Reflow row. 480px not walked. |
| Graph nonvisual equivalent | — | not walked | pending / **L** | The "graph" in Operations is a four-row list of node names, readiness pills and "N downstream" text. No edge/dependency list exists, so a nonvisual equivalent of the graph cannot be fully assessed on this asset (see §8 L3). |

**Mandatory accessibility gate:** every mandatory criterion passes — **not determinable (no).** Known blocker candidate from automation: SC 1.4.10 Reflow fails on `p-operations-workspace.html` at 320px (E). Manual keyboard, focus, screen-reader, zoom and touch criteria remain unwalked, so the gate is **insufficient evidence**, not pass.

## 6. Findings register (critical / major / minor — no scores)

All findings are **E** (evaluator judgment from code reading and automated/scripted checks; no learner evidence yet). "Domain-contract link" refers to the claim IDs in §9.

| # | Class | Description | Evidence (pass, task, quote/screenshot) | Domain-contract link |
|---|-------|-------------|------------------------------------------------|----------------------|
| F1 | major (E) | Operations Draft B ignores the fixture toggle: switching to "Limited" updates only the top-right label; B still shows "100 nodes", "49 available · 51 locked", "12 records", "3 records". Draft B therefore cannot demonstrate a truthful empty state, and gives a **false** picture for the limited fixture. | Scripted run: B-limited values read `100 nodes, 12 records, 3 records, 4 themes, Export, Check`, label `limited`. Source: `sections()` hardcodes values. | C20 (O8), C13 |
| F2 | major (E) | Guided G3 is internally inconsistent: in the ACTIVE fixture an open Blocker already exists, so "Create Blocker" yields "Possible duplicate Blocker" and creates nothing, and the walkthrough's final step resolves the pre-existing Blocker — contrary to the task goal that stuckness stays visible. | Replay G3. | C03 |
| F3 | minor (E) | G2 asks for 30 minutes but "Log work here" always adds 25. | Replay G2. | C02 |
| F4 | major (E) | G1: "Start studying" silently creates a 20-minute SessionWork the learner never entered. Conflicts with the principle that nothing is recorded without an explicit act. | Replay G1: START → min 20. | C01, C26 |
| F5 | minor (E) | Pass success message lists Reviews on 11-18, 11-20, 11-24, but the 11-24 Review already exists, so only two are created (reviews 4→6). | Replay G4. | C04 |
| F6 | minor (E) | "Recorded time" excludes blocked work minutes (10 min logged as blocked, total stays 45) although the timeline shows the item. May confuse C03 comprehension. | Replay G3. | C03 |
| F7 | major (E) | Operations at 320px scrolls horizontally in both drafts (353px A, 475px B). | Playwright overflow measure; overflowing elements `.pill`, `.link` in rows (A). | C24, C23 |
| F8 | major (E) | Operations in Limited fixture, Draft A: summary cards show 0 evidence records but the "Selected SkillNode" inspector still says "Evidence: 2 records" — self-contradictory; a zero shown next to a stale non-zero. | Scripted run A-limited. | C20 |
| F9 | minor (E) | Operations nav (A) and all "Inspect / Explore / Open →" links are stubs (`href="#…"`, class toggle only). O3 (most recent evidence record), O4 (due vs overdue reviews), O5, O6, O7 cannot be answered from this page. | Source read. | C15–C19 |
| F10 | minor (E) | axe `region`: scaffolding banners and variant switcher sit outside landmarks (both pages). | §5.1. | C23 |
| F11 | minor (E, unverified) | Guided result box is both `role=status`/`aria-live` and programmatically focused — possible double announcement; `aria-labelledby` points to missing `#study-heading`. | Source read; needs NVDA. | C26 |
| F12 | note | Companion §6 says the Seeded/Limited setup buttons live in Draft B; in the file they appear in **both** drafts. Companion §5 says the Guided "Reviews list shows four items" but the Guided page shows reviews only as an id list in the state table. Correct the companion before the learner passes. | Source read. | — |

No critical findings yet. A critical finding requires a domain-boundary or safety violation observed in a pass.

## 7. Distinction ledger

- **Observed learner outcomes** (behaviour, times, errors, verbatim quotes): §3–§4 only. **Currently none.**
- **Evaluator judgments** (classification, severity, comprehension scoring): §5–§6, marked **E**. Everything the agent produced above is E.
- **Prototype limitations** (asset cannot evidence the claim): §8, marked **L** — never counted as pass or fail of the product claim.

## 8. Prototype limitations observed (extend runbook §14)

| # | Limitation | Contract claim left untested | Effect on matrix |
|---|-----------|------------------------------|------------------|
| L1 | No mastery action exists in the Guided page (by design, G9). | C11 mastery separate, deliberate, two-step | Expectation probe only; not pass/fail. |
| L2 | No "could not compute" state exists in the Operations page (by design, O9). | C21 | Expectation probe only. |
| L3 | The Operations "graph" is a four-row list; no edges, dependencies or dependency inspection beyond "N downstream" text. | C25 graph nonvisual equivalent; part of C14 | Cannot be fully evidenced with this asset. |
| L4 | Operations destinations (Evidence, Reviews, Analytics, Portfolio, Health) are stubs; no evidence records, review dates or health content exist. | C15, C16, C17, C18, C19 (O3–O7) | O3/O4 cannot be completed; O5–O7 only judge the one-line captions. |
| L5 | Operations Draft B ignores the Limited fixture (F1). | C20 in B | O8 evidence valid for Draft A only (and A has F8). |
| L6 | No omnibar exists in either prototype. | C27 | Untested; record coverage only. |
| L7 | In-memory reducer, fixed timestamps and fixed IDs; "server changed" is a scripted button, not a real second actor. | C08 (partly), C10 | Behaviour demonstrated, not independently produced. |
| L8 | G2 cannot record exactly 30 minutes (adds 25); G3's Create Blocker is blocked as duplicate in the ACTIVE fixture. | C02, C03 | Learner failure on those literal steps must be classed **L**. |
| L9 | Single learner has prior exposure to SkillTrace; cold-start claims (C01, C13) are biased toward success. | C01, C12, C13 | Note in every comprehension cell. |

## 9. Claim-by-claim matrix (input to G-FinalValidationVerdict)

One row per product requirement. Disposition stays **blank** until the verdict ticket fills it: accept / revise / reject / **insufficient evidence**. "Threshold result" below is the evaluator's view of evidence availability; **E-replay** means the agent confirmed the prototype's logic behaves as claimed but no learner observed it.

| Claim ID | Requirement (source ticket) | Scenario(s) | Measurement | Threshold result | Evidence ref (§) | Disposition (verdict ticket) |
|----------|-----------------------------|-------------|-------------|------------------|------------------|------------------------------|
| C01 | Cold start & discovery completes without CLI vocabulary (G-CoreWorkflows) | G1 | first-attempt, errors, recovery | Insufficient evidence (no learner data). E-replay: start works; F4 side effect. | §3.1, F4, L9 | |
| C02 | Session resume / log work without second Session (G-CoreWorkflows) | G2, G8 | first-attempt, refusal | Insufficient evidence. E-replay: second Session refused, resume/log work OK; F3, L8. | §3.1, F3 | |
| C03 | Blocked work ≠ Blocker; Blocker persists across close (G-DomainContract) | G3, G5 | comprehension, outcome | Insufficient evidence. E-replay: Blocker persists across close (G5); G3 flow inconsistent (F2, F6). | §3.1, F2, F6 | |
| C04 | Evidence → eligibility → pass distinct and learner-initiated (G-DomainContract) | G4 | comprehension, outcome | Insufficient evidence. E-replay: three distinct steps; F5. | §3.1, F5 | |
| C05 | Safe Session close implies nothing (G-CoreWorkflows) | G5 | comprehension | Insufficient evidence. E-replay: close leaves Blocker open, node active, no evidence. | §3.1 | |
| C06 | Refusal is safe, recoverable, leaves correct state (G-DomainContract) | G6 | recovery ≥90%, verbatim | Insufficient evidence. E-replay: refusals leave state unchanged; recovery path exists. | §3.1 | |
| C07 | Correction supersedes; original never edited/deleted (G-DomainContract) | G6 | comprehension | Insufficient evidence. E-replay: original kept, marked superseded. | §3.1 | |
| C08 | Stale confirmation refuses without writing (G-DomainContract) | G6, G8 | outcome | Insufficient evidence. E-replay: stale confirm refused, no write. L7. | §3.1, L7 | |
| C09 | Review completion independent of Session; no demotion (G-DomainContract) | G7 | comprehension, outcome | Insufficient evidence. E-replay: review done, Session/progress unchanged. | §3.1 | |
| C10 | Refusals/operational failures create no records (G-DomainContract) | G8 | outcome, comprehension | Insufficient evidence. E-replay: no EvidenceRecord on unrunnable gate. | §3.1 | |
| C11 | Mastery is separate, deliberate, two-step (G-CoreWorkflows) | G9 (**L**) | expectation probe | Insufficient evidence — prototype limitation, not scored. | L1 | |
| C12 | Guided navigation is task-led and predictable (G-InformationArchitecture) | G1–G8 | errors, comprehension | Insufficient evidence. Top nav and mode switcher are inert (E). | §6 F11 | |
| C13 | Operations home orientation in ≤1 glance (P-OperationsWorkspace hybrid) | O1 A/B | time, comprehension | Insufficient evidence. F1 affects B. | F1, L9 | |
| C14 | Graph readiness/evidence inspectable (G-OperationsSurfaces) | O2 | outcome | Insufficient evidence. Readiness and "10 downstream" visible; required evidence not shown (L3, L4). | L3, L4 | |
| C15 | Evidence Vault inspectable; immutability legible (G-OperationsSurfaces) | O3 | outcome, comprehension | Insufficient evidence; asset cannot evidence (stub). | F9, L4 | |
| C16 | Retention/Reviews inspectable (G-OperationsSurfaces) | O4 | outcome | Insufficient evidence; asset cannot evidence (only "3 records"). | F9, L4 | |
| C17 | Analytics show derivations, no fake telemetry (G-OperationsSurfaces) | O5 | comprehension | Insufficient evidence; one-line caption only. | L4 | |
| C18 | Portfolio export honest and redacted (G-OperationsSurfaces) | O6 | comprehension | Insufficient evidence; one-line caption only. | L4 | |
| C19 | Health is ordinary capability, not a score (P-OperationsWorkspace) | O7 | comprehension | Insufficient evidence; caption says "not a learner score" but no health view exists. | L4 | |
| C20 | Empty/limited states truthful, no zeroes-as-truth (G-OperationsSurfaces) | O8 | outcome, comprehension | Insufficient evidence. E: **fails as built** in Draft B (F1) and partly in A (F8). | F1, F8, L5 | |
| C21 | Could-not-compute surfaced honestly (G-ValidationContract) | O9 (**L**) | expectation probe | Insufficient evidence — prototype limitation, not scored. | L2 | |
| C22 | Dark dense system readable; status never colour-only (G-VisualSystem) | all | a11y §5 | Partial: axe contrast clean; status pills carry text as well as colour (E code read). Not manually walked. | §5.1 | |
| C23 | WCAG 2.2 AA mandatory criteria (G-AccessibilityContract) | §5 matrix | mandatory gate | Insufficient evidence; known reflow failure on Operations. | §5, F7 | |
| C24 | Narrow-window degradation keeps critical actions (G-AccessibilityContract) | §11 narrow | walkthrough | Guided: no overflow at 320px (E). Operations: horizontal scroll at 320px (F7). 480px and task completion at narrow widths not walked. | §5.1, F7 | |
| C25 | Graph nonvisual equivalent complete (G-AccessibilityContract) | §11 graph | SR + keyboard | Insufficient evidence (L3). | L3 | |
| C26 | Interaction budget: explicit actions, focus on outcome (G-InteractionModel) | all | errors, focus checks | Insufficient evidence. E: focus moves to result box on each action; F4 silent 20-min record. | F4, F11 | |
| C27 | Omnibar as accelerator, navigation-only (G-InteractionModel) | record coverage | errors | Not covered — no omnibar in either prototype (L6). | L6 | |

## 10. Verdict readiness statement (filled by evaluator)

- All contract scenarios executed? **No.** None of the 18 learner tasks × 3 passes has been run. Missing: pointer, keyboard-only and screen-reader passes for G1–G9 and O1–O9 (+ O1 in Draft B), plus manual narrow-window/zoom, touch, reduced-motion and focus checks.
- Thresholds table (§4) complete? **No** — all rows insufficient evidence.
- Mandatory accessibility gate result (§5.2)? **Not passed / not determinable.** Automated axe is clean apart from landmark `region` notes on scaffolding, but Operations fails 320px reflow (F7) and all manual criteria are unwalked.
- Remaining insufficient-evidence claims (for the verdict ticket to disposition): **C01–C27 all** (C22 and C24 are partial). Defects worth fixing in the prototypes *before* the learner passes, so learner failures are not prototype artefacts: F1 (Draft B fixture), F2/F3/F8 (G2, G3 and Draft A limited-state contradictions), F7 (320px overflow). Alternatively keep them and class resulting learner failures as **L**.

---
*Evidence file for wayfinder map #327; the engine never reads it. The decision lives in G-FinalValidationVerdict's ticket; this report is its evidence.*
