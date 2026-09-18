# P-StudyFortnight — candidate-trigger matrix (contract §8c)

Nine deferred candidates; triggers verbatim from `docs/POST_V2_ROADMAP.md` Beyond and #280.
Dispositions: reconsideration-supported / deferral-supported / insufficient-evidence — never auto-implementation.

## 1. Learner-facing diagnostic analytics

**Trigger.** a first real blocker or failed assessment attempt (friction to diagnose), or learner demand for the primitive

**Positive case.** B06–B08: 2/3/4 failed attempts produce zero learner-visible signal; B11: failed review leaves nothing pointing at rework; B13: broken resource invisible in node view/today; B02: silent session-on-passed

**Negative case.** Learner can function without it: blockers/eligibility/report surfaces carry the facts when sought

**Boundary case.** P-DiagnosticsSim (#285) already shaped the friction surface; this fortnight adds the demand-side evidence shape

**Measurable observation this fortnight.** Friction exists and is invisible at exactly the trigger's shape; demand is the learner's call on reading this artifact

**Disposition.** Reconsideration-supported (demand branch only; first-real-friction branch still needs lived data — learner verdict required)

## 2. Practice profiles + prompt extraction

**Trigger.** a first real review backlog (reviews accumulating under retention pressure)

**Positive case.** B10/B11 exercise review flows but no backlog accumulates (no pass by contract)

**Negative case.** Zero reviews scheduled all fortnight; a sequencing layer would build nothing

**Boundary case.** B10 shows the boundary semantics a backlog would stress

**Measurable observation this fortnight.** Not trippable by simulation, as the contract predicted

**Disposition.** Deferral-supported (unchanged trigger; insufficient evidence)

## 3. Badge issuance

**Trigger.** a concrete portfolio consumer demands a badge primitive

**Positive case.** —

**Negative case.** —

**Boundary case.** —

**Measurable observation this fortnight.** UNTESTABLE by the fortnight: no consumer, no passed nodes by contract

**Disposition.** Insufficient evidence (stays deferred)

## 4. Tier 3 MC/PKM integrations

**Trigger.** fresh-user demand (MC-1/MC-2, PKM-2/3/4) / ecosystem settling (PKM-4); MC-3 no-go by construction; PKM-1 shipped

**Positive case.** —

**Negative case.** —

**Boundary case.** —

**Measurable observation this fortnight.** UNTESTABLE: no PKM in use; outreach tests the in-vault variant, not demand

**Disposition.** Insufficient evidence (stays deferred)

## 5. Full gate-runner / scheduler-queue

**Trigger.** a concrete Phase 4/5 seed artifact whose objective gates are hand-run often enough to automate; earliest re-check is v2.5 receipt load

**Positive case.** B12 chain exercised manual evidence handling, not gate running

**Negative case.** All three beginner gates are manual (learner authority) — no objective gate was hand-run in the arc

**Boundary case.** v2.5 receipt load unchanged

**Measurable observation this fortnight.** Hand-run load not demonstrated; simulation cannot supply it

**Disposition.** Deferral-supported (unchanged; hand-run load unobserved)

## 6. Verification-sweep scheduling automation

**Trigger.** disjunction: demonstrated manual-sweep cadence, a downstream slot needing scheduled checks, or serve/today background-sweep work

**Positive case.** B13: broken marker appears only after a manual verify-resource

**Negative case.** No sweep cadence demonstrated; single broken-resource incident, manually handled

**Boundary case.** —

**Measurable observation this fortnight.** No cadence emerged from the fortnight

**Disposition.** Deferral-supported (unchanged)

## 7. Resource deep-verification (cert metadata, content-hash drift)

**Trigger.** a content-drift incident a hash check would have caught, or a host/publisher requiring pinned-content verification

**Positive case.** B13 simulates a dead link (reachability), not content drift

**Negative case.** No drift incident; no pinned-content host in the arc

**Boundary case.** —

**Measurable observation this fortnight.** Trigger untripped; cert-metadata slice remains first if it ever trips

**Disposition.** Deferral-supported (unchanged)

## 8. Portable evidence locator

**Trigger.** a second external consumer of evidence records beyond the portfolio export exists

**Positive case.** —

**Negative case.** —

**Boundary case.** —

**Measurable observation this fortnight.** UNTESTABLE: no second consumer exists

**Disposition.** Insufficient evidence (stays deferred)

## 9. Default-deny share-profile extensions

**Trigger.** a second sharing/export surface demands a privacy posture

**Positive case.** —

**Negative case.** —

**Boundary case.** —

**Measurable observation this fortnight.** UNTESTABLE: existing Share profile in force

**Disposition.** Insufficient evidence (stays deferred)
