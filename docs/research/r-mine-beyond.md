# R-MineBeyond — evidence brief on each deferred Beyond candidate

Research ticket [#277](https://github.com/earledotpy/skilltrace/issues/277),
part of wayfinder map [#275](https://github.com/earledotpy/skilltrace/issues/275).

Scope: the six **deferred** items in the "Beyond this roadmap" list of
[`docs/POST_V2_ROADMAP.md`](../POST_V2_ROADMAP.md). Hard-boundary
restatements (auto-master/auto-pass, LLM-graded evidence) and boundary-gated
items (cloud sync, Elo/BKT, generative tutoring) are out of scope here — they
belong to G-BoundaryGated, not this ticket.

Method per item: (a) restate what the roadmap's named re-open trigger demands,
(b) check whether lived v2.x experience has tripped it against the repo's own
records — `execution/events.yaml`, `graph/state.yaml`,
`execution/{reviews,sessions,session_work,blockers}.yaml`, `evidence/*.yaml`,
`graph/resources.yaml`, and the v1.6–v2.4 specs — read-only, (c) a preliminary
graduate / defer / reject read with warrant.

**Repo evidence snapshot (as of this research, on the working tree):**

- `execution/events.yaml` — 36 events total: 30 `verify-resource` (all
  `broken: false`), 4 `sync`, 1 `start`, 1 `session close`. No `pass_node`,
  `master_node`, review, or evidence events ever.
- `graph/state.yaml` — zero `passed`, zero `mastered` nodes; exactly one
  `active` node (`agents.concepts.agent_fundamentals_01`, started
  2026-09-16 from web); the rest `locked`/`available`.
- `execution/reviews.yaml` — empty. `execution/blockers.yaml` — empty.
  `evidence/attempts.yaml`, `evidence/evidence_records.yaml` — empty.
- `execution/sessions.yaml` — one completed session ever
  (`ses.2026-09-16.01`, ~3.5 h). Days practiced = 1.
- `graph/resources.yaml` — 56 `last_verified` values: 29 from the 2026-07-10
  bulk sweep, 4 dated 2026-09-05, 12 dated 2026-09-06, 11 unverified-by-design
  (source-prose notes, e.g. `hf-agents-course`: "human last_verified pending").
  Zero `broken: true` ever.

---

## 1. Diagnostic analytics (learner-facing)

**Trigger.** Roadmap: "why am I stuck / why recommended" primitives, distinct
from v1.6's operational event-log analytics and v2.2's pre-release
graph-impact diagnostic; "re-opens if diagnostic-as-a-primitive is wanted."

**Lived experience.** The question the primitive answers has not arisen.
`blockers.yaml` is empty (nothing to answer "why am I stuck" about), there is
exactly one `active` node and no recommendation churn to explain (4 `sync`

## 2. Practice profiles + prompt extraction

**Trigger.** Roadmap: protocols as opaque advisory session-template values,
prompt extraction as disposable derived output, strictly advisory (never
gate/evidence/pass-master authority) per R-Practice
([#195](https://github.com/earledotpy/skilltrace/issues/195)); "re-opens
post-v2.1, once the retention overlay has produced enough data to sequence
practice."

**Lived experience.** The precondition is explicitly data-shaped, and the data
does not exist. `execution/reviews.yaml` is empty: the v2.1 FSRS retention
overlay has never scheduled a single review, so it has produced *zero*
retention data to sequence practice against. One session, one active node, no
attempts. The overlay is installed but starving; there is nothing for practice
profiles to read.

**Read: defer.** The named trigger ("enough data") is objectively not met —
it is not met by any amount. Re-opening now would build a sequencing layer on
an empty model. Revisit only after reviews actually accumulate (the natural
checkpoint is the first time `suggest reviews` retention section has real
entries under pressure).

## 3. Badge issuance

**Trigger.** Roadmap: "no badge primitive in the engine; re-opens if a
portfolio consumer demands one."

**Lived experience.** The portfolio shipped in v2.0 (bundle, preview, JSON
contract, manifest, per-node pages — spec-v2.0-portfolio-builder). No badge
primitive exists, and no consumer has demanded one: there are zero
`passed`/`mastered` nodes, so the portfolio currently has nothing to decorate,
and no external consumer of `portfolio.json` is evidenced anywhere in the
specs or event log.

**Read: defer** (leaning reject while the demand signal stays absent). This is
a pure consumer-demand trigger and the demand is nil. Warrant for the lean:
badges are cosmetic over achievement; with zero achievements they are
unbuildable in any meaningful sense, and adding the primitive before a
consumer exists risks designing the wrong shape.

## 4. Full gate-runner / scheduler-queue

**Trigger.** Roadmap: v2.2 ships only the bounded receipt + read-only
diagnostic (R-Provenance [#194](https://github.com/earledotpy/skilltrace/issues/194));
"re-opens when a concrete Phase 4/5 seed artifact needs automated gate runs —
the receipts are the precondition."

**Lived experience.** Both halves of the trigger are unmet. No Phase 4/5 (or
capstone) seed artifact exists — the seed graphs stop at v1.9's Phase 3
content, and Phase 4/5 seed graphs are themselves a separate Beyond item. And
the precondition is unused: `evidence/evidence_records.yaml` is empty, so zero
gate-run receipts have ever been written by real use (v2.2's receipts are
shipped and tested, but no objective-gate evidence record exists to carry
one). A runner with no receipts and no artifacts to run would automate
nothing.

**Read: defer.** Sequencing is working as designed: receipts (v2.2) precede
the runner (Beyond), and the runner's trigger is downstream of the Phase 4/5
seed-graph item, which is itself downstream of "adaptable ideas" demand. The
correct next move on this chain, if any, is seed content — not the runner.

## 5. Verification-sweep scheduling automation

**Trigger.** Roadmap: sweeps stay manual in v1.7/v2.3; "re-opens when
unattended sweeps are actually wanted: demonstrated manual-sweep cadence, a
downstream slot needing scheduled checks, or serve/today background-sweep
work. Doctrine rider: whatever schedules only ever flags (`broken`), never
asserts `last_verified`."

**Lived experience.** None of the three disjuncts is met. (i) There is no
*demonstrated cadence* to scale up: the sweep history is two bursts — the
2026-07-10 bulk sweep (29 resources) and incremental verifies on 2026-09-05/06
(16 events) — roughly quarterly, not a rhythm demanding automation. (ii) No
downstream slot needs scheduled checks (v2.3 explicitly re-deferred
scheduling; v2.4's interface sublayer is presentation-only). (iii) No
serve/today background-sweep work has been proposed since v2.4 shipped. Also
telling: across all 30 `verify-resource` events, `broken` has never been
`true` — the hygiene problem automation would solve has not once occurred in
lived use, and the v2.3 polite sweep already made the manual run cheap and
polite.

**Read: defer.** The trigger is a disjunction and every branch is false. The
manual+v2.3-polite posture is demonstrably sufficient; automating a
twice-quarterly, never-failing chore adds a scheduler surface (with the
doctrine rider to enforce) for zero observed pain.

## 6. Resource deep-verification (cert metadata, content-hash drift)

**Trigger.** Roadmap: only cert-*metadata* inspection and hash-drift
detection are new (implicit TLS validation already exists in `check_url`);
"re-opens on evidence of content drift harming study (an incident a
content-hash check would have caught) or a host/publisher requiring
pinned-content verification."

**Lived experience.** Both named triggers are incident-shaped and no incident
has occurred. All 56 verified resources are `broken: false` across the whole
verification history; no drift event, no study-harm event, and no
pinned-content publisher requirement appears in `resources.yaml` or any spec.
The nearest adjacent fact is that cert metadata already exists as
*license prose* (e.g. `kaggle-learn`, `hf-agents-course` entries carry
certificate/licensing notes), i.e. the information a cert-metadata inspector
would formalize is already human-readable where it is needed — inspection
would be a convenience, not a gap. And the only live verification concern in
the registry is the opposite one: 11 resources are deliberately
`last_verified`-pending by design pending re-pinning.

**Read: defer.** No incident, no pinning requirement. Note for the future
re-open: if it ever trips, the cert-metadata half is the cheaper first slice
(structured fields over existing license prose), while content-hash drift
needs a stored hash baseline the registry does not currently carry — a
schema-adjacent change, not a slot.

---

## Summary

| Beyond item | Trigger type | Tripped by lived v2.x? | Read |
|---|---|---|---|
| Diagnostic analytics (learner-facing) | demand ("primitive is wanted") | No — no blockers, one active node, one session | Defer |
| Practice profiles + prompt extraction | data (retention overlay has "enough data") | No — reviews empty, zero FSRS data | Defer |
| Badge issuance | demand (portfolio consumer) | No — portfolio shipped, no consumer, zero passed/mastered | Defer |
| Gate-runner / scheduler-queue | dependency (Phase 4/5 artifact + receipts used) | No — no Phase 4/5 content, zero evidence records/receipts | Defer |
| Sweep scheduling automation | disjunction (cadence / downstream slot / background work) | No — two sparse bursts, zero `broken` ever | Defer |
| Resource deep-verification | incident (drift harm / pinned content) | No — no incidents; cert info already prose | Defer |

**Overall read:** every deferred Beyond item has a demand-, data-, dependency-,
or incident-shaped trigger, and lived v2.x experience has tripped none of
them. The dominant pattern is that the repo is early in its *learning* life
(one session, one active node, zero evidence records, zero reviews): the
Beyond items are mostly consumers of progress this repo has not yet produced.
Recommendation: keep all six deferred; the earliest natural re-check points
are the first real review backlog (items 2, 1) and the first real evidence
record (item 4).


events total, two touching no records). The v1.6 event-log analytics already
serve the operational view, and v2.2 shipped the *pre-release* diagnostic
lane. "Wanted" is a learner-demand claim, and the one active learner has never
asked it: zero `passed`/`mastered`, one session.

**Read: defer.** The trigger is demand-shaped and there is no demand signal.
No harm observed in waiting — when the graph is actually being worked (several
active nodes, blockers, failed attempts), the "why" question becomes real, and
the v2.2 `graph impact` advisory plus v1.6 analytics will likely have produced
the vocabulary a learner-facing primitive would reuse.
