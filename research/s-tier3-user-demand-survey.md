# SkillTrace — Multi-curriculum demand survey

**For:** existing SkillTrace test cohort
**From:** SkillTrace maintainer (earledotpy)
**Length:** 5 short questions (≤3 min to answer)
**Why you're being asked:** we're scoping post-v1 Tier 3 work and need actual
user signal — not just ecosystem research — on whether running two
SkillTrace curricula in one repo (without a separate clone) is a feature
real people want.

This is **not** a marketing email and not a feature announcement. It's a
short scoping survey. You can answer in one short paragraph per question
or in a single block — whatever's easiest.

---

## The 5 questions

### Q1. Have you ever wanted to run **two different SkillTrace curricula in one repo without making a second clone**?

- [ ] Yes
- [ ] No
- [ ] Hadn't thought about it

### Q2. If yes — what was the use case? (Skip if Q1 ≠ Yes.)

Pick any that apply, or describe your own:

- [ ] Side-by-side comparison of two curricula (e.g. learning ML while
      comparing it to an older "before-v1.3" version)
- [ ] Shared resources across curricula (e.g. one `resources/` library
      feeding two skill graphs)
- [ ] Switching contexts without losing the other curriculum's progress
      (e.g. work-vs-personal, two parallel learning tracks)
- [ ] Parallel learning tracks (e.g. Phase 2 ML and Phase 3 agentic in
      the same workspace)
- [ ] Other: ____________

### Q3. If yes — did you work around it? How? (Skip if Q1 ≠ Yes.)

- [ ] Made a second clone on the same machine
- [ ] Used a separate machine / VM
- [ ] Used symlinks or file copies
- [ ] Gave up
- [ ] Other: ____________

### Q4. If no — what stopped you? (Skip if Q1 = Yes.)

- [ ] Lack of need (one curriculum is enough)
- [ ] Lack of a clean way to do it, but I might want it
- [ ] Tried it once, the friction killed the idea
- [ ] Other: ____________

### Q5. Where would multi-curriculum sit in your workflow, **if it existed and worked well**?

- [ ] Daily — I switch curricula as part of the work day
- [ ] Weekly — I bounce between curricula on a cadence
- [ ] Only on context switch — e.g. when I start a new project / job
- [ ] Never — I answered "No" to Q1

---

## Optional follow-ups (for "Yes" respondents who want to go deeper)

**Q6.** Which axis matters more to you: **isolated progress** (each
curriculum tracks its own `passed`/`mastered` and never shares) vs
**shared progress** (one `passed`/`mastered` set, two curricula
referencing the same nodes)? Or do you want both as a config option?

**Q7.** Would you tolerate a thin **`skilltrace curricula` orchestrator
CLI** that switches the active curriculum (changing which `graph/`
subtree and `state.yaml` are "live") without any engine code changes —
just file-system + config swap? Or does that feel too thin to count as
the feature?

**Q8.** If you had multi-curriculum, would you also want
**cross-curriculum analytics** (e.g. "you mastered 12 nodes in
Curriculum A that map to 4 nodes in Curriculum B")? Or is that scope
creep?

**Q9.** Anything else we should know before we slot this into the
post-v1 roadmap?

**Q10.** Free field — anything you wish SkillTrace asked you about
before deciding what to build next.

---

## How to respond

- Reply to the issue / email / message the maintainer sent you with this
  survey. Inline answers, bullets, or one-paragraph-per-question — all
  fine.
- **Deadline:** [FILL IN — suggest 7 days from send date].
- **Anonymity:** responses will be summarised anonymously in the
  ticket resolution; quotes may be used with your handle unless you
  say otherwise.
