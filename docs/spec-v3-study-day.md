# Spec — SkillTrace v3 Study-Day Product (UI/UX Specification and Implementation Handoff)

**Status:** locked hand-off (map #327, ticket #342) — no open product or architecture decision blocks the implementation wayfinder.
**Scope:** the complete learner-visible Guided and Operations experience of the v3 study-day product. This document assigns no release version, no dates, and no sized tasks; it performs no implementation.
**Authority:** this spec is the single product contract. It normatively restates every closed decision of wayfinder map #327; the closed tickets become history that this document supersedes. Terms are used exactly as defined in `CONTEXT.md`; no new domain term is introduced here.

**Source decisions (history, superseded by this restatement):** G-InformationArchitecture #330 · G-DomainContract #331 · G-CoreWorkflows #332 · G-OperationsSurfaces #333 · G-VisualSystem #334 · G-InteractionModel #335 · G-AccessibilityContract #336 · P-CoreJourney #337 · P-OperationsWorkspace #338 · G-ValidationContract #339 · G-UsabilityVerdict #340 · G-ArchitectureConsequences #341 · G-PreferenceReopen #346 · G-SingleLearnerValidation #347 · T-ValidationExecution #344 · G-FinalValidationVerdict #345.

---

## 1. Destination and scope

SkillTrace's v3 study-day product is a dual-mode web experience over the existing engine: **Guided** mode optimizes ordinary study; **Operations** mode exposes rich graph, evidence, retention/review, analytics, and portfolio inspection. Both modes render the same engine facts and use identical dispatcher commands. The primary success condition is making the complete study loop easier; dedicated-product polish is the quality bar, and Operations mode supplies engine visibility.

The supplied prototype is a major design reference, not an implementation or domain authority: its dark density and capability set survive as product capabilities with canonical semantics; its React/Vite code, mock data, client-side mutations, fake telemetry, and combined pass/master action are rejected (see §20 and §3).

In scope: every learner-visible screen and state across cold start, discovery, Today, Study cockpit, SkillNode detail, Blockers, evidence, Session close, pass/master, Reviews, retention, graph exploration, Health, analytics, and portfolio, with workflow priorities (§10–§11), the standards that bind them (§5–§9), what validation observed (§12–§13), the migration posture (§14), the architecture consequences (§15), the acceptance criteria (§17), and the ordered implementation slices with dependencies (§18).

Out of scope (returns only through a separately opened effort): release slicing, task sequencing, version assignment; implementing or shipping the UI; migrating production routes; choosing the implementation stack; embedded IDE, scheduler, or PKM integration; a permanently supported second web UI; reopening curriculum direction, engine semantics, FSRS/retention math, or release criteria (except where a UI decision exposes a genuine contradiction — none was found); the shipped SkillNode Log work form defect #343; the deferred accessibility re-validation effort (§12.4).

## 2. Persona and modes

**PM-1.** There is one persona: the **Learner** — the single person whose curriculum and progress the repository holds (per `CONTEXT.md`). SkillTrace remains single-learner by design.

**PM-2.** The Learner appears in two modes, which are navigation/presentation context, never domain state:
- **Guided** — ordinary study: today's priorities, the Session, work, evidence, pass/master, Reviews. Learner-first language; canonical distinctions preserved; no CLI vocabulary required to understand or recover from any outcome.
- **Operations** — the same Learner doing deep engine inspection: graph, evidence history, Reviews, Health (study guidance and repository diagnostics), analytics, portfolio. Canonical IDs, record types, gate details, commands, source files, and event provenance appear here as labelled technical detail.

**PM-3.** AI review is advisory commentary only. It is never a persona with authority, never an acceptance authority, and its annotations (Advisory) are never presented as evidence, eligibility, or progress.

**PM-4.** The CLI remains fully available and secondary. The web exposes only the canonical commands needed to complete the specified journeys (§4, §19); a command's presence in the registry is not product justification.

## 3. Hard boundaries (HB)

The product contract inherits every engine hard boundary unchanged; these are acceptance criteria of severity above usability.

- **HB-1.** Nothing in the web automates or implies `pass_node`, `master_node`, or `delete_record`. Passing and mastering are explicit learner commands only; no route, panel, timer, navigation, mode switch, evidence submission, or Blocker resolution performs or implies them.
- **HB-2.** AI review never carries acceptance authority. Advisory annotations never count as evidence and never change eligibility.
- **HB-3.** Asserted progress (`active`/`passed`/`mastered`) never moves backward. No UI action, refresh, or sync demotes it. A later unsatisfactory Review creates failure-side pressure, never demotion.
- **HB-4.** No hard-prerequisite override exists anywhere in the product. A locked SkillNode cannot be started or passed regardless of evidence.
- **HB-5.** Evidence records are immutable. Corrections supersede; no edit or delete affordance exists on any surface. Acceptance freezes at submission.
- **HB-6.** Every mutation is an explicit POST through the live dispatcher with the command's authoritative outcome and exactly one audit event. A page load, prefetch, hover, or client-side state transition is never a learner command and writes nothing.
- **HB-7.** Files remain the sole source of truth; the web interface reads the engine and is never a second domain model, second state store, or source of truth. Eligibility is derived on demand, never stored as truth.
- **HB-8.** `graph/edges.yaml` is the sole relationship truth. No UI element may invent, hardcode, or imply a relationship, and remediation edges never unlock anything.

## 4. Domain mapping (surface → canonical facts and commands)

Default-deny: no learner-visible fact, state, label, control, or action exists unless it binds to a canonical term and names its truth or derivation, read view, and — when mutating — dispatcher command. The table of §3.1 of G-DomainContract is restated here normatively.

| Surface | Canonical facts and owner (truth / derivation) | Actions and constraints |
|---|---|---|
| Today, Next, discovery | `SkillNode`, node state, `Recommendation`, `NextAction`, `GraphEdge`, derived readiness, `Session`, `Days practiced` — derived read-time | Read/navigation only. Focus, queue, pressure, search results, resume destinations are projections, never records or commands. Guidance recommends; it never grants permission. |
| Study cockpit | `Session` (open/completed; stale is derived), `SessionWork`, selected `SkillNode`, `Blocker`, `ArtifactSpec`, pass-eligible facts | `start`, `work`, `session close`, `blocker create`, `blocker resolve`, `evidence submit`. Resume, Inspect, Focus are links. A second `start` while a Session is open is refused by the engine. |
| SkillNode detail | one Progress record; node metadata; `GraphEdge`; `LearningResource`; `ArtifactSpec`; `ValidationGate`; `EvidenceRecord`; `AssessmentAttempt`; `Blocker`; `RemediationAction`; `Review`; recent event facts | One canonical destination, composed differently by mode. Records are never collapsed into a generic progress, skill-health, or evidence-state object. |
| Readiness and relationships | derived `locked`/`available`; asserted progress forward-only | Read explanations and links only. No override, client setter, or graph-derived unlock. |
| SessionWork and Blockers | blocked flag on `SessionWork` is a session-scoped observation; `Blocker` is an explicit persistent-stuckness record | Copy must distinguish **blocked work** from a **Blocker**. Blocked work never creates a Blocker; resolving a Blocker passes nothing and changes no node state. |
| Evidence | `ArtifactSpec`, node `ValidationGate`, immutable `EvidenceRecord`, accepted/rejected outcome, derived superseded standing, derived pass eligibility | `evidence submit` (and correction as a new superseding submit with required reason). Optional specs never count toward eligibility. AssessmentAttempts and Advisory are not evidence. |
| Assessment and remediation | immutable `AssessmentAttempt`; execution-only `RemediationAction` | Contextual exposure only where a journey needs it. Attempts never grant eligibility; RemediationActions never change state, resolve Blockers, or activate edges. |
| Passing and mastering | derived eligibility + the learner's explicit asserted act | Separate confirmation journeys under `pass` and `master`. No combined action, optimistic mutation, automatic transition, AI authority, or override. Mastery is explicit and permanent. |
| Reviews and retention | `Review` (scheduled/completed/cancelled; overdue derived), `Memory state`, `Retention confidence`, Retention suggestion | `review schedule`, `review complete`, `review cancel` as ordinary dispatcher actions. A **suggested check** is not due or scheduled; only the learner command creates a Review. Retention is derived context — never node state, never a certainty percentage. |
| Learning resources | `LearningResource`, `Verified`, `Web check`, `Broken marker` | Read status and links only. Resource verification/replacement is not a target surface. Resource status never affects readiness, eligibility, or progress. |
| Graph | `SkillNode`, `GraphEdge`, node state, derived readiness/recommendation | Visual graph and accessible list are alternate presentations of the same facts. No client domain state. |
| Health | two explicit projections: **study guidance** (learner execution/evidence/retention facts) and **repository diagnostics** (curriculum/resource integrity) | No composite Health score, no shared warning total, no cross-source severity. Diagnostics warn; they never become acceptance authority. |
| Analytics | `Study velocity`, `Blockers by domain`, `Review completion`, `Evidence coverage`, `Rolling window`, `Soft data threshold` | Real derived facts only, limited-data warnings, accessible alternatives. Analytics may warn/reorder, never block, record, or transition domain state. |
| Portfolio | Portfolio export, Share profile (default-deny per-export contract), Redaction override, Portfolio bundle, Honesty banner | Preview and export as Operations capabilities. Never a user profile or account; output is a dated disposable snapshot, never live truth. |
| Event log | append-only event facts and terminal/serve provenance | Recent audit entries shown as record detail in the contextual inspector only. No standalone Event-log surface, no audit-log route; events never reconstruct state. |
| Settings | no canonical Settings domain object | **No generic Settings destination.** Analytics window controls live under Analytics; portfolio privacy under Portfolio; policy/resource configuration only where an explicit canonical command exists. |

**Terminology contract (binding on all copy):** use **retention status** learner-facing, **Memory state** for canonical Operations detail; distinguish **suggested check / scheduled review / overdue review**; distinguish **blocked work / Blocker**; distinguish **study guidance / repository diagnostics**; never invent generic Progress, Practice, Retention-health, Settings, Share-profile, Export, or Event-log-state objects; reserve raw IDs, canonical record names, gates, commands, and provenance for Operations or clearly labelled detail (§8, R1).

## 5. Information architecture and navigation

- **IA-1.** One URL-addressable shell carries both modes. Mode and inspector context ride URL parameters (e.g. `?mode=guided|operations`, context params per §6); the server is stateless and no view state is stored.
- **IA-2.** **Guided** is task-led with predictable homes: Today (`/`) is the home; Next supports selection; Find a skill (`/find`) is a dedicated discovery route; an open Session is surfaced as the prominent resume destination; Health is contextual/ambient in Guided, never a competing top-level task.
- **IA-3.** **Operations** home (`/operations`) is a capability directory under persistent section navigation. The canonical capability destinations — Graph, Evidence, Reviews, Health, Analytics, Portfolio — are never collapsed into a generic "More" destination. On narrow windows the section navigation becomes a labeled disclosure/menu retaining ordinary links, visible current-section state, and coherent focus order.
- **IA-4.** Mode switching is explicit and reversible. A switch preserves a meaningful SkillNode, Session, or Evidence context when the target surface supports the contextual inspector; otherwise it returns to the predictable mode home (Guided → Today; Operations → `/operations`). The underlying destination remains canonical and deep-linkable; mode never changes what a destination is.
- **IA-5. History rule (as amended by G-ArchitectureConsequences).** Mode changes and meaningful destination changes create normal back/forward history entries. At tier 0 a URL-changing transient control — a GET filter, a search submit — *is* a navigation and does create a history entry; non-navigating controls (disclosures, menus, panels) create none. `history.replaceState` is refused (ADR 0008); no client scripting is granted to suppress entries.
- **IA-6.** Generic Settings does not exist (§4). The **contextual inspector** is not a destination: it opens inside a route that names it (§6 note 2) with the selected fact's canonical record, related SkillNode, and relevant event provenance.

## 6. Route table (RT) — normative

This table replaces `docs/spec-tier1-serve.md` §C as the normative route contract (per ADR 0007 Amendment 2026-09-25: new top-level views are permitted **only** where this table names them). Paths are **flat and mode-neutral**: a destination exists once; mode is presentation context via URL parameter, never a path prefix. View identity remains the screen name, never the path; `FROZEN_ROUTES`, the SA6 frozen-table test, the sublayer scaffold, and the golden snapshots are repointed to this table in the implementation change that adopts it, each keeping its exact assertion (the ADR 0009 discipline).

| ID | View | Route | Contract |
|---|---|---|---|
| RT-01 | `today` | `/` | §10.1 |
| RT-02 | `next` | `/next` | §10.2 |
| RT-03 | `find` | `/find` | §10.3 (repathed from `/nodes/jump`) |
| RT-04 | `node` | `/nodes/{id}` | §10.4 |
| RT-05 | `session` (Study cockpit) | `/session` | §10.5 (one open Session by engine invariant) |
| RT-06 | `session-close` | `/session/close` | §10.6 (GET panel; POST rides same path) |
| RT-07 | `node-pass` | `/nodes/{id}/pass` | §10.7 (full-page safety panel; POST rides same path) |
| RT-08 | `node-master` | `/nodes/{id}/master` | §10.8 step 1 (eligibility explanation) |
| RT-09 | `master-confirm` | `/nodes/{id}/master/confirm` | §10.8 step 2 (permanent confirmation) |
| RT-10 | `evidence` (node requirements workspace) | `/nodes/{id}/evidence` | §10.9 (+ `submit` action routes per §10.9) |
| RT-11 | `evidence-index` (repository history) | `/evidence` | §11.2 |
| RT-12 | `reviews` | `/reviews` | §10.10 / §11.3 (+ `schedule`, `complete`, `cancel` action routes) |
| RT-13 | `operations` (capability directory home) | `/operations` | §11.1 |
| RT-14 | `graph` | `/graph`, node-centered `/graph/{id}` | §11.4 |
| RT-15 | `health` | `/health` | §11.5 (path retained; reclassified as Operations capability) |
| RT-16 | `analytics` | `/analytics` | §11.6 (rolling window and theme ride URL params) |
| RT-17 | `portfolio` | `/portfolio` (+ `/portfolio/preview`, non-writing) | §11.7 |

Notes:
1. Every full-page safety panel is a route (tier 0 — no overlay modals as the norm); write POSTs ride the panel's path. Action routes named in a screen contract (e.g. work log, blocker create/resolve, evidence correction) ride as POSTs from their owning view or its panel route; this table lists the destinations, §10–§11 bind the behaviors.
2. The contextual inspector renders inside RT-11, RT-12, RT-14, RT-15, RT-16 and node detail where a selected fact names it; it has no route of its own. Selected contexts are URL-addressable within their owning route; transient filters, panels, and map layout never become domain state.
3. **Closed destinations (never, in v3):** `/today` alias (one view, one URL; `today` stays on `/`); a standalone audit-log route (event provenance is record detail in the inspector); generic Settings; `/blockers` as a top-level destination (Blockers surface in Today's queue, the Study cockpit, node detail, and the inspector); any delete/edit affordance route.
4. **Omnibar** (specified, **carried unvalidated** — C27): a navigation accelerator inside the shell (no route of its own). It resolves to existing destinations only. It never launches commands, asserts progress, searches domain truth beyond navigation targets, or becomes a second acceptance path. Implementation priority: last (see SL7 note, §18).
5. Filters and search are GET parameters on their owning route, URL-addressable and history-bearing per IA-5, with labeled controls and no-results recovery.

## 7. Interaction contracts (IC)

- **IC-1.** Guided uses server-rendered links and forms as its baseline. Any richer client behavior requires separate justification by measurable task benefit and must preserve the no-JavaScript path. The existing read-only analytics chart tooltip is the only tier-1 grant and is unchanged (ADR 0008).
- **IC-2.** Pass, mastery, refusal, and stale-state flows use full-page safety panels, not overlay modals. Commands remain explicit learner actions and validate against fresh server state. (The glossary term is **Confirmation panel**, not modal.)
- **IC-3.** Study timing is explicit and recorded: elapsed/recorded time is captured through explicit start, stop, and close commands. No live timer, polling, countdown, or auto-refresh is in the initial product budget. A presentation-only timer is never a SessionWork field, eligibility fact, or authority; page load, navigation, inspection, or timer expiry never records work. *(R6)*
- **IC-4.** Search and filters are server-side GET interactions with URL-addressable results, labeled controls, no-results recovery, and no live client dependency.
- **IC-5.** After any successful command, refusal, validation error, or stale confirmation, the server returns a **fresh full page**. Focus lands on the result heading or the refusal/recovery panel; non-sensitive form values are preserved where safe; an explicit next action is provided.
- **IC-6.** No global custom keyboard shortcuts are added. Native links, buttons, forms, and disclosure controls retain standard keyboard behavior.
- **IC-7.** Server validation is unchanged: every POST re-dispatches against freshly loaded truth; exit `0/2/1` maps to `303` + flash; a write route never returns 4xx; a refusal is answered with a fresh full-page panel. Review schedule/complete/cancel join this path as ordinary dispatcher commands — no new write mechanism.
- **IC-8. Refusal and recovery contract (applies to every mutation).** State what happened in learner-first language; preserve canonical terms where precision matters; refresh derived facts from current truth; identify the next valid command or discovery path; never require CLI vocabulary; never convert refusal or failure into fake completion, hidden mutation, or automatic recovery. Refusals and failures write no records. *(R5: recovery must be completable without a hint ladder — the panel itself names the next safe action.)*
- **IC-9. Stale confirmation refuses noticeably.** A stale pass or mastery panel is not actionable until fresh truth is shown; when a stale confirmation refuses, the refusal is noticeable **at the moment it fires** — the fresh page states the refusal, what changed, and the next safe route; it writes nothing. *(R4)*
- **IC-10.** Blocked SessionWork is labelled blocked work, never a Blocker; **Create Blocker** is offered after persistent blocked work and is never a side effect. *(G-CoreWorkflows §4)*

## 8. Visual system (VS)

- **VS-1. Character.** A dark-first, learner-first technical system: a calm study workspace (Guided) with precise technical information (Operations). It must not look or behave like an IDE, control room, operations cockpit, game, or developer-tool clone. One clear focal hierarchy; density is available precision, not spectacle; operational detail supports learner goals.
- **VS-2. Tokens.** Defined by semantic roles, never component-specific hard-codes: canvas (base, raised, subtle, selected); text (primary, secondary, muted — muted never below the accessibility floor); borders (subtle, default, strong — border-first, quiet solid surfaces); one cyan/blue action/focus accent shared across modes that encodes no rank, eligibility, mastery, health, or severity; five semantic status tokens (information, success, warning, failure, focus), each used only with a non-color cue where meaning matters; scales for spacing, type, radius, motion, elevation. Dark is default; the accessible light companion preserves identical semantic meaning.
- **VS-3. Colour semantics.** Green = explicit success; amber = advisory attention; red = failure or unsafe outcome; purple reserved for mastery/retention context, never celebration. Colour never implies eligibility, rank, authority, or progress. Every meaningful state carries text and, where useful, a consistent icon. Disabled is not refusal; advisory pressure is not failure; a suggested check is not a scheduled Review; blocked work is not a Blocker; Retention confidence is not mastery; a queued or optimistic client state is not success.
- **VS-4. Typography.** System sans-serif for titles, instructions, statuses, reading content; system monospace for Node IDs, EvidenceRecord IDs, paths, commands, timestamps, and compact technical data — never woven into sentences *(R1: everywhere learner-visible, a readable SkillNode title stands in for raw ids; raw ids survive only as labelled technical data in Operations, record detail, and the inspector)*. 14px desktop base target; readable and operable at 200% zoom; density may reduce whitespace, never required text size or line height.
- **VS-5. Space and components.** 4px base rhythm, primarily 8/12/16/24px gaps; dense fact lists may use 8px; primary tasks and dialogs larger. Prose measure ≤70ch. Restrained 4–8px radii; shadows only for transient overlays. Glass, neon glow, floating cards, decorative terminal framing, and routine elevation shadows are prohibited. **Cards are not the default layout primitive** — sections, rows, tables, disclosures, and inspector regions carry structure. Normative component vocabulary: surface/section containers; primary and secondary command bars; queue items; fact rows and relationship rows; requirement and evidence rows; status labels; contextual inspector; progressive disclosure; table and chart-with-table pairings; dialogs; banners; purpose-built empty, limited, refusal, operational-failure, and recovery states. Every interactive component defines rest, hover, keyboard focus, active/pressed, selected, disabled-with-nearby-reason, loading, refusal, and failure states. Hover is never the only source of information.
- **VS-6. Mode treatment.** One visual language and token set. Guided: more whitespace, stronger reading hierarchy, one visually dominant action, secondary queues. Operations: denser facts, persistent section navigation, wider tables, contextual inspector. Neither mode invents colors, meanings, terms, or success styling; a Guided action and its Operations counterpart expose the same canonical fact and dispatcher outcome.
- **VS-7. Data visualization.** Tables are authoritative. Simple lines/bars/labelled distributions may supplement when they materially clarify a canonical metric; every chart requires an accessible equivalent, meaningful name, visible values or a route to exact values, and text distinguishing available from limited data. Gauges, composite scores, decorative heatmaps, fake trends, target-attainment badges, and telemetry charts are prohibited.
- **VS-8. Icons.** Restrained line vocabulary; icons supplement labels, never replace them; same meaning across modes; status icons pair with text; decorative icons hidden from assistive technology.
- **VS-9. Motion.** Brief state-transition feedback only, nominally 120–180ms (the legacy celebration keyframe survives only as such feedback at a real event). No ambient dashboard motion, looping telemetry, parallax, or attention-seeking animation; reduced-motion preferences remove all nonessential animation; motion never communicates a domain state, mutation result, or authority by itself.
- **VS-10. Anti-patterns (exact list, binding).** The system must never imply: pass eligibility from colour/count/percentage/queue position; mastery from Retention confidence, review streak, or a mastered-looking card; a Blocker from blocked SessionWork; a scheduled/overdue Review from a Retention suggestion; repository health from study guidance or one composite Health score; success/asserted progress from an optimistic client transition; objective-gate success from simulated console output; hard-prerequisite override or automatic availability from a remediation edge; evidence correction from an edit/delete affordance; SessionWork or Session closure from timer expiry, page load, navigation, or mode switch; a rank/"behind"/"ahead" judgment from Days practiced; health/risk/certainty/authority from a gauge, sparkline, or decorative telemetry; CLI dependence as a learner requirement when the web provides the same canonical command and outcome; a separate Guided/Operations domain model through visual differences.

## 9. Accessibility contract (AX)

WCAG 2.2 AA is the normative accessibility and responsive baseline for every learner-visible screen and state, Guided and Operations alike. This bar is carried as full specification content; its **verification is partially deferred** (§12.4) — deferral moves verification, never the standard.

- **AX-1.** All text, controls, focus indicators, boundaries, and meaningful status graphics meet AA contrast (4.5:1 normal, 3:1 large text and meaningful UI boundaries); status is never colour-only; visible keyboard focus required.
- **AX-2.** Every action is available through a visible, keyboard-focusable control with logical tab order; skip links and native keyboard behavior required. At tier 0 there are no overlay dialogs as the norm, so no keyboard trap exists; any future modal surface is the only permitted trap and must provide Escape and an accessible close control.
- **AX-3.** Native HTML structure and semantics; ARIA only where native semantics cannot express the required relationship.
- **AX-4.** Usable at 200% zoom and reflow; horizontal scrolling only for genuinely two-dimensional data, never concealing or reordering row/column meaning; tables preserve row/column association and provide caption and headers.
- **AX-5.** Minimum 44×44 CSS-pixel targets where technically feasible; no essential information or action is hover-, drag-, or spatial-gesture-only; graph positioning has equivalent keyboard and pointer controls.
- **AX-6.** Reduced-motion respected; timers, elapsed-time, staleness warnings, and long-running results are supplemental — no essential state depends on animation, audio, or a timeout-only message.
- **AX-7.** Changed results, validation, refusals, unavailable data, and recovery states are announced through a non-color mechanism identifying the affected surface — server-side this is focus management on the fresh page (IC-5), not a live region.
- **AX-8.** Errors and refusals preserve safe input, remain available until resolved or dismissed, and provide keyboard-reachable recovery actions.
- **AX-9.** **Equivalent representations.** Graph and canvas views have a complete nonvisual equivalent: keyboard-reachable nodes/edges, meaningful names, current state, prerequisite context, and the same read and navigation actions. Dense Operations surfaces (graph, Evidence, retention/Reviews, analytics, Portfolio) expose the same canonical facts and permitted actions through semantic lists/tables. No essential fact or learner action may exist only in a visual graph.
- **AX-10. Narrow window (mandatory degradation).** At 320 CSS px and at 200% zoom: Today, Active Session/Study cockpit, SkillNode detail, Blockers, Evidence, and pass/master/close actions remain available; complex graph/analytics detail progressively discloses into equivalent list/table views; secondary regions stack; the Operations inspector becomes a route or full-width panel; section navigation becomes a labeled disclosure; primary actions stay reachable without obscuring context; sticky regions yield safely. The numeric re-measure of the disputed 320px reflow (F7) is part of the deferred effort (§12.4) — the requirement itself stands.
- **AX-11. Verification gate (owned by this handoff).** Automated axe + colour-contrast checks and golden snapshots run per slice, on real fixture data, kept cheap so that the deferred manual effort is re-verification, not discovery. Each acceptance criterion names its verification method and fixture/state coverage. Manual keyboard-only, screen-reader, touch, focus, reduced-motion, and F7 re-measure runs are a named deferred fresh effort (§12.4): never a pass, never a blocker to this contract's acceptance, and never grounds to weaken the standard.

## 10. Guided screen and state contracts (SC)

**SC-00. Template.** Every screen contract below carries, in order: route (RT), purpose, canonical facts read, states (populated / empty / limited / refusal / stale / failure / recovery), learner commands invoked, narrow-window degradation, accessibility hooks, and validation disposition tags (accepted / revised→Rn / carried-unvalidated). Where a contract is silent, §3–§9 bind.

**SC-00a. Cross-cutting state rules.** Every surface distinguishes **empty** (the queried population contains nothing — explain why, preserve discovery), **limited** (valid values exist but a policy threshold is not met — retain values, state the threshold), and **could not compute** (a required source failed to load — an operational failure with precise recovery; never zeroes, never warnings about the learner, never fabricated health facts). *(R7)* Nothing rendered may be silently zero-as-truth; numbers are truthful and consistent across surfaces (a count card, its destination view, and the fixture must agree).

### 10.1 Today (RT-01)

- **Purpose.** The predictable Guided home; the study day starts here.
- **Facts.** Derived readiness, Recommendations, `Session` (open/stale), due Reviews, open Blockers, pass-eligible nodes, Days practiced — all derived read-time.
- **Priority order (exactly one visually dominant action at a time):** 1. Resume the open Session (if one exists); 2. overdue Reviews and open Blockers affecting current work; 3. a pass-eligible SkillNode; 4. the highest-ranked normal recommendation; 5. Next and Find available as secondary discovery paths. A learner with no history receives one dominant **Start studying** action for the top available SkillNode plus ordinary discovery alternatives.
- **States.** *Empty/locked/stale:* when no recommendation is available, readiness is stale, or every visible SkillNode is locked, Today states the authoritative reason, preserves discovery, and offers the next safe recovery path — never framed as learner failure, never hiding the CLI dependency behind silence, never offering a prerequisite override. *Refusal:* starting a second Session while one is open is refused; Today shows the open Session and its safe actions instead.
- **Commands.** `start` (Start studying / resume); links only otherwise. A suggested check is never represented as due or scheduled until the learner schedules a Review.
- **Narrow window.** Priority queue stacks; the dominant action stays reachable; secondary queues follow.
- **Accessibility.** AX-1..AX-11; queue items are list items with meaningful labels.
- **Dispositions.** C01 revised→R6 (starting study announces its recorded timing; nothing is recorded unannounced); C20 revised→R7 (numbers truthful and consistent); C12 revised→R1, R5.

### 10.2 Next (RT-02)

- **Purpose.** Bounded, ranked selection of study targets.
- **Facts.** `Recommendation`, `NextAction`, derived readiness, Session context.
- **States.** Populated list with honest reasons ("Why this?" human copy); empty when nothing is recommendable (authoritative reason + recovery); stale readiness prompts a safe refresh; locked nodes shown only as explanation, never as targets.
- **Commands.** None — navigation only. Focus, queue, and pressure are projections.
- **Narrow window.** Rows stack; filters remain labeled GET controls.
- **Dispositions.** C12 revised→R1 (titles, never raw ids in prose), R5.

### 10.3 Find a skill (RT-03)

- **Purpose.** Dedicated discovery/search across the curriculum.
- **Facts.** `SkillNode`, node metadata, derived readiness.
- **States.** Search and filters are GET interactions (IC-4) with URL-addressable results, labeled controls, and a no-results recovery that preserves discovery. Empty curriculum explains the curriculum/source, not the learner.
- **Commands.** None — navigation only.
- **Dispositions.** C12 revised→R1; C14 revised→R2 applies wherever evidence figures surface from search context.

### 10.4 SkillNode detail (RT-04)

- **Purpose.** One canonical detail destination for one SkillNode, composed differently by mode.
- **Facts.** Progress record; node metadata; `GraphEdge`; `LearningResource`; `ArtifactSpec`; `ValidationGate`; `EvidenceRecord`; `AssessmentAttempt`; `Blocker`; `RemediationAction`; `Review`; recent event facts. Records are never collapsed into a generic progress/skill-health/evidence-state object.
- **States.** Brief-first composition: title and state first *(R1)*; evidence requirements wanted vs recorded as distinct labelled facts *(R2)*; advisory discrepancy between asserted progress and later live evidence shown as an advisory warning, never a demotion; empty/limited/failure per SC-00a.
- **Commands.** Links to `session`, evidence workspace, pass/master panels, reviews; contextual `work` where a Session is open (**Log work here**).
- **Narrow window.** Sections stack; the inspector becomes full-width.
- **Dispositions.** C03 accepted (blocked work vs Blocker distinction, minor notes); C14 revised→R1, R2.

### 10.5 Study cockpit / Active Session (RT-05)

- **Purpose.** One session timeline for the single open Session: timer, chosen SkillNode, SessionWork, Blockers, evidence requirements, safe closure.
- **Facts.** `Session` (open/completed; stale derived), `SessionWork` history, selected SkillNode, unresolved `Blocker`s, `ArtifactSpec` requirements and `EvidenceRecord` history, pass-eligible facts, the next valid learner action.
- **Behavior.** Selecting or inspecting a SkillNode never starts work. **Start studying** is the explicit `start` command: it refuses a locked node, opens the Session, records its first SessionWork, and moves an available node to asserted `active`. Starting a second Session is refused by the engine; Guided explains that the learner may log work on the chosen node within the current Session, or close it first; recovery returns to the existing Session and its latest safe actions *(R5)*. Switching the inspected node never closes, replaces, or implicitly extends the Session. Timer is presentation-only (IC-3); page load, navigation, inspection, and timer expiry never record work *(R6)*. Starting study announces exactly what is being recorded.
- **Blocked work and Blockers.** Blocked SessionWork is a session-scoped observation, labelled blocked work, never a Blocker *(IC-10)*. After persistent blocked work, Guided may explicitly offer **Create Blocker** (`blocker create`, requires an obstacle description, refuses a locked node; a second open Blocker warns about likely duplication but is not forbidden). After creation, Guided shows the open Blocker and its obstacle, available LearningResources as advisory study material, available RemediationActions as deliberate corrective interventions (never resolving the Blocker, changing node state, or claiming an unlock), and a clear path back to current work. `blocker resolve` requires a resolution summary and is terminal for that record; resolution closes no Session, marks no work complete, passes no node.
- **Log work.** Invokes `work` against the open Session and the explicitly bound SkillNode; notes and elapsed minutes optional; notes required when work is marked blocked. Work on a locked node is refused; work on a passed/mastered node remains honest history and never demotes.
- **AssessmentAttempt.** Contextual, never a required wizard step; the interface states that the attempt is immutable history and does not establish pass eligibility; a gateless node may record an attempt with a curriculum-quality warning.
- **States.** Stale open Session warns but never blocks work or closure; every refusal/failure per IC-8 with no records written.
- **Narrow window.** Cockpit stays usable at 320px (AX-10): timeline, dominant action, closure reachable.
- **Dispositions.** C02 accepted (resume/log work, no second Session; minor fixture notes); C03 accepted; C06 revised→R5; C08 revised→R4 (stale refusal noticeable); C26 carried-unvalidated (focus behaviour).

### 10.6 Safe Session closure (RT-06)

- **Purpose.** Close the Session without implying anything else.
- **Facts.** Elapsed SessionWork, latest relevant SkillNode, unresolved Blockers, evidence/eligibility state that remains after closure.
- **Behavior.** Closing is always a separate explicit `session close` action. A current close records the current end; a stale or apparently forgotten Session may be closed with an explicit honest end time in the past; future end times and end times before the Session start are refused with recovery to valid closure choices. Passing, evidence submission, Blocker resolution, navigation, panel closure, and mode switching **never** close the Session. A refusal to close never discards SessionWork; it refreshes current Session facts and keeps closure available.
- **Safe closure implies nothing:** work is saved; no pass, no resolution of Blockers, no completion of Reviews *(C05 contract)*.
- **Dispositions.** C05 accepted; C06 revised→R5; C08 revised→R4.

### 10.7 Passing (RT-07)

- **Purpose.** The explicit, separate, learner-initiated assertion of `passed`.
- **Facts.** Freshly derived pass eligibility and its supporting facts; current node state and the resulting asserted `passed` state; review-scheduling consequences; required vs accepted evidence *(R2)*.
- **Behavior.** Eligibility never pushes passing as an automatic next event; passing is a distinct full-page confirmation journey under the canonical `pass` command. Passing is legal directly from `available`; `active` is not presented as permission or prerequisite; a locked node cannot be passed regardless of evidence. Navigation, evidence submission, and Blocker resolution never imply or perform passing.
- **Confirmation panel (advisory presentation only).** Discloses freshly derived eligibility, current→resulting state, review-scheduling consequences, and that asserted progress never moves backward. The POST revalidates against current truth; a stale or changed confirmation refuses without writing, refreshes authoritative facts, and returns the learner to the next safe action *(IC-9/R4)*.
- **Evidence-vs-pass separation (R3, heavy).** Evidence submission and passing are presented as two separate decisions: the evidence journey ends in records; the pass panel is reached only by an explicit **Pass SkillNode** action that restates the accepted evidence it rests on. **Passing visibly changes the Review state**: the pass result page shows the review-scheduling consequence — scheduled Reviews appearing, or the explicit statement that policy leaves scheduling manual and offers the schedule action *(C04, C09)*.
- **Dispositions.** C04 revised→R3, R2; C08 revised→R4; C11 revised→R3 extension (pass vs master visibly distinct).

### 10.8 Mastery (RT-08, RT-09)

- **Purpose.** A later, separate, two-step, permanent assertion.
- **Facts.** Derived mastery eligibility; current `passed` state; the satisfactory Review and its date; the required pass↔Review spacing; policy facts.
- **Behavior.** Step 1 (RT-08) explains why mastery is or is not eligible. Step 2 (RT-09) requires explicit permanent confirmation, disclosing: current `passed` state; the satisfactory Review and its date; the required spacing; that `mastered` is permanent; that later unsatisfactory Reviews create failure-side pressure but never demote progress. Passing and mastering are never combined (no combined action anywhere in the product). The final POST revalidates mastery eligibility against current truth; a stale or ineligible confirmation refuses, preserves context, refreshes facts, and offers the next valid route without a partial state change.
- **Visible distinction from passing (R3 extension).** The two-step mastery journey and the one-step pass panel are visibly distinct journeys — different titles, copy, and step affordances — so the learner never conflates mastering with passing *(C11)*.
- **Dispositions.** C11 revised→R3 extension; carried-unvalidated: C15–C19 stub surfaces do not bear on it.

### 10.9 Evidence journey and corrections (RT-10)

- **Purpose.** One requirements-and-history flow per node, with authority visibly distinct by ValidationGate kind.
- **Facts.** Required and optional `ArtifactSpec`s with minimum counts; accepted live records; rejected history; superseded history; derived pass eligibility; gate kinds; Gate-run receipts where present.
- **Wanted vs recorded (R2).** The workspace labels **evidence wanted** (required specs, minimum counts) and **evidence recorded** (accepted live, rejected, superseded) as distinct, visible facts **before work begins**; the two figures are never collapsed into one ambiguous number *(C14, C17)*. Optional specs remain visible but are never presented as eligibility gaps when their minimum count is zero. Only accepted, non-superseded records for required specs count toward derived pass eligibility.
- **Manual gate.** Guided shows the artifact, the relevant gate standard or rubric, live EvidenceRecord history, and a mandatory Accept or Reject choice with no default verdict. Either choice creates an immutable EvidenceRecord; a rejection is an honest record, not a command failure.
- **Objective gate.** Submission invokes the gate; Guided shows the authoritative accepted/rejected result and, when present, the Gate-run receipt (command, repository-relative inputs, exit class, available exit/output hashes). An inability to run the gate is an operational failure creating **no record**, with a precise recovery path.
- **Corrections.** A separate **Correct earlier evidence** action invokes a new `evidence submit` with a required superseding record and reason. The prior record remains visible; superseded status is derived and **visible on the record itself**, not only in message wording; no edit or delete path exists. A rejected record remains rejected; a new attempt is a new record.
- **Dispositions.** C04 revised→R3, R2; C07 accepted (supersession must be visible on the record); C10 accepted (refusals write nothing); C15 carried-unvalidated (Vault legibility).

### 10.10 Reviews and retention (RT-12, Guided side)

- **Purpose.** The web review loop (P1.9 replacement row) inside the Guided study day.
- **Facts.** `Review` (scheduled/completed/cancelled; overdue derived), retention status (learner-facing derived), Memory state and Retention confidence (canonical Operations detail, never learner-facing certainty), Retention suggestions.
- **Behavior.** Due Reviews participate in Today's priority queue after Session resume and before ordinary recommendations. Scheduling occurs only through the explicit `review schedule` command; a suggested check may offer scheduling but never appears as already scheduled or overdue. Completing a Review is independent of the originating Session: it requires an explicit satisfactory or unsatisfactory outcome and a result summary; cancelling requires a reason and preserves cancelled history. Neither action demotes asserted progress or masters a node. An unsatisfactory outcome creates pressure, never demotion.
- **States.** Distinguish no review-worthy node, no scheduled records, and failed retention derivation *(SC-00a)*.
- **Dispositions.** C09 revised→R3 (review state visibly changes on pass; overdue legible); C16 carried-unvalidated.

## 11. Operations screen and state contracts

### 11.1 Operations home — capability directory (RT-13)

- **Purpose.** Orientation and entry to the six capabilities; hybrid verdict: persistent section navigation as shell chrome, the capability directory as the home.
- **Facts.** Derived counts per capability (home-only count cards, capability-linked), recent relevant facts as links.
- **States.** Orientation in ≤1 glance *(C13 contract)*; count cards exist only on this home and link to their capability; truthful numbers consistent with destination views *(R7)*. Health is an ordinary capability, never a score or banner on the home.
- **Dispositions.** C13 accepted (B preferred; hybrid stands); C20 revised→R7.

### 11.2 Evidence — repository index (RT-11)

- **Purpose.** Repository-wide immutable-history index, complementary to the node-bound workspace (§10.9).
- **Facts.** `EvidenceRecord` history, `ArtifactSpec`, `ValidationGate` kind, outcome, standing.
- **Behavior.** Default newest submission first, stable secondary ordering by Node ID and record ID. Filters by SkillNode, ArtifactSpec, ValidationGate kind, accepted/rejected outcome, live/superseded standing — GET, URL-addressable (IC-4). Search covers SkillNode title, Node ID, EvidenceRecord ID, and artifact path; notes and free text are excluded from the initial index. **Bulk mutation is absent**; no edit/delete affordance (HB-5). Selecting a record opens the contextual inspector with canonical record, related SkillNode, gate detail, Gate-run receipt where present, and event provenance.
- **States.** Empty explains unmet requirements without calling the learner blocked; unavailable evidence stores are operational failures.
- **Dispositions.** C15 carried-unvalidated; C07 accepted (immutability legibility rests on visible superseded status).

### 11.3 Reviews — one queue (RT-12, Operations side)

- **Purpose.** Full queue inspection over §10.10's same commands.
- **Behavior.** One queue ordered: overdue → scheduled by date → unsatisfactory/failed follow-up → completed and cancelled history. Selecting a Review opens its canonical record, owning SkillNode, result or cancellation reason, and related event provenance. Schedule, complete, and cancel are explicit dispatcher actions where the contract permits them. Retention suggestions occupy a **separately labelled advisory group**, never the scheduled/overdue queue, and create no record until the learner schedules a Review.
- **States.** Distinguish no review-worthy node / no scheduled records / failed retention derivation.
- **Dispositions.** C09 revised→R3; C16 carried-unvalidated.

### 11.4 Graph (RT-14)

- **Purpose.** First-class graph inspection capability (new locked row P6.1).
- **Facts.** `SkillNode`, `GraphEdge`, node state, derived readiness/recommendation facts; `graph/edges.yaml` remains the sole relationship truth.
- **Behavior.** Opens in a **learning-neighborhood view** centered on the selected SkillNode: the node, its immediate incoming and outgoing GraphEdges, and an expandable full hard-prerequisite ancestor closure. The full curriculum is available explicitly, never the default visual burden. Filters, selection, and focused/full mode provide inspection without storing graph layout as domain state. Normal rendering includes only valid relationships; invalid/dangling references and no-op edges appear in Repository diagnostics with exact source references, never implying a relationship currently changes readiness. A visual edge never invents a relationship; asserted progress remains visible even when a baseline edit would conflict with it. Selecting a node or edge opens canonical detail and the contextual inspector. **Complete accessible list equivalent required (AX-9):** keyboard-reachable nodes/edges with names, state, prerequisite context, and the same read/navigation actions.
- **States.** Empty graph explains the empty curriculum/source and offers discovery/recovery; an unreadable graph is an operational failure.
- **Dispositions.** C14 revised→R1, R2 (readable titles; evidence figures labelled); C25 carried-unvalidated (nonvisual equivalent never walked).

### 11.5 Health (RT-15)

- **Purpose.** Two explicitly named, independent projections — never an aggregate.
- **Sections.** **Study guidance** projects learner execution, evidence, and retention facts, links findings to owning SkillNodes or records, and may offer only canonical learner commands. **Repository diagnostics** projects graph, evidence, execution, policy, and resource integrity with exact source/location detail. No composite Health score, shared warning count, or cross-source severity total. A diagnostic may explain the repository correction expected when canonical documentation supplies it; Health is not a repair center and exposes no generic mutation. No finding blocks or accepts evidence, passes a node, or changes eligibility.
- **States.** Sections fail independently; one unavailable diagnostic source does not erase valid study guidance or imply a composite result.
- **Dispositions.** C19 carried-unvalidated.

### 11.6 Analytics (RT-16)

- **Purpose.** Four canonical metrics as inspectable themes: Study velocity (predictable entry theme, with ordinary links to the others), Blockers by domain, Review completion, Evidence coverage.
- **Behavior.** The default rolling window comes from policy and is always displayed; window, theme, grouping, and valid node-state filters ride URL parameters (RT-16 note) and may narrow rows but never redefine a metric. Every theme states its derivation, numerator/denominator where applicable, time window, grouping, and source records. Below `Soft data threshold`, available values remain visible under a limited-data warning; a computation failure is distinct and emits no zeroes *(R7)*. Tables are authoritative; charts supplement only when they encode the same values with an accessible equivalent (the existing tier-1 tooltip grant). One theme at a time; only real multi-point trends render; non-entry themes collapsed by default (P2.2 as superseded). No composite score, target-attainment badge, synthetic trend, streak, or invented health measure. Export is an explicit disposable Export action, not live truth.
- **States.** Limited data remains useful but not conclusive; failed derivations identify the unavailable source and recovery path; **could-not-compute** is a distinct honest state *(C21 contract — carried-unvalidated)*.
- **Dispositions.** C17 carried-unvalidated; C21 carried-unvalidated (probe never run); C22 accepted (dark dense readability).

### 11.7 Portfolio (RT-17)

- **Purpose.** An export configurator — never a live showcase, editor, or account.
- **Facts.** Portfolio export, Share profile (default-deny per-export contract), Redaction override, Portfolio bundle, Honesty banner.
- **Workflow.** Select → inspect redactions → preview exact output (RT-17 preview, non-writing, same selection/redaction/rendering pipeline as export) → choose format and destination → explicitly export. Presets are filters; the learner explicitly selects SkillNodes and any Redaction override dimensions; the default-deny Share profile remains visible and authoritative. The output records its date, format, destination, selection metadata, and active redactions. Where superseded evidence, stale resources, or unverified claims are present, the exact preview and export carry the Honesty banner. A completed bundle is a dated disposable artifact; the web cannot reopen it as live truth.
- **States.** No selected nodes explains that export has not been configured; preview/export failures write no partial destination and preserve the selection for recovery.
- **Dispositions.** C18 carried-unvalidated.

### 11.8 Contextual inspector (no route — RT note 2)

- **Purpose.** The shared drill-down for any selected fact on an Operations surface (and node detail).
- **Behavior.** Opens with the fact's canonical record, related SkillNode, and relevant event provenance; the owning surface supplies the action and the dispatcher remains authoritative. Progressive disclosure is consistent: summary first, canonical record second, diagnostic provenance last. Local Operations may show notes, Blocker text, Review summaries, source paths, raw IDs (mono, labelled — R1), gate details, commands, and provenance — explicitly private repository diagnostics, never included in a Portfolio export unless the corresponding default-deny redaction override is enabled for that invocation. Returning to Guided preserves the selected SkillNode, Session, or Evidence context where the target surface supports it. Event provenance renders as record detail here — there is no standalone Event-log surface or audit-log route.
- **Dispositions.** C15/C16/C19 carried-unvalidated (stub surfaces).

## 12. Validated findings (evidence honesty)

### 12.1 Evidence base and gate sentence

The validation gate was executed as a **single learner-confirmed pointer pass** on real Pandas fixtures (`docs/validation/v3-observation-report.filled.md`), plus automated axe and colour-contrast checks and the learner's own zoom/narrow-window observations — on Guided G1–G9 and Operations O1–O8 plus O1 in Draft B on reset fixtures, with 21 findings, **zero critical, no domain-boundary violation observed**. The learner — the primary user — decided on 2026-11-07 that the pointer pass is sufficient for what they need; the keyboard-only and screen-reader passes, touch, focus, reduced-motion, and the O9 could-not-compute probe were **not run**. The gate is therefore **satisfied as re-scoped, not as originally contracted**: the numeric multi-pass thresholds (≥80% first-attempt, ≥90% recovery) were not walked or not met, and no claim was passed on their absence. Deferral is a scope decision, never a result. Deferred or insufficient evidence is still never a pass, and the deferred work does not reopen map #327.

### 12.2 Disposition matrix C01–C27

Disposition rule (locked): **accept** — observed (O) or evaluator-replay-confirmed (E) with no unresolved major finding bearing on it (minors noted, not disqualifying); **revise** — the requirement stands but a major observed presentation/comprehension failure means its rendered expression must change before the specification locks; **insufficient evidence / deferred** — no usable evidence (not run, not covered, not assessable, or ruled out of scope) — *never a pass*; **reject** — reserved for the hard rule (domain-boundary violation, fabricated/hidden state, unsafe action, inaccessible essential path). **Hard rejection rule: no trigger — zero rejects.**

| Claim | Requirement (source) | Disposition | Basis |
|---|---|---|---|
| C01 | Cold start & discovery without CLI vocabulary | **revise** | G1 unaided in 47 s, zero CLI vocabulary — but F4 (silent 20-min SessionWork on start) is major → R6 |
| C02 | Session resume / log work, no second Session | **accept** (minor notes) | G2 unaided; second-Session refusal understood with hint; F3/L8 fixture-level minors |
| C03 | Blocked work ≠ Blocker; Blocker persists across close | **accept** (minor notes) | Distinction restated in own words; persistence observed; F2/L8 asset bug, F6 recorded-time exclusion noted |
| C04 | Evidence → eligibility → pass distinct, learner-initiated | **revise** | F18 (evidence/pass experienced as one gate) and F16 (no visible Review change); G4 needed hint 3 → R3 |
| C05 | Safe Session close implies nothing | **accept** | G5 statement and Q4 both correct |
| C06 | Refusal safe, recoverable, leaves correct state | **revise** | State correct in replay, but recovery 0/2 unaided — F15 → R5 |
| C07 | Correction supersedes; original never edited/deleted | **accept** (minor notes) | In-task wording correct; post-G9 recall wobbled (M2); supersession must be visible on the record |
| C08 | Stale confirmation refuses without writing | **revise** | Mechanism works (E replay) but F14: learner never noticed it fire → R4 |
| C09 | Review completion independent of Session; no demotion | **revise** | G7 evidence weak; F16 overdue and review change invisible → R3 |
| C10 | Refusals / operational failures create no records | **accept** (minor notes) | Messages clear; aftermath confirmed by E replay |
| C11 | Mastery separate, deliberate, two-step | **revise** | Asset could not present it (L1); Q1 conflated mastering with passing → R3 extension |
| C12 | Guided navigation task-led and predictable | **revise** | 0 errors outside refusals, but hint-dependence (G4/G6/G8), F13 raw ids, F19 status scannability → R1, R5 |
| C13 | Operations home orientation in ≤1 glance | **accept** | Both drafts oriented correctly; B preferred (51 s vs 96 s); hybrid stands |
| C14 | Graph readiness / evidence inspectable | **revise** | Availability found; F17 (ambiguous Evidence figure — wanted vs recorded) major; L3 four-row graph → R1, R2 |
| C15 | Evidence Vault inspectable; immutability legible | **insufficient evidence — carried unvalidated** | Destination stub (L4); O3 unanswerable |
| C16 | Retention / Reviews inspectable | **insufficient evidence — carried unvalidated** | Stub (L4); O4 unanswerable |
| C17 | Analytics show derivations, no fake telemetry | **insufficient evidence — carried unvalidated** | Caption-level only |
| C18 | Portfolio export honest and redacted | **insufficient evidence — carried unvalidated** | Stub (L4); menu item inert |
| C19 | Health ordinary capability, not a score | **insufficient evidence — carried unvalidated** | No health view exists (L4) |
| C20 | Empty/limited states truthful, no zeroes-as-truth | **revise** | F1 (fixture toggle ignored) and F8 (0-card vs "Evidence: 2 records") majors → R7 |
| C21 | Could-not-compute surfaced honestly | **no evidence — carried unvalidated** | O9 not run; asset has no such state (L2) |
| C22 | Dark dense system readable; status never colour-only | **accept** (minor notes) | axe contrast clean in all states; status pills carry text; readability reported across zoom/widths |
| C23 | WCAG 2.2 AA mandatory criteria | **deferred — never a pass** | Keyboard, screen-reader, touch criteria not walked (re-scope decision) |
| C24 | Narrow-window degradation keeps critical actions | **deferred — never a pass** | F7 disputed (scripted 320px overflow 353/475px vs learner seeing no sideways scroll); re-measure transfers to deferred effort |
| C25 | Graph nonvisual equivalent complete | **no evidence / deferred — never a pass** | Screen-reader pass not run; graph stub (L3) |
| C26 | Interaction budget: explicit actions, focus on outcome | **deferred — never a pass** | Focus untested without keyboard pass; pointer-side failures carried as revisions (F4, F11, F19) |
| C27 | Omnibar as accelerator, navigation-only | **not covered — carried unvalidated** | No omnibar in either prototype |

**Tally: 7 accept (5 with minor notes), 9 revise, 11 insufficient-evidence/deferred/not-covered (C15–C19, C21, C23–C27), 0 reject.**

### 12.3 Stated limits of the evidence

Method deviations M1–M4 (including the post-G9 recall wobble), unhashed learner prototype copies, and L9 prior-exposure bias on cold-start claims ride with the verdict. Fixture/asset bugs F2, F3, F5, F12 are prototype limitations, not specification requirements.

### 12.4 Deferred validation effort (fresh effort, never a blocker here)

Prioritized for the later effort, so that it is re-verification rather than discovery: 1. keyboard-only, screen-reader, touch, and focus re-runs **with the F7 narrow-window re-measure first** (C23–C26, C25); 2. the stubbed Operations surface claims (C15–C19); 3. C21 (could-not-compute probe) and C27 (omnibar). AX-11 keeps automated axe/contrast checks cheap per slice to serve this.

## 13. Mandatory specification revisions R1–R7

Each revision is an acceptance criterion of this contract (§17), bound to its owning screens and slice (§18).

| ID | Revision (source findings) | Bound into | Owning slice |
|---|---|---|---|
| **R1** | Readable SkillNode titles everywhere learner-visible; raw ids only as labelled technical data in Operations, record detail, and the inspector (F13, F19) | VS-4, §10.1–10.4, §11.4, §11.8 | SL3 |
| **R2** | Evidence **wanted** vs **recorded** as distinct, labeled facts, visible before work begins (F17) | §10.9, §10.4, §11.2, §11.4 | SL5 |
| **R3** | Evidence submission and pass as two separate decisions; passing visibly schedules/changes Review state; mastery visibly distinct from passing (F18, F16, Q1) — *heavy* | §10.7, §10.8, §10.10, §11.3 | SL5 (+SL6 for the visible review change) |
| **R4** | Stale-confirmation refusal noticeable at the moment it fires (F14) — *heavy* | IC-9, §10.6–10.8 | SL4 |
| **R5** | Refusal/failure recovery completable without a hint ladder — the panel names the next safe action (F15) — *heavy* | IC-8, §10.5, §10.1–10.3 | SL4 |
| **R6** | No silent timing: Session start records nothing unannounced; explicit recorded timing (F4) | IC-3, §10.1, §10.5 | SL4 |
| **R7** | Empty/limited-state numbers truthful and consistent across surfaces (F1, F8) | SC-00a, §10.1, §11.1, §11.6 | SL2 |

## 14. Migration posture

Graduate in stages toward **one target product**; no permanent parallel UI, no second package, no second stack, no feature flag: v3 routes replace Tier-1 routes **in place**.

- **MIG-1.** Each slice replaces the named prior surface at its own completion; the replaced surface's code and superseded snapshots die in the slice that replaces them (exit conditions, §18). Parallel existence is bounded to the migration window only.
- **MIG-2.** SL2 retires the v2.4 unified-home recipe (hero + six-card bento, 30px display heading, dense band on home) on `/`. `/health` and `/analytics` keep their paths but are reclassified as Operations capabilities at SL7. The existing `/nodes/jump` path is repathed to `/find` at SL3 (RT-03).
- **MIG-3.** Cutover completes at SL7: after it there is never more than one live home, one live Today, or one live Operations entry.
- **MIG-4.** `docs/spec-tier1-serve.md` §A/§B "Tier 1 as built" text and `USER_GUIDE.md` are superseded by this specification at acceptance (§20); `§C` keeps its history with a pointer, per ADR 0007's amendment.

## 15. Architecture consequences (locked; no structural replacement)

Every validated requirement of this spec sits inside the current stdlib / server-rendered / interface-sublayer posture. Named consequences and their triggers, as traced by G-ArchitectureConsequences:

- **ARC-1. ADR 0006 stands unamended.** Stdlib `ThreadingHTTPServer`, zero new runtime dependencies (`PyYAML>=6.0`, Python ≥3.14), fresh `load_context_lenient` per request, in-process dispatch for writes, one inline `<style>` block, no static-file routing, loopback bind. Two named escalations with triggers, neither executed by this spec: (1) `render.py` → structured-section-data refactor — pre-sanctioned by ADR 0006, triggered when the v3 route table lands, executed in the implementation map with ADR 0009's `views/` package as its structural home; (2) stylesheet size — revisited only if the token system makes the inline block unmanageable, which would be a serve-trait amendment to 0006.
- **ARC-2. ADR 0007 amended (2026-09-25).** The downward-only restructure gate is replaced: new top-level views are permitted **only where §6 of this specification names them**. §6 is the normative route table. The core decision is untouched: Python-derived View/Card/Command/active-view vocabulary, import-time and request-time validation, one audit event per action, `criterion.layers.present` stays 5, no `criterion.web.interface.valid`.
- **ARC-3. ADR 0008 stands unamended.** Every new v3 interaction is tier 0; the analytics chart-tooltip grant is the only tier-1 budget. Reopen only through the written evidence packet: an adopted-path interaction demonstrably failing at tier 0, prototyped with the exact JS it needs. Server-rendered SVG through the existing sparkline seam plus table/list equivalents carries the graph; pan/zoom/heatmap remain behind the tier-2 wall.
- **ARC-4. State ownership unchanged.** Markdown/YAML files are the truth, read fresh per request; no server-side view-state file; no client state model. Mode, inspector context, and filter state live in the URL (IA-1). Session and timer facts are engine records. `web/interface/` reads the dispatcher registry and is never a second domain model.
- **ARC-5. URL behavior.** New views only where §6 names them; view identity stays the screen name, never the path; the `/today` alias remains closed (`today` on `/`); flash `notice`/`kind` carry unchanged; GET filters are URL-addressable and history-bearing (IA-5); non-navigating disclosures create no history entry.
- **ARC-6. Server validation unchanged** (IC-7).
- **ARC-7. Release gates.** `criterion.layers.present` stays 5. DD6's per-route budget gate (`/analytics` the only route emitting `<script>`) and SA1 (the sublayer emits none) are unchanged. The golden snapshots in `tests/web/snapshots/` grow with the §6 table at implementation. SA6 (`test_sa6_no_new_top_level_view_beyond_the_frozen_table`), the sublayer scaffold's frozen-table test, `FROZEN_ROUTES`, and the two spec-text gates pinning §C's "no new top-level view" line are **repointed to §6** in the change that adopts it, each keeping its exact assertion — the ADR 0009 discipline.
- **ARC-8. Accessibility verification gate** (AX-11) is owned by this specification; automated accessibility tooling joins `[project.optional-dependencies] dev` — dev-only, never a runtime dependency.
- **ARC-9. No new ADR is warranted**: nothing here is hard to reverse (0006/0008 carry written reopen paths; 0007 keeps its reversal-cost section), surprising (the amendment records why the gate moved), or a fresh trade-off (the stack-vs-scope trade-off was settled when the posture was retained).

## 16. Preference sweep outcome (locked rows)

Full sweep of the locked preference table and `spec-tier1-serve.md` §C's "Not a route" table, per G-PreferenceReopen:

- **SUP-P1.** **P1.9 superseded** — replaced by the web review loop row (P1.9 replacement): "A web review loop, in both modes" as specified in §10.10/§11.3 (Apply · spec + prototype for the completion panel).
- **SUP-P2.** **P5.1–P5.4 superseded wholesale** by §8: type (VS-4), spacing (VS-5), density-by-mode (VS-6; Today-cap and rich-home-cap block counts retired), dark-first tokens with light companion (VS-2).
- **SUP-P3.** **P5.5 discharged**; **P2.1** two density registers stand, re-labeled by mode (Guided airy / Operations dense), numbers owned by §8.
- **SUP-P4.** **P2.2 superseded in part** — default theme becomes Study velocity; segmented control replaced by ordinary links between themes (one theme at a time; tables authoritative; collapsed-by-default non-entry themes stand).
- **SUP-P5.** **P3.1/P3.2 superseded in part** — raw IDs permitted as technical data in Operations/record-detail/inspector in the mono role, never woven into sentences; no IDs in prose, link labels, breadcrumbs, flash banners, or confirmation copy; titles everywhere.
- **SUP-P6.** **New locked row P6.1** — Graph inspection is a first-class Operations capability, as specified in §11.4 (spec + prototype).
- **SUP-P7.** Route-absence dispositions: `--state` filtering **reopens** (Operations node-state filters; Evidence index outcome/standing filters); `/reviews` writes **reopen** (§10.10/§11.3, riding the one write path); graph/dependency view **reopens, condition fully met** (§11.4 + P6.1). **Stay closed:** `/today` alias (never); no delete affordance; no audit-log route (provenance renders in the inspector).
- **SUP-P8.** Standing rows confirmed: P1.1a/b, P1.2–P1.4, P1.10, P1.5 (celebration as brief state-transition feedback under VS-9's zero-JS warrant), P1.6/P1.7, P1.8 (stays Defer), P2.3/P2.4 (per-layer warning counts now satisfied through §11.5 repository diagnostics), P2.5–P2.8, P3.3–P3.6, P4.1–P4.4 (history-rule and Confirmation-panel collisions reconciled at tier 0).
- **SUP-P9.** No composite score, invented Settings, audit-state object, or second domain model returns.

## 17. Acceptance criteria (product level)

The product is accepted when:

- **AC-1.** Every route in §6 exists with its screen contract (§10–§11) implemented, including every named state (populated/empty/limited/refusal/stale/failure/recovery).
- **AC-2.** All seven mandatory revisions R1–R7 are observably satisfied on their bound screens (§13).
- **AC-3.** Every hard boundary HB-1..HB-8 holds on every surface; no route, panel, or timer automates or implies pass, master, or delete; refusals and failures write no records.
- **AC-4.** The domain mapping §4 is complete: no learner-visible fact, control, or action lacks a canonical binding; no invented objects exist.
- **AC-5.** AX-1..AX-10 hold as specification content, with AX-11's automated verification (axe, colour-contrast, golden snapshots on real fixtures) green per slice; the deferred manual passes (§12.4) are tracked in the fresh effort, never silently dropped and never falsely claimed.
- **AC-6.** VS-1..VS-10 hold, including the exact anti-pattern list.
- **AC-7.** IC-1..IC-10 hold; the tier budget is exactly the existing analytics tooltip grant.
- **AC-8.** Migration MIG-1..MIG-4 completed: one target product, no parallel UI remnants.
- **AC-9.** Release gates per ARC-7 repointed and green; `pytest` green; lint gate green.

## 18. Ordered implementation slices (SL)

Contract decomposition, not release slicing: no versions, dates, sized tasks, or final sequencing — those belong to the implementation wayfinder (§19). Dependencies in brackets; suggested starting order as listed. Each slice's exit condition cites clause IDs and its replacement (MIG-1).

| ID | Slice | Scope (clauses) | Depends on | Exit condition (summary) |
|---|---|---|---|---|
| **SL1** | Shell & tokens | Route substrate over §6 (flat, mode-neutral; mode/context params), IA-1..IA-6, dark-first token system VS-1..VS-5, accessibility floor AX-1..AX-3, AX-7 | — | Shell renders every §6 destination stub or real; tokens live; automated a11y harness runs on fixtures; §6 adopted — `FROZEN_ROUTES`/SA6/snapshots repointed per ARC-7 |
| **SL2** | Today & honest states | §10.1, SC-00a, R7 | SL1 | Priority queue exact; cold start without CLI vocabulary; truthful empty/limited/stale states; **replaces** the v2.4 unified-home recipe on `/` (MIG-2) |
| **SL3** | Discovery & node detail | §10.2–10.4, R1, IA-5 GET filters | SL1 | `next`/`find` with URL-addressable filters/search; node detail brief-first with readable titles; **replaces** `/nodes/jump` with `/find` |
| **SL4** | Study cockpit | §10.5–10.6, R4, R5, R6, IC-3, IC-8..IC-10 | SL3 | Start/resume/log-work/close with explicit recorded timing and announced recording; blocked-work vs Blocker; stale refusals noticeable; unaided recovery paths |
| **SL5** | Evidence & assessment | §10.7–10.9, R2, R3, R4, R5, HB-5 | SL4 | Wanted-vs-recorded visible before work; submission and pass as two decisions; pass panel shows visible Review-state consequence; corrections supersede visibly; pass/master panels with fresh-truth revalidation |
| **SL6** | Reviews & retention loop | §10.10, §11.3 (Guided side), P1.9 replacement | SL3, SL5 | Web schedule/complete/cancel as dispatcher actions; due Reviews in Today's queue at the exact priority; advisory suggestions never in the queue; pass visibly changes Review state |
| **SL7** | Operations | §11.1–11.8, R7, AX-9..AX-10, ARC-3 (SVG + equivalents) | SL1; reuses SL2–SL6 contracts | Capability home with truthful home-only count cards; graph with complete list equivalent; Evidence index; Health two sections; Analytics four themes; Portfolio configurator with redaction preview; `/health` and `/analytics` reclassified (MIG-2); **cutover complete** (MIG-3). Omnibar (§6 note 4, carried-unvalidated C27) implemented last within this slice or deferred to the fresh validation effort's follow-up |

SL7 is the largest slice and may be internally sequenced by the implementation wayfinder (e.g., home+graph before analytics+portfolio), provided every exit clause lands before cutover.

## 19. Handoff boundary

**Closed questions — the implementation wayfinder must NOT reopen:**

- Routes, view identities, and the closed-destination list (§6, RT-01..RT-17 + notes).
- Mode architecture: dual-mode over one engine, mode as URL presentation context (§2, §5).
- Stack posture: stdlib server-rendered tier-0 with the single analytics tooltip grant (§15, ADR 0006/0007/0008 status).
- Domain bindings, terminology contract, and hard boundaries (§3, §4).
- Validation dispositions: the C01–C27 matrix, the seven revisions, and the deferred-effort boundary (§12–§13). Insufficient evidence is never upgraded to a pass; the deferred manual passes return only through the fresh effort.
- Preference dispositions (§16) and supersessions (§20).
- The slice decomposition's contract content (§18 scope columns).

**Owned decisions — the implementation wayfinder decides:**

- Final sequencing of SL1–SL7 into releases/tasks, internal splitting of SL7, version numbers, dates.
- Test selection and mechanics: which tests per slice, golden-snapshot repointing mechanics, fixture scenarios for AX-11 automation (the exit conditions in §18 stay binding).
- The `render.py` → structured-section-data refactor's execution details (ARC-1 escalation 1) inside ADR 0009's `views/` package.
- Copy micro-wording within the terminology contract (§4) and VS/AX constraints.
- Omnibar implementation timing within SL7 or deferral alongside the fresh validation effort (§6 note 4).

## 20. Supersession (declare-only)

At acceptance of this specification, the following are superseded **by declaration**; the historical files are not edited (frozen history convention):

| ID | Superseded | By |
|---|---|---|
| SUP-1 | `docs/spec-tier1-serve.md` §A/§B "Tier 1 as built" text | This specification (§5–§11, §15) |
| SUP-2 | `docs/spec-tier1-serve.md` §C frozen route table (kept as history with a pointer, per ADR 0007 Amendment 2026-09-25) | §6 of this specification |
| SUP-3 | `docs/spec-tier1-serve.md` §C-ter "repository diagnostics are CLI-only with zero web presence" | §11.5 Repository diagnostics |
| SUP-4 | `docs/USER_GUIDE.md` web sections describing Tier 1 as built | This specification |
| SUP-5 | `docs/spec-v2.4-interface-sublayer.md` §B stale visual prose: 14/11/999 radii, 1040px shell, single 960px desktop-only breakpoint, serif-prose/sans-chrome font split, light-first token table | §8 (VS-2, VS-4, VS-5, AX-10) |
| SUP-6 | The v2.4 unified-home recipe (G-Direction #248: hero + six-card bento, 30px display heading, dense band on home) | §10.1 priority-led Today + §8 VS-5/VS-6 |
| SUP-7 | Locked preference rows P1.9, P5.1–P5.4 (wholesale), P2.2 and P3.1/P3.2 (in part); P5.5 discharged | §16 |
| SUP-8 | CONTEXT.md **Confirmation modal** (already amended to **Confirmation panel** by G-ArchitectureConsequences) | IC-2 |

No new domain term is introduced by this specification; `CONTEXT.md` requires no glossary change.

## 21. References

`CONTEXT.md` (ubiquitous language) · `docs/SAFETY_BOUNDARIES.md` · `docs/adr/0006-stdlib-only-serve-shell.md` · `docs/adr/0007-reintroduce-interface-layer.md` (Amendment 2026-09-25) · `docs/adr/0008-inline-progressive-enhancement-posture.md` · `docs/adr/0009-web-views-package-facade.md` · `docs/validation/v3-observation-report.filled.md` (pointer-pass evidence) · `docs/validation/v3-usability-runbook.md` · `prototype/p-core-journey.html`, `prototype/p-operations-workspace.html` (throwaway decision aids, never read by the engine) · map #327 and its closed tickets #328–#341, #344–#347 (history superseded by this restatement).
