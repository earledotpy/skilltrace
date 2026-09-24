# Research brief — supplied interface prototype audit

**Issue:** [#328 — R-PrototypeAudit](https://github.com/earledotpy/skilltrace/issues/328)
**Map:** [#327 — v3 study-day UI/UX product specification](https://github.com/earledotpy/skilltrace/issues/327)
**Audit base:** `origin/main` at `e53f592b8855a8d6a984076ff7e291dbe3eada94`
**Prototype:** `C:\Users\jerem\Downloads\skilltrace.zip`, 181,358 bytes, SHA-256 `c2c9311355cfc3eea46093f0908886f71b130a1d2a7c83d44bcc0fb7aafd6b80`
**Method:** extracted the supplied ZIP read-only and inspected every source file; traced all six workspaces, five global dialogs, client state transitions, mock fields, controls, and dependencies back to that source. Claims about SkillTrace are checked against the repository's `CONTEXT.md`, ADRs, and shipped specs. Prototype citations below use paths inside the supplied archive.

## Executive finding

The prototype is a useful **visual and information-architecture reference**, not a domain or implementation reference. Its strongest portable ideas are the dark, dense, learner-first hierarchy; persistent operational context; a focused recommendation surface; split graph/inspector exploration; evidence inspection plus export selection; retention triage; and a global accelerator concept. Those ideas must be re-expressed through SkillTrace's real records, derived views, URL-addressable Views, and dispatcher-backed actions.

The prototype's behavior is largely a second mock domain model. It embeds relationships and asserted progress in client objects, has no URL routing, lets direct UI setters pass or master a `ready` SkillNode without eligibility, permits a backward transition, invents SM-2 semantics, resolves a Blocker by unlocking nodes and reviews, and simulates gates, telemetry, exports, and evidence acceptance. None of that behavior is portable. The React/Vite dependency set, persistent client store, simulated terminal, and code workbench are also implementation artifacts rather than requirements.

### Disposition counts

| Disposition | Meaning | Count |
|---|---|---:|
| **Adopt** | Carry the product idea essentially unchanged into the v3 specification. | 12 |
| **Transform** | Retain the intent, but rebuild it with canonical fields, real navigation, server/engine authority, and accessible behavior. | 24 |
| **Evaluate** | Test in a throwaway prototype or usability session before deciding. | 12 |
| **Reject** | Do not carry into v3; it is false, unsafe, out of scope, or an implementation detail. | 25 |

## Non-negotiable interpretation

1. The prototype is evidence of design intent, not engine truth. The map already establishes this; this audit applies that rule screen by screen.
2. Every meaningful v3 destination must be URL-addressable. The prototype's `WorkspaceId` switch is not navigation ([prototype `src/App.tsx:23-41`]). Current SkillTrace requires Views to be URL-addressed and bookmarkable ([ADR 0007 `docs/adr/0007-reintroduce-interface-layer.md:55-75`]).
3. UI actions must compose existing commands. Prototype `setNodes`, `setReviews`, and `setBlocker` are not commands and append no audit event. Current rules require every UI mutation to invoke the dispatcher and append one event ([ADR 0007:90-97]).
4. Pass and mastery remain separate, explicit, learner-initiated commands with derived eligibility and server-enforced refusals. The combined “PASS SKILL & AWARD MASTERY SEAL” affordance is rejected.
5. UI reads engine-derived facts fresh; it never owns progress, eligibility, memory state, or events. This preserves the current web-only interface boundary ([ADR 0007:40-53, 77-88]).
6. No conclusion here changes curriculum direction, retention mathematics, engine semantics, release criteria, or implementation slicing.

## Evidence baseline and limitations

The archive is a generated Google AI Studio React example rather than a repository of SkillTrace. Its README only says to install Node dependencies, set `GEMINI_API_KEY`, and run Vite ([prototype `README.md:5-20]`); the manifest requests Gemini server capability but no Gemini call appears in the inspected application source ([prototype `metadata.json:1-6`; `src/**/*.tsx`, `src/**/*.ts`). The archive supplies no tests, no API, no persistence, and no SkillTrace engine integration.

Static tracing is conclusive for the supplied behavior. A local install could not be completed within the command timeout, so this audit does not claim runtime screenshots or interaction-test results. The UI nevertheless exposes its states and handlers in source, and the findings do not depend on rendering it.


## Inventory at a glance

### Application shell and dependencies

- `App.tsx` mounts a full-viewport, overflow-hidden shell with fixed Sidebar + Header + one switched workspace + five always-mounted global dialogs (`src/App.tsx:23-71`).
- Sidebar has six destinations, a simulated repository/branch/PID/engine footer, a live session timer, and counts/badges (`src/components/Sidebar.tsx:6-16,56-69,71-153`).
- Header has omnibar trigger, active-blocker alert, transient toast, four budget choices, streak, simulated CLI, and avatar (`src/components/Header.tsx:18-103`).
- State is entirely React `useState` seeded from mock arrays: workspace, budget, streak, modal flags, nodes/selection/filter/search, reviews, blocker, timer/work/code/test output, evidence/privacy, toast (`src/context/AppContext.tsx:127-175`). It has no API, persistence, authentication, error boundary, loading state, or engine calls.
- Dependencies are React 19, React DOM, Vite, Tailwind 4, Lucide, Motion, Express, dotenv, Google GenAI, TypeScript tooling (`package.json:6-33`). Fonts and Material Symbols load from Google; the logo and an evidence image load from remote Googleusercontent URLs (`index.html:12-18`; `src/data/mockData.ts:325-343,428-429`).

### Navigation paths actually implemented

| From | Action | Destination/state | Implementation reality | Disposition |
|---|---|---|---|---|
| Startup | load | Daily Brief | fixed initial `workspace`, no URL | **Transform** into Guided-mode URL home |
| Sidebar / Daily Brief shortcuts / omnibar / simulated CLI | select workspace | Daily Brief, Skill Graph, Active Session, Retention & Reviews, Evidence Vault, Analytics & Portfolio | client state switch; no history, deep link, refresh, or back/forward | **Transform**: keep two-mode information architecture, require canonical URL routes |
| Daily Brief | Reviews Due | Retention | client switch | **Transform** to a Review queue view |
| Daily Brief | Resume / Launch Session, graph inspector | Active Session | client switch; launch does not bind the selected SkillNode | **Transform** through real `start` semantics |
| Daily Brief | Resolve Impasse | Blocker dialog | modal opens; submit changes mock state | **Transform** to explicit `blocker resolve` with required summary; no magical node unlock |
| Daily Brief | per-review Probe Recall | Retrieval Probe dialog | modal opens | **Evaluate** the interaction, but use Review outcomes and real schedule semantics |
| Daily Brief | View Vault | Evidence Vault | client switch | **Transform** |
| Graph | select node, prerequisite, dependent | same Graph workspace, new selection | selection only; not addressable | **Transform** to `/nodes/<id>` and relationship links |
| Graph | Launch Session | Active Session | selected node is not carried into session | **Transform** |
| Graph | Pass + Mastery | Attestation dialog | direct setters later set either state | **Reject** combined action; **Transform** into separate dispatcher-backed confirmations |
| Retention | Start Rapid Retrieval / Probe Recall | Retrieval Probe | opens first or chosen review | **Evaluate**; use satisfactory/unsatisfactory result + summary, not invented SM-2 buttons |
| Retention | CLI Probe | clipboard only | no command or review action | **Reject** as primary interaction; command copy may be **Evaluate** in Operations mode |
| Evidence | filter, select record, privacy choice | same Evidence view | local state | **Transform** to real query/URL and explicit portfolio selection/export commands |
| Evidence | Export Bundle / command tile / Generate ZIP | toast or copied string | no file; contradictory `--format=zip` vs visible `--tar`; fake hash | **Reject** fake behavior; **Transform** real Export semantics if selected by product spec |
| Analytics | Export telemetry CSV | toast only | no file | **Transform** to a real derived export, if retained |
| Global | ⌘/Ctrl+K | Omnibar | toggles modal; no arrow-key handling despite button copy | **Evaluate** as accelerator only after URL/navigation and keyboard design |
| Global | backtick | simulated CLI | custom command parser, not dispatcher | **Reject** embedded terminal; keep CLI secondary outside the primary web product |
| Global dialogs | backdrop / close control | dismiss | inconsistent Escape and focus behavior | **Transform** into accessible, URL-stable confirmations |

## Field and record mapping

The prototype's TypeScript interfaces are a **field/action mapping proposal only**. They must not become a second schema.

| Prototype field/type | Intended information | Canonical source / v3 treatment | Disposition |
|---|---|---|---|
| Skill identity/name/domain/description/difficulty/x/y | identity and graph presentation | curriculum markdown + joined view; layout belongs in view state | **Transform**; never put x/y in truth |
| `status: mastered/passed/ready/in_progress/locked` | lifecycle/readiness | canonical: `locked/available/active/passed/mastered`; split readiness from asserted progress | **Transform**; delete `ready`, `in_progress`; forbid backflow |
| `prereqs`, `dependents` | relationships | `graph/edges.yaml` sole truth; derive both directions | **Reject** embedded fields; **Transform** view |
| `retention` | memory health | derived Retention confidence (0–1, read-time) | **Transform** with context |
| `evidenceContract` | pass requirements | derive ArtifactSpec requirements, gate, pass eligibility | **Transform** into summary |
| Review identity/context | review context | derive from canonical Review + SkillNode | **Transform** |
| retention/status/lastReviewed/elapsed/interval/sm2Factor | schedule/health | FSRS-derived memory state, policy thresholds, scheduled/overdue Review facts | **Reject** stored/mock SM-2; **Transform** view |
| challenge/requiredProof | retrieval prompt/support | learner review material/resource where available; not universal Review fields | **Evaluate**; don't invent fields |
| grade `again/hard/good/sovereign` | result | satisfactory/unsatisfactory + required summary | **Reject** grade/math; **Transform** interaction |
| Blocker id/node/title/timestamps | persistent stuckness | canonical Blocker identity, SkillNode, obstacle, open/closed facts | **Transform** |
| misconception/epiphany/diff/traceback/evidenceFile/AST | post-mortem proposal | evidence is separate submitted/accepted history | **Evaluate** summary; **Reject** hardcoded proof |
| blockedNodes/blockedCount | Blocker effect | remediation may reorder; Blocker never locks/unlocks | **Reject** direct unblock |
| Evidence path/node/title/category/hash | artifact/provenance | immutable EvidenceRecord + receipt + joined SkillNode/spec | **Transform**; no evidence node states |
| evidence status/AST/badge/revisions/attested/logged | fake acceptance/audit | frozen outcome and exact authority/receipt/provenance | **Reject** fabricated; **Transform** genuine facts |
| selected | portfolio selection | ephemeral view state or explicit manifest input | **Evaluate** persistence |
| portfolioPrivacy | export choice | explicit Export option with preview | **Transform** |
| WorkChunk minutes/description/timestamp/verified | work performed | SessionWork + exact node, duration/notes; no auto verification | **Transform**; **Reject** flag |
| timer seconds/running/target | open Session clock | derive from Session timestamps | **Transform** |
| code tabs/text/output | IDE/test runner | outside Study cockpit by map | **Reject**; **Evaluate** only later integration |
| budget/streak/PID/MEM/branch/cycle | workload/system/motivation | cadence advisory; velocity derived; no invented gamification/process telemetry | **Reject** streak/PID/MEM/cycle; **Transform** workload |


## Action and command mapping

Every mutation must be a real dispatcher command with server-side preconditions, confirmation where required, one audit event, truthful result/refusal, and a fresh re-render. The prototype has no such seam.

| Prototype action | Source behavior | Required v3 action | Disposition |
|---|---|---|---|
| budget 30/45/60/120 | display-only string | explicit policy command, or preferably advisory workload control explaining effect | **Evaluate** |
| omnibar node selection | local filter/selection | URL-addressable finder/deep link into canonical joined view | **Evaluate** accelerator; **Transform** target |
| omnibar quick actions | local navigation/modal | same commands/URLs as visible controls; no hidden privileged mutation | **Transform** |
| `passNode(id)` | any node → `passed`, retention 85 | explicit `pass`; omit impossible action; server checks lock and pass eligibility | **Reject** setter; **Transform** confirmed command |
| `masterNode(id)` | any node → `mastered`; can demote | explicit `master`; server checks passed, later satisfactory Review, spacing; forward-only | **Reject** setter; **Transform** two-step flow |
| combined attestation | one dialog offers both and promises tests/scheduling | separate pass/mastery flows with exact preconditions and consequence | **Reject** combined control/false attestation |
| `submitReviewGrade` | arbitrary percentage/interval/status mutation | Review completion with satisfactory/unsatisfactory + summary; derive memory; no automatic mastery | **Reject** SM-2 mutation; **Transform** Review completion |
| blocker resolution checkboxes | ignored by resolver | optional next actions must be separate explicit commands | **Reject** combined resolver |
| `resolveBlocker` | resolved + silently unblocks Review; CTA claims nodes | explicit `blocker resolve` + summary; edge effects only affect recommendation | **Reject** magical unblock; **Transform** resolver |
| pause/resume/extend | local interval/seconds | read open Session; `work` records effort; extend only if real command exists | **Transform** visibility; **Evaluate** extension |
| edit code / run tests | strings + timeout pass | no IDE/test execution in cockpit | **Reject** |
| add work chunk | local item, `verified: true` | explicit `st work` bound to node, honest duration/notes, no acceptance effect | **Transform**; **Reject** verified flag |
| evidence checkbox/privacy | local state | explicit Export selection; preview included/excluded content and privacy | **Evaluate/Transform** |
| copy simulated CLI | clipboard, sometimes mismatched flags | generate from real command metadata; no fake terminal | **Evaluate** copy only |
| export telemetry/portfolio | toast/copy only | real dispatcher/export command, snapshot-labeled, never read back | **Transform** if retained; **Reject** fake completion/hash |
| simulated `st verify` | canned success | only real gate submission emits exit class + receipt | **Reject** fake verifier |


## Screen-by-screen audit

### 1. Daily Brief

**What it offers.** A morning header; recommended deep-work hero with SkillNode, prerequisite/unlock/contract facts, vector illustration, and Launch Session; an active Blocker summary; six command tiles; due Review list with retention bars and Probe Recall; and recent Evidence stream with View Vault (`src/views/DailyBriefView.tsx:16-367`). This is the prototype's best learner-loop composition: orient, choose, act, handle friction, then inspect proof.

**Portable product ideas.** Transform the brief into Guided-mode Today: one prioritized next action, its honest reasons, current Session state, attention items, and a short evidence/review tail. Preserve the visual hierarchy, not the copy or “morning trajectory” metaphor.

**Transformations and rejections.** Remove hardcoded cycle/week/day, streak, fixed counts, fixed recommendation, “High Unlock Factor,” engine/process language, and pretend “Launch.” Derive recommendation and graph facts. Make every count live. Reviews, Blockers, and evidence link to canonical records. “Resume Active Session” only appears when an open Session exists. The shortcut registry should not be a six-card CLI-flavored section in Guided mode.

**Missing states.** No loading, no recommendations, no open Session, no due Review, no active Blocker, no recent Evidence, partial-data/join error, refusal, and recovery.

**Accessibility.** The vector has no equivalent explanation; status is color-coded; shortcut tiles are clickable `div`s; text is frequently 10–12px monospace; pulse has no reduced-motion treatment.

**Disposition.** **Transform** as Guided entry; **adopt** dense focus + primary action + adjacent queues; **reject** gamification, fake telemetry, and shortcut registry.

### 2. Skill Graph + Node Inspector

**What it offers.** Domain filter, text filter, zoom, legend, fixed-coordinate SVG DAG, selected-path emphasis, node cards, inspector with status/difficulty/retention/description/prerequisites/unlocks/evidence contract, Launch Session, and combined pass/master (`src/views/SkillGraphView.tsx:49-372`).

**Portable product ideas.** The split canvas/inspector, visible relationship context, filters, legend, and adjacent-node navigation are strong Operations concepts.

**Transformations and rejections.** Render relationships from `graph/edges.yaml` only. Use canonical five states and derived readiness. Do not embed `x/y`, relationships, or progress. Make selected SkillNode a real `/nodes/<id>` destination. Recompute layout; keyboard navigation and a non-graph list are required. “Unlocks Next” describes edges, not universal locking. Show pass/master eligibility and separate actions.

**Missing states.** Empty filter, no graph, one node, broken edge, partial join, selected-node missing, loading, and wide/narrow layouts.

**Accessibility.** Nodes/rows are clickable `div`s; SVG lacks title/description and nonvisual structure; color carries state; zoom buttons lack names; no keyboard pan; fixed 1700×850 canvas + 384px inspector breaks narrow windows; motion lacks reduced motion.

**Disposition.** **Transform** for Operations; **adopt** split exploration; **reject** client graph truth, fixed curriculum coordinates, embedded pass/master.

### 3. Active Session

**What it offers.** Session/node/domain/PID/target header; extend/pause/resume; stopwatch/progress; editable Python/JSON/Markdown tabs; fake AST/test console; SessionWork form/list; 3-of-3 evidence checklist; combined pass/master (`src/views/ActiveSessionView.tsx:40-288`).

**Portable product ideas.** Large elapsed-time anchor, clear SessionWork capture, current SkillNode, evidence requirements, Blockers, and safe close form a strong Study cockpit.

**Transformations and rejections.** Per the map, remove source editing and test execution. Show open Session from timestamps, chosen nodes, honest SessionWork, evidence requirements/eligibility, Blockers, and safe close. Timer extension needs a real command or removal. Evidence checkmarks must be derived. Remove PID and “sovereign” language. Add the missing close/end flow.

**Missing states.** No/stale open Session, no node, running/paused, over target, work validation/error/save failure, no requirements, ineligible pass, ineligible mastery, close confirmation/success. Multi-node interleaving is absent.

**Accessibility.** Textarea lacks label; timer has no live semantics; test state is weakly announced; dense 10px copy; checkmarks lack text state; two-column priority needs reflow.

**Disposition.** **Transform** into Study cockpit; **adopt** time/work/requirements hierarchy; **reject** IDE, test runner, PID, fake verification, combined assertion.


### 4. Retention & Reviews

**What it offers.** “SM-2” decay chart, threshold, review queue, per-item challenge/proof, CLI copy, probe interaction, 14-day smoothing grid, and domain health bars (`src/views/RetentionView.tsx:32-326`).

**Portable product ideas.** Review triage, reveal-then-retrieve flow, urgency grouping, domain summaries, and forecast/health inspection are portable Operations capabilities.

**Transformations and rejections.** Use Review status/overdue, Retention confidence, policy threshold, and FSRS-derived suggestions. Review completion requires summary and satisfactory/unsatisfactory. No grade button may alter retention/mastery. Prototype statuses must not shadow canonical states. A Blocker may add remediation pressure but does not make a Review a blocked queue card. Smoothing is advisory and not a stored schedule.

**Missing states.** No Reviews, history only, no suggestion, overdue, due now, blocked prerequisite, no prompt, completion failure, empty domain. `hoveredDay` is set but never rendered (`src/views/RetentionView.tsx:6,270-289`).

**Accessibility.** Decay SVG has no summary/table; status is color-heavy; forecast hover has no focus/output; tiny 9–11px mono copy; “rapid retrieval” is unexplained.

**Disposition.** **Transform** with canonical semantics; **evaluate** retrieval/reveal and density; **reject** SM-2, arbitrary percentages/intervals, blocked-by-Blocker UI.

### 5. Evidence Vault & Portfolio

**What it offers.** Privacy toggle, category tabs, artifact cards with code/notebook/image/formula previews, selection, provenance-like metadata, audit HUD, fake signature, CLI copy, and fake ZIP (`src/views/EvidenceVaultView.tsx:28-312`).

**Portable product ideas.** Evidence inspection, filters, inline preview, immutable history/provenance, selection-driven portfolio, privacy preview, and export are strong capabilities.

**Transformations and rejections.** Map cards to EvidenceRecords, acceptance authority/outcome, gate-run receipt, ArtifactSpec, SkillNode, fingerprints, supersession, and annotations. Evidence never has node states. Do not infer AST/branch coverage/mastery. Selection is not evidence mutation. Real Export previews privacy, generates a real derived snapshot, and is never read back.

**Missing states.** No/rejected/manual/unrunnable/Evidence, superseded chain, correction, missing artifact, changed-artifact warning, private notes, empty selection, export progress/failure, large set.

**Accessibility.** Status relies on color; command tile is not keyboard semantic; signature is unreadable; formula is plain text; image alt is only caption; remote failure unhandled; filter/selection changes not announced.

**Disposition.** **Transform** as capability; **adopt** preview/history/selection; **reject** node-state evidence, fake verification/signatures/export.

### 6. Analytics & Portfolio Telemetry

**What it offers.** Hardcoded KPIs (completion, streak, focused time, Blocker rate), velocity, burndown/projection, deterministic 14-week heatmap, Blocker taxonomy, milestones, fake CSV (`src/views/AnalyticsView.tsx:4-336`).

**Portable product ideas.** A periodic retrospective, completion/work/Blocker/Review/evidence summaries, trends, filters, and export can serve Operations.

**Transformations and rejections.** Replace numbers with derived output plus window/timestamp. No streak/flame, “mastery telemetry,” unsupported taxonomy, scheduled milestones as learner progress, fake confidence cone, or simulated heatmap. Give every chart a table/text summary. Export must be real. Prefer one-theme-at-a-time analytics to this maximal wall.

**Missing states.** No activity, partial window, no evidence/reviews/Blockers, partial layer, export unavailable/failure, insufficient sample.

**Accessibility.** KPIs rely on bars/colors; heatmap cells are mouse-only `div`s with `title`; charts lack summaries; tiny labels; no reduced-motion semantics.

**Disposition.** **Evaluate** restrained retrospective; **transform** metrics to real facts; **reject** fake telemetry, streaks, gamification, React implementation.


## Dialog and global interaction audit

### Attestation modal — **Reject / Transform**

It combines pass and mastery and makes unsupported AST/review-scheduling claims (`src/components/AttestationModal.tsx:35-87`). Replace with two separate dispatcher-backed confirmations. Mastery retains its required second confirmation. Copy shows derived eligibility and exact consequence, not automated acceptance. Add dialog semantics, labelled description, focus trap/return, Escape, and server error recovery. **Reject** combined “Sovereign” concept; **transform** safe confirmation.

### Blocker resolution modal — **Transform**

Failure context, learner explanation, resolution evidence, and synthesis are a strong visual pattern (`src/components/BlockerModal.tsx:59-141`). But checkboxes are ignored, resolution silently changes a Review, and the CTA claims node unlocks. Keep a required resolution summary and optionally linked evidence/history; separate follow-on commands. Never make Blocker resolution an automatic pass/master or evidence acceptance. **Evaluate** whether four panels help when not every Blocker has code diffs.

### Retrieval Probe modal — **Evaluate / Transform**

Prompt → reveal → grade is a useful skeleton (`src/components/CardProbeModal.tsx:58-146`). Keep learner-controlled reveal and result recording only if testing shows value. Replace grades with canonical Review completion and required summary. No fake AST proof or direct memory update. Support keyboard reveal, focus, Escape/cancel, reduced motion, recovery.

### Simulated CLI — **Reject**

The modal accepts handcrafted commands and calls local pass/master setters (`src/components/CliModal.tsx:40-110`). It is neither the real CLI nor dispatcher and creates a second mutation path. Remove it. If command copy helps experts, expose real help/commands as secondary text. It also lacks dialog semantics, focus trap, Escape, and an accessible input label.

### Omnibar — **Evaluate**

Node search and quick navigation are promising accelerators (`src/components/OmnibarModal.tsx:21-130`). Retain only over the same URL destinations. It needs combobox/listbox semantics, active option, arrow/Enter/Escape/Home/End, empty results, focus return, and deterministic ordering. It must never be the only route to a mutation; quick actions show canonical availability and language.

### Toasts, blocker alert, budget, streak, shell

- Toasts last 3.2 seconds and lack live-region/dismissal (`src/context/AppContext.tsx:170-175`): **Transform** into persistent acknowledged notices/errors.
- Pulsing Blocker alert uses color/pulse: **Transform** with text and reduced motion.
- Budget segmented control is local-only: **Evaluate** as an advisory workload preference with stated consequences.
- Streak/flame: **Reject** as invented gamification.
- Avatar: **Reject** as nonessential; remote-only logo: **Evaluate** branding, but package assets locally.

## Visual-system disposition

### Adopt

- **Dark, dense technical foundation:** near-black surfaces, thin borders, restrained shadows, cyan/green accents, and generous internal spacing create a credible workbench (`src/index.css:3-68`; `src/App.tsx:44-52`).
- **Hierarchy through size and surface:** one dominant focal panel, secondary queues, then dense detail.
- **Consistent state colors:** blue action/attention, green verified/complete, amber warning, red blocker/error, provided each state also has text/icon and passes contrast testing.
- **Tabular monospace numerals:** useful for timers, counts, IDs, dates, and measurements; not for all prose.
- **Card and panel rhythm:** bordered containers are effective for dense independent facts.

### Transform

- **Brand voice:** remove military/sovereign/impasse/“engine” posturing. Use the canonical product vocabulary and calm learner-first language.
- **Color tokens:** the prototype hardcodes colors throughout instead of semantic tokens. Define tested semantic tokens with light/high-contrast and non-color cues.
- **Typography:** 9–12px monospace everywhere is too small. Use readable body text, reserve mono for code/IDs, and test zoom to 200%.
- **Motion:** pulses and animated graph glow need `prefers-reduced-motion`, must not be the only urgency cue, and should stop when off-screen.
- **Density:** keep Operations dense, but give Guided mode more whitespace and a single primary action.
- **Icons:** use a small consistent local set; the prototype declares Material Symbols remotely and also depends on Lucide without a coherent rule.
- **Illustrations:** retain only where they teach the selected SkillNode; provide equivalent text and mark decorative SVGs accordingly.
- **Cards:** preserve clickable-card visuals only when the whole card has one action; otherwise use a heading link and separate controls to avoid ambiguous nested targets.

### Reject

- Simulated terminal chrome, PID, memory footprint, branch dirtiness, `SYNC: PASS`, DAG counts, and “healthy engine” decoration in learner UI.
- “Mastery engine,” “sovereign mandate,” “military tech,” streak flames, unlock-factor marketing, and fake cryptographic theater.
- Fixed graph coordinates as curriculum data, fixed progress percentages, and hardcoded “verified” aesthetics.
- Remote fonts/assets as hard requirements for a local-first offline tool.
- A permanent Operations shell in Guided mode. Guided should be task-led; Operations may use the persistent shell.
- React/Vite/Tailwind/Motion/Google GenAI as a v3 requirement. They are replaceable implementation details; ADR 0008 currently grants JavaScript only for chart hover/focus tooltips and requires tier-0 degradation (`docs/adr/0008-inline-progressive-enhancement-posture.md:21-51`). Any broader JS need must return through the architecture decision.


## Accessibility and responsive acceptance gaps

The viewport and some `md/lg` classes do not make the product accessible or narrow-safe. v3 must require:

1. **Structure:** one `main`, meaningful headings, landmarks, skip link, visible focus, and `aria-current`; every destination works without the omnibar.
2. **Dialogs:** semantic name/description, initial focus, trap, Escape, focus return, in-flight guard, and server error/retry. Permanent actions are not dismissed by accidental backdrop click.
3. **Keyboard:** graph nodes/relationships, cards, filters, forecast, heatmap, and clickable `div`s have keyboard equivalents or semantic alternatives; no drag-only operation.
4. **Charts:** concise summary plus accessible table/list of the same real data; tooltips work on focus and hover.
5. **Status:** no color/pulse-only meaning; async success/error uses a live region and errors are not 3.2-second toasts.
6. **Text/zoom:** no essential 9–11px text; 200% zoom and user font scaling; readable line lengths.
7. **Motion:** honor reduced motion; avoid looping pulse/rotation for nonurgent information.
8. **Pointer/touch:** adequate targets; no hover-only detail.
9. **Narrow window:** replace the fixed sidebar/inspecter/1700px canvas and wide grids with deliberate Guided and Operations layouts.
10. **Errors:** loading, empty, partial join, refusal, stale record, save failure, conflict/retry, and server-unavailable states have copy/recovery.

Validate with automated checks plus keyboard-only, screen-reader, zoom, reduced-motion, color-vision, and narrow-window moderated sessions on real fixtures.

## Domain and safety mismatch register

| Severity | Prototype behavior | Why unsafe/inaccurate | Required correction |
|---|---|---|---|
| **Critical** | `passNode` sets any node `passed` without eligibility/lock check (`src/context/AppContext.tsx:237-247`) | passing is explicit and server-guarded; locked is the wall | real `pass`; derived eligibility; truthful refusal |
| **Critical** | `masterNode` sets any node `mastered`; no later Review/day spacing; can demote (`:249-259`) | mastery is distinct; asserted progress is forward-only | separate two-step flow with mastery eligibility |
| **Critical** | Combined pass/master and “sovereign” claims | collapses acts and implies automation | remove; exact preconditions/consequences |
| **Critical** | Blocker resolution changes Review and claims node unlocks (`:298-310`; modal `:122-159`) | Blocker is a record; remediation only reorders | resolve summary; no hidden effects |
| **Critical** | WorkChunk auto-set `verified: true` (`:210-219`) | acceptance is separate/immutable | work never implies verification |
| **Critical** | Node embeds prerequisites/dependents/status | canonical graph/progress sources | derive from engine |
| **Critical** | Review grades mutate retention/status | memory is derived; no automatic mastery | complete Review; separately master later |
| **High** | Hardcoded tests, AST, hashes, ZIP, CSV | false trust claims | real receipts/exports only |
| **High** | Evidence status is node state/privacy | evidence is historical | EvidenceRecord + outcome + export privacy |
| **High** | Simulated terminal calls setters | second mutation path, no event/registry | remove; dispatcher only |
| **High** | Fake analytics/milestones/streaks | unsupported/fabricated; anchors are reference-only | derived facts with windows |
| **High** | Dependents always “Locked,” prereqs “Mastered” | states/edge types vary | canonical state + typed edge |
| **High** | Graph-selected node not carried into Session | can attribute work wrongly | name/display exact node |
| **High** | No errors, persistence, concurrency, events | cannot be a workflow | designed recovery; one event/mutation |
| **Medium** | Editable source implies mutable evidence | EvidenceRecord is immutable | submission freezes; correction supersedes |
| **Medium** | “Unlock factor” recommendation language | no hard-prerequisite override | canonical reasons |
| **Medium** | Remote assets/API key | local-first/offline posture | package assets; no secret to read truth |

Corrections preserve: explicit learner pass/master/delete; no AI acceptance authority; no backward asserted progress; no hard-prerequisite override; immutable EvidenceRecords/Node IDs; and web reads engine, never the reverse.


## Recommended v3 product decomposition

This is an audit disposition, not an implementation-slice decision.

### Guided mode — **adopt/transform**

1. **Today:** one recommended next action, why now, current Session, due Reviews/Blockers/evidence attention, recent proof. Transform Daily Brief; remove operations telemetry.
2. **Study cockpit:** open Session clock, chosen SkillNode(s), SessionWork, evidence requirements/eligibility, Blockers, safe close. Transform Active Session; no IDE/tests.
3. **SkillNode detail:** brief, canonical state, graph context, evidence requirements/records, eligibility, separate start/pass/master, Review history. URL-addressable.
4. **Review/Blocker/Evidence tasks:** real summaries/outcomes and recovery. Do not combine commands.
5. **Session close:** explicit honest end and next step. Add from the domain; absent from prototype.

### Operations mode — **adopt/transform/evaluate**

1. Persistent shell with URL-addressable Graph, Reviews, Evidence, Health, Analytics, Portfolio.
2. Graph plus list/inspector with canonical typed edges, filters, accessible alternatives.
3. Review queue/forecast and memory health using real FSRS-derived facts.
4. Evidence inspection, provenance/history, portfolio selection/privacy, real Export.
5. Health and restrained one-theme analytics with real windows and table equivalents.
6. Omnibar only after base routes; test its expert acceleration.

## Validation questions for later v3 decisions

1. Does one dominant next step improve completion without hiding legitimate alternatives?
2. Can learners understand recommendation reasons and adjust nonblocking workload safely?
3. Does the cockpit make SessionWork capture and close fast enough to complete the loop?
4. Which pass/master confirmations work under real eligibility and refusal?
5. Does retrieval reveal improve Review completion, or should Review remain conventional?
6. Which graph interactions survive keyboard/narrow tests, and which degrade to lists?
7. Do provenance/privacy previews build confidence without overwhelming Guided mode?
8. Which single analytics answer is useful weekly?
9. Does omnibar beat normal navigation/search?
10. Can validated interactions fit tier-0 plus existing chart-tooltip JS? If not, exact evidence triggers a separate architecture decision; React/Vite is not automatic.

## Final classification ledger

### Adopt (12)

1. Dark, dense technical foundation.
2. Consistent bordered panel/card rhythm.
3. One dominant focal action with secondary queues.
4. Split graph/inspector exploration.
5. Visible relationship context on SkillNode detail.
6. Evidence inline preview.
7. Immutable history/provenance visibility.
8. Selection-driven portfolio concept.
9. Review reveal/retrieve skeleton, pending test.
10. Due/urgency grouping.
11. Periodical retrospective capability.
12. Global accelerator concept, pending URL/keyboard validation.

### Transform (24)

1. Daily Brief → Guided Today.
2. Workspace switch → dual-mode URL routes.
3. Recommendation hero → derived recommendation + reasons.
4. Counts/badges → live derived counts.
5. Graph node state → canonical lifecycle/readiness.
6. Embedded relationships → derived GraphEdge view.
7. Graph coordinates → ephemeral layout.
8. Inspector → URL-addressable SkillNode detail.
9. Timer → open Session derived view.
10. Work chunk → SessionWork command.
11. Evidence checklist → requirements/eligibility.
12. Review deck → Review/FSRS view.
13. Reveal/grade → Review outcome + summary.
14. Forecast → derived suggestion/load.
15. Evidence cards → EvidenceRecord + receipts/history.
16. Portfolio privacy → export preview.
17. Analytics wall → one-theme retrospective.
18. Blocker post-mortem → summary + separate follow-ons.
19. Omnibar → accessible secondary accelerator.
20. Toast → persistent status/error.
21. Blocker alert → accessible attention cue.
22. Budget → advisory workload control, if persisted.
23. Visual tokens → semantic tested local theme.
24. Responsive classes → deliberate narrow layouts.

### Evaluate (12)

1. Restricted operation metaphor.
2. Guided density/airiness.
3. Exact Today information order.
4. Timer extension.
5. Review reveal flow.
6. Blocker panels for non-code blockers.
7. Evidence preview depth.
8. Portfolio selection persistence.
9. Graph zoom/pan versus list-first.
10. Omnibar value.
11. Command copy for experts.
12. Analytics themes/export timing.

### Reject (25)

1. React/Vite/Tailwind/Motion as requirements.
2. Google GenAI/AI Studio dependency.
3. Persistent client domain/state model.
4. Simulated CLI mutation parser.
5. Embedded code editor.
6. Embedded test runner.
7. PID/memory/branch/engine telemetry.
8. Streak/flame/gamification.
9. Cycle/week/day trajectory framing.
10. “Sovereign” mastery language.
11. Combined pass/master.
12. Direct pass without eligibility.
13. Direct master without later Review.
14. Backward-capable setter.
15. Blocker-caused node unlock.
16. Blocker resolution changing Reviews.
17. Auto-verified SessionWork.
18. SM-2 math/grade vocabulary.
19. Stored/arbitrary retention percentages.
20. Evidence node-state labels.
21. Fabricated verification/signatures/hashes.
22. Fake portfolio ZIP/CSV completion.
23. Fake velocity/confidence projections.
24. Hardcoded coordinates/relationships in view data.
25. Remote-only fonts/logo/image requirements.
