# R1 — Learning-app daily-loop UI/UX trends (2023–2026)

**Research date:** 2026-09-14
**Ticket:** R1 — daily-loop interaction design & visual-direction survey for
the SkillTrace web UI.
**Scope:** what the day's first screen shows, how "what do I do next" is
answered, how progress legibility works, friction at the moment of
doing/reviewing, celebration/ritual, and tone (CLI-ish vs human) across
spaced-repetition tools, daily-loop platforms, self-directed technical
dashboards, and 2024–2026 entrants — then mapped onto SkillTrace's surfaces
(today-focus, queue, node detail, retention pressure, health surface) and its
constraints (single learner, evidence-gated, server-rendered, stdlib-only,
no build step, whitespace-forward mandate).

**Method:** live fetches of official sites, manuals, app source, changelogs,
and app-store listings on 2026-09-14. Several target sites are client-rendered
or bot-blocked and returned no readable text; those are marked
**official-canonical** and their product claims are labeled *known-product*
(operator/product knowledge, not verified this session) and are never
load-bearing. Community sources (app reviews, forums, Reddit) are used only
for friction and anti-pattern evidence, never for product claims. Visual
details beyond what page copy states are marked *design-asset observation*
and should be re-checked against live sites before design tokens are set.

### Evidence-quality legend

| Label | Meaning |
| --- | --- |
| Official-primary | Vendor page/docs/source fetched and read this session |
| Official-canonical | Official URL exists; unreadable this session (JS/bot-block) — claims marked *known-product* |
| Community | Reviews/forums — friction and sentiment evidence only |
| Secondary | Reputable third-party write-up (marked explicitly) |
| Unverified | Not located or not verifiable this session — excluded from findings |

All URLs accessed 2026-09-14. Source IDs `[S#]` resolve to §11.

## 1. Executive findings

1. **The strongest 2023–2026 convergence: one screen, one default action,
   honest per-day counts.** Every healthy daily loop answers "what does today
   look like" in a single glance (due counts, a path's next circle, a daily
   goal) and offers exactly one obvious CTA (Anki's *Study Now*, Duolingo's
   continue-lesson button) ([S2], [S11], [S12-index], [S13]).
2. **The industry's center of gravity moved from trees/XP to
   position-and-mastery.** Duolingo replaced its skill tree with a single
   path so learners stop asking "am I doing this right?"; RemNote's headline
   progress feature is "Mastery Tracking — See your progress per topic";
   Frontend Mentor replaced points with a review-built *skills profile*
   ([S11], [S10], [S15]).
3. **Scheduler transparency is now a product surface, not a settings dump.**
   Anki's FSRS era exposes a *Desired Retention* knob with a *Help Me Decide*
   helper and a simulator; Mochi shows next-due estimates on review-button
   tooltips; Anki's answer buttons preview the interval they will produce
   ([S3], [S10], [S2]).
4. **AI entered the loop as a tutor behavior, not a scheduling engine.** The
   verified AI-study posture is Socratic and adaptive ("asks questions that
   help you find the answers yourself" — Anthropic [S17]; "builds practice
   around the gaps" — Brilliant [S13]).
5. **Streaks are everywhere in consumer apps and are retention-engineered**
   (Duolingo's own design post is literally titled "our addictive and
   delightful widget" [S12-index]; DataCamp advertises "keeping your streak
   alive" [S14]) — and they generate a documented anxiety/hollow-streak
   backlash (§9). Professional/technical tools (Mochi, Mnemosyne, Frontend
   Mentor, Recall) mostly skip streaks entirely ([S7]–[S9], [S15], [S19]).
6. **Non-punitive re-entry is the quiet differentiator.** Anki's manual makes
   returning after a break a resume, not a reset: "you don't have to start
   anew and can just start back from where you left" ([S2]). No surveyed
   healthy tool punishes absence in copy; only consumer gamified layers do
   (§9).
7. **Completion rituals diverge by audience:** consumer apps celebrate
   (milestones, confetti, widgets); professional tools acknowledge (Anki's
   fixed "Congratulations! You have finished this deck for now." line [S5],
   Mochi's empty due queue [S9]). Both keep the *optional next step* (custom
   study, extra practice) strictly opt-in.
8. **Airy and server-rendered are compatible.** The survey's calmest,
   most whitespace-forward surfaces (Mochi's web app, Frontend Mentor, Anki's
   HTML-fragment desktop UI) are low-JS or fragment-rendered — SkillTrace's
   stdlib-only constraint does not preclude the target aesthetic
## 2. Spaced repetition

### 2.1 Anki (desktop + AnkiWeb)

**Daily home.** The home screen *is* the deck list: "your decks and subdecks
will be displayed in a list. New, Learn, and Due (To Review) cards for that
day will be also displayed here" ([S2]). No hero, no streak, no
recommendations — the day is expressed as three per-deck counts. Positioning
copy stays utilitarian: "Anki is a flashcard program that helps you spend
more time on challenging material, and less on what you already know"
([S1]).

**"What do I do next."** Clicking a deck opens the *deck overview*: counts
for New / Learning / To Review and one primary button, **Study Now** ([S2];
label verified in app source, `tr.studying_study_now()` [S4]). Buried cards
appear "in grey" with an **Unbury** action on the same screen ([S2], [S4]);
alternative paths — **Custom Study** and filtered ("cram") decks — are
bottom-bar links, not competing CTAs ([S4]).

**Progress legibility.** Nearly none on the home; progress lives in the
reviewer's per-card interval previews and the Stats graphs ("Each answer
button shows the next time a card will be reviewed again if you select that
button" [S2]; the FSRS section discusses reading a retention-rate graph
before drawing conclusions [S3]). Streaks: none. Past-vs-future framing is
implicit: today's due counts vs. future intervals on buttons.

**Friction at the moment of doing.** The reviewer contract is a two-tap
rhythm: question, then **Show Answer** (Space), then **Again / Hard / Good /
Easy**, each labeled with its resulting interval; the manual even coaches
button distribution ("Good... you'll typically use this button about 80-95%
of the time") and explicitly permits reducing to Again + Good if four
buttons are too many ([S2]). A recall-time rule is documented: "if you can't
answer within about 10 seconds, it's probably better to move on and show the
answer" ([S2]). Editing content mid-review is out-of-band (the browser);
template work is expert territory.

**Celebration/ritual.** One fixed string when the day's queue empties:
"Congratulations! You have finished this deck for now. If you wish to study
outside of the regular schedule, you can use the custom study feature." —
verbatim in multiple 2024–2025 Anki forum threads ([S5],
community-verified). No confetti, no summary; the ritual is the emptied
queue plus an opt-in *custom study* escape hatch.

**CLI-ish vs human.** Highly engine-ish vocabulary: *burying*, *leeches*,
*ease*, *fuzz factor*, *v3 scheduler*; the buried-count tooltip literally
reads "counts differ" ([S2], [S4]). The FSRS panel's *Help Me Decide* helper
([S3]) is the rare humanizing touch on a knob-dense policy surface. "Falling
behind" is framed non-punitively: "if you are returning to Anki after a long
break, you don't have to start anew and can just start back from where you
left" ([S2]).

**2024–2026 movement.** FSRS is a first-class scheduler with *Desired
Retention*, a recommended-retention helper, and a simulator ([S3]); current
desktop version 26.08.1 ([S1]).

### 2.2 AnkiDroid

Official Play listing: 4.8 stars from 164K reviews, 10M+ installs; key
features listed by the maintainers include "spaced repetition (supermemo 2
algorithm)", "progress widget", "detailed statistics", "dark mode", "fully
customisable", "100+ localisations", "open source" ([S5]).

Friction and tone evidence (community, from the same listing's reviews): one
2026 reviewer praises retention but flags "a bit confusing to navigate and
not really modern-looking"; another notes "It doesn't look outdated
anymore." A maintainer replies publicly: "We're getting more
modern-looking! Settings -> New study screen. I'm working on a new 'Browse'
screen, and working away at the code to eventually get the Deck Picker up to
scratch (probably one for 2027 — we're all volunteers)" ([S5]). Takeaway:
the mobile face of the most-used SRS long read as utilitarian/dated and is
mid-modernization (2025–2026 "new study screen"), confirming that
utility-first engines drift toward cockpit-itis without deliberate design
investment.

### 2.3 Mnemosyne

Official site frames the product as two things: "a free flash-card tool
which optimizes your learning process. It's a research project into the
nature of long-term memory." Design stance: "We strive to provide a clear,
uncluttered piece of software, easy to use and to understand for newbies,
but still infinitely customisable through plugins and scripts for power
users." Scheduling pitch: "Difficult cards that you tend to forget quickly
will be scheduled more often, while Mnemosyne won't waste your time on
things you remember well." Optional anonymous statistics uploads feed memory
research ([S6]). The main-window layout — scheduled count, New/Due numbers,
grade buttons, no decorative progress — is documented in the repo's prior
source comparison ([S38], internal). Tone: the most deliberately
anti-gamified of the family; legibility = schedule transparency, not
celebration.

### 2.4 Mochi (mochi.cards)

**Pitch/home.** "Spaced repetition flashcards made easy... Take notes and
make flashcards using markdown, then study them using spaced repetition."
Claims "Local first — Your data is stored safely on your device and syncs
seamlessly when you're online"; free tier is "Free forever. No sign-up
required" ([S7]). The docs define the daily loop around **"New cards"** and
**"Due today"** pages, with FSRS, cramming, archiving, and reverse-review
docs alongside ([S8]).

**"What do I do next."** Per-deck due counts plus, since 2026, a synthesized
**inbox**: "The inbox now prioritizes overdue cards in the queue" and "Added
labels to cards in the inbox" (v1.21.15) ([S9]) — a cross-deck daily queue,
the survey's cleanest "what next" after Duolingo's path.

**Friction at doing/reviewing.** Reveal-and-grade is minimal, and friction
tuning is visibly active in the 2026 changelog: "Added a setting to display
a dedicated 'Show next side' button on the review page" (v1.21.16); "Added
back next due date estimation in the forget / remember review button
tooltips" (v1.21.15); "Fixed max interval not being respected with FSRS
algorithm" (v1.21.17) ([S9]). Honest-record options ship too: "Added the
ability to delete individual reviews from the review history" ([S9]).

**Progress legibility.** Due counts, review history, and a charted dashboard
(mobile changelog references scrubbing dashboard charts [S9]). No streaks,
XP, or leagues anywhere in official material ([S7]–[S9]).

**Celebration.** None gamified; the reward state is an empty due queue, and
the notes-with-cards context supplies motivation ("After finishing my
writing I'm instantly motivated to hop over and memorize" — user testimonial
[S7]).

**Tone/visual.** Human, stationery-like: the tagline is "Flashcards & notes.
An app to help you learn and remember things."; testimonials foreground UI
joy — "your UX is waay ahead" (Andres B.), "absurdly beautiful, it is
extremely intuitive" (Danielton), "clean and simple interface" (Shreyas J.)
([S7]). Design-asset observation: soft spring-green/pastel palette, rounded
cube motif, monospace wordmark, airy single-column marketing page ([S7]).
Actively shipped: v26.8.2 released 2026-08-10 ([S9]).

### 2.5 RemNote

Official positioning: "The AI note taking tool that actually helps you
learn... Trusted by 1,000,000+ students to get higher grades." The daily
loop is exam-anchored and schedule-framed: "**Exam Scheduler** — Set your
exam date and we'll tell you exactly what to study each day"; "You'll get a
personalized practice schedule each day, tailored to your exam date";
"**Spaced Repetition** — Cards resurface at the optimal time for retention.
Study less, remember more" ([S10]).

**Progress legibility** is human-framed rather than stats-framed:
"**Mastery Tracking** — See your progress per topic" ([S10]) — the best
one-line formulation of evidence-gated progress found in this survey. The AI
layer adds "Explanations on Your Cards" and "AI Tutor Chat" ([S10]).

**Tone.** Benefit-led student copy with zero scheduler jargon on the
marketing surface ("mastery", "personalized practice schedule") — a
deliberate contrast with Anki's engine vocabulary. (The in-app **Daily
Queue** concept is *known-product*; not verified on fetched pages this
session.)

### 2.6 Absorb (absorb.app)

**Unverified this session.** absorb.app and www.absorb.app refused
connections repeatedly on 2026-09-14 (socket errors); no credible secondary
was found. Excluded from all findings; treat any claims about its loop as
unverified (§10).

## 3. Daily-loop platforms

### 3.1 Duolingo

**Home.** The 2022 redesign (still the operating model; a 2025 design post
"refreshed our core tabs" is listed on the design blog index [S12-index])
replaced the skill tree with a single path: "The home screen is now designed
as a path that you'll follow step by step." Unit headers were rewritten from
codes to intents — "'get directions' instead of 'City 3'" and "'discuss
destinations' instead of 'Travel 2'" — explicitly so learners know what they
are learning; practice is "built into your path"; and "you'll see more of
our cast of quirky characters cheering you along your learning path"
([S11]).

**"What do I do next."** The path's next circle plus a large lesson button =
one default action; choice is demoted to a Quests tab and (subscribers) a
Practice Hub tab ([S11]). Duolingo's stated problem framing is exactly
SkillTrace's: "We often hear from learners that they're not sure whether
they're using Duolingo the 'correct' or 'best' way... we thought we could do
better at guiding learners through lessons!" ([S11]).

**Progress legibility.** Position-on-path replaced crowns: "instead of
crowns to track your progress, you can see how you're progressing down the
path" ([S11]). Streaks, XP, and leagues persist app-wide; streak definitions
live in the help center but those pages are JS-empty on text fetch ([S28],
[S29]) — streak mechanics (freezes, milestone celebrations) are
*known-product*.

**Ritual.** Streak milestones, animations, and OS widgets; the design blog's
own post is titled "How we developed our addictive and delightful widget"
([S12-index] — title-level evidence; full text not captured this session).
Note the vendor's adjective choice.

**Friction/anti-patterns.** See §9: guilt-framed notifications, ad-tab
crowding of navigation, a hall-of-shame listing, sustained user complaints
([S31]–[S35]).

### 3.2 Brilliant

2026 positioning pivots to an AI personal tutor: "Meet Koji, your personal
tutor... Built by top learning experts from MIT and Harvard." Adaptivity is
mastery-framed: "Koji tracks what you've mastered and where you're stuck,
then builds practice around the gaps. He speeds up when you're ready, and
slows down when you need it." Motivation is explicit and self-aware:
"Brilliant is designed to feel like a challenge, not a chore. Streaks,
levels, and daily goals motivate you to build on your progress and keep
moving forward" ([S13]). Visual: dark hero, large type, character
illustration ([S13]; design-asset observation). Daily-problem URLs redirect
to the marketing home in this session's fetches, so daily-loop specifics
(daily challenge, streak ring) are *known-product* and unverified.

### 3.3 Codecademy Go

**Official-canonical only.** Codecademy's help-center index was readable
but surfaced no Go-specific article in its categories; Go marketing pages
404 at previously-used paths ([S22], [S33]). The app exists (it is
registered in SkillTrace's own resource registry, `graph/resources.yaml`),
but its 2023–2026 daily-loop claims (daily practice, streaks, offline
review) are *known-product* and unverified this session.

### 3.4 Exercism

Official-primary is limited to GitHub: "Exercism — Crowd-sourced code
mentorship. Practice having thoughtful conversations about code."; verified
domains exercism.org / exercism.io; the site is an open-source Ruby app
with a Go CLI for offline exercise submission ([S21]). exercism.org itself
returned HTTP 403 to every fetch ([S36]) — its dashboard (per-track
progress, syllabus tree, mentoring slots) is *known-product* and unverified
this session.

### 3.5 LeetCode

leetcode.com returned HTTP 403 to every fetch ([S37]). The daily-challenge
pattern — a labeled "Daily Challenge" entry with monthly badge/streak
mechanics — is *known-product* and unverified this session; its relevance
here is the *one-per-day, opt-in, deadline-scoped* shape rather than any
verified copy.

### 3.6 AI study surfaces

**Claude (Anthropic) — verified.** Anthropic's current higher-education
page states the learning-mode behavior in terms that are the best
in-the-wild articulation of Socratic AI: "Claude's learning mode works like
a good tutor: it asks questions that help you find the answers yourself.
For students, that means developing transferable skills. For faculty, that
means a thinking partner who can hold the thread of a long research
conversation." Rigor framing: "Claude engages with complexity without
simplifying it away. It pushes back, asks follow-up questions" ([S17]). The
original 2025 education announcement has rotated off the newsroom index
([S18]) but the behavior language is live on an official page.

**ChatGPT Study Mode — official-canonical.** OpenAI's announcement and
help-center article exist at canonical URLs but refused connections this
session ([S26], [S27]); the Socratic behavior claim (step-by-step guidance,
hints, knowledge checks, avoids direct answers) is *known-product* and must
be re-verified before being relied upon.

**Grok / "Atlas-style" study features — not found.** No official xAI
source for study/education features was locatable this session; excluded
from findings (§10).

## 4. Self-directed technical dashboards

**freeCodeCamp — official-canonical.** freecodecamp.org and /learn/ are
client-rendered; text fetches returned no readable content this session
([S25]). Curriculum/percent framing (certifications with named required
projects) is *known-product*, unverified this session.

**roadmap.sh — verified.** "roadmap.sh is a community effort to create
roadmaps, guides and other educational content to help guide developers in
picking up a path and guide their learnings." Scale and momentum: "the 6th
most starred project on GitHub", "367K GitHub Stars", "+3.2M Registered
Users"; a 2026 AI pivot is visible in navigation: "Learn with AI", "Lesson
Packs", "AI Tutor" ([S16]). Roadmap pages present topic graphs with
per-node completion flags (design-asset observation; the page text confirms
roadmap/progress framing). Tone: developer-plain, community-flavored;
jargon is audience-appropriate rather than engine-appropriate.

**Frontend Mentor — verified.** "Learn to code for free by building
real-world projects... Build real projects to professional designs and
briefs, get AI code reviews that build a profile of your strengths, and
grow alongside a community reviewing each other's code. Join 1,194,336
developers..." Progress legibility is artifact- and profile-based: "Get an
AI code review with line-level findings scored against the brief's
requirements. Every review adds to your skills profile, so you can watch
your strengths build." Difficulty ladder: "Pick from 120+ professional
projects across five difficulty levels." Anti-tutorial positioning: "Stop
watching tutorials and start building" ([S15]). Notably there is no streak
and no daily loop — progress is evidence-shaped (shipped projects +
review-scored skills profile), the closest commercial analogue to
SkillTrace's evidence gating.

**DataCamp — verified.** Structure: Career Tracks / Skill Tracks / Courses
/ Certifications / Projects / Assessments / DataLab; official streak
language on the homepage: "Unlock skills faster in the DataCamp Mobile app
by practicing code, watching videos, and keeping your streak alive!"; "Join
19M+ learners worldwide" ([S14]). Tone: corporate-clean. The desktop
learning surface (daily XP goals, streak page) is *known-product* beyond
that quote.

## 5. Notable 2024–2026 entrants

**Recall (getrecall.ai) — verified.** "Recall — Your AI Knowledge Base...
Summarize anything forget nothing." Retention is explicit: "Recall helps
you retain the information you consume by employing spaced repetition and
active recall strategies ensuring that the key points are not just captured
but also remembered. Run a quiz on any content you save into Recall and
click 'Review' to access your personalized learning schedule" ([S20]).
Graph-native: "Recall is built on a graph database, meaning that related
content is automatically linked together"; surfacing: "Augmented
Browsing... these connections resurface as you browse" ([S20]). Ownership
posture: "Export your notes to Markdown anytime. We never train AI on your
content, and you keep full ownership of your data"; "Trusted by 700,000+
professionals" ([S19]). The daily loop is a review/quiz schedule over saved
summaries (docs step "6. Review Content" [S20]) — the closest entrant
analogue to SkillTrace (graph + retention + local ownership), but with
AI-generated cards rather than learner-produced evidence.

**Traversary — not found.** Exact-phrase and platform searches (Brave,
DuckDuckGo, Bing) surface only an OED/Wiktionary archaic adjective, a
Shopify store (traversary.ca), and usernames; no study tool of this name
could be located or verified this session. Recorded as *not found*; if it
exists it has no official web presence discoverable via 2026 search.

**SuperMemo web — not verified.** No official web-app claim could be
checked this session; excluded (§10).

**Lexy/study-agent-style entrants.** No official sources located; excluded
from findings (see §10 ledger).

## 6. Convergence table (pattern → tools → stakes → differentiators)

| Pattern | Tools exhibiting it | Table stakes (2023–2026) | Differentiating | Evidence quality |
| --- | --- | --- | --- | --- |
| One today surface, single default next action | Anki (Study Now), Duolingo (path + lesson button), Brilliant (daily goals), Mochi (due today), LeetCode (daily challenge) | Day answerable in one glance; one obvious CTA; counts before everything else | Auto-picking the single next item (Duolingo, Brilliant) vs learner-owned selection (Anki, Mochi) | Strong for Anki/Duolingo (official); known-product for Brilliant/LeetCode |
| Day-scoped queue with visible counts | Anki (New/Learn/Due), Mochi ("Due today" + overdue-prioritizing inbox), Duolingo (per-day lessons), DataCamp (daily XP goal) | Per-day counts; overdue shown honestly; queue visibly empties | Cross-deck overdue-prioritized inbox (Mochi 2026); practice woven into the path (Duolingo) | Strong (official) |
| Progress as position/mastery, not raw XP | Duolingo (position on path), RemNote ("Mastery Tracking — see your progress per topic"), Frontend Mentor (skills profile), roadmap.sh (per-node flags), freeCodeCamp (percent of certification, known-product) | Per-topic/per-path legibility; past-vs-future "you are here" framing | Evidence-gated mastery (Frontend Mentor review-built profile; SkillTrace evidence records) | Strong (official) |
| Transparent control at the decision point | Anki (Again/Hard/Good/Easy with interval previews), Mochi (next-due estimates on Forget/Remember tooltips) | Show consequences of a choice on the control itself | Full policy transparency (FSRS desired-retention + simulator) | Strong (official) |
| Calm completion & non-punitive re-entry | Anki ("finished this deck for now" + custom study; falling-behind resume), Mochi (empty inbox) | A named done-state that invites optional extra work; no guilt copy on return | Re-entry framed as resume ("start back from where you left") | Strong (official) |
| Ritual via streak + widget | Duolingo (streak milestones, widget), Brilliant (daily goals), DataCamp ("keeping your streak alive") | Daily-goal ring or streak with milestone moments | Streak-saver mechanics (freezes/earn-back) — engagement-tuned, ethically contested (§9) | Strong (Duolingo/DataCamp); known-product (Brilliant) |
| Humanized engine vocabulary | Duolingo ("get directions" not "City 3"), RemNote (mastery/schedule over ease factors), Mochi (plain voice) | Translate scheduler-speak into intent-language on surfaces | Keep exact engine vocabulary for records; surface intent-language to the learner | Strong (official) |
| No-streak, artifact-based progress | Frontend Mentor, Mnemosyne, Mochi, Recall | Competence shown by artifacts/review state, not points | Portfolio/skills profile built from reviews (Frontend Mentor 2026) | Strong (official) |

## 7. The eight patterns most relevant to SkillTrace

1. **One today screen; one default action.** Anki's overview pattern
   (counts + *Study Now*) generalizes to any evidence-gated engine:
   SkillTrace's today-focus should be today's due reviews plus one
   recommended node with a visible rationale. Duolingo's insight applies
   directly — learners "are not sure whether they're using the app the
   'correct' way", and the cure is a confident default, not more panels
   ([S2], [S11]).
2. **Answer "what next" with a queue the learner can veto.** Mochi's 2026
   inbox (overdue-prioritized, labeled [S9]) is the closest analogue to
   SkillTrace's `next` ranking: visible, ordered, explained, reversible.
   Keep the ranking pure and deterministic; present *why* per item
   (readiness + retention pressure), never a black box.
3. **Make the day's scope visible and finishable — and make done explain
   itself.** Day-scoped counts plus a named done-state. Anki's
   "Congratulations! You have finished this deck for now." with an opt-in
   *custom study* affordance is the right shape, but new users misread the
   empty-deck case as an error ([S2], [S5]). SkillTrace's done-state should
   say *why* it is done ("2 reviews due, 1 gate ready — nothing else
   eligible").
4. **Progress = position + mastery, in learner language.** RemNote's "See
   your progress per topic" and Duolingo's position-on-path are the
   strongest framings ([S10], [S11]). Map SkillTrace node states
   (`locked/available/active/passed/mastered`) to a consistent visual
   grammar with counts and "you are here"; never visualize demotion
   (asserted progress never moves backward — see CONTEXT.md).
5. **Retention pressure must be a transparent, advisory knob.** Anki
   exposes *Desired Retention* with *Help Me Decide* and a simulator
   ([S3]); Mnemosyne states its scheduling philosophy in one plain
   sentence ([S6]). SkillTrace's retention-pressure surfaces should show
   the policy, its inputs, and its effect (suggested reordering) and never
   block or scold — matching the safety rule that advisory policies "warn
   and reorder recommendations; they never block."
6. **Health surface = calm ledger, not guilt dashboard.** AnkiDroid's
   "detailed statistics" ([S5]) and Mochi's review history ([S9]) are
   reference points; SkillTrace's health surface should read as an
   audit-friendly ledger (evidence coverage, blockers, overdue reviews,
   gate receipts) in neutral tone — the anti-thesis of streak-guilt
   screens (§9).
7. **Capture evidence at the moment of doing, frictionlessly.** Mochi's
   markdown-first capture and RemNote's in-notes card creation exist to
   avoid breaking flow ([S7], [S10]); Frontend Mentor makes submission
   itself the progress event (submit, then AI review, then skills profile)
   ([S15]). SkillTrace's session-to-evidence logging should be one
   pre-filled form derived from session context, not a wizard.
8. **Translate engine vocabulary on the web surface.** Duolingo rewrote
   unit names from codes to intents ([S11]); Anki shows the cost of not
   doing so (burying/leeches/ease jargon; a buried-count tooltip that
   reads "counts differ" [S4]). Keep CONTEXT.md terms exact in the engine;
   on web surfaces, pair each term with an intent phrase ("available —
   ready to start", "active — in progress") and confine jargon to tooltips
   and advanced views.

## 8. Visual-direction scouting (2023–2026)

Four live directions with named examples. Palette/typography specifics
beyond page copy are *design-asset observations* (from fetched site assets)
and should be re-verified against live sites before design tokens are set.

**A. Pastel stationery / soft-workbench minimalism** — *Mochi* (Absorb
reportedly adjacent; unverified). Airy single-column layouts, warm
off-whites with one saturated pastel accent, rounded forms, monospace as
the technical accent (wordmark, code blocks), markdown-native content
model, sparse or geometric illustration. Density: very low. Best fit for
SkillTrace's constraints — server-rendered-friendly, near-zero chrome, dark
mode as a palette swap. Sources: [S7] copy + design-asset observation.

**B. Big-path gamified classroom** — *Duolingo*, softened in *Brilliant*:
display-weight rounded typography, saturated primary color, confetti and
milestone animation, path/map navigation, mascot illustration throughout.
Density: medium-low but visually loud. Not a direction for a desktop,
evidence-gated single-learner tool, but its *mechanics* (single path,
position, milestone moments, widget ritual) remain the industry's most
validated habit loop ([S11], [S12-index], [S13]).

**C. Craft-bench neutral (developer-grade)** — *Frontend Mentor*,
*roadmap.sh*, and the GitHub-ecosystem aesthetic: humanist/neo-grotesque
sans at comfortable reading sizes, strong display-vs-body scale contrast,
high-contrast dark mode as a first-class theme, flowchart/grid canvases,
color reserved for state, near-zero illustration. Density: low-to-medium
core with dense appendix views. This is the credible "airier but still
technical" direction for a server-rendered desktop UI. Sources: [S15],
[S16].

**D. Calm AI-tutor surface** — *Anthropic/Claude education surfaces*,
*Recall* (and Brilliant's Koji as the consumer end): warm neutral canvas,
copy-led interfaces (more words, fewer icons), conversational blocks,
restrained accent color, graph views and explicit privacy statements as
trust devices. Sources: [S17], [S19], [S13].

**Cross-cutting conventions (2023–2026):**

- **Dark mode is table stakes at every layer.** AnkiDroid lists "dark
  mode" as a key feature ([S5]); Anki's own surfaces ship named themes
  (Auto, Light, Rust, Coal, Navy, Ayu — observed in the docs theme
  switcher [S2]); every marketing site surveyed offers one.
- **Typography:** neo-grotesque/humanist sans default; monospace as
  technical accent; scale contrast (roughly 2–3× display-to-body) carries
  the "airy" feel more than padding alone. (Design-environment
  observation; verify tokens per product.)
- **Cards over tables** for learner-facing surfaces; dense tables survive
  only in health/stats appendixes (Anki stats, DataCamp dashboards).
- **Illustration:** mascots for consumer mass-market; line/geometric for
  dev tools; none-and-typographic is a legitimate, current choice
  (Mochi-adjacent).
- **Whitespace-forward is achievable server-rendered:** Anki's desktop UI
  is HTML fragments inside a shell ([S4]); Mochi's web app and Frontend
  Mentor ship low-JS flows ([S7], [S15]).
