# Spec — v2.4 Preference-driven, de-CLI-flavoured interface sublayer (hand-off)

**Status:** locked hand-off (map [#208](https://github.com/earledotpy/skilltrace/issues/208)) — no open product, architecture, or UX question blocks the v2.4 build of `src/skilltrace/web/interface/`.
**Target:** `v2.4`, slot 4 of [`docs/POST_V2_ROADMAP.md`](../POST_V2_ROADMAP.md); the rewritten slot row lands in the same change (G-Slot [#226](https://github.com/earledotpy/skilltrace/issues/226)).
**Map:** [#208 Map — v2.4 interface direction (research, audit, prototypes, ADR 0007 amendment)](https://github.com/earledotpy/skilltrace/issues/208).
**Decisions:** [G-Preferences #219](https://github.com/earledotpy/skilltrace/issues/219) · [G-RouteSurface #220](https://github.com/earledotpy/skilltrace/issues/220) · [G-Direction #224](https://github.com/earledotpy/skilltrace/issues/224) · [G-JS #225](https://github.com/earledotpy/skilltrace/issues/225) · [G-Slot #226](https://github.com/earledotpy/skilltrace/issues/226) · [G-MentorVoice #229](https://github.com/earledotpy/skilltrace/issues/229) · the seven audits [A-Today #209](https://github.com/earledotpy/skilltrace/issues/209) · [A-Next #210](https://github.com/earledotpy/skilltrace/issues/210) · [A-Node #211](https://github.com/earledotpy/skilltrace/issues/211) · [A-Health #212](https://github.com/earledotpy/skilltrace/issues/212) · [A-Analytics #213](https://github.com/earledotpy/skilltrace/issues/213) · [A-Modals #214](https://github.com/earledotpy/skilltrace/issues/214) · [A-Chrome #215](https://github.com/earledotpy/skilltrace/issues/215). ADR 0007 (amended), ADR 0006, `docs/spec-tier1-serve.md` §B/§C/§L-bis.
**Prototype (throwaway):** `prototype/p24-evolve.html` (P1 base + palette), `prototype/p24-radical.html` (the winning Today shape + verbs), `prototype/p24-reconsider.html` (the two borrows). None ships; the engine never reads them.
**Build plan:** 5 `wayfinder:task` slices — S1 Interface seam → S2 Sublayer scaffold + chrome → S3 Today card-stack → S4 Next / node / finder → S5 Health / analytics / safety panels — in §I, the #62 five-slice pattern.

> **Hand-off gate (map `Destination`, the #62 standard):** a builder can implement `src/skilltrace/web/interface/` without reopening a product, architecture, or UX question. All terms per `CONTEXT.md`; §C's route table is normative and already landed in `docs/spec-tier1-serve.md`.

---
## A. The design direction (G-Direction #224)

The v2.4 direction is **owner-decided** and locked here in full. It is a **hybrid**:

- **Base architecture — and every surface except Today — is P1-Evolve** (the current dashboard language, tightened): single column, airy, de-CLI-flavoured, **tier-0 zero JS**. Shell, nav, node detail, `/next`, the health roll-up, `/analytics`, the finder, the error shell and the pass/master panels all keep P1's shape. This is the direction a builder can implement without a single open UX question.
- **Today's shape is P3-Radical's card-stack:** the focus card *is* the page; queue and pressure recede behind the `/next` stop rather than competing on the home. Today renders **three card-level blocks** (≤ 4 per P5.3):

  1. **the focus card** — title, state + plain-language reason, one-line brief, the single primary CTA;
  2. **the count set** — items ready / reviews waiting / days practiced, as labeled counts plus one muted pointer (the raw backlog never renders; zero-count pills dropped);
  3. **the resumable-active line** — only while a session is open.

  That is ≤ 4 card-level blocks, exactly one primary CTA, zero tables, and no `<details>` on the primary path (P5.3) — against the live `/today` baseline of 7 competing blocks with the focus named up to 4×.

- **From P3, also adopted:** the **grouped action verbs** as affordance labels, derived from the locked `NextAction` intent set `start | submit_evidence | pass | schedule_review | explore` (G-MentorVoice #229); and the **title-first finder** stays where G-RouteSurface #220 put it — the nav field plus `/nodes/jump` — *not* a promoted primary navigator.
- **Enrichment from P2-Reconsider — both borrows adopted, as enrichment, never as a re-spine:**

  - the **pathway summaries + current-spine abstraction** ride on node detail and `/next` (a "where you are in the sequence" layer), never on the home IA;
  - the **derived week view** is an `/analytics` candidate (spec-future — not a v2.4 build slice; see §I scheduling note).

**Ruled out (recorded, never to be silently resurrected):** P2's spines as home IA; P3's palette-first canvas as primary navigator; P3's all-receded home including Health (probed and declined — G-RouteSurface #220's header calm line stands); P1's rail / 1040px-daily-loop layout / any bento; and the master purple `#7c3aed`.

### Today's focus CTA — the pronoun form

Today's focus CTA takes the **pronoun form**, settling P1.1's `Start <title>` wording in favour of a friendly first-person affordance (G-Direction #224); the intent→affordance label for `start` is `Continue <title>` / `Start this session` (see §E) and the full-title form is unchanged everywhere else on the route surface.

### Days practiced — the locked record window (fog graduated here)

The map's `Not yet specified` item — the exact **record window** for the days-practiced derivation — is decided here and locked:

> **A *practiced day* is a distinct calendar day on which the learner logged study work — i.e. a day with at least one session started (`sessions.started_at`) **or** at least one work item logged (`work.created_at`). Evidence submissions alone do **not** count.** The union of the two sources, deduplicated by day; no new engine data, no schema change (per P1.7 and `CONTEXT.md` — *Days practiced*). Evidence-only days are deliberately excluded: evidence submission is a product of study, not study work itself, and P1.7 scopes the count to "days with logged *work*".

Placement and honesty are already locked: one quiet line inside Today's P1.2 count set (G-Direction #224), plus a quiet factual line at session close (P1.7). A mirror, never a metronome — the count never appears in a refusal, a pressure bit, a ranking, or eligibility (`CONTEXT.md` — *Days practiced*).

---
## B. Palette, type, spacing tokens (G-Direction #224)

**Palette — cream + terracotta.** The canonical nine tokens, all in `:root`, hexes **only** there (P5.4):

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#fbf7f0` | page background (cream) |
| `--fg` | `#2b2622` | primary text |
| `--muted` | `#7a6f63` | secondary text (`--mut` → `--muted`) |
| `--border` | `#ece2d3` | hairlines |
| `--accent` | `#b0562c` | one accent (terracotta) |
| `--warn` | `#faf0d7` | warning / master step 1 |
| `--err` | `#f6ded4` | error / master step 2 (permanent) |
| `--ok` | `#e7f3ec` | pass / success |
| `--advisory` | `#e7eef5` | advisory |

Plus the private supporting set `--card` / `--pill` / `--accent-ink` / `--accent-soft` / `--*-ink`. **One accent**; muted semantics for exactly the five node states plus attention/warn/err; alias classes collapse to one name each (`warn`, `err`); dead CSS removed (`header h1`/`.sub`, the four `900px` breakpoints under desktop-only). Light-first; dark mode stays out of scope (P5.4).

**Type scale.** Base `16px` humanist, line-height ~`1.55`; a display heading at ~**2× base (32px)** used on **Today's opening question only** (P5.1); steps `24 / 14 / 13.5`px; prose measure **70ch** (the 65–75 band per P5.2).

**Spacing.** Card padding band `24–32px`; section gap `40px` (the 32–48 band) > intra-card gap `14px` (the 12–16 band) — **section gap > intra-card gap** is the locked invariant (P5.2). Today density cap per P5.3.

**Radius.** `14 / 11 / 999`px.

**Font-role split.** serif for prose, sans for chrome, mono used **once** (for the one permitted raw identifier on node detail — §E).

**Shell.** 1040px with a **720px daily-loop column** and **one 960px breakpoint** (desktop-only; P5.5 decided here by G-Direction).

**Modal treatment.** The refined **page-level safety panel** — a bordered panel rendered inside the one nav-carrying shell (server-fresh, 303+flash-only writes, **no overlay**): routine `pass` confirm → `--accent` border; master **step 1** (facts) → `--warn` border; master **step 2** (permanent) → `--err` border, two-step structure preserved (P4.4); panel padding at the locked card band; no `<dialog>`, no popover, no backdrop.

---
## C. The locked preference table (G-Preferences #219)

The **33 rows** below are the locked content a builder renders; the authoritative wording lives in G-Preferences #219's resolution comment. Each row carries its apply/reject/defer verdict and binding (`spec` = must-list and acceptance gate; `prototype` = scoreable criterion, already exercised; `downstream` = decided in a named receiver). Rows deferred here are **not** built.

**Group 1 — Daily-loop behaviour (P1.1–P1.10):**

| # | Decision (locked wording) | Verdict | Binding |
|---|---|---|---|
| P1.1 | **One focus, one action.** Exactly one primary CTA per view; the focus is named **once**. Today renders a single focus card that *contains* its own CTA — title, one human line of why, and `Start <title>` / `Continue <title>` (label tracks whether a session is open) inside the card. The separate focus bar and the separate start-confirm card are **removed**. | **Apply** (option a) | `spec` |
| P1.2 | **Bounded day.** Beyond the focus, Today may carry a small labeled count set (reviews due, open blockers, in-progress) plus **one** muted pointer — "N more ready when you are" — linking to `/next`. The raw backlog never renders on Today. | **Apply** (option b) | `spec` |
| P1.3 | **Zero-count pills are dropped**, not rendered ("0 reviews" is noise, not information). | **Apply** | `spec` |
| P1.4 | **Overdue is resumable, never shaming.** Longest-waiting first; copy says "start back where you left". No growing shame counter; missed days never framed as the learner's failure. | **Apply** | `spec` |
| P1.5 | **Factual celebration at real events only** (evidence accepted, node passed, review batch cleared, session closed) + a **CSS-only** keyframe at pass/master — zero JS, zero dependency. | **Apply** (option a) | `spec` (content) + `prototype` (treatment) |
| P1.6 | **Celebration copy is past-tense and factual.** Never comparative, never predictive: no "you're ahead of 90%", no "your memory is 95%". **Nothing** fires per click. | **Apply** | `spec` |
| P1.7 | **Days practiced** — a derived count of distinct days with logged work, shown as one honest line on Today inside the P1.2 count set, plus a quiet factual line at session close. Derivable from existing `sessions.started_at` / work `created_at` records; **no schema change**. No target, no countdown, no freeze, no loss framing, no "don't break it". A missed day is simply **absent**, never a break. It never appears in a refusal, a pressure bit, a ranking, or eligibility — a mirror, not a metronome. Counts days with logged *work*, never openings or clicks. | **Apply** (option a) | `spec` (content) + `prototype` (placement) |
| P1.8 | **Pre-session planning prompt** ("when will you work on this, and what will you produce?"). Strong evidence (implementation intentions, d≈0.65) but needs a new stored field on session-open — new engine data, out of this map. | **Defer** | trigger: the practice-profiles slot, or evidence that learners open sessions without clear intent |
| P1.9 | **A web review loop** (retrieval-first, keyboard-first, outcome/interval preview, failure framed as a scheduling event). The web has **no** review-completion flow at all today — `review complete` is CLI-only, so there is no surface to prefer. | **Defer** | trigger: any slot that adds a review write flow to the web |
| P1.10 | **Pressure attaches to memory, never to a broken run.** "3 reviews are waiting — forgetting is expected", never "you missed 4 days". | **Apply** (the honest residue of the streak pattern) | `spec` |

**Group 2 — Information hierarchy & density (P2.1–P2.8):**

| # | Decision (locked wording) | Verdict | Binding |
|---|---|---|---|
| P2.1 | **Two density registers.** An *airy daily register* (`/today`, `/next`, node brief) and a *dense diagnostics register* (`/health` detail, `/analytics` tables, node drill-down). Same tokens, different density band. Tables are legitimate — in the register that earns them. | **Apply** | `spec` |
| P2.2 | **Analytics: one theme at a time** behind a segmented control (default = most recent activity), tables **collapsed** by default, and **pseudo-sparklines cut** — only real multi-point trends render. Today three of the four "sparklines" are single bars. | **Apply** (option a) | `spec` (density) + `prototype` (control shape); *mechanism* → `downstream` G-RouteSurface |
| P2.3 | **Health goes ambient.** Chrome carries **one** calm line when everything is fine ("Everything looks good") and an **attention pill with a count** when not, linking to detail on demand. Layer names become human labels or hide behind detail. Today's rail health card is **dropped** (health currently renders 3×). Warnings now flip state. | **Apply** (option a) | `spec` |
| P2.4 | **Per-layer warning counts stop being dropped from the web** — the CLI shows them, the web silently discards them. | **Apply** | `spec` |
| P2.5 | **Node detail is brief-first**: title, state, one-line why, resources, next human action. Artifact specs, gate-run receipts, evidence history and drill-down facts sit **one click deep**. The triple-redundant pass requirements (brief / How-to-proceed / drill-down) are stated **once**. Guard: the *next human action* must never be behind a disclosure. | **Apply** | `spec` |
| P2.6 | **A no-op evidence form (no spec, no gate) is omitted, not captioned** — see P4.2. | **Apply** | `spec` |
| P2.7 | **"Why this?" reframed** on `/next`: one human sentence on the card ("You're mid-node, and it unlocks X") plus an optional disclosure with human-labeled reasons. Never factor names, never the engine boundary disclaimer verbatim. | **Apply** (option a) | `spec` |
| P2.8 | **The web never silently drops an advisory the CLI shows** (`NextModel.warnings`, per-theme Mentor summaries, per-layer warning counts). A dropped advisory is a content gap, not a copy gap. | **Apply** | `spec` |
**Group 3 — De-CLI-flavouring + copy standards (P3.1–P3.6):**

| # | Decision (locked wording) | Verdict | Binding |
|---|---|---|---|
| P3.1 | **Forbidden-vocabulary rule**, enforced by **one translation module** no surface may bypass (the single-redaction-module shape already used by the share profile). Never in user-facing web copy: command names (`skilltrace …`), flags (`--notes`, `--format`), exit codes/classes, ADR numbers, raw record ids (spec/session/review), file paths, engine layer nouns as labels, `[advisory]` tags, engine-voice phrases ("the domain refuses", "same guarded writer as the CLI", "Verbatim CLI fields"). | **Apply** | `spec` |
| P3.2 | **Titles everywhere** in prose, nav, breadcrumbs, link labels and confirmation copy. The node id may appear **only** as small muted secondary text on the node detail page, and as the example inside the jump field's placeholder — never in prose, link labels, breadcrumbs, flash banners, or confirmation copy. | **Apply** (allowance confirmed) | `spec` |
| P3.3 | **Shared Mentor seam re-opened, narrowly.** The seam emits **structured next-action facts** (command + node + intent) alongside human copy, and **each surface renders its own affordance**: the CLI keeps printing the command line (you type it), the web renders a button. The CLI's *voice* is unchanged; only the seam's data shape and the web's presentation change. Web-side-only translation was rejected: reverse-engineering human copy out of prose strings, or duplicating derivations, is the exact drift ADR 0002 cut the interface layer for. | **Apply** (option b + expansion) | `spec` + map fence amendment + **G-MentorVoice** |
| P3.4 | **The five canonical state words stay visible**: `locked / available / active / passed / mastered`, always paired with a plain-language reason line ("locked — needs *Data cleaning* first"). No UI synonyms ("Ready", "In progress") — they would fork the glossary and make every future doc, spec and ticket ambiguous. Engine *nouns* around them remain banned by P3.1. `locked` is never softened into something implying choice. | **Apply** | `spec` |
| P3.5 | **Flash + refusal copy standard.** Every post-write banner and every refusal is translated human copy that (i) states what changed in plain words, (ii) names side effects ("reviews scheduled for 3, 10, 30 days"), (iii) for refusals, names the missing requirement truthfully and never pre-judges, (iv) carries no flags, exit classes or command names, (v) points operational failures at `/health`, not `skilltrace validate`. Refusal truthfulness is non-negotiable: friction as clarity, never as a maze. | **Apply** | `spec`; *flash-in-URL carry* → `downstream` G-JS |
| P3.6 | **The ALL-CAPS `.kicker` register is killed** (`DO THIS NEXT`, `DRILL-DOWN — READ-ONLY FACTS`, `START HERE — TODAY'S TOP PICK (LIGHTWEIGHT CONFIRM)`) — replaced by sentence-case small headings everywhere; the dense register uses table headers. Uppercase letterspaced kickers are how the page shouts engine section labels; P5.1's scale already supplies the replacement. | **Apply** (option a) | `spec` |

---
**Group 4 — Safety confirmations (P4.1–P4.4):**

| # | Decision (locked wording) | Verdict | Binding |
|---|---|---|---|
| P4.1 | **The ADR 0007 × G2 collision resolved by splitting structural from judgment.** **Omit** actions that can never succeed for *structural* reasons — pass/master on a `locked` node, the evidence form on a node with no spec and no gate. Keep **live-with-advisory-text** for eligibility that fresh per-request data can change. The wall is still **shown**: the node renders with its unmet prerequisites (G2's "locked rendered, never hidden" survives intact). ADR 0007 is amended to record the split. | **Apply** (option b) | `spec` + map fence amendment + amendment input to G-RouteSurface |
| P4.2 | Rationale recorded: G2's "never pre-disable" existed because *stale derived* data lies; ADR 0007's omission is computed **fresh per request**, so structural omission doesn't lie — and an evidence form that can never submit is furniture, not an offer. Judgment calls stay live because the domain's refusal on click is the only always-truthful answer. | **Apply** | `spec` |
| P4.3 | **Friction only at acceptance moments** (pass / master). Start, work-log, blocker and evidence-submit stay **single-step with zero added friction**. Deliberate friction at acceptance is warranted by the safety rules and honest communication, not by learning science; friction *inside* the loop is an anti-pattern. | **Apply** | `spec` |
| P4.4 | **Master stays two-step** (friction scales with irreversibility). Step 1 shows the mastery facts; its Continue is **omitted** when the node is structurally walled (`locked`, or not `passed`) and stays **live with advisory text** when eligibility is a judgment. Step 2 **re-renders the node and facts freshly** and states permanence in plain words ("Mastered never moves backward — this is permanent") plus what was reviewed. No new gating, same guarded writer, one event. Merging to one screen was rejected: it trades a real safety ritual for one less click. | **Apply** (option a) | `spec` |

---
**Group 5 — Visual-direction constraints (P5.1–P5.5):**

| # | Decision (locked wording) | Verdict | Binding |
|---|---|---|---|
| P5.1 | **Type scale**: base `14px/1.5` → **16px humanist, ~1.55**; a display heading at **~2× base**, used on Today's opening question **only**. | **Apply** | `spec` (scale) + `prototype` (display-heading treatment) |
| P5.2 | **Spacing band**: card padding **24–32px** (from 14px); **section gap 32–48px > intra-card gap 12–16px**; prose measure **65–75ch**. | **Apply** | `prototype` (numbers) + `spec` ("section gap > intra-card gap") |
| P5.3 | **Today density cap**: **≤4 card-level blocks, one primary CTA, zero tables, no `<details>` on the primary path.** | **Apply** | `spec` ("no tables on daily surfaces") + `prototype` (the cap) |
| P5.4 | **Palette fully tokenised**: no hex literals outside `:root`; **one accent**; muted semantic colours for exactly the five node states plus attention/warn/err; alias classes collapsed to one name each (`warn`, `err`); dead CSS removed (`header h1`/`.sub`, the four `900px` breakpoints under desktop-only). Light-first; dark mode stays out of scope — full tokenisation is what makes it a cheap token swap later instead of a redesign. | **Apply** | `spec` |
| P5.5 | **Hue, shell width, rail, breakpoints, bento-vs-single-column, modal treatment** are **not** decided here. | — | `downstream` G-Direction + prototype briefs |

---
## D. Route surface & interaction posture (G-RouteSurface #220 · G-JS #225)

### D1. Route surface — **restructurable downward only**

The route decision (G-RouteSurface #220) is **downward-only**: views may be **merged, folded, re-placed, de-nav-ed, or retired** where one audit verdict *and* one locked preference row both warrant it; **no new top-level view** is added in v2.4. **Paths are frozen verbatim** — `/` stays Today (no `/today` alias), `/nodes/<id>` stays plural; the path is engine vocabulary, while P3.2's ban on machine vocabulary governs prose, labels and breadcrumbs — not the address.

The **normative route table lives in `docs/spec-tier1-serve.md` §C**, not in this spec (ADR vs normative table split). §C already landed on `main` (commit `8d6ae8d`, PR for #220) and a builder implements against it. For convenience, the v2.4-relevant shape is reproduced here:

- **GET views (9):** `/` `today`; `/next` `next`; `/nodes/jump` `finder`; `/nodes/{id}` `node`; the three acceptance steps `/nodes/{id}/pass` `pass-step`, `/nodes/{id}/master` `master-step`, `/nodes/{id}/master/confirm` `master-confirm`; `/health` `health`; `/analytics` `analytics`. A view's identity is its **screen name**, never its path — the active-view marker derives from the seam, not URL string-matching (ADR 0007 Vocabulary).
- **POST routes (9):** `/work`; `/session/close`; `/analytics/export`; `/nodes/{id}/start`; `/nodes/{id}/pass` (**hard boundary, never automatable**); `/nodes/{id}/master/confirm` (**hard boundary, never automatable**); `/nodes/{id}/blockers`; `/blockers/{id}/resolve`; `/nodes/{id}/evidence`. Anything else → 404 with full chrome via the shared error body.
- **Response contract:** every POST → `303 See Other` + flash notice, refusals included; **no 4xx ever leaves a write**.
- **Deliberate non-routes (recorded with warrants, §C):** `--state` filtering on the web (the `show-locked` half is expressed as a "Not ready yet — and why" card, never a flag); `/reviews` (deferred P1.9 — re-opens when a slot adds a review write flow); graph/dependency view (no verdict + no preference row; graph-viz tech already out of scope); `/today` alias (closed, never).

**Health & Analytics as nav stops (decided in #220):** Health is **de-nav-ed** to the header pill strip + `Full roll-up →`; Analytics sits in a **separated periodic nav group** with a one-theme `theme=` param reusing the `{all, velocity, blockers, reviews, evidence}` export vocabulary (no new vocabulary, no JS); the page chrome carries **two nav groups** and **nothing is marked current on node pages**; `aria-current` + the visible marker are sourced from the seam (ADR 0007 active-view), never string-matched.

### D2. Interaction posture — **tier 0, JavaScript budget = 0** (G-JS #225)

Locked: **no inline script, no fetch-swap partial refresh, no `<dialog>` confirms, no keyboard shortcuts, no command palette, no optimistic UI.** Every adopted interaction is reachable with HTML and CSS alone (native `<details>` sit off the primary path; the finder is server-rendered; the week view navigates by query-param links). **No ADR 0008** — 0008 stays reserved-and-unused, ADR 0006 stands unamended. The interface sublayer **emits no `<script>`** — a **grep-able, testable gate** that is part of v2.4's acceptance; it can only be lifted by an evidence packet (a named adopted-path interaction, demonstrably failing at tier 0, prototyped with the exact JS it needs — G-JS #225 §7).

**Charts — the static form only:** server-rendered inline SVG through the existing `analytics/sparkline.py` seam, **real multi-point series only** (P2.2 bans pseudo-sparklines); nothing interactive (no hover/tooltip/zoom/axes at scale — R3's tier-2 wall, off the daily loop's critical path). The deferred days-practiced **heatmap is refused**, three times over (P1.7; `CONTEXT.md` *Days practiced*; a density grid is a streak/loss mechanic) — it returns only as a fresh effort that re-opens the preference table.

**Flash-in-URL carry — kept (tier-0 posture).** `notice`/`kind` stay in the query string exactly as §C ratified them (names unchanged — the URL is not a design surface). Two hard rules: (1) **the URL is a copy surface, so P3.5 covers it** — every carried notice is already short human copy (no flags, command names, exit classes, paths, record ids or ADR numbers; today's notices are verbatim CLI stdout — the P3.5 translation module is the fix, and the address bar sits inside its remit); (2) **no URL-level redaction, ever** — copy is fixed at its source by the one translation module (P3.1), never stripped at the address bar. Idempotence from the 303 contract: a bare GET re-renders the same banner and never re-submits the write. **Dismissal** is a plain link to the current path without the query string (mechanism locked; wording per P3.5).

---
## E. Card vocabulary — the v2.4 evolution (fog graduated here)

G-Direction #224 handed G-Spec the card-vocabulary fog. It is written as a **spec rule, not a second ADR 0007 amendment** — this is a rendering rule (the architecture amendment already landed with G-RouteSurface #220), decided at G-Direction's recommendation and locked here:

**The Richer Card (spec rule).** Within ADR 0007's four objects — View, Card, Command, Active-view-state — a rendered **Card** carries at minimum `{state, title, one-line why, resources, one next action, optional disclosure}`. Compared against ADR 0007's Card fields, v2.4 adds the **one-line why** and the **optional disclosure** as first-class fields and requires the **next action** to be expressed as an **intent + affordance**, never as a raw command string.

**Affordance rule (P3.3 + G-MentorVoice #229, normative).** A Card **must never carry a command string as its affordance**. ADR 0007's `command-binding` survives as the **write path** (the POST target) and is **never rendered** — the intent's affordance label renders instead. The locked `NextAction` fact shape (no prose):

- `intent` — closed Literal set **`start | submit_evidence | pass | schedule_review | explore`**; grows only by editing the contract, never by string-typing;
- `node_id: str | None` — the node the action binds to;
- `command: str | None` — the CLI command; present only when the intent has one, **never rendered by the web**;
- `eligible: bool | None` — the pass-case eligibility judgment, the only affordance-selection input the renderer needs.

**Intent→affordance (normative for the sublayer and the prototypes):** `pass` → the `/nodes/{id}/pass` acceptance step; `master` → the existing two-step per P4.4; `start` / `submit_evidence` / `schedule_review` → a sublayer button as command-binding routes land (ADR 0007's downward-only route gate). **On the live Tier 1 web today, where no route exists: render the human copy only** — no button to nowhere, no command name. Affordance labels: `Continue <title>` / `Start this session` (Today's focus takes the pronoun form, §A), `Submit your next piece of evidence`, `Mark <title> passed`, `Schedule a review`, `Explore what this unlocks`.

**Absent fact = no affordance** (P4.1): a structurally impossible action is omitted, not rendered-then-refused; judgment eligibility renders live with advisory text. The web **never reverse-engineers prose strings** and never re-derives which action is possible — it reads the facts (the ADR 0002 lesson).

---

## F. Confirmation-copy standards for safety modals (A-Modals #214 evidence base)

The live mutation surface is *architecturally* sound (every action nest-dispatches the canonical registry command with `source="web"`, appends one audit event, pass/master behind confirmation; no hard-boundary violation). The change is *copy and visibility*, per the locked rows and the modal treatment in §B. The standards a builder renders:

- **The confirmation-copy shape** (A-Modals newly-surfaced #2, now locked): state the **state change** in plain words ("Mark as passed" / "Mark as mastered — permanent"), its **reversibility**, its **side effects**, and **no engine internals** (no "same guarded writer as the CLI", no "nest-dispatch", no raw spec ids — render the spec by its human title). Keep the honest consequences line (e.g. "reviews scheduled for 3, 10, 30 days"); drop all engine/CLI-speak chrome.
- **Friction only at acceptance** (P4.3): pass renders the page-level safety panel; start, work-log, blocker, evidence-submit and session-close stay **single-step, zero added friction**. Blocker-create/resolve are currently correct — **keep**.
- **Pass panel:** `--accent` border; server-fresh facts; eligibility renders as advisory text beside the action (judgment), not a pre-disabled state; the one honest consequence line; domain refusal on click is truth (P3.5).
- **Master two-step** (P4.4): step 1 (facts) `--warn` border, Continue **omitted** on a structural wall, live-with-advisory-text otherwise; step 2 (permanent) `--err` border, **re-renders node + facts freshly**, permanence in the locked plain words. Continue's live-when-ineligible defect (A-Modals newly-surfaced #3) is fixed by the P4.1 omission rule.
- **Evidence no-op form** (P2.6): a node with no spec and no gate renders **no** evidence form at all — omitted, not captioned.
- **No overlay** (§B, G-Direction #224): the panel is a bordered element inside the one nav-carrying shell; no `<dialog>`, no popover, no backdrop (the overlay is the one interaction that would drag JS into the acceptance path).

---
## G. De-CLI-flavour copy standards (P3.1–P3.6, consolidated)

The de-CLI standard is the map's core complaint, made normative:

- **One translation module (P3.1).** Every user-facing web string passes through it; **no surface may bypass it**. The forbidden vocabulary list: command names (`skilltrace …`), flags (`--notes`, `--format`), exit codes/classes, ADR numbers, raw record ids (spec/session/review), file paths, engine layer nouns as labels, `[advisory]` tags, engine-voice phrases. The address bar is inside its remit too (D2).
- **Titles everywhere (P3.2).** Prose, nav, breadcrumbs, link labels and confirmation copy always use the node's human title. The node id appears **only** as small muted secondary text on the node detail page and as the example inside the jump field's placeholder.
- **Sentence-case headings, no ALL-CAPS kickers (P3.6).** `DO THIS NEXT`, `DRILL-DOWN — READ-ONLY FACTS`, `START HERE — TODAY'S TOP PICK` are all replaced by sentence-case small headings; the dense register uses table headers.
- **Canonical state words stay (P3.4).** `locked / available / active / passed / mastered`, each paired with a plain-language reason line; no UI synonyms; `locked` is never softened into implying choice.
- **Flash + refusal standard (P3.5).** Every banner/refusal is translated, human copy that names what changed and any side effects, and for refusals names the missing requirement truthfully; operational failures point at `/health`, not `skilltrace validate`. Refusal is clarity, never a maze; the web never silently drops an advisory the CLI shows (P2.8).
- **Why-this reframed (P2.7).** One human sentence on the `/next` card plus an optional disclosure with human-labelled reasons; never factor names, never the engine-boundary disclaimer verbatim.
- **Today's copy honesty (P1.4, P1.5, P1.6, P1.7).** Overdue is resumable, never shaming; celebration is past-tense and factual, only at real events, nothing per click; the days-practiced line is a mirror, never a metronome.

**The seam, restated (P3.3 + G-MentorVoice #229).** The shared Mentor seam emits structured next-action facts (§E) alongside human copy; the CLI's voice (its five sections, register, printed command lines) is **unchanged and out of scope**; the web re-composes the same facts with its own presentation. The `CONTEXT.md` *Mentor* entry already records the canonical headings as the CLI's presentation (landed `f1e9c59`); `Next-action fact` is already in the glossary.

---
## H. Audit-verdict summary (per surface — keep / change)

One ticket per view surface walked the live page + code (not the stale v1.4 spec), with CLI parity as reference only. Every verdict was absorbed into the locked preference rows and §A–§G above; this is the summary a builder references when re-checking a surface:

| Surface (audit) | Headline verdict | Concrete change now locked |
|---|---|---|
| Today / `/today` (A-Today #209) | **change** — the daily-loop card-stack replaces the live 7-block board | P1.1 single focus card that contains the one CTA; P1.2 bounded count set; code-factored focus/start-confirm merged; raw "Node id" work field replaced by a friendly chooser (flagged dependency, composes dispatcher output only); Mentor `today` prose no longer the flavour source (§G seam). |
| Next / `/next` (A-Next #210) | **change** — the four sharp de-CLI artefacts die | DO-THIS-NEXT command lines → grouped-action-verb affordances (§E); filter gloss removed (minutes/limit are honest sliders, the flag names are not); "Why this?" reframed, ranker internals hidden (P2.7); show-locked ID dump → "Not ready yet — and why" card; zero-rec empty state redesigned; candidate titles become links (nav). |
| Node / `/nodes/{id}` (A-Node #211) | **change** — brief-first, state-aware | P2.5 brief-first; pass requirements stated once; P2.6 no-op evidence form omitted; the attention state + disclosure one click deep; the spine path summaries ride here (§A). |
| Health / `/health` (A-Health #212) | **change** — de-nav-ed to the ambient line, detail on demand | P2.3 ambient headline plus attention pill; P2.4 per-layer warning counts restored; Today's rail health card dropped; `--state` stays CLI-only (recorded non-route). |
| Analytics / `/analytics` (A-Analytics #213) | **change** — a periodic retrospective stop, one theme at a time | P2.2 `theme=` segmented control on the `{all, velocity, blockers, reviews, evidence}` vocabulary; tables collapsed; pseudo-sparklines cut; real multi-point SVG only (D2); separated periodic nav group; week view = future candidate. |
| Modals / POST flows (A-Modals #214) | **change (architecturally sound)** — copy + visibility only | §F confirmation-copy standard; P4.1 structural omission (master step-1 Continue omitted on a wall; step-2 re-checks); page-level safety panel, no overlay; refusals translated (P3.5). |
| Chrome / shell (A-Chrome #215) | **change** — brand, wayfinding, token hygiene | header mark + brand; two nav groups with seam-sourced `aria-current`; health pill strip; one unified full-chrome error body (404/500 non-routes share it); palette fully tokenised (P5.4); dead CSS removed. |

**Filed outside the map (spec must-fix):** the audits' one live defect — [/node graph-edge links 404 #228](https://github.com/earledotpy/skilltrace/issues/228) (hrefs built from titles while the route resolves by id) — is a standalone `bug`, named as a must-fix in build slice S4 (see §I).

---
## I. Build-slice plan — 5 `wayfinder:task` slices, the #62 five-slice pattern

The hand-off ships the spec and the locked decisions; the follow-on build effort (beyond this map's destination) opens the slices as `wayfinder:task` children, wired S1 → S2 → S3 → S4 → S5 so the frontier is **S1 only**. Each slice is stdlib-only unless a new dependency is explicitly decided (none is in v2.4); hard boundaries are carried verbatim; `pytest` green at every gate.

| # | Slice | Scope (locked) | Per-slice acceptance (unlocks the next slice) |
|---|---|---|---|
| **S1** | Interface seam (engine side) | The Richer-Card derivative + the `NextAction` typed part on the canonical `MentorCard` (colocated with the state dispatch in `mentor/prose.py`, fed by `prose.py`'s per-state branches and `today.py::_focus_action`'s single producer); the days-practiced derivation (`sessions.started_at` ∪ `work.created_at`, deduplicated by distinct day; the §A window); `render.cards_to_lines` byte-identical CLI lines + the web affordance mapping in `views.render_cards`; a forbidden-vocabulary translation module no surface may bypass (P3.1). | CLI output byte-identical; `render.py` non-retrofit rule honored (the other "Do this next" producers — `next`, `suggest`, `report` — migrate here when S2–S5 touch them, never before); days-practiced counts the locked window, never openings/clicks; no surface bypasses the translation module; `pytest` green. |
| **S2** | Sublayer scaffold + chrome | `src/skilltrace/web/interface/` — View / Card / Command / Active-view-state objects over the live dispatcher registry (ADR 0007); import-time + request-time validation (serve refuses to start on inconsistency); the palette tokens (§B), two density registers (P2.1), font-role split; shared chrome — brand, two nav groups, seam-sourced `aria-current`, one full-chrome error body, health pill strip with attention state (P2.3). | Sublayer imports clean and raises on any unresolvable card/command/view; request-time gating splits structural (omitted) from judgment (live advisory); `:root` holds every hex (P5.4), one accent; nav/active derive from the seam, no URL string-match; grep-able gate: the sublayer emits **no `<script>`**; `pytest` green. |
| **S3** | Today card-stack | The P3 card-stack Today (§A) — focus card (contains the one primary CTA, pronoun form), bounded count set (incl. the days-practiced quiet line), resumable-active line; zero-count pills dropped; overdue resumable-copy; page-level `start` affordance. | ≤ 4 card-level blocks, exactly one primary CTA, zero tables, no `<details>` on the primary path (P5.3); focus named once; raw backlog never on Today; celebration past-tense/factual at real events only (CSS-only keyframe); `pytest` green. |
| **S4** | Next / node / finder | `/next` — human controls, candidate titles become links, one legible reasoning layer ("Why this?"), "Not ready yet — and why" card; node detail — brief-first state-aware collapse (P2.5), no-op evidence form omitted (P2.6), spine path summaries (§A), the tolerated raw-id as muted secondary + the single mono use (§B/E); title-first finder on `/nodes/jump` (absent param → title-first list); **fix #228** (graph-edge links built from ids not titles). | `--state` never surfaces as a flag/web filter (recorded non-route); no command names/flags/raw-record ids in any prose/label/breadcrumb/bookmark; candidate titles are links; the finder is naive-first and server-rendered; #228's 404s are gone; `pytest` green. |
| **S5** | Health / analytics / safety panels | Health ambient register; Analytics one-theme `theme=` with collapsed tables + static server-rendered SVG series (real multi-point only) + separated periodic nav group; the page-level safety panels (§B/§F) — pass `--accent`, master step 1 `--warn` / step 2 `--err`, structural omission per P4.1; flash/refusal translation incl. the URL-as-copy rule (D2) and plain-link dismissal. | Every POST → 303 + translated flash; no 4xx from a write; refusals truthful, human, no internals; master two-step gated per P4.4; interactive charts absent (static SVG only); the days-practiced heatmap not built (recorded refusal); `pytest` green; `skilltrace health` green; doc gates green. |

**Scheduling notes (recorded, not builds):** the derived **week view** and the **spine abstraction's `/analytics` placement** are spec-future candidates, not S5 scope; G-Direction's requested hygiene items — the **`--mut` → `--muted`** token migration inside the existing sheet and any dead-CSS removal (P5.4) — are folded into S2/S5 so the sheet converges on the locked tokens as surfaces move over.

---
## J. Landing (same change as this spec)

- **POST_V2 v2.4 slot row** — replaced with G-Slot #226's paste-ready locked row (theme rewritten to the preference-driven de-CLI direction; acceptance carries the route-surface / design-direction / interaction-posture gates by name; ROI **M** (M, M); Enables unchanged).
- **ADR 0007** — the architecture amendment (downward-only route gate, usable Vocabulary identities, structural/judgment request-time gating) already landed on `main` (commit `8d6ae8d`, G-RouteSurface #220); this spec renders it. **ADR 0008** is **not** produced — the JS budget is 0 and 0008 stays reserved-and-unused; **ADR 0006 stands unamended** (G-JS #225).
- **spec-tier1-serve.md §C** — the stale sentence "the JavaScript-budget decision (ADR 0008, G-JS) remains open and unclaimed by it" is replaced with the locked answer (budget 0, no ADR 0008, ADR 0006 unamended, no `<script>`). §B is already aligned (structural vs judgment) and the normative route table is untouched.
- **CONTEXT.md glossary** — *Days practiced* (record-window wording already matches the §A decision), *Next-action fact*, and the *Mentor* section amendment (canonical headings = the CLI's presentation) all landed in earlier commits (`33bd1ad`, `f1e9c59`); this spec introduces no new glossary term, so no further glossary edit is required.

---

## Acceptance — map is done when

- [ ] This spec plus the three throwaway prototypes are linked from map #208's `## Decisions so far`, and this file is the hand-off artifact.
- [ ] No product, architecture, or UX decision remains that would block the five S1–S5 build slices (the S3 Today shape, S4 finder, S5 panels and charts all cited above by their locked source).
- [ ] Map #208's `## Not yet specified` is empty; its `## Out of scope` records the refused/closed patches (dark mode, mobile/PWA, graph-viz tech, CLI voice, new engine data, post-destination implementation, interactive charts + the days-practiced heatmap).
- [ ] The rewritten v2.4 slot row, the §C sentence fix, and (where newly introduced) any glossary terms land in the same change.
- [ ] `pytest` green; `skilltrace health`/`today`/`next --minutes 60`/`node <seed id>` exit 0 on seed; doc gates green; the grep-able no-`<script>` gate is part of v2.4 acceptance.

---

## References

`CONTEXT.md` (glossary: *Days practiced*, *Next-action fact*, *Mentor*, *Interface sublayer*), `docs/adr/0006-stdlib-only-serve-shell.md`, `docs/adr/0007-reintroduce-interface-layer.md` (amended), `docs/spec-tier1-serve.md` §B/§C/§L-bis (normative route table), `docs/POST_V2_ROADMAP.md` v2.4 slot, map #208 + its child tickets (audits #209–#215, R3 `docs/research/r3-interaction-ceiling.md`, G-Preferences #219, G-RouteSurface #220, G-Direction #224, G-JS #225, G-Slot #226, G-MentorVoice #229), `docs/SAFETY_BOUNDARIES.md`, `AGENTS.md` hard boundaries, prototypes `prototype/p24-*.html` (throwaway decision aids).