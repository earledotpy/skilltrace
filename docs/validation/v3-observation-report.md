# v3 moderated validation — observation report

**Ticket:** [T-ValidationExecution — run the moderated usability and accessibility contract](https://github.com/earledotpy/skilltrace/issues/344) (wayfinder map #327)
**Protocol:** `docs/validation/v3-usability-runbook.md` (implements [G-ValidationContract — define moderated usability and accessibility validation](https://github.com/earledotpy/skilltrace/issues/339)).
**Consumers:** this report is the *evidence* for [G-FinalValidationVerdict — decide the final product direction from observed evidence](https://github.com/earledotpy/skilltrace/issues/345) — it is not the verdict. Insufficient evidence is recorded explicitly; it is never a pass.

**Status:** TEMPLATE — unfilled. Fill during/after the moderated sessions. Keep the three-way distinction everywhere: **O** = observed learner outcome, **E** = evaluator judgment, **L** = prototype limitation.

---

## 1. Fixture reset procedure (as executed)

| Item | Record |
|------|--------|
| Prototype files + integrity (path, mtime/hash) | `p-core-journey.html`: / `p-operations-workspace.html`: |
| Reset method used per mode (reload / scenario reset / fixture toggle) |  |
| Baseline checks performed before each scenario (per runbook §5) — pass/fail |  |
| Any scenario voided for dirty state (which, why, rerun?) |  |
| Fixture date pinned | 2026-11-17 (Guided) / n/a (Operations) |

## 2. Participant profile and counterbalance order

| ID | Profile | Prior SkillTrace exposure | Keyboard-only | Screen reader (+ which) | Order 1 → Order 2 | Dates | Notes (consent, accommodations) |
|----|---------|---------------------------|---------------|-------------------------|-------------------|-------|--------------------------------|
| P1 |  |  |  |  |  |  |  |
| P2 |  |  |  |  |  |  |  |
| P3 |  |  |  |  |  |  |  |
| P4 |  |  |  |  |  |  |  |
| P5 |  |  |  |  |  |  |  |
| P6 (opt) |  |  |  |  |  |  |  |
| P7 (opt) |  |  |  |  |  |  |  |

Evaluator/moderator/a11y-specialist names (hats worn): moderator: / evaluator: / a11y: 

## 3. Scenario results (raw rows — one per participant × task)

Columns per runbook §10: task (G1–G9, O1–O9), variant (A/B), fixture, outcome, time (s), errors (count + verbatim), recovery (none / self / hint level N; CLI vocabulary needed? y/n), comprehension (verbatim + correct/partial/incorrect), a11y defects (description + severity).

### 3.1 Guided (`p-core-journey.html`)

| P | Task | Reset used | Outcome | Time (s) | Errors | Recovery | CLI vocab? | Comprehension (verbatim → class) | A11y defects |
|---|------|-----------|---------|----------|--------|----------|------------|----------------------------------|--------------|
|  |  |  |  |  |  |  |  |  |  |

### 3.2 Operations (`p-operations-workspace.html`)

| P | Task | Variant | Fixture | Outcome | Time (s) | Errors | Recovery | CLI vocab? | Comprehension (verbatim → class) | A11y defects |
|---|------|---------|---------|---------|----------|--------|----------|------------|----------------------------------|--------------|
|  |  |  |  |  |  |  |  |  |  |  |

## 4. Raw measurements vs thresholds (computed from §3)

| Measure | Threshold (contract) | Observed | Pass? |
|---------|----------------------|----------|-------|
| First-attempt completion, critical learner actions | ≥80% |  |  |
| Recovery after refusal/failure | ≥90% |  |  |
| Every critical action successful for every participant | 100% |  |  |
| Critical safety / domain-boundary violations | 0 |  |  |
| Refusals recoverable without CLI vocabulary | all recorded cases |  |  |

List any critical action that failed for any participant (action, participant, task, outcome).

## 5. Accessibility findings

### 5.1 Automated (per prototype)

| Prototype | Tool + version | Viewport/zoom | Violations (full list, with rule IDs) |
|-----------|----------------|---------------|----------------------------------------|
| p-core-journey |  | 100% / 200% / 320px |  |
| p-operations-workspace |  | 100% / 200% / 320px |  |

### 5.2 Manual walkthrough matrix (rows = checks from runbook §11; record per representative state)

| Check | Guided states walked | Operations states walked | Pass/Fail | Defect description (severity) |
|-------|----------------------|--------------------------|-----------|-------------------------------|
| Keyboard-only operation |  |  |  |  |
| Focus behaviour |  |  |  |  |
| Screen reader |  |  |  |  |
| Contrast |  |  |  |  |
| 200% zoom / reflow |  |  |  |  |
| Reduced motion |  |  |  |  |
| Touch |  |  |  |  |
| Narrow window (480/320 px) |  |  |  |  |
| Graph nonvisual equivalent | — |  |  |  |

**Mandatory accessibility gate:** every mandatory criterion passes — yes/no + blocking criterion list: 

## 6. Findings register (critical / major / minor — no scores)

| # | Class | Description | Evidence (participant, task, quote/screenshot) | Domain-contract link |
|---|-------|-------------|------------------------------------------------|----------------------|
|  |  |  |  |  |

## 7. Distinction ledger

- **Observed learner outcomes** (behaviour, times, errors, verbatim quotes): §3–§4 only.
- **Evaluator judgments** (classification, severity, comprehension scoring): §5–§6, marked **E**.
- **Prototype limitations** (asset cannot evidence the claim): §8, marked **L** — never counted as pass or fail of the product claim.

## 8. Prototype limitations observed (extend runbook §14)

| # | Limitation | Contract claim left untested | Effect on matrix |
|---|-----------|------------------------------|------------------|
|  |  |  |  |

## 9. Claim-by-claim matrix (input to G-FinalValidationVerdict)

One row per product requirement. Disposition stays **blank** until the verdict ticket fills it: accept / revise / reject / **insufficient evidence**.

| Claim ID | Requirement (source ticket) | Scenario(s) | Measurement | Threshold result | Evidence ref (§) | Disposition (verdict ticket) |
|----------|-----------------------------|-------------|-------------|------------------|------------------|------------------------------|
| C01 | Cold start & discovery completes without CLI vocabulary (G-CoreWorkflows) | G1 | first-attempt, errors, recovery |  |  |  |
| C02 | Session resume / log work without second Session (G-CoreWorkflows) | G2, G8 | first-attempt, refusal |  |  |  |
| C03 | Blocked work ≠ Blocker; Blocker persists across close (G-DomainContract) | G3, G5 | comprehension, outcome |  |  |  |
| C04 | Evidence → eligibility → pass distinct and learner-initiated (G-DomainContract) | G4 | comprehension, outcome |  |  |  |
| C05 | Safe Session close implies nothing (G-CoreWorkflows) | G5 | comprehension |  |  |  |
| C06 | Refusal is safe, recoverable, leaves correct state (G-DomainContract) | G6 | recovery ≥90%, verbatim |  |  |  |
| C07 | Correction supersedes; original never edited/deleted (G-DomainContract) | G6 | comprehension |  |  |  |
| C08 | Stale confirmation refuses without writing (G-DomainContract) | G6, G8 | outcome |  |  |  |
| C09 | Review completion independent of Session; no demotion (G-DomainContract) | G7 | comprehension, outcome |  |  |  |
| C10 | Refusals/operational failures create no records (G-DomainContract) | G8 | outcome, comprehension |  |  |  |
| C11 | Mastery is separate, deliberate, two-step (G-CoreWorkflows) | G9 (**L**) | expectation probe |  |  |  |
| C12 | Guided navigation is task-led and predictable (G-InformationArchitecture) | G1–G8 | errors, comprehension |  |  |  |
| C13 | Operations home orientation in ≤1 glance (P-OperationsWorkspace hybrid) | O1 A/B | time, comprehension |  |  |  |
| C14 | Graph readiness/evidence inspectable (G-OperationsSurfaces) | O2 | outcome |  |  |  |
| C15 | Evidence Vault inspectable; immutability legible (G-OperationsSurfaces) | O3 | outcome, comprehension |  |  |  |
| C16 | Retention/Reviews inspectable (G-OperationsSurfaces) | O4 | outcome |  |  |  |
| C17 | Analytics show derivations, no fake telemetry (G-OperationsSurfaces) | O5 | comprehension |  |  |  |
| C18 | Portfolio export honest and redacted (G-OperationsSurfaces) | O6 | comprehension |  |  |  |
| C19 | Health is ordinary capability, not a score (P-OperationsWorkspace) | O7 | comprehension |  |  |  |
| C20 | Empty/limited states truthful, no zeroes-as-truth (G-OperationsSurfaces) | O8 | outcome, comprehension |  |  |  |
| C21 | Could-not-compute surfaced honestly (G-ValidationContract) | O9 (**L**) | expectation probe |  |  |  |
| C22 | Dark dense system readable; status never colour-only (G-VisualSystem) | all | a11y §5 |  |  |  |
| C23 | WCAG 2.2 AA mandatory criteria (G-AccessibilityContract) | §5 matrix | mandatory gate |  |  |  |
| C24 | Narrow-window degradation keeps critical actions (G-AccessibilityContract) | §11 narrow | walkthrough |  |  |  |
| C25 | Graph nonvisual equivalent complete (G-AccessibilityContract) | §11 graph | SR + keyboard |  |  |  |
| C26 | Interaction budget: explicit actions, focus on outcome (G-InteractionModel) | all | errors, focus checks |  |  |  |
| C27 | Omnibar as accelerator, navigation-only (G-InteractionModel) | record coverage | errors |  |  |  |

## 10. Verdict readiness statement (filled by evaluator)

- All contract scenarios executed? (list any missing)
- Thresholds table (§4) complete?
- Mandatory accessibility gate result (§5.2)?
- Remaining insufficient-evidence claims (for the verdict ticket to disposition): 

---
*Evidence file for wayfinder map #327; the engine never reads it. The decision lives in G-FinalValidationVerdict's ticket; this report is its evidence.*

