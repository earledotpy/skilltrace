# R1 â€” learning-app daily-loop UI/UX trends

**Ticket:** #216 (part of wayfinder map #208)
**Slug:** `r1-daily-loop-trends`
**Research date:** 2026
**Status:** throwaway research artifact â€” feeds G-Preferences, never engine truth.

**Method & evidence-quality flagging.** Claims are drawn from web fetches of
official product pages, manuals, and first-party design/eng posts (cited
inline). Some product surfaces (Exercism.org, LeetCode's app UI, Absorb,
Codecademy Go's logged-in dashboard) were **blocked at fetch time** (403 /
socket errors), so characterizations of their logged-in daily-loop UI are
*known-literature*, flagged as such and never load-bearing. Where the
documentation I did fetch supports a claim, that claim is primary-sourced.

**Prior art read, not repeated:** `docs/research/mnemosyne-ankidroid-vs-skilltrace.md`
(queue contracts, stats, sync),
`docs/research/what-can-skilltrace-learn-from-comparable-open-sourced.md`,
`CONTEXT.md` (states, today-focus, health surface vocabulary).

---

## 1. Convergence table
| C1 | **Single primary "continue" affordance** on the daily home â€” one big button that starts today's work | Anki (Study Now on deck overview), AnkiDroid (deck list â†’ tap deck), Mochi (start studying), Brilliant (Koji next-step), DataCamp (daily challenge), LeetCode (Daily problem), Duolingo (path continue) | **Table-stakes** | Strong â€” 7+ independent products |
| C2 | **Small bounded "due today" count model** â€” the home answers "how much today" with a small set of labeled counts, not a backlog | Anki deck overview (New / Learning / To Review split, buried shown in grey), AnkiDroid deck counts, Mochi due counts, LeetCode one-daily framing, DataCamp 5-minute daily challenge | **Table-stakes** | Strong â€” 5+ independent |
| C3 | **Deterministic queue with keyboard-first review loop** â€” question â†’ reveal â†’ grade, minimal friction | Anki (Space/Enter reveal, 1â€“4 ease buttons), AnkiDroid (tap/swipe gesture grading), Mnemosyne (uncluttered review window, grading), RemNote (queue in the daily document), Mochi (slick keybinds praised in testimonials) | **Table-stakes** for SRS; the *sub-5-second grading loop* is the differentiator of the best ones | Strong â€” 5 independent, docs-sourced |
| C4 | **Streak with slack** â€” consecutive-day ritual, plus explicit forgiveness (freezes) rather than rigid loss | Duolingo (streak, Streak Freeze up to 2, milestone animations), Codecademy Go (streaks, known-literature), DataCamp mobile (daily challenge + XP, known-literature), LeetCode (daily streak, known-literature), Brilliant (Streaks and Leagues explicitly named as their "few core habit loops") | **Table-stakes** mechanism; *slack design* is differentiating | Strong for Duolingo/Brilliant (first-party); medium elsewhere |
| C5 | **Celebration ritual at the moment of completion** â€” short satisfying animation/sound at milestone, not after every unit | Duolingo (+1.7% D7 retention from streak-extension animations, milestone days), Brilliant (sounds/haptics as you interact), Duolingo widget ritual | **Differentiating** when earned (session/milestone); hollow if per-click | Strong â€” first-party A/B data from Duolingo |
| C6 | **Progress made legible per unit of the graph** â€” percent-complete per block/track/topic with in-place "mark done" | roadmap.sh (click nodes, track your progress along a roadmap â€” done/in-progress/skip encoding, known-literature for encoding detail), freeCodeCamp (percent bars per certification block, known-literature), Exercism (track progress pages, known-literature), RemNote ("Mastery Tracking: see your progress per topic"), Brilliant (levels per topic, deliberately reductive view) | **Table-stakes** | Strong â€” 5 independent |
| C7 | **Curated "today" section at the top of a stats surface** â€” textual today summary kept visually separate from long-horizon graphs | Anki statistics ("a brief list of textual statistics about the reviews that you have completed today", with an explicit warning that single-day stats are noisy â€” look monthly), AnkiDroid (review heatmap), Exercism/Codecademy dashboards (known-literature) | **Differentiating when honest** (today separated from trend, noise warned about) | Strong for Anki (manual) |
| C8 | **Milestone framing of mastery with reductive progress levels** â€” simple levels shown even though the underlying graph is more complex | Brilliant (levels "intentionally displays a more reductive view of concept connections and prerequisites than the underlying realityâ€¦ clear and satisfying milestones") | **Differentiating** | Medium â€” single first-party source, but explicit |
| C9 | **Local-first with markdown/graph ownership** â€” data on device, plain-text notes as the base of the loop | Mochi ("Local first. Your data is stored safely on your device and syncs seamlessly", markdown-based, testimonials praising local-first + markdown), Obsidian-family study flows, RemNote (offline mode) | **Differentiating in SRS** (Anki/Mnemosyne also local-first; modern entrants lean sync-first) | Strong â€” first-party |
| C10 | **Graph-view as the roadmap surface** â€” the map itself is the home for exploration, with node detail on click | roadmap.sh (interactive roadmaps, click nodes to read more; 367K GitHub stars), Anki deck tree | **Differentiating** vs list/queue homes | Strong |
| C11 | **AI tutor in the loop, asking not telling** â€” AI sees the current context, intervenes where stuck, never hands the answer | Brilliant's Koji ("never, ever just hands you the answerâ€¦ sees what's on your screen"), RemNote AI tutor/explanations, Frontend Mentor AI code reviews building a skills profile | **Differentiating** (2024â€“2026 entrant pattern) | Strong for Brilliant (first-party), medium elsewhere |
| C12 | **Home-screen/widget-level ritual prompt** â€” the loop begins before the app is opened | Duolingo widget ("addictive and delightful widget" article), mobile push streak reminders | **Differentiating on mobile; N/A-ish for desktop-first** (translate as a desktop home/status ritual) | Medium â€” mobile-first pattern |

### What reads as CLI-ish / engine-ish (to remove) vs human (to keep)

- **CLI-ish/engine-ish:** raw IDs and paths on the home, symmetric tabular
  stats dumps (Mnemosyne's classic science-log vibe), backlog counts without
  a "today" boundary, verbs as buttons ("run gate", "sync readiness"),
  monospace-everywhere density, JSON-shaped receipts shown verbatim (show a
  human summary, keep the receipt one click deep).
- **Human:** an opening question answered in prose ("Continue X â€” 3 reviews,
  1 blocker cleared"), whitespace, one big continue affordance, milestone
  celebration on pass, a health surface that warns in language not tables.

---

## 2. The 6â€“8 patterns most relevant to SkillTrace's shape

SkillTrace is a single-learner, evidence-gated, graph-based study engine with
a today-focus, queue, node detail, retention pressure, and a health surface.

**P1 â€” Today-first home with one primary continue affordance (C1+C2).**
The best tools make the home a single question answered instantly: Anki's
deck overview shows New/Learning/To Review counts and one Study Now button
([Anki manual, Studying](https://docs.ankiweb.net/studying.html)). SkillTrace's
today-focus should open with today's counts as a small labeled set (reviews
due, active nodes, blockers, remediation pressure) and one big continue
button into the top-ranked node. Do not show the backlog on the home; put it
behind the queue/health surface.

**P2 â€” Frictionless reveal-and-grade loop (C3).**
Anki's flow â€” Space reveals, 1â€“4 grades, buttons that show the *next
interval* if chosen ([Anki manual](https://docs.ankiweb.net/studying.html)) â€” is the
reference standard for review friction. SkillTrace equivalents: any review
surface (retention review, self-check) should be keyboard-reachable end to
end, and buttons should preview consequences ("confirm â†’ mastery review in
~21d"), not just name the action. Mochi's testimonials
([mochi.cards](https://mochi.cards/)) show users switching from Anki purely on
UX ("your UX is waay aheadâ€¦ slick keybinds") â€” proof the loop *is* the
differentiator.

**P3 â€” Progress legible per unit of the graph (C6, C8).**
roadmap.sh makes the map itself interactive with per-node progress tracking
([about](https://roadmap.sh/about)); Brilliant deliberately shows reductive
per-topic levels rather than the full prerequisite reality
([about](https://brilliant.org/about/)). SkillTrace's node states
(`locked/available/active/passed/mastered`) are the honest version of this:
render the *five states* as the level language, and percent-complete per
topic (derived) as the block language. Never show eligibility math on the
node card; show the state word and one line of "why locked" when relevant.

**P4 â€” Today separated from trend, with honesty about noise (C7).**
Anki's statistics window leads with a small textual "today" block and
explicitly warns that single-day stats are a poor progress indicator â€” look
monthly ([Anki manual, Stats](https://docs.ankiweb.net/stats.html)). SkillTrace's
health surface should copy this honesty contract: a today strip up top, a
quiet trend area below, and language like "bad days are normal" rather than
alarm-red velocity charts. This fits the engine's advisory-policy rule:
pressure reorders and warns, never blocks.

**P5 â€” Streak-like ritual with slack, grounded in evidence records not
engagement (C4+C5).**
Duolingo's first-party data: streak-extension animations increased D7
retention by +1.7%; Streak Freezes (up to two) *increased* daily actives
(+0.38%) rather than encouraging absence; 7-day streak learners are 3.6Ã—
more likely to finish the course
([Duolingo blog](https://blog.duolingo.com/how-duolingo-streak-builds-habit/)).
The SkillTrace-honest translation: a "days practiced" style ritual grounded
in *evidence records and sessions* (immutable, truthful), with a
forgiveness concept (a missed day is recorded truthfully; pressure warns,
never fabricates). Brilliant deliberately packs "a few core habit formation
loopsâ€¦ Streaks and Leagues" and avoids too many incentives
([Brilliant](https://brilliant.org/about/)) â€” pick one ritual, execute it well.

**P6 â€” Celebration that is earned, local, and cheap (C5).**
Celebration at session end and at pass (a hard, human-accepted gate â€” the
owl moment) with motion/sound; nothing per-click. Duolingo measured this
specifically as the animation at *streak extension and milestone days*
([blog](https://blog.duolingo.com/how-duolingo-streak-builds-habit/)); Brilliant
uses sounds/haptics on interaction ([about](https://brilliant.org/about/)).
Server-rendered stdlib-only SkillTrace can still do a CSS keyframe
pass-animation â€” zero dependency.

**P7 â€” Node detail: brief-first, evidence deep-on-request (progressive
disclosure).**
NN/g's progressive disclosure: show few important options first, defer
specialized options to a secondary screen; it makes apps easier to learn and
less error-prone ([NN/g](https://www.nngroup.com/articles/progressive-disclosure/)).
Node detail should read like a card: title, state, one-line readiness/why,
resources, and the next human action â€” with artifact specs, gate receipts,
and evidence history one click deep. This is also the fix for the
gate-receipt verbosity of v2.2 (human summary on the surface, receipt
verbatim underneath).

**P8 â€” The graph-view earns its home (C10) but the queue stays deterministic
(C3).**
roadmap.sh's success (367K stars) shows learners want the map as an
exploration home. But SkillTrace's queue must remain the deterministic pure
ranking (per the mnemosyne-ankidroid comparison doc: `next` is pure
recommendation; upstream mutable staged queues should not be imported). The
convergent pattern is: map for orientation and node detail, queue for "do
now", and never let the map become a mutable itinerary.

---

## 3. Visual-direction scouting (2023â€“2026)

Constraints to respect: desktop-browser, server-rendered, stdlib-only, no
build step, zero added dependencies; the owner wants airier,
whitespace-forward, less technical/CLI-flavoured.

**Direction A â€” "Calm paper" (SRS-native, recommended baseline).**
Inspired by Mnemosyne's explicit product ethos ("a clear, uncluttered piece
of softwareâ€¦ easy to use for newbies, infinitely customisable for power
users" â€” [mnemosyne-proj.org](https://mnemosyne-proj.org/)) and Mochi's clean
modern SRS look ([mochi.cards](https://mochi.cards/), testimonials: "clean and
simple interface", "absurdly beautiful"). Concretely:

- Typography: one humanist UI face at a generous 16px base, ~1.5â€“1.6 line
  height; one display weight for the today-heading only (a 1.8â€“2.2Ã— scale
  jump reads as a question, not a dashboard).
- Density band: **low** â€” single-column reading measure (65â€“75ch), cards
  with 24â€“32px padding, section spacing larger than intra-card spacing.
- Palette: near-white paper ground, one accent for the continue affordance,
  state colors muted and semantic only (5 node states). Dark mode as a
  token swap, not a redesign.
- Layout: card-based single column with a slim right rail on wide screens
  (rail = health strip). Progressive disclosure per NN/g
  ([nngroup](https://www.nngroup.com/articles/progressive-disclosure/)).

**Direction B â€” "Warm expressive minimal" (the 2025 mainstream).**
Interface trends converge on expressive/variable typography, softened color
with accessible high-contrast accents, dark mode as a default option,
generous whitespace, and sustainable/ethical minimalism
([CareerFoundry 2025](https://careerfoundry.com/en/blog/ui-design/ui-design-trends/);
Material 3 Expressive, Google's 2025 evolution of Material You pushing
expressive color/shape/typography â€”
[Wikipedia: Material Design](https://en.wikipedia.org/wiki/Material_Design)).
For study tools this reads as: bigger display headings, fewer borders
(spacing does the grouping), one saturated accent per surface. Duolingo's
core-tabs-refresh framing (craft, consistent spacing, restrained palette) is
indexed at [design.duolingo.com](https://design.duolingo.com/) â€” article body
fetch-degraded, treat specifics as *known-literature*.

**Direction C â€” "Bento home" (bento-grid dashboard).**
The 2023â€“2025 dashboard convention: home as a small set of differently-sized
rounded cards (bento grid) â€” a big "today" card, small streak card, small
health card. Visible across 2025 trend submissions (bento/glass/gradient
trend work) on Behance
([results](https://www.behance.net/search/projects?search=ui%20design%20trends%202025))
and mainstream trend write-ups (dark-mode and minimalism entries â€”
[CareerFoundry](https://careerfoundry.com/en/blog/ui-design/ui-design-trends/)).
Good fit for SkillTrace's home *only* if the today card stays dominant â€” a
bento home where the continue affordance is one card among six is a
regression (see C1).

**Direction D â€” "Engine-flavoured technical dashboards" (avoid generally;
useful for the health surface only).**
Anki's Browse/Stats windows (sidebar + dense table + graphs â€”
[Anki manual, Browsing](https://docs.ankiweb.net/browsing.html),
[Stats](https://docs.ankiweb.net/stats.html)) and classic AnkiDroid deck
counts/heatmap ([AnkiDroid manual](https://ankidroid.org/docs/manual.html)).
High information density, monospace numerals, table-first. This is the right
visual register for SkillTrace's *health/graph-impact diagnostics* â€” an
opt-in dense surface â€” and the wrong register for the daily home.

**Direction E â€” "Roadmap canvas" (graph-forward).**
roadmap.sh's node-canvas: nodes as colored rounded shapes on a connected
canvas, click â†’ resources; progress marked per node
([roadmap.sh](https://roadmap.sh/about),
[repo](https://github.com/kamranahmedse/developer-roadmap)). Relevant to
SkillTrace's graph view and the `graph impact` advisory: encode the five
node states as shape/outline/color on the canvas, keep text in node detail,
not on the canvas. Server-rendered stdlib-only means an SVG canvas â€”
achievable without dependencies.

**Cross-cutting token recommendations (G-Preferences inputs):**
1. Base type 16px humanist, ~1.55 line-height; display heading ~2Ã— base,
   today-only.
2. Whitespace-forward: section gaps â‰¥ intra-card gaps; single-column measure
   65â€“75ch; card padding 24â€“32px.
3. Semantic state palette (5 node states) muted; one strong accent for the
   primary continue affordance; high-contrast text.
4. Two density registers: airy daily surfaces (Directions A/B), dense
   diagnostics surface (Direction D) â€” same tokens, different density band.
5. Light-first with a dark-mode token swap.

---

## 4. Anti-patterns to avoid

1. **Gamification that lies.** Any streak or ritual not grounded in the
   immutable evidence/session records fabricates the story. Duolingo's data
   supports *honest* streaks
   ([blog](https://blog.duolingo.com/how-duolingo-streak-builds-habit/)); the
   anti-pattern is a streak that counts openings or clicks.
2. **Hollow celebration.** Animation after every click trains it out; the
   measured effect lives at streak extension and milestones, not per action
   (same source). For SkillTrace: celebrate pass (a real gate) and session
   completion, never button presses.
3. **Loss-framing without slack.** Rigid streaks demotivate and even prevent
   starting; Duolingo's freezes *increased* actives (same source). SkillTrace
   must never use loss-framed pressure that blocks (engine rule: advisory
   warns and reorders, never blocks; asserted progress never demotes).
4. **Reductive-level confusion.** Brilliant shows reductive levels *on
   purpose* and says so ([about](https://brilliant.org/about/)); the
   anti-pattern is showing reductive levels that contradict the graph's hard
   prerequisites (SkillTrace's `locked` is the only wall â€” a level metaphor
   that implies you can "choose" a locked node is a lie).
5. **Backlog-on-home clutter.** Anki's falling-behind handling (longest
   waiting prioritized, backlog absorbed transparently â€”
   [manual](https://docs.ankiweb.net/studying.html)) is good *behavior*; showing
   the raw backlog count on the home is the anti-pattern. Bound the day;
   handle the backlog in the queue.
6. **Engine-speak as UI.** Receipts, exit classes, hashed outputs, IDs and
   paths surfaced on daily surfaces (see Â§1). Gate receipts live in node
   detail, one click deep (P7).
7. **Clutter by symmetric tabular dumps.** Mnemosyne's science-log register
   (anonymous stat upload â€” [mnemosyne-proj.org](https://mnemosyne-proj.org/))
   and Anki's dense stats are correct *for their audience*; symmetric
   stats-on-home is the anti-pattern. Today strip â‰  trend area â‰  health
   surface (P4).
8. **Engagement-maximizing dark patterns.** The general gamification
   criticism (points/badges/leaderboards optimizing engagement over the
   learner's goal â€” see the education criticism sections of
   [Wikipedia: Gamification](https://en.wikipedia.org/wiki/Gamification)) maps
   directly to N=1: SkillTrace's only stakeholder is the learner; any
   notification/redness engineered for engagement is self-harm. Pressure is
   advisory, warned in language, and reorders â€” nothing more.

---

## Source list

Primary (fetched, cited above):

- Anki manual â€” Studying (deck overview, Study Now, answer buttons + interval
  previews, shortcuts, falling behind): <https://docs.ankiweb.net/studying.html>
- Anki manual â€” Statistics (today block, today-noise warning, true retention):
  <https://docs.ankiweb.net/stats.html>
- Anki manual â€” Browsing (dense sidebar/table register):
  <https://docs.ankiweb.net/browsing.html>
- AnkiDroid manual (deck list, deck counts, overview screen, gesture grading,
  heatmap): <https://ankidroid.org/docs/manual.html>
- Mnemosyne Project homepage (clear/uncluttered ethos, research framing):
  <https://mnemosyne-proj.org/>
- Mochi homepage (local-first, markdown, keybind testimonials):
  <https://mochi.cards/>
- RemNote homepage (exam scheduler "exactly what to study each day", mastery
  tracking per topic, AI tutor): <https://www.remnote.com/>
- Duolingo blog â€” streak habit research (+1.7% D7 animation effect, Streak
  Freeze +0.38% actives, 3.6Ã— course completion at 7-day streak):
  <https://blog.duolingo.com/how-duolingo-streak-builds-habit/>
- Brilliant â€” About (Koji ask-not-tell tutoring, deliberate reductive levels,
  "Streaks and Leagues" as few core habit loops, sounds/haptics):
  <https://brilliant.org/about/>
- roadmap.sh â€” About (interactive roadmaps, progress tracking, Astro+Tailwind):
  <https://roadmap.sh/about>
- roadmap.sh â€” roadmaps index (node-canvas model): <https://roadmap.sh/roadmaps>
- developer-roadmap repo (per-topic markdown content per node):
  <https://github.com/kamranahmedse/developer-roadmap>
- Frontend Mentor homepage (AI code review building a skills profile,
  challenge difficulty levels): <https://www.frontendmentor.io/>
- DataCamp mobile (daily 5-minute coding challenges, XP):
  <https://www.datacamp.com/mobile>
- NN/g â€” Progressive Disclosure (defer specialized options; easier to learn,
  less error-prone): <https://www.nngroup.com/articles/progressive-disclosure/>
- CareerFoundry â€” 5 UI trends 2025 (expressive type, dark mode, minimalism,
  accessibility-first): <https://careerfoundry.com/en/blog/ui-design/ui-design-trends/>
- Wikipedia â€” Material Design (Material 3 Expressive, 2025; Material You 2021
  custom themes): <https://en.wikipedia.org/wiki/Material_Design>
- Wikipedia â€” Gamification (techniques and criticism sections):
  <https://en.wikipedia.org/wiki/Gamification>
- Duolingo design blog index (core-tabs refresh, widget article â€” body fetch
  degraded, index only): <https://design.duolingo.com/>
- Behance search results (2025 trend surface: bento, glassmorphism, gradient
  palettes â€” direction corroboration only):
  <https://www.behance.net/search/projects?search=ui%20design%20trends%202025>

Blocked at fetch (characterizations above are *known-literature*, flagged):
Exercism.org (403), LeetCode app UI (403/404), Absorb (socket errors),
Codecademy logged-in daily loop (redirects to marketing), freeCodeCamp
logged-in dashboard (JS-only page).

Sibling-convention note: blocked sources flagged as *known-literature*,
matching #217/#218.
