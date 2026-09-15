# R-LocalPolish — chrome/shell presentation polish inside locked constraints

**Ticket:** R-LocalPolish (part of wayfinder map #258)
**Research date:** 2026-09-15
**Status:** throwaway research artifact — feeds polish tickets, never engine truth.
**Scope note:** value-add ONLY — what `r1-daily-loop-trends.md`, `r1-learning-app-daily-loop-uiux-trends-2023-2026.md`, `r2-learning-ux-preferences.md`, and `r3-interaction-ceiling.md` do **not** already say, scoped to chrome/shell presentation polish (chrome density, wayfinding, typography, trust cues, professional finish without a design-system rewrite).
**Shell-audit note:** chrome/home fidelity deltas vs the prototype are owned by [R-ShellAudit](https://github.com/earledotpy/skilltrace/issues/259) (`docs/research/r-shell-audit.md` on branch `research/r-shell-audit`, unmerged — absent from this branch's tree); patterns below avoid fidelity deltas by construction and de-duplicate against that audit's verdict (seam-driven nav, Go button, pill strip, sticky header waived; headings/border/CTA-scale to the fidelity tickets).

**Locked context (cited, never relitigated):** stdlib-only serve shell (`docs/adr/0006-stdlib-only-serve-shell.md`), web-only interface sublayer (`docs/adr/0007-reintroduce-interface-layer.md`), narrow tier-1 JS posture — chart hover tooltips only, zero JS on home (`docs/adr/0008-inline-progressive-enhancement-posture.md`), cream+terracotta §B tokens + dense register (`src/skilltrace/web/views.py` `_STYLE`), P3.1 voice rules (`src/skilltrace/web/interface/translate.py`), downward-only route surface (`docs/spec-tier1-serve.md` §C). Every pattern below is plain server-rendered HTML+CSS with zero new dependencies.

---

## 1. One sticky chrome, one active-view marker (`aria-current="page"`)

(a) The pattern in one sentence: keep the existing sticky header as the single persistent chrome and mark exactly one nav link per view with `aria-current="page"`, styled by the already-locked terracotta underline — never two markers, never a marker on the health strip or flash line.

(b) Why it fits SkillTrace's locked constraints: the sticky header and the `aria-current` underline rule already exist in the locked stylesheet (`src/skilltrace/web/views.py` `_STYLE`: `header{position:sticky…}`, `.nav a[aria-current="page"]{border-bottom:2px solid var(--accent)…}`); this pattern only asks that every view set it exactly once, which is pure server-side active-view derivation (ADR 0007: active-view state is the URL; `docs/spec-tier1-serve.md` §C: "the active-view marking derives from the seam"), zero JS, zero new tokens, zero new routes.

(c) Smallest concrete application: header nav on every surface (`/` topline, `/next`, node detail, `/health`) — the seam emits `aria-current="page"` on the one link matching the current view identity (`today`/`next`/`node`/`health`); the `/nodes/jump` header form and the health-strip pills never carry it.

(d) Primary-source citation(s): MDN `aria-current` — "Only mark one element in a set of elements as current with `aria-current`" and "`page`: Represents the current page within a set of pages" (<https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-current>); WAI-ARIA `aria-current` spec (<https://w3c.github.io/aria/#aria-current>); repo: `src/skilltrace/web/views.py` `_STYLE` sticky-header + `aria-current` rules, `docs/adr/0007-reintroduce-interface-layer.md` §Vocabulary (active-view state is the URL), `docs/spec-tier1-serve.md` §C (view identity per row).

## 2. Keyboard-visible focus ring plus skip link, CSS-only

(a) The pattern in one sentence: add a single `:focus-visible` outline rule in the one accent/ink token pair plus a "Skip to content" link as the first element in the shared `page()` shell, so keyboard wayfinding is visible without changing any mouse/touch appearance.

(b) Why it fits SkillTrace's locked constraints: `:focus-visible` by definition only renders for keyboard/script focus and leaves pointing-device focus alone (no visual change for mouse users, no token rewrite — outline can reuse `--accent` on `--card`); it is two CSS rules inside the existing single inline `<style>` block, zero JS (tier-0 legal; ADR 0008 grants script only for chart tooltips), and it repairs the one gap in the otherwise keyboard-first story without touching the review-loop grading semantics that r2 already owns.

(c) Smallest concrete application: shared chrome — skip link targets `main.wrap` on all views; focus ring applies to nav links, the hero's single CTA, bento-card links, `/next` queue rows, node-detail forms, and `/health` table links.

(d) Primary-source citation(s): MDN `:focus-visible` — "applies while an element matches `:focus`… and the UA determines via heuristics that the focus should be made evident" and "using `:focus-visible` (instead of `:focus`) allows authors to change the appearance of the focus indicator without changing when the focus indicator appears" (<https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/:focus-visible>); Selectors Level 4 `the-focus-visible-pseudo` (<https://drafts.csswg.org/selectors/#the-focus-visible-pseudo>); WCAG 2.1 SC 1.4.11 Non-Text Contrast via MDN accessibility note (focus indicator ≥ 3:1); repo: `src/skilltrace/web/views.py` `page()` (the one shell every view shares).

## 3. Tabular numerals on every count, one declaration

(a) The pattern in one sentence: set `font-variant-numeric: tabular-nums` on the count-bearing classes (`.count strong`, `.health-strip .pill`, `th/td`, `.weekstrip`, queue/spine rows) so due counts, review tallies, and health numbers align vertically instead of jittering between proportional glyphs.

(b) Why it fits SkillTrace's locked constraints: it is a font-feature switch on the locked system font stacks — no webfont, no new dependency, no token change, no layout-system rewrite; it works inside both the airy daily register and the dense diagnostics register (`--card-pad-dense` etc. in `_STYLE`), and it makes the "small bounded due-today count model" read as a ledger rather than CLI-ish jitter.

(c) Smallest concrete application: health strip pills on every page, `.count strong` figures on the hero/topline, `/next` queue-row counts, `/health` and `/analytics` tables, node-detail evidence/gate counts.

(d) Primary-source citation(s): MDN `font-variant-numeric` — "`tabular-nums`: activating the set of figures where numbers are all of the same size, allowing them to be easily aligned like in tables" (<https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/font-variant-numeric>); CSS Fonts Module Level 4 `font-variant-numeric-prop` (<https://drafts.csswg.org/css-fonts/#font-variant-numeric-prop>); repo: `src/skilltrace/web/views.py` `_STYLE` (§B type scale + dense register classes listed above).

## 4. Sticky table headers in the dense register only

(a) The pattern in one sentence: give long dense tables (`/health` roll-up, `/analytics` tables, node drill-down evidence/review tables) `thead th{position:sticky;top:<header-height>;background:var(--card)}` and leave airy daily surfaces untouched, so column labels survive scrolling without any script.

(b) Why it fits SkillTrace's locked constraints: `position:sticky` is pure CSS in the existing `<style>` block (tier 0, no script, no dependency); it applies only where the locked dense register already governs (`--card-pad-dense` / `.browsetable` in `_STYLE`), so the airy 720px daily-loop column keeps its whitespace-forward feel while the opt-in dense surfaces gain the one affordance that makes them feel professional.

(c) Smallest concrete application: `/health` detail tables and `/analytics` tables first; node-detail drill-down drawers second; never the hero, topline, or bento cards (no tables there by design).

(d) Primary-source citation(s): MDN `position: sticky` (sticky positioning — element sticks within its nearest scrolling ancestor; standard dense-table header technique) (<https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/position>); repo: `src/skilltrace/web/views.py` `_STYLE` (sticky `header`, `.browsetable`, dense-register tokens), `docs/spec-tier1-serve.md` §E (full tables are snapshot/appendix surfaces, not daily UI).

## 5. Honor `prefers-reduced-motion` on the one animation

(a) The pattern in one sentence: wrap the existing `@keyframes settle` success-flash animation (and any future transition) in `@media (prefers-reduced-motion: reduce){…animation:none}` so the earned pass/session celebration degrades to an instant state change for users who request reduced motion.

(b) Why it fits SkillTrace's locked constraints: the animation already exists and is already minimal (`.banner.ok/.banner.success{animation:settle .6s ease-out}` in `_STYLE`); the guard is ~3 lines of CSS, zero JS, zero tokens, and it is the only motion in the product — r1/r2 bless *earned, cheap* celebration and r3's tier-0 CSS stance covers it, but none of the four files name the reduced-motion guard, which is what makes the celebration professionally finished rather than merely cheap.

(c) Smallest concrete application: success banners on node detail (pass/master confirmations) and `/next`/`/` flashes rendered through the `notice`/`kind` URL-carry path (`docs/spec-tier1-serve.md` §C response contract).

(d) Primary-source citation(s): MDN `prefers-reduced-motion` — "used to detect if a user has enabled a setting on their device to minimize the amount of non-essential motion" (<https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion>); Media Queries Level 5 `prefers-reduced-motion` (<https://drafts.csswg.org/mediaqueries-5/#prefers-reduced-motion>); repo: `src/skilltrace/web/views.py` `_STYLE` (`@keyframes settle` + `.banner.ok/.banner.success`).

## 6. A one-line local-trust footer: loopback-live vs snapshot labeling

(a) The pattern in one sentence: render one muted one-line footer inside the shared shell stating the surface's liveness contract — live pages ("Local only · served from your files · fresh on every load") vs the disposable export ("Snapshot <generated-at> — not live · run `st ui`" in P3.1-clean wording) — so the learner never wonders whether a number is live.

(b) Why it fits SkillTrace's locked constraints: every fact it states is already locked spec — loopback-only foreground serve with fresh-per-request reads (ADR 0006), "snapshot, not live" export banner (spec §D), files-are-truth freshness (spec §C), P3.1-clean wording via the `translate` seam (`src/skilltrace/web/interface/translate.py`); it is one server-rendered line, no new route (downward-only gate untouched), no new token (`--muted`/`--step-135` already exist), no design-system work.

(c) Smallest concrete application: shared `page()` footer on `/`, `/next`, node detail, `/health` (live wording); the `data/export.html` snapshot banner (§D wording) is its counterpart — the pair is the trust cue.

(d) Primary-source citation(s): repo specs as primary sources — `docs/adr/0006-stdlib-only-serve-shell.md` (loopback-only, fresh reads per request, no cache), `docs/spec-tier1-serve.md` §C (read seam: `load_context_lenient` anew per GET) + §D ("snapshot, not live — run `st ui`" banner, disposable artifact), `src/skilltrace/web/interface/translate.py` (P3.1 voice gate the line must pass); adjacent first-party trust-device precedent: Recall's explicit ownership/export statements as surveyed in `docs/research/r1-learning-app-daily-loop-uiux-trends-2023-2026.md` §5 (export-to-Markdown, "you keep full ownership") — cited here only for the *label-the-contract* move, not for any loop claim.

---

## No-preference-row violations

None of the six patterns reopens a locked preference-table row: no new top-level view and no route added (downward-only gate, `docs/spec-tier1-serve.md` §C, intact); no dark mode, no mobile/PWA work, no interactive charts or heatmaps (ADR 0008 narrow grant untouched — patterns are tier-0 CSS/HTML); no prototype-fidelity delta argued; no study-day handoff copy; P3.1 voice preserved (pattern 6 routes through `translate`); cream+terracotta §B tokens reused, never extended. Any finding during implementation that implies touching a locked row (e.g. heatmap revival, chart axes/zoom, dark-mode token swap) STOPS and is reported as "needs fresh effort" per the map rule — no such finding arose in this pass.

## Overlap with r1/r2/r3

- r1 (`r1-daily-loop-trends.md` P1/P3/P4/P7, Directions A–D; `r1-learning-app-…md` §6–§8) already owns: one continue affordance, per-unit progress legibility, today-vs-trend honesty, progressive disclosure, and the calm-paper/craft-bench visual directions — patterns 1–6 assume them and add nothing to them.
- r2 (`r2-learning-ux-preferences.md` P1/P5/P9/P11/P13, §2.3/§2.6) already owns: one-click start, position-and-competence salience, progressive disclosure, state-lines-carry-reasons, factual celebration — pattern 5 extends celebration only with the reduced-motion guard; pattern 6 extends state-line honesty only to surface liveness, not to gate semantics.
- r3 (`r3-interaction-ceiling.md` §§2–3, tier ladder) already owns: CSS-only primitives (`:has()`, container queries, popover/details, view transitions) and the tier-0/1/2 budget — all six patterns are sited explicitly at tier 0 inside r3's ladder and use no primitive r3 does not already bless, except `tabular-nums`/`sticky-th`/`prefers-reduced-motion`/`aria-current`, which are the value-add.

## Recommended follow-ups

- Polish ticket: apply `aria-current="page"` exactly once per view from the interface-seam view identity.
- Polish ticket: add `:focus-visible` accent outline + skip-to-content link in the shared `page()` shell.
- Polish ticket: add `tabular-nums` to count classes and `sticky thead` + `prefers-reduced-motion` guard to the dense tables/success banners.
- Polish ticket: add the one-line live-vs-snapshot trust footer in P3.1-clean wording.
