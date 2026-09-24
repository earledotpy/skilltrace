# R-CurrentBaseline — shipped study-day interface baseline

**Issue:** [#329](https://github.com/earldotpy/skilltrace/issues/329)  
**Map:** [#327 — v3 study-day UI/UX product specification](https://github.com/earldotpy/skilltrace/issues/327)  
**Observed baseline:** `origin/main` at `e53f592` (2026-09-23)  
**Method:** source/spec/test inspection plus direct rendering against this repository's real curriculum/progress/execution fixtures. No prototype or mock data was treated as authority.

## Executive finding

The shipped interface is a disciplined, server-rendered **read-first study dashboard with safe daily writes**, not yet a complete study-day product. Its strongest qualities are the unified Today overview, honest derived facts, consistent domain vocabulary, a single dispatcher-backed mutation seam, explicit pass/master confirmation, and useful empty/error copy. Its central product weakness is that the learner-visible loop is fragmented: Today can start or continue work, but there is no persistent Study cockpit; the open session, chosen SkillNode, SessionWork, timer, evidence obligations, blockers, and safe close are split between Today and a disclosure-heavy SkillNode page; reviews, remediation, attempts, retention confidence, portfolio inspection, and graph exploration are absent or CLI handoffs.

The current release is therefore a strong **safety and information-architecture baseline**, but a weak baseline for the map's “complete learner-visible study loop.” Preserve the engine/read/write boundaries and much of the copy discipline. Reopen the screen model, active-session workflow, narrow-window behavior, and Operations coverage.

## Scope and evidence method

### Primary sources inspected

- Current route and write implementation: [`web/handler.py`](../../src/skilltrace/web/handler.py), [`web/views/`](../../src/skilltrace/web/views/), and [`web/interface/`](../../src/skilltrace/web/interface/).
- Normative product/architecture contracts: [`docs/spec-tier1-serve.md`](../../docs/spec-tier1-serve.md), [`docs/spec-v2.4-interface-sublayer.md`](../../docs/spec-v2.4-interface-sublayer.md), [ADR 0007](../../docs/adr/0007-reintroduce-interface-layer.md), and the shipped [v2.4 release note](../../docs/RELEASE_NOTES.md).
- Executable evidence: [`tests/web/`](../../tests/web/), [`tests/interface_sublayer/`](../../tests/interface_sublayer/), and the byte-pinned route fixtures in [`tests/web/snapshots/`](../../tests/web/snapshots/).
- Real repository fixtures: `graph/`, `evidence/`, `policy/`, and `execution/`. The checked-in progress store has 49 `available` and 51 `locked` nodes, no active/passed/mastered record, and empty session/blocker/review stores; the pinned snapshot fixture supplies active/passed/overdue/blocker states so all lifecycle branches are observable without mutating the research checkout.

A direct render sweep against the real fixture produced:

| Route | HTTP | Approx. body bytes | Forms | `<details>` | Tables | Scripts |
|---|---:|---:|---:|---:|---:|---:|
| `/` | 200 | 4,848 | 2 | 0 | 1 | 0 |
| `/next` | 200 | 14,207 | 2 | 5 | 0 | 0 |
| `/nodes/jump` | 200 | 43,726 | 2 | 0 | 1 | 0 |
| available SkillNode | 200 | 6,012 | 4 | 8 | 3 | 0 |
| `/health` | 200 | 1,899 | 1 | 0 | 0 | 0 |
| `/analytics` velocity | 200 | 5,058 | 3 | 1 | 0 | 1 |
| pass / mastery / final confirm | 200 | 1,853 / 1,683 / 2,082 | 2 / 1 / 2 | 0 | 0 / 1 / 1 | 0 |
| unknown route | 404 | 845 | 1 | 0 | 0 | 0 |

The finder size is notable: its default `/nodes/jump` response renders the complete 100-node browse inventory, not a compact discovery landing state. The navigation jump can also resolve a legacy `node_id` query directly, so the header accelerator and full finder have overlapping jobs.

`python -m pytest tests/interface_sublayer -q` completed **36 passed**. The broader `tests/web` run exceeded the command window; its byte snapshots and assertions were inspected directly, and the direct route sweep above is the runtime check used for this note.


## Route and screen baseline

| Destination | What the learner can do now | Engine fact vs. presentation choice | Assessment / decision posture |
|---|---|---|---|
| **Today `/`** | See one focus, state/reason, start or continue, close an open session, preview a ranked queue, pressure, downstream skills, a seven-day strip, recent sessions, and ready/locked counts. | Focus, ranking, readiness, pressure, and history are engine derivations. Hero + six bento cards, one primary CTA, cream/terracotta visual register, and links-only bento are presentation choices. | **Preserve:** canonical state + reason, one dominant next move, calm pressure, honest zero/empty copy, and Today as a live summary. **Reopen:** seven equal bento blocks create a dashboard rather than a focused study workspace; active-session work is reduced to “Continue where you left.” |
| **Next `/next`** | Set time/option count; compare ranked SkillNodes; open “Why this?”; inspect why locked candidates are not ready. | Ranker output and unsatisfied prerequisites are engine facts. Human field labels, one optional disclosure per option, and always-visible locked half are presentation choices. | **Preserve:** title-first candidates, human controls, advisory-not-blocking disclosure, and structural lock explanation. **Reopen:** the route is mostly a verbose list; it does not become a workspace when time or candidate context changes. |
| **SkillNode `/nodes/{id}`** | Read state/why/resources/evidence progress; start; log SessionWork; create/resolve Blocker; submit/supersede EvidenceRecord; open pass; inspect evidence/resources/reviews/execution/graph/event tables. | State, eligibility inputs, evidence records, resources, edges, reviews, blockers, and events are engine facts. The “This skill / Write actions / Drill-down” grouping, disclosure nesting, and table treatment are presentation choices. | **Preserve:** fact/provenance drill-down, no-op evidence omission, structural pass/master omission, required blocker/evidence fields. **Reopen:** this is the de facto study cockpit but is not organized as one; the action hierarchy is labels and `<details>`, with no persistent session context or timer. |
| **Jump `/nodes/jump`** | Search by words/synonyms/ID; see ranked result cards; browse all nodes by subject. Locked results name a blocking prerequisite. | Read-only discovery and edge facts come from the engine. Default full browse, result-card anatomy, and anchoring are presentation choices. | **Preserve:** title-first discovery, all-match visibility, entry-node recovery, and prerequisite naming. **Reopen:** 43 KB default inventory, no query-state distinction between search and browse, and overlap with the header accelerator. |
| **Health `/health`** | See five read-only study-guidance areas: stuck, due review, evidence gaps, rhythm, and resources; drill to related SkillNodes. | Counts are derived; the five-card order and nonpunitive mirror language are product/presentation choices. Repository diagnostics are deliberately absent. | **Preserve:** study-only Health, no composite score/streak, links to owning detail, limited-data treatment. **Reopen:** several cards are summaries without an in-page next action; the persistent header health pill reports repository warning counts while the destination is study guidance, a semantic seam worth resolving in v3. |
| **Analytics `/analytics`** | Select Velocity/Blockers/Reviews/Evidence, 7/30/90-day and prefix/track views; export MD/HTML/JSON; inspect detail tables. Velocity has focusable SVG-point tooltips. | Metrics and warnings are engine derivations. One theme per page, export buttons, and the single tooltip enhancement are presentation choices. | **Preserve:** real multi-point charts only, no pseudo-sparklines, advisory warnings, static/native-title fallback. **Reopen:** analytics is an event-log report, not the map's promised rich retention/review/evidence/portfolio inspection; details expose Node IDs rather than titles. |
| **Pass / mastery routes** | Review fresh facts and consequences; explicitly confirm pass; for mastery, read facts then confirm permanence. Domain refusal remains possible on click. | Pass/master eligibility is recomputed from engine facts. Panel sequence, labels, and permanence copy are presentation choices. | **Preserve strongly:** fresh recomputation, explicit learner command, pass consequence/cadence disclosure, two-step mastery, permanent-forward wording. **Reopen:** an ineligible pass still exposes an enabled confirm button by deliberate “truth on click” policy; evaluate whether guided mode can retain safety while improving preflight clarity. |

The router's complete top-level set is the nine-entry interface table (`today`, `next`, `node`, `finder`, `health`, `analytics`, and three acceptance steps), and it rejects other top-level additions under the old downward-only gate ([`cards.py:166-217`](../../src/skilltrace/web/interface/cards.py)). The v3 map explicitly supersedes that product posture by asking for a dual-mode product and a Study cockpit; it does not supersede the engine or safety contracts.
## Learner-visible workflow baseline

### Cold start → discovery

1. Today derives a focus and shows `Start studying`; a learner can also enter Next or the finder.
2. SkillNode's start control is a single form with optional session template. It explains that the action marks the SkillNode `active` and never moves backward ([`forms.py:23-57`](../../src/skilltrace/web/views/forms.py)).
3. Discovery never starts work: selection only navigates ([`finder.py:103-156`](../../src/skilltrace/web/views/finder.py)). This is a good Guided-mode boundary.

**Preserve:** explicit start, title-first selection, and navigation-only discovery.  
**Reopen:** a cold learner sees a dashboard and a very large browse inventory, not a guided explanation of the smallest useful first session.

### Active study

- With an open session, Today replaces start with **Continue where you left**, shows the open-since time, and exposes **Close session** ([`today.py:101-166`](../../src/skilltrace/web/views/today.py)).
- The node page separately offers start, SessionWork logging, Blocker create/resolve, and Evidence submit in nested disclosures ([`node.py:85-151`](../../src/skilltrace/web/views/node.py)).
- There is no dedicated route or persistent region that unifies the open session, selected SkillNode, accumulated SessionWork, timer, evidence requirements, Blocker, and safe closure. The v3 Study cockpit is therefore a genuine new product need, not a restyle.

**Reopen:** the active-session state model and workflow priority. The engine facts already exist; the interface should not invent a parallel session model.

### Evidence, pass, and mastery

- Evidence is immutable/supersede-only; the form omits itself when no valid spec/gate combination exists, auto-resolves a single spec, shows manual verdict controls only for manual gates, and places correction behind Advanced ([`forms.py:87-166`](../../src/skilltrace/web/views/forms.py)).
- Pass shows current requirements, the checking authority, whether proof is missing, forward-only consequence, and review cadence before the explicit POST ([`steps.py:37-135`](../../src/skilltrace/web/views/steps.py)).
- Mastery is two steps and the final page recomputes facts; the confirmation states that mastery is permanent and later failure does not demote ([`steps.py:138-271`](../../src/skilltrace/web/views/steps.py)).

**Preserve strongly:** this is the best safety UX in the shipped interface. Do not combine pass/master, auto-assert either state, let AI accept evidence, or hide an unmet hard prerequisite.

### Review, retention, remediation, and portfolio

- Reviews appear as dates/status/outcomes and a terminal handoff; `review schedule/complete/cancel` are not browser writes.
- Remediation rows/handoffs exist, but create/complete are terminal-only.
- Attempt history can appear in drill-down, but `attempt record` is terminal-only.
- There is no web portfolio or retention-confidence view; Analytics has no retention-confidence theme.

This is the largest completeness gap relative to map #327. It should be addressed by reading existing engine facts and dispatcher commands, not by creating browser-side authority or state.

## Mutation and safety baseline

### What is strong

- Every browser mutation nests through the process-wide CLI registry with `Context.source="web"`; handler stdout and `CommandResult.exit_code` are the outcome contract ([`writes.py:36-55`](../../src/skilltrace/web/views/writes.py)).
- Every write is POST → 303 with translated success/refusal/operational copy; pass/master refusals return to their acceptance context ([`writes.py:87-130`](../../src/skilltrace/web/views/writes.py)).
- The complete web POST inventory is start, work, session close, blocker create/resolve, evidence submit, pass, master confirm, and analytics export ([`handler.py:143-185`](../../src/skilltrace/web/handler.py)).
- Advisory policies do not pre-block learner actions; structural absence and judgment eligibility are deliberately distinguished.
- No browser surface invokes delete, AI acceptance, hard-prerequisite override, or progress demotion.

### What needs product attention

- Start remains an enabled submit on a locked SkillNode with advisory text; the handler refuses on click. This preserves action truth but is a Guided-mode friction point.
- An ineligible pass also remains clickable and relies on a translated refusal. This is safe, but the learner must enter a confirmation route to learn ineligibility and then encounter another refusal.
- Operational errors say to see `/health`, but `/health` is now study guidance while repository diagnostics are CLI-only. The error destination and header warning count need a clearer v3 information contract.
- `work` and `session close` have web handlers, but the node-detail Log work form shown in the current code does not include a `node_id` field; `post_work` rejects a missing Node ID. This is a shipped workflow seam to verify in implementation follow-up: either the form's context binding is missing or the intended host is another surface. It must not be “fixed” by inferring a Node ID outside the submitted learner context.


## Copy baseline

### Preserve

- Canonical node state words remain visible; plain-language reasons accompany them.
- Titles, not Node IDs, are the primary nouns throughout Today, Next, Health, and SkillNode.
- Copy explains consequences without CLI command strings: pass permanence, review cadence, evidence immutability, and blocked prerequisites.
- Nonpunitive rhythm language is explicit; Health says “mirror, not a metronome.”
- Refusal and recovery copy points back to useful context.

### Reopen

- The interface is de-CLI in much of the primary path, but drill-down/Analytics still surface raw record IDs, gate commands, and event command names. That is acceptable in an explicit Operations view; it is poor Guided-mode copy.
- “Ask there for the exact form” is a dead end for reviews, remediation, and attempts. Guided mode needs an in-product explanation of what is not yet web-enabled; Operations mode can expose precise mechanics.
- The header says “Needs attention — 38 warnings” from repository validation while the Health destination intentionally contains no repository diagnostics. The warning count and destination currently encode different meanings of Health.
- The interface uses both “This skill” and “SkillNode,” “session” and “SessionWork,” and “proof” and “EvidenceRecord.” Canonical domain meaning must stay exact; Guided copy can use human phrasing while Operations preserves canonical labels.

## Accessibility and narrow-window baseline

### Accessibility strengths

- Semantic `header`, labelled `nav`, `main`, heading, footer, and a skip link are present ([`shell.py:251-281`](../../src/skilltrace/web/views/shell.py)).
- Keyboard focus uses a visible `:focus-visible` ring; reduced-motion preference disables the earned-success animation.
- `aria-current="page"` derives from the interface view seam. Velocity points are keyboard focusable with native `<title>` fallback and Escape-dismissable tooltips.
- Canonical copy avoids relying on colour alone, and server rendering keeps core function available without JavaScript.

### Gaps to reopen

- The only viewport breakpoint changes the Analytics grid to one column. The bento uses `auto-fit/minmax(300px,1fr)`, navigation wraps, and content wraps, but there is no explicit narrow-window composition for the header jump, filter row, evidence/work forms, dense tables, or acceptance facts. `overflow-x:clip` prevents a page-level scrollbar but can hide overflow rather than reflow it.
- Dense tables have sticky headers but no demonstrated horizontal-scroll wrapper, caption, or narrow transformation. Long URLs/IDs and tables are likely review risks on small windows.
- Many form labels are not associated with controls through `for`/`id`; some are visually adjacent only. Radio groups and repeated controls need explicit grouping/accessible names.
- The health strip is a labelled `div`, not a status region; banners are not `role="status"`/`role="alert"`. Redirect notices therefore lack an announced semantic.
- `<details>` is used heavily for the action workflow. Native semantics are helpful, but focus, target size, expanded-state discoverability, and mobile reachability need usability validation.
- SVG analytics charts use a generic `aria-label="sparkline"` rather than a value/summary-specific accessible name; tooltip markup needs screen-reader validation.

The current code tests the single breakpoint literally, so narrow-window improvement will require reopening a previously locked presentation choice ([`test_style_tokens.py:119-129`](../../tests/web/test_style_tokens.py)). This is a presentation change, not an engine or safety change.

## Empty, degraded, failure, and recovery states

| State | Current behavior | Assessment |
|---|---|---|
| No Today focus | “What is today about?” plus sync/Next pointer | Good recovery, no dead end. |
| No candidates | Next says everything in reach is already listed | Clear but sparse. |
| No blocker | Health has explicit “smooth sailing” plus how to log one | Preserve. |
| No reviews | Links to pass a SkillNode so checks can schedule | Helpful, but the destination is terminal-only for manual scheduling. |
| No session history | Explains the readable line format that will appear | Good empty-state preview. |
| No search results | Entry-node links plus Browse by subject | Good recovery. |
| Limited evidence | Analytics/Health prefix facts with session count and suppress misleading certainty | Preserve. |
| Lenient join degradation | Banner names failed supporting layers, says remaining actions work, and points to Health | Helpful intent, but the destination mismatch above weakens recovery. |
| Invalid query | 400 unified error body for bad Next/Analytics inputs | Good server correctness; copy is generic. |
| Unknown node/route | 404 unified full-chrome body with Back to Today | Preserve. |
| Write refusal | 303 back to context with warning copy | Good truthful model; Guided copy/preflight can improve. |
| Write operational failure | 303 with error copy pointing to `/health` | Needs a precise destination contract under the study-only Health decision. |


## Preserve vs. reopen

### Preserve as decisions or invariants

1. **Single dispatcher-backed write path** and one audit event per mutating command.
2. **Explicit learner pass/master**, with fresh facts, consequences, and strong mastery permanence language.
3. **Engine-derived state/eligibility/history**, including honest lock reasons and advisory-never-blocks behavior.
4. **Immutable evidence / correction by supersede**, and no client-side acceptance authority.
5. **Canonical state words with plain-language explanation** and title-first primary nouns.
6. **Nonpunitive Health/Next/Today language**, limited-data honesty, and useful empty/recovery copy.
7. **Server-rendered, dependency-light core**, native HTML function, keyboard focus, skip link, reduced motion, and real-data-only charts.
8. **No parallel domain/state model in the web sublayer.**

### Reopen as v3 product/architecture decisions

1. **Dual-mode information architecture:** task-led Guided mode versus dense Operations mode, with clear transitions and shared engine facts.
2. **Study cockpit:** persistent active-session context, chosen SkillNode, timer, SessionWork, Blocker, evidence obligations, and safe close.
3. **Complete Guided loop:** decide which review, remediation, attempt, retention, graph, and portfolio actions belong in-product versus explicitly CLI-only; remove “ask there” dead ends.
4. **Screen composition:** current route list is an adequate backend seam, not the target Guided/Operations navigation. The old downward-only route gate should not silently constrain the new product map.
5. **Narrow-window and accessibility contract:** forms, dense facts/tables, header, dialogs/panels, announcements, labels, charts, focus, and target sizes.
6. **Health semantics:** align ambient repository attention, learner study guidance, and operational error destinations.
7. **Operations terminology:** retain precise canonical facts and raw IDs only where their diagnostic value is intentional and labelled.
8. **Copy system:** keep one semantic translation/command source, but define separate Guided and Operations registers rather than forcing one register across both modes.
9. **Client interaction budget:** reopen JavaScript architecture only for validated interactions that server-rendered HTML cannot deliver well; do not adopt a framework or parallel state store by default.

## Implication for map #327

The next product decisions should start from the gaps above, not from a blank sheet. The v3 specification can preserve the current safety spine and factual derivations while defining two coherent modes. Its first load-bearing design task is the Guided-mode Study cockpit and its state/priority model; its first load-bearing validation task is a narrow-window, keyboard/screen-reader, empty/refusal/recovery walkthrough using the repository's real and pinned lifecycle fixtures.

No engine semantics, release criterion, route-safety rule, or hard boundary needs to change merely to deliver that product. Any architecture change beyond the current ADR 0007 sublayer and ADR 0008 narrow script posture should be justified by those validated interaction needs.


