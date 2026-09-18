# P-StudyFortnight — current vs proposed comparisons (contract §8d)

Identical input for discovery: `python for beginners`. Identical state for health: baseline fixture at day 14.

## Discovery — current engine

```text
[ENGINE OUTPUT] the only discovery surface's flags
usage: skilltrace next [-h] [--minutes MINUTES] [--limit LIMIT]
                       [--show-locked]

options:
  -h, --help         show this help message and exit
  --minutes MINUTES  Minutes available this session.
  --limit LIMIT      Maximum number of recommendations.
  --show-locked      Also show locked nodes (never recommended as available).
```

```text
[ENGINE OUTPUT] intent probe
OPTION 1 — 105-MIN SESSION
Explain what an AI agent is and how tools extend an LLM
  [Ready to start]

Explain what an AI agent is and how tools extend an LLM is the top pick for this session — it's in the 'foundational' track and scores highest overall. Passing this unlocks 10 downstream skills. Define agent, tool, and action loop; contrast CodeAgents with tool-calling agents.

Where to learn
  Hf Agents Course -- https://huggingface.co/learn/agents-course/unit0/introduction

How to proceed
… (75 more lines)
```

```text
[ENGINE OUTPUT] synonym probe: guess the id 'variables_01'
node: FAILED -- unknown node variables_01.
```

```text
[ENGINE OUTPUT] synonym probe: guess 'python.vars_01'
node: FAILED -- unknown node programming.python.vars_01.
```

```text
[ENGINE OUTPUT] no-results probe
node: FAILED -- unknown node nonexistent.foo_01.
```

```text
[ENGINE OUTPUT] ambiguity probe: two plausible
THIS SKILL
Choose the right chart for the question
  [Ready to start]

You're clear to begin Choose the right chart for the question -- nothing is blocking you. It needs 1 accepted submission(s) to pass. You decide when the work is good enough, not an AI.

Where to learn
  Data To Viz -- https://www.data-to-viz.com/
  Fundamentals Of Dataviz -- https://clauswilke.com/dataviz/

… (5 more lines)
```

## Discovery — PROPOSED mockup

Dropdown/cards/combination surface for the same input; static illustration labeled PROPOSED in the HTML artifact (`prototype/study-fortnight.html`). Keyboard, mobile and no-script behavior are proposed properties only — no shipped surface was exercised in a browser, so they are reported untested.

## Health — current engine

```text
[ENGINE OUTPUT] health roll-up
graph: 100 nodes, 157 edges — OK
evidence: 81 specs, 81 gates, 3 records, 1 attempts — OK, 38 warning(s) (see `skilltrace validate evidence`)
execution: 4 sessions, 8 work items, 1 blockers, 1 remediation actions, 0 reviews — OK
policy: 12 policy file(s) — OK
resources: 45 resource(s) — OK
progress store: 49 node(s); states: active=3, available=46
[warning] 51 node(s) missing from the progress store — run `skilltrace sync`.
resources: 45 resource(s); verified=45, stale=0, unverified=0, broken=0
… (1 more lines)
```

```text
[ENGINE OUTPUT] evidence warnings detail
evidence: 81 specs, 81 gates, 3 records, 1 attempts
[warning] node agents.capstone.deployed_agent_integration_01 has no gate — it cannot accept evidence and is never pass-eligible.
[warning] node agents.capstone.deployed_agent_integration_01 has no required artifact spec — it is never pass-eligible.
[warning] node agents.concepts.agent_fundamentals_01 has no gate — it cannot accept evidence and is never pass-eligible.
[warning] node agents.concepts.agent_fundamentals_01 has no required artifact spec — it is never pass-eligible.
[warning] node agents.data.llamaindex_rag_01 has no gate — it cannot accept evidence and is never pass-eligible.
[warning] node agents.data.llamaindex_rag_01 has no required artifact spec — it is never pass-eligible.
[warning] node agents.deploy.docker_engine_build_run_01 has no gate — it cannot accept evidence and is never pass-eligible.
… (32 more lines)
```

```text
[ENGINE OUTPUT] review health
Scheduled Reviews
------------------
Your retention checks keep passed skills from fading. No reviews currently scheduled.

Ready for Mastery Verification
------------------------------
No reviews currently scheduled. Pass a skill to schedule spaced retention checks.
Recent Review Outcomes
… (2 more lines)
```

```text
[ENGINE OUTPUT] blocker health
Where you are stuck
-------------------
You have no open blockers -- smooth sailing!

Current Obstacles
-----------------
No open obstacles logged. When you encounter persistent friction, run `skilltrace blocker create`.
Resolved History
… (4 more lines)
```

```text
[ENGINE OUTPUT] progress health
Your Learning Journey
---------------------
You have completed 0 of 100 skills (0 mastered, 0 passed) across 4 study sessions (5.2 hours).

Track Breakdown
---------------
1. Math Foundations -- 0% complete (0/31 nodes)
   Currently working on Apply order of operations. Next up: finish active evidence submissions.
… (13 more lines)
```

```text
[ENGINE OUTPUT] resource health
resource-report: 45 resource(s), 100 node(s); stale after 180d; summary: active=45, retired=0.
  [verified] khan-arithmetic — last verified 2026-07-10
  [verified] khan-algebra — last verified 2026-07-10
  [verified] khan-precalculus — last verified 2026-07-10
  [verified] khan-statistics-probability — last verified 2026-07-10
  [verified] khan-linear-algebra — last verified 2026-07-10
  [verified] khan-differential-calculus — last verified 2026-07-10
  [verified] 3blue1brown-essence-linear-algebra — last verified 2026-07-10
… (39 more lines)
```

```text
[ENGINE OUTPUT] review suggestions
suggest reviews: nothing due — 0 scheduled ahead.

suggest reviews: Retention suggestions
suggest reviews: ----------------------
suggest reviews: nothing fading — no retention suggestions right now.
```

```text
[ENGINE OUTPUT] baseline day 14 — analytics velocity advisories
[advisory] Study velocity is below target: 1.3 work items/week average (target: 2).
[advisory] Review completion is below target: 0% (target: 80%).
[advisory] Evidence coverage is below target: 1% (target: 60%).

VELOCITY
--------
… (12 more lines)
```

## Health — PROPOSED mockup

A single learner-facing Health view over exactly those facts (Study rhythm, Stuck right now, Due for review, Evidence gaps, Study resources, collapsed Repository diagnostics). Static illustration, labeled PROPOSED.

## Engine observations worth a decision

- **H1 The fixture clock cannot date engine-written records** — `start`/`close` stamp real wall-clock ids and timestamps (sessions came out `ses.2026-09-18.*`; record `created_at` likewise), `review schedule` reads `_now_iso()` directly, and `close --end` validates against the real clock. Fabricated histories therefore cannot be date-labeled by the engine itself: the fortnight's records carry real dates in an isolated fixture, and the simulated-day labels exist only in this artifact. Fixing it would mean threading `Context.clock` through those writers.
- **H2 `next` prints a stale command form** — `next`'s DO THIS NEXT line says `skilltrace session start --node <id>`; that command does not exist — the real form printed by `today` is `skilltrace start <id>`. A learner following `next` verbatim hits an argparse error.
- **H3 `next` ignores the learner's active work** — With one, two, and three active strands, OPTION 1 stayed a never-touched agents node every day. Only `today` picked up the open-session thread. Recommendation ranking and the daily view disagree about what matters.
- **H4 Discovery is id-only** — No command accepts a subject query; `node` fails with a bare 'unknown node <id>' on a near-miss (`variables_01`, `python.vars_01`). Math/data/Python browsing is impossible without memorized ids.
- **H5 Failures and resource problems are invisible where the learner looks** — 2/3/4 failed attempts, a failed review, a rejected artifact, and a broken resource change nothing in `today` or `node`; each is reachable only through a separate command the learner must know to run.
- **H6 Advisories overstate penalty on a sparse, pass-free fortnight** — 'Review completion is below target: 0% (target: 80%)' printed with zero reviews ever scheduled, and 'evidence coverage is below target: 1%' with no passes possible under the contract. Only `analytics velocity` qualifies itself with a limited-data advisory.
- **H7 Two review surfaces disagree on the due date** — On the due date `reviews` lists the review as due while `suggest reviews` says 'nothing due — 1 scheduled ahead'. A day later both agree it is overdue.
- **H8 The 12 h stale-session policy is never surfaced** — A session left open 13 hours still reads as '~0 min' with no staleness note.
- **H9 `graph impact` escapes `--root` isolation** — Run against a fixture, it compared the fixture's edges to the host repo's git HEAD and reported unrelated no-op edges — advisory output from a fixture is meaningless.
- **H10 `--show-locked` renders no locked rows visibly** — Probing locked-skill visibility via `next --show-locked` returned the same available-node OPTION 1 output; locked skills stayed undiscoverable.
- **H11 Starting a passed node opens a session silently** — `start` on a passed node returned exit 0 and opened a session with no transition line and no explanation. The asserted state held (verified in the store) — the invariant is intact; the affordance is unexplained.

## Runnable vs reported-untested

- **Objective-gate judgment (check-script run)** — All three beginner entry gates are manual (`authority: manual`); no objective gate was hand-run. (UNTESTED)
- **Mastery path and mastery eligibility** — No pass occurs in the locked arc (no required pass); mastery needs passed + spaced review. (UNTESTED)
- **Review auto-scheduling after pass** — Scheduling is pass-driven; automating `pass` is forbidden, so the auto-schedule path was never triggered. (UNTESTED)
- **Resource reachability checks (`check-resource(s)`)** — Deliberately not called: they perform network reads and this prototype stays offline. (UNTESTED)
- **`graph impact` on a fixture** — Depends on git context; observed to escape `--root` (H9). Needs a git-context fixture to test properly. (UNTESTED (observed hazard))
- **`replace-resource` success path** — No same-node candidate exists for the broken math resource; refusal observed ('share no node') instead. (UNTESTED)
- **Honest backdated `close --end` under a simulated clock** — Refused as future-dated because the check uses the real clock (H1). (UNTESTED)
- **Keyboard / mobile / no-script behavior** — No shipped surface was probed in a browser; these remain PROPOSED mockup properties only. (PROPOSED-ONLY)
- **Human comprehension, real study time, sustained demand** — Cannot be measured from automation (contract §7). (NOT MEASURABLE)
- **Badge, MC/PKM, portable evidence locator, share-profile triggers** — Untestable by construction: no consumer, no PKM in use, no second export surface. (UNTESTED BY CONSTRUCTION)
- **Sweep cadence, content-drift incident, gate-runner hand-run load** — Trigger conditions cannot be produced inside a fortnight. (UNTESTED BY CONSTRUCTION)

## Protected-record hashes

```json
{
  "graph\\state.yaml": "f641403abe1122ed7a37f68e138125a2018e9a599c2953f61d994819ab15bbee",
  "execution\\blockers.yaml": "999622b0eab7b7e2302029e6a0fb04e6bedfadb8d57e94fad5558dc09b385348",
  "execution\\events.yaml": "e38c0b503fcf42ff1609ee1a5702fe8a84a821fc2564091aa227e472413f54e4",
  "execution\\remediation_actions.yaml": "c723ccfc8503f46c39dae126ce44456efcb5246c56b439cab8d4382fb7a13da1",
  "execution\\reviews.yaml": "485729ddbbebec93d41295ee1ab0a26ab758918c843e71667f1a38291e6027d8",
  "execution\\session_work.yaml": "a442dd7706bd7e20ac511a4cb786edf9a1e96922c3257f945d33408957684798",
  "execution\\sessions.yaml": "2920037276e0d46d34a1729b6bf66be3dcdd5b97916ceb6030f5619f35f153ad",
  "evidence\\artifact_specs.yaml": "0763e0bcc0880e6f8fe45103ed267b44297ed69abac8506303629b9f67852cbe",
  "evidence\\attempts.yaml": "6432e3b88ad380b79882bb7832be3c9bd0bb0526221cd48752dc21637b28b3f5",
  "evidence\\evidence_records.yaml": "9889acfd0170755a177e2d6f6de24728d15756ef9c30661fc9fdf0e871ba175e",
  "evidence\\validation_gates.yaml": "da7e4b90fe23af9c96cc6bb0abf0cf4ff763da4902d72d961f4c2bbed64d2d43"
}
```

```json
{
  "graph\\state.yaml": "f641403abe1122ed7a37f68e138125a2018e9a599c2953f61d994819ab15bbee",
  "execution\\blockers.yaml": "999622b0eab7b7e2302029e6a0fb04e6bedfadb8d57e94fad5558dc09b385348",
  "execution\\events.yaml": "e38c0b503fcf42ff1609ee1a5702fe8a84a821fc2564091aa227e472413f54e4",
  "execution\\remediation_actions.yaml": "c723ccfc8503f46c39dae126ce44456efcb5246c56b439cab8d4382fb7a13da1",
  "execution\\reviews.yaml": "485729ddbbebec93d41295ee1ab0a26ab758918c843e71667f1a38291e6027d8",
  "execution\\session_work.yaml": "a442dd7706bd7e20ac511a4cb786edf9a1e96922c3257f945d33408957684798",
  "execution\\sessions.yaml": "2920037276e0d46d34a1729b6bf66be3dcdd5b97916ceb6030f5619f35f153ad",
  "evidence\\artifact_specs.yaml": "0763e0bcc0880e6f8fe45103ed267b44297ed69abac8506303629b9f67852cbe",
  "evidence\\attempts.yaml": "6432e3b88ad380b79882bb7832be3c9bd0bb0526221cd48752dc21637b28b3f5",
  "evidence\\evidence_records.yaml": "9889acfd0170755a177e2d6f6de24728d15756ef9c30661fc9fdf0e871ba175e",
  "evidence\\validation_gates.yaml": "da7e4b90fe23af9c96cc6bb0abf0cf4ff763da4902d72d961f4c2bbed64d2d43"
}
```