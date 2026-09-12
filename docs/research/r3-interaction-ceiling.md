# R3 — Interaction ceiling on the stdlib-only stack

Research ticket R3 (map #208). Question: given ADR 0006's posture — stdlib
`http.server.ThreadingHTTPServer`, server-rendered HTML assembled in code, one
inline `<style>`, zero JS frameworks, zero build step, PyYAML as the only
runtime dep, loopback single desktop-Chrome user — how far can a modern
learning-app *feel* go, and where exactly is the wall?

Repo context read: `docs/adr/0006-stdlib-only-serve-shell.md`,
`src/skilltrace/web/` (handler.py, server.py, views.py — ~80 KB of
server-rendered views, no JS today = tier 0). ADR 0007 governs the interface
layer cut; this doc feeds G-JS and a future ADR 0008. Throwaway research
artifact — not engine truth.

---

## 1. Progressive enhancement with ~50–300 lines of inline vanilla JS

**What practitioners achieve.** Vanilla HTML already carries most of the
interaction load once the modern primitives are used. `<dialog>` with
`showModal()` gives focus trapping, `::backdrop`, and Esc-to-close natively
(Chrome 37+, widely available) — a modal is roughly 20 lines of JS including
wiring a form submit to `fetch()`. The `popover` global attribute (Baseline
newly-available April 2024; Chrome 114+) gives light-dismiss, Esc handling, and
top-layer stacking with **zero JS** via `popovertarget`/`popovertargetaction`,
with `auto`/`hint`/`manual` modes ([MDN popover](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/popover)).
Even the declarative `command`/`commandfor` button API is shipping for
`<dialog>` control ([MDN `<button>`](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button#popover)).

Within ~300 lines you can realistically get:

- **Modals & popovers** — mostly declarative; `<dialog>` + `popover` cover it.
- **Fetch-based partial refresh** — a single delegated handler
  (`document.body.addEventListener('submit'|'click', …)` on elements with
  `data-*` attributes) posting forms and swapping server-returned HTML
  fragments via `element.outerHTML = await res.text()`. Caveat: fetch rejects
  only on network failure, not 4xx/5xx — you must check `response.ok`
  yourself ([MDN Using Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)).
  This is exactly the htmx contract reimplemented in miniature: respond with
  HTML, swap a target ([htmx docs](https://htmx.org/docs/)).
- **Optimistic UI** — update the DOM, fire the request, roll back on failure.
  Fine for *advisory* state; per the safety constraints, safety-critical
  mutations (pass/master, evidence) remain server-validated, render-from-server.
- **Keyboard shortcuts & command palettes** — a `keydown` listener matching a
  declarative key→action map plus a `<dialog>`-based palette filtering a
  server-rendered node list. Command palettes are a well-trodden ~150-line
  vanilla pattern; CSS anchor positioning (Chrome 125+,
  [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_anchor_positioning))
  can position the result list without JS geometry math.

**Failure modes to respect** (the real ceiling markers):

- **Double-submit**: naive fetch-on-submit re-fires on repeated clicks/Enter.
  Fix is one uniform guard: disable button + `if (inFlight) return` +
  re-enable in `finally` — encode it in one helper.
- **Stale reads**: after a POST that swaps a fragment, other page regions are
  stale. Under files-are-truth the safest pattern is *re-render the affected
  region from the server* on every mutation response (fragment-per-region);
  never trust client state. Serialize mutations or use a request-generation
  counter to prevent interleaving.
- **HTML escaping / XSS**: `views.py` hand-assembles HTML — every interpolated
  string must go through `html.escape()` server-side; never build markup from
  raw evidence/node text with f-strings alone. Client-built HTML needs the
  same discipline (use `textContent`, not `innerHTML`, for user data).
- **Confirmation integrity**: pass/master modals must submit through the
  server's confirm flow; client JS may *prevent* accidental clicks but must
  never *enable* unconfirmed writes (the client is never trusted).

## 2. CSS-only power, 2025–26 (desktop Chrome)

Support status in desktop Chrome:

| Feature | Shipped in Chrome | Status |
|---|---|---|
| `:has()` | 105 | Stable |
| Container queries (`@container`) | 105 | Stable |
| `popover` + `popovertarget` | 114 | Baseline 2024 |
| Same-document View Transitions | 111 | Stable; Baseline 2025 |
| Scroll-driven animations (`scroll()`/`view()`) | 115 | Stable in Chrome |
| CSS anchor positioning | 125 | Stable in Chrome |
| Cross-document View Transitions (`@view-transition`) | 126 | Stable in Chrome (not cross-browser Baseline) |
| `::details-content` | 131 | Baseline 2025 |
| `:open`, `scroll-state()`, upgraded `attr()` | 133 | Stable |

Sources: [MDN popover](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/popover),
[MDN animation-timeline](https://developer.mozilla.org/en-US/docs/Web/CSS/animation-timeline),
[MDN anchor positioning](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_anchor_positioning),
[MDN ::details-content](https://developer.mozilla.org/en-US/docs/Web/CSS/::details-content),
[Chrome 133 beta](https://developer.chrome.com/blog/chrome-133-beta/).

Safely CSS-only for SkillTrace:

- **Expandable study cards / evidence drawers**: `<details>/<summary>` is fully
  functional with zero JS; `::details-content` + `@starting-style` transitions
  the expansion smoothly in pure CSS.
- **Tooltips, readiness info popovers, confirmation hovers**: `popover="auto"`
  + `popovertarget` is declarative, light-dismissible (outside click/Esc),
  top-layer, with `::backdrop` and `:popover-open` styling; entry/exit
  animation via `@starting-style` and `transition-behavior: allow-discrete`.
- **Responsive dashboard layout**: container queries let each card adapt to its
  own box — same card in a sidebar and a main pane.
- **Reading progress / scroll reveals**: scroll-driven animations replace
  IntersectionObserver JS, run off the main thread.
- **Anchored elements** (recommendation card pinned to a wrapping node row):
  anchor positioning with `position-try-fallbacks`, no measuring JS; pairs
  naturally with popovers.
- **State-driven styling without conditional classes**: `:has()` — e.g.
  `article:has(input:invalid)` or `:has(.gate)` — lets cards style themselves
  from structure.

**Not safely CSS-only**: anything requiring DOM insertion/removal (adding an
evidence record), form submission sequencing, or state that survives reload —
that is exactly where tier 1's small script begins.

## 3. Server-rendered transition feel: View Transitions without a framework

**Same-document (SPA-style)**: `document.startViewTransition(callback)`
snapshots the old state, runs the DOM update, then animates between snapshots
with CSS. Chrome 111+; MDN Baseline 2025 newly-available (Firefox/Safari now
ship it too) ([Chrome docs, same-document](https://developer.chrome.com/docs/web-platform/view-transitions/same-document),
[MDN](https://developer.mozilla.org/en-US/docs/Web/API/Document/startViewTransition)).

**Per-element and stagger**: `view-transition-name` captures an element into
its own transition group (names must be unique); `view-transition-class` adds
a non-unique styling hook so many elements (e.g., every list item) animate as
one — the standard mechanism for staggers (Baseline newly-available Oct 2025)
([MDN view-transition-class](https://developer.mozilla.org/en-US/docs/Web/CSS/view-transition-class)).

**Cross-document (MPA) transitions** — the big one for a server-rendered app.
Pure CSS opt-in, **no JS at all**:

```css
@view-transition { navigation: auto; }
```

Applies only to same-origin, non-redirected `traverse`/`push`/`replace`
navigations. Chrome 126+ (Safari 18.2; Firefox lags — MDN marks the rule
"limited availability") ([MDN `@view-transition`](https://developer.mozilla.org/en-US/docs/Web/CSS/@view-transition),
[Chrome cross-document docs](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document)).
Event hooks `pageswap` (outbound) and `pagereveal` (inbound) let a small
script set transition types or customize — the only JS needed for polished MPA
transitions. Feature-detect fallback is trivially graceful: no support, the
page just loads with no animation.

**Limits without a framework**: same-origin only; no state persists across the
navigation; no client routing; DOM changes that aren't navigations still need
`startViewTransition` from script. But the classic MPA pains (old/new content
coexisting, focus, reading position) are solved by the API itself
([MDN View Transitions API](https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API)).

For SkillTrace: loopback latency makes MPA navigation already near-instant;
`@view-transition { navigation: auto; }` is a one-line CSS rule that makes it
*fluid*. This single rule closes the largest "app feel" gap of server-rendered
sites.

## 4. The wall: what genuinely requires a build step / framework / dependency

- **Fine-grained reactivity at scale** (Solid/Vue-style signals): a dependency,
  not a platform primitive. Hand-rolling a state→DOM dependency graph across a
  large DOM gets messy fast. *Not needed*: the daily loop is write → re-render;
  that is one render function, not a reactive graph.
- **Component state / derived view state** (filters, selection, optimistic
  updates across many views): where a small reactive dependency starts paying
  for itself. *Not needed at tier 0–1*: selection is per-page, filters can be
  server-side query params.
- **Offline / PWA**: service worker + manifest + cache strategies — real
  infrastructure, but dependency-free in principle and *orthogonal to the
  framework question*. SkillTrace is loopback local, so offline is free by
  construction. Not needed.
- **Rich charts** (zoom, axes, tooltips at scale): the pragmatic call is a
  chart dependency or a hand-rolled SVG helper. A daily study loop needs only
  a sparkline/progress bar — server-rendered inline SVG, zero JS.
- **Persistence**: already solved by files-are-truth + the CLI/registry; the
  web UI is read-mostly with two confirmed POST flows through the same
  dispatch as the CLI (ADR 0006/0007).

**Which the daily loop needs** (log session → see progress → pick next node):
none of the above, at tier 0–1. The only near-unavoidable dependency on the
horizon is charting *if* progress visualization grows beyond a sparkline — and
even that is a nice-to-have, not a gate.

## 5. Precedents: the htmx school of thought, and what its ideas cost without it

**HTMX's ideas** (dependency: a single ~14 kB vendored script, no build step):

- **HTML as protocol / HATEOAS**: the server's HTML response encodes all
  follow-up actions (links, forms with method/action/inputs); the client needs
  no out-of-band knowledge ([HTMX HATEOAS essay](https://htmx.org/essays/hateoas/),
  [Hypermedia Systems](https://hypermedia.systems/)). A browser already *is*
  the client — HATEOAS costs **nothing** on a stdlib server: plain links and
  forms are the whole client.
- **Locality of Behaviour**: behaviour should be visible on the unit of code —
  contrast `hx-get` on a button with a click handler a file away
  ([LoB essay](https://htmx.org/essays/locality-of-behaviour/)). Without HTMX,
  LoB is partially preserved: inline `popovertarget`, `href`, `form action`,
  and CSS keep behaviour on the element. What's lost is *asynchronous*
  locality — partial updates, live search, polling. That is the real tax of
  no-build: **full-page navigations replace in-page updates**.
- **MPAs are underrated**: hypermedia navigation suffices for many apps;
  htmx's value is sparing full navigations when partial updates feel better
  ([HATEOAS essay](https://htmx.org/essays/hateoas/)). On a loopback server
  with cross-document view transitions, the full-page cost is largely
  cosmetic and is being paid back.

**Other no-build precedents**: Chrome DevRel's Stack Navigator demo — a
two-page server-rendered site with cross-document view transitions and default
CSS only, no client JS, no build ([Chrome DevRel](https://developer.chrome.com/docs/web-platform/view-transitions));
MDN's MPA view-transition demo ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API));
and the classical precedents — wikis, forums, early-2000s web apps, MDN itself —
server-rendered pages where links/forms are the only mutation interface.

**Takeaway**: a stdlib-only Python server rendering plain HTML, enhanced with
`@view-transition`, `popover`, `<details>`/`::details-content`, container
queries, `:has()`, and server-rendered SVG sparklines is the *htmx philosophy
achieved with zero dependencies* — the browser already implements the
hypermedia client htmx recreates in script. The cost is partial-page updates;
the mitigation is one delegated fetch-swap handler (~100 lines, tier 1).



---

## Capability ladder

### Tier 0 — pure server-rendered (today)

- **Enables**: the six-route MVP; full links/forms interaction; `<details>`
  drawers, `popover` tooltips, container-query layout, `:has()` styling — all
  zero-JS; **plus `@view-transition { navigation: auto; }` as a one-line CSS
  rule** for fluid MPA navigation (technically tier 0 since it's pure CSS in
  the existing `<style>` block).
- **Risks**: full-page reloads on every action; confirm modals need the
  server's confirm flow (already built); feels "document-like" between
  navigations.
- **Budget**: ~0–20 lines of new CSS.
- **ADR 0008 would say**: HTML/CSS remain the only client technologies;
  cross-document view transitions adopted as progressive enhancement with a
  no-support fallback of plain navigation; no client script shipped.

### Tier 1 — inline vanilla progressive enhancement (~50–300 lines)

- **Enables**: `<dialog>`-based confirm modals driving the same POST endpoints;
  fetch-based partial refresh (fragment-per-region swap, server re-renders
  from truth on every mutation); keyboard shortcuts; a `<dialog>` command
  palette over server-rendered node lists; double-submit guards; optimistic
  *advisory* UI only.
- **Risks**: double-submit (fix: one uniform in-flight guard), stale reads
  after fragment swaps (fix: re-render affected regions from the server; never
  trust client state), escaping holes in client-built HTML (fix:
  `textContent`/server escape discipline), confirmation integrity (fix:
  client can prevent but never enable unconfirmed writes).
- **Budget**: 50–300 lines, one inline `<script>` block or a single static
  file served by the handler; still zero dependencies, zero build.
- **ADR 0008 would say**: one progressive-enhancement script with a written
  convention (delegated handlers, `data-*` attributes, in-flight guard,
  fragment swap contract); safety-critical mutations remain server-validated;
  no client-side caching of server truth (fresh reads per request preserved).

### Tier 2 — small inline interaction layer (~300–1000 lines)

- **Enables**: animated fragment swaps, richer palettes with filtered results
  and anchor-positioned lists, drag-free animated list reordering, multi-region
  coordinated updates, undo toasts backed by server-side revert commands,
  inline editing with live validation.
- **Risks**: this is where an ad-hoc framework starts forming — state-sync
  bugs, listener leaks on swapped fragments (re-init discipline), escaping
  regressions, testing burden shifting from pytest to untested JS.
- **Budget**: 300–1000 lines; warrants its own file, conventions, and tests.
- **ADR 0008 would say**: explicit scope cap (no client-side state
  computation, no client routing, no caching of server truth); re-init
  contract for swapped fragments; client-HTML escape discipline; rationale for
  staying under a framework; a revisit trigger (a concrete interaction that
  demonstrably fails here).

## Verdict

**Tiers 0–1 plausibly deliver the airier, less-technical, fluid daily-loop
feel; the feel is not gated on tier 2.** The reasons are specific to
SkillTrace's constraints working in its favor:

1. **Loopback latency makes MPA navigation feel instant**, and cross-document
   view transitions (one CSS rule, Chrome 126+) make it *fluid* with no JS —
   the biggest app-feel gap of server-rendered sites is closed for free.
2. **Declarative HTML absorbed most of what JS frameworks used to do**:
   `popover`, `<dialog>`, `:has()`, anchor positioning, container queries
   cover modals, menus, tooltips, and state styling with near-zero script.
3. **Files-are-truth is an architectural ally**: every request re-reads the
   files, so server fragments are always fresh and the fragile part of
   fetch-based enhancement (client state sync) never arises; partial refresh
   becomes "re-render this region from truth" — also the safety-correct
   pattern for evidence-gated progress.
4. **The htmx critique is validated, but the dependency isn't needed**: the
   ideas (HTML as protocol, LoB, fragments-over-JSON) cost a few hundred lines
   for one known app — exactly the tier 1 budget; the library buys generality
   a single-user tool doesn't need.

Tier 2 is a *comfort* upgrade (animated swaps, richer palette, inline
editing), worth reaching incrementally, not a prerequisite. Recommendation:
adopt tier 0's one-line CSS now, prototype tier 1's ~150-line script for the
confirm-modal + partial-refresh + shortcuts trio, and stay below tier 2 until
a concrete interaction demonstrably fails.

## Source list

- MDN, "View Transition API" — https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API
- MDN, "Document.startViewTransition()" — https://developer.mozilla.org/en-US/docs/Web/API/Document/startViewTransition
- MDN, "@view-transition" — https://developer.mozilla.org/en-US/docs/Web/CSS/@view-transition
- MDN, "view-transition-class" — https://developer.mozilla.org/en-US/docs/Web/CSS/view-transition-class
- Chrome for Developers, View Transitions (same-document / cross-document / overview) — https://developer.chrome.com/docs/web-platform/view-transitions/
- MDN, "popover (global attribute)" — https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/popover
- MDN, "<button> (command/commandfor)" — https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button#popover
- MDN, "CSS anchor positioning" — https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_anchor_positioning
- MDN, "::details-content" — https://developer.mozilla.org/en-US/docs/Web/CSS/::details-content
- MDN, ":has()" — https://developer.mozilla.org/en-US/docs/Web/CSS/:has
- MDN, "CSS scroll-driven animations / animation-timeline" — https://developer.mozilla.org/en-US/docs/Web/CSS/animation-timeline
- MDN, "CSS containment / container queries" — https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment
- MDN, "Using the Fetch API" — https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch
- Chrome 133 beta notes — https://developer.chrome.com/blog/chrome-133-beta/
- htmx, "Documentation" — https://htmx.org/docs/
- htmx, "HATEOAS" essay — https://htmx.org/essays/hateoas/
- htmx, "Locality of Behaviour" — https://htmx.org/essays/locality-of-behaviour/
- Gross, Stepinski, Akşimşek, *Hypermedia Systems* — https://hypermedia.systems/

3. **Files-are-truth is an architectural ally**: every request re-reads the
   files, so server fragments are always fresh and the fragile part of
   fetch-based enhancement (client state sync) never arises; partial refresh
   becomes "re-render this region from truth" — also the safety-correct
   pattern for evidence-gated progress.
4. **The htmx critique is validated, but the dependency isn't needed**: the
   ideas (HTML as protocol, LoB, fragments-over-JSON) cost a few hundred lines
   for one known app — exactly the tier 1 budget; the library buys generality
   a single-user tool doesn't need.

Tier 2 is a *comfort* upgrade (animated swaps, richer palette, inline
editing), worth reaching incrementally, not a prerequisite. Recommendation:
adopt tier 0's one-line CSS now, prototype tier 1's ~150-line script for the
confirm-modal + partial-refresh + shortcuts trio, and stay below tier 2 until
a concrete interaction demonstrably fails.
