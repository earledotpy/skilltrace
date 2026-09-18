# P-StudyFortnight — per-day reports (contract §8a)

Eight 105-minute sessions, days 1/3/5/7/8/10/12/14; Day 1 = 2026-09-22 (UTC).
Each day: starting facts -> explicit actions -> expected vs observed -> friction -> uncertainty.
ENGINE OUTPUT quotes are verbatim captures; FABRICATED marks hand-authored scenario data.

## Day 1 — 2026-09-22

**Shape.** Session 1 (105 min): discovery (math/data/Python), select entry, open session, first artifact work

**Starting facts.** Fresh fixture; empty progress; `sync` derives 49 nodes available.

**Explicit actions.** `today --minutes 105`, `next --minutes 105 --limit 5`, `next --show-locked --limit 3`, `node × 3 (entry details)`, `resources --node-id math entry`, `start MATH`, `work --minutes 70`, `close`

**Expected.** A beginner could ask the engine for math/data/Python foundations and get walkable entry points.

**Observed.** Read-only surfaces work, but discovery is id-only: nothing accepts a subject query; `today` and `next` both top-rank an agents-course node (off the beginner arc) every single day of the fortnight.

**Friction.**
- No text/keyword discovery surface exists (`next` takes only minutes/limit/show-locked).
- Learner must already know `programming.python.variables_01`-style ids to see any skill.
- `next` prints a stale command form (`skilltrace session start --node …`) while `today` prints the real one (`skilltrace start …`).
- `next --show-locked` sized a 60-min session and still rendered no locked rows visibly.

**Uncertainty.** Whether the agents-first ranking is goal-weighting (seed intent) or accidental; real learner intent not measurable from simulation.

```text
[ENGINE OUTPUT] Day 1 — recommendations sized
OPTION 1 — 105-MIN SESSION
Explain what an AI agent is and how tools extend an LLM
  [Ready to start]

Explain what an AI agent is and how tools extend an LLM is the top pick for this session — it's in the 'foundational' track and scores highest overall. Passing this unlocks 10 downstream skills. Define agent, tool, and action loop; contrast CodeAgents with tool-calling agents.

Where to learn
  Hf Agents Course -- https://huggingface.co/learn/agents-course/unit0/introduction

How to proceed
  Start studying Explain what an AI agent is and how tools extend an LLM and submit evidence when your work is ready. Estimated effort: 60–120 min.

… (73 more lines)
```

```text
[ENGINE OUTPUT] Day 1 — discovery probe: math entry detail
THIS SKILL
Apply order of operations
  [Ready to start]

You're clear to begin Apply order of operations -- nothing is blocking you. It needs 3 accepted submission(s) to pass. You decide when the work is good enough, not an AI.

Where to learn
  Khan Arithmetic -- https://www.khanacademy.org/math/arithmetic

How to proceed
  0 of 3 Order of operations problem-set evidence.

… (2 more lines)
```

## Day 3 — 2026-09-24

**Shape.** Session 2: return to unfinished work, evidence inspection, continued artifact work

**Starting facts.** MATH active (in progress); 0/3 evidence; no session open.

**Explicit actions.** `today`, `node MATH`, `work MATH (continue)`, `eligibility MATH`, `close`

**Expected.** Today foregrounds the unfinished thread; work continues it.

**Observed.** `node` correctly shows [In progress] and the 0-of-3 bar; `eligibility` reads 0/3 NOT ELIGIBLE. But `work` refuses — a closed session cannot be reopened; returning to unfinished work requires a fresh `start` (a new session record per study day).

**Friction.**
- 'Return to unfinished work' has no resume affordance: work requires an open session, so each study day re-`start`s (more sessions, no thread continuity).
- `today` still says 'your best focus today is [agents node]' even with an in-progress node.

**Uncertainty.** Whether repeated start/close is by design (session = day) — the record trail suggests yes, but the learner-facing copy never says so.

```text
[ENGINE OUTPUT] Day 3 — today: what is unfinished?
TODAY

There's no session open — your best focus today is Explain what an AI agent is and how tools extend an LLM. There's Study velocity is below target: 0.4 work items/week average (target: 2). and Review completion is below target: 0% (target: 80%). needing attention — but finishing your open work matters more than starting something new.

Where to learn (top focus)
  Hf Agents Course -- https://huggingface.co/learn/agents-course/unit0/introduction

How to proceed
  Start studying Explain what an AI agent is and how tools extend an LLM.

DO THIS NEXT
  Start studying agents.concepts.agent_fundamentals_01: `skilltrace start agents.concepts.agent_fundamentals_01`
… (2 more lines)
```

## Day 5 — 2026-09-26

**Shape.** Session 3: discovery round 2, second-strand selection, artifact work

**Starting facts.** MATH active; PY available; workload warn threshold at 2 active nodes.

**Explicit actions.** `today`, `next --limit 8`, `node PY`, `resources PY`, `start PY`, `work PY`, `close`

**Expected.** Second strand opens with a workload warning at the threshold.

**Observed.** Warning fired exactly: 'this start makes 2 active nodes — at or past the workload warning threshold of 2.' Advisory only; action proceeded.

**Friction.**
- Discovery round 2 again shows the same agents OPTION 1; strand browsing is impossible without ids.

**Uncertainty.** None for the threshold; ranking behavior carried from Day 1.

```text
[ENGINE OUTPUT] Day 5 — open the Python-strand session
opened session ses.2026-09-18.02.
programming.python.variables_01: available -> active.
[warning] this start makes 2 active nodes — at or past the workload warning threshold of 2.
```

## Day 7 — 2026-09-28

**Shape.** Session 4: evidence submission + gate judgment readout, next-action readback

**Starting facts.** MATH manual gate (learner authority), spec minimum 3 accepted submissions.

**Explicit actions.** `today`, `submit MATH (no verdict)`, `submit MATH --accept`, `eligibility MATH`, `today`, `close`

**Expected.** Submission without a verdict is refused; explicit learner verdict accepted; eligibility readback honest.

**Observed.** Refusal path is clean and explicit ('manual-authority node requires an explicit verdict … nothing written'). Accept wrote ev…001 (accepted); eligibility read 1/3 accepted, NOT ELIGIBLE. Gate readout matches the learner-authority boundary.

**Friction.**
- The node view says 'It needs 3 accepted submission(s) to pass' — countable, but the learner must find `eligibility` themselves; `today` never mentions evidence progress.
- No open session existed on this day, so `close` refused — a submission day with no artifact work is a session-less day.

**Uncertainty.** Objective-gate path (check-script judgment) not exercised in the baseline; math/data/Python entry gates are manual.

```text
[ENGINE OUTPUT] Day 7 — submit without a manual verdict
[error] manual-authority node requires an explicit verdict: pass --accept or --reject.
evidence submit: refused for node math.arithmetic.order_operations_01 — nothing written.
```

```text
[ENGINE OUTPUT] Day 7 — scripted learner's manual gate
verdict: ACCEPTED
evidence submit: wrote ev.math.arithmetic.order_operations_01.001 (accepted).
```

```text
[ENGINE OUTPUT] Day 7 — gate readback
eligibility math.arithmetic.order_operations_01: NOT ELIGIBLE
  spec spec.math.arithmetic.order_operations: 1/3 accepted (below minimum)
```

## Day 8 — 2026-09-29

**Shape.** Session 5: third-strand selection, artifact work (no-pass session permitted)

**Starting facts.** 3rd active node crosses the warn-2 threshold again.

**Explicit actions.** `today`, `node SQL`, `start SQL`, `work SQL --minutes 105`, `close`

**Expected.** Third strand opens; warning repeats; session ends without a pass — no demotion pressure.

**Observed.** Warning repeated; session closed; SQL stays active at 0/1 evidence. No-pass sessions are unproblematic.

**Friction.**
- Three strands at once is fine mechanically, but no surface summarizes 'you have 3 strands going' outside the workload warning.

**Uncertainty.** None.

```text
[ENGINE OUTPUT] Day 8 — open the SQL-strand session
opened session ses.2026-09-18.03.
data.sql.select_basics_01: available -> active.
[warning] this start makes 3 active nodes — at or past the workload warning threshold of 2.
```

## Day 10 — 2026-10-01

**Shape.** Session 6: blocker/failure handling inside honest-work shape

**Starting facts.** PY practice hit reassignment confusion; 3rd active warning expected on start.

**Explicit actions.** `today`, `start PY`, `work PY --blocked`, `attempt record PY --outcome failed`, `blocker create PY`, `blockers`, `suggest remediation`, `close`

**Expected.** Failed attempt and blocker recorded; remediation pressure appears.

**Observed.** Both records wrote cleanly (immutable attempt; open blocker listed). `suggest remediation` honestly reported there is no remediation edge covering this blocker and pointed at the ad-hoc action command.

**Friction.**
- Failed attempts are invisible in `today`/`next` — the learner's own failure exists only via `suggest remediation` or raw listings.
- Blocker resolution later requires typing the id `blk.<node>.001` — the learner must copy it from a listing.

**Uncertainty.** Whether any beginner node has a remediation edge (19 remediation edges exist in the graph; none from the Python entry).

```text
[ENGINE OUTPUT] Day 10 — record the failed attempt
attempt att.programming.python.variables_01.001: failed
attempt record: wrote att.programming.python.variables_01.001 (failed).
```

```text
[ENGINE OUTPUT] Day 10 — name the persistent stuckness
opened blocker blk.programming.python.variables_01.001.
```

```text
[ENGINE OUTPUT] Day 10 — remediation pressure
suggest remediation: no remediation edge covers blocker blk.programming.python.variables_01.001 on programming.python.variables_01 — log an ad-hoc action: skilltrace remediation create programming.python.variables_01 --description "..." --blocker blk.programming.python.variables_01.001 (~30 min, due 2026-09-19).
```

## Day 12 — 2026-10-03

**Shape.** Session 7: return to unfinished work, correction/supersession

**Starting facts.** Open blocker on PY; day-7 accepted record ev…001 on MATH.

**Explicit actions.** `today`, `blocker resolve --summary`, `remediation create --blocker`, `submit --supersedes ev…001 --reason … --accept`, `submit --supersedes ev…002 … --accept (depth 2)`, `eligibility MATH`, `close`

**Expected.** Correction supersedes the old record; the chain stays as history; eligibility counts only live records.

**Observed.** Supersession wrote ev…002 then ev…003 (both accepted, chained); the original record was never edited or deleted. Supersede also requires the explicit manual verdict (`--accept`), same as first submission.

**Friction.**
- `today` showed the open blocker line — good; but nothing anywhere shows the correction chain except `report evidence`.
- Session-less day again: no `start` issued, so `close` refused (honest, but the copy doesn't guide).

**Uncertainty.** None beyond display gaps.

```text
[ENGINE OUTPUT] Day 12 — supersede the day-7 record
verdict: ACCEPTED
evidence submit: wrote ev.math.arithmetic.order_operations_01.002 (accepted).
```

```text
[ENGINE OUTPUT] Day 12 — supersede the superseding record
verdict: ACCEPTED
evidence submit: wrote ev.math.arithmetic.order_operations_01.003 (accepted).
```

## Day 14 — 2026-10-05

**Shape.** Session 8: close sessions honestly, final evidence inspection, day report

**Starting facts.** MATH 1/3 live accepted (after chain), PY blocker resolved + 1 failed attempt, SQL 0/1, 0 passes — by design.

**Explicit actions.** `today`, `eligibility SQL`, `close`, `report progress/evidence/blockers`, `reviews`, `retention status`, `analytics velocity/blockers`, `health`

**Expected.** A readable fortnight summary: what moved, what stands, what needs attention.

**Observed.** Reports are honest and detailed (progress per track, evidence chain, resolved blocker history). `health` rolls up repo diagnostics fine. But learner-facing advisories are misleading at this scale: 'Review completion is below target: 0% (target: 80%)' with zero reviews ever scheduled; evidence coverage 1% reads as failure, though the arc had no passes by contract.

**Friction.**
- Advisory copy doesn't qualify sparse-history baselines (velocity does — it prints a limited-data advisory only in `analytics velocity`).
- No single learner-facing 'Health' view exists: the facts are spread across five commands.
- Report progress 'Currently working on Apply order of operations. Next up: finish active evidence…' — the strongest line in the fortnight, buried in a report.

**Uncertainty.** Real comprehension/time cannot be measured from automation (contract §7).

```text
[ENGINE OUTPUT] Day 14 — progress report
Your Learning Journey
---------------------
You have completed 0 of 100 skills (0 mastered, 0 passed) across 4 study sessions (5.2 hours).

Track Breakdown
---------------
1. Math Foundations -- 0% complete (0/31 nodes)
   Currently working on Apply order of operations. Next up: finish active evidence submissions.

2. Programming & Tooling -- 0% complete (0/18 nodes)
   Currently working on Use variables and expressions in Python. Next up: finish active evidence submissions.

… (9 more lines)
```

```text
[ENGINE OUTPUT] Day 14 — analytics: velocity
[advisory] Study velocity is below target: 1.3 work items/week average (target: 2).
[advisory] Review completion is below target: 0% (target: 80%).
[advisory] Evidence coverage is below target: 1% (target: 60%).

VELOCITY
--------
  Sessions in window : 4
  Nodes touched      : 3
  Study time         : 310 min (5.2 h)

  Group (Prefix)                Sessions    Nodes
  ----------------------------------------------
… (6 more lines)
```

```text
[ENGINE OUTPUT] Day 14 — health roll-up
graph: 100 nodes, 157 edges — OK
evidence: 81 specs, 81 gates, 3 records, 1 attempts — OK, 38 warning(s) (see `skilltrace validate evidence`)
execution: 4 sessions, 8 work items, 1 blockers, 1 remediation actions, 0 reviews — OK
policy: 12 policy file(s) — OK
resources: 45 resource(s) — OK
progress store: 49 node(s); states: active=3, available=46
[warning] 51 node(s) missing from the progress store — run `skilltrace sync`.
resources: 45 resource(s); verified=45, stale=0, unverified=0, broken=0
health: OK (39 warning(s)).
```
