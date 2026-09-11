# R2 — Evidence-based learning-UX preferences

**Research date:** 2026-09-14
**Ticket:** R2 (#217), part of wayfinder map #208. Feeds G-Preferences
(apply / reject / defer); this doc is a throwaway research artifact, not
engine truth.
**Question:** what does learning-science and UX-research literature actually
support about interface properties that help *retention, motivation, and
follow-through* for self-directed learners — vs what is merely fashionable?

**Method:** live fetches of primary sources on 2026-09-14 — official docs
(Anki manual, SDT, Bjork lab, Fogg, NN/g, Duolingo's own design blog),
Semantic Scholar API records for key papers, Wikipedia as a router to
primary citations, and the deceptive-patterns taxonomy. Several target
pages (supermemo.com, supermemo.guru, characterlab.org, some Semantic
Scholar rate-limited calls) were blocked or 404 this session; claims
resting on them are labeled *known-literature* and are never load-bearing.
R1 (#216, sibling doc
`r1-learning-app-daily-loop-uiux-trends-2023-2026.md`) already surveyed
product practice; this doc covers the underlying evidence and
cross-references it.

### Evidence-quality legend

| Label | Meaning |
| --- | --- |
| **Strong** | Multiple independent experiments or meta-analyses; survives replication scrutiny |
| **Moderate** | Consistent evidence but with moderators, mixed effect sizes, or lab-heavy designs |
| **Weak** | Small/single studies, practitioner literature, or contested |
| **Speculative** | Plausible extrapolation; no direct evidence found this session |
| *known-literature* | Canonical citation exists but its page was not readable this session — flagged, never load-bearing |

## 1. Executive answer

The literature supports a specific profile for a single-learner tool:
**make starting frictionless, make acceptance deliberate, show progress as
position-and-competence (never as manufactured urgency), frame failure as
information during review, and let the schedule — not guilt — carry
retention pressure.** Almost nothing in the evidence base supports the
consumer-gamification stack (streak loss-aversion, leaderboards, XP) as a
*learning* intervention; it is retention engineering whose learning-side
value is unproven and whose failure mode (break-and-quit) is documented
even by its strongest commercial advocate [S8].

## 2. Probe findings

### 2.1 Progress salience

- **Visible progress helps, but the mechanism that survives scrutiny is
  *competence feedback*, not streaks.** The strongest motivation result in
  the diary literature is Amabile & Kramer's *progress principle*: across
  ~12,000 knowledge-worker diary entries, the single most important factor
  in a good inner workday was simply *making progress in meaningful work*
  — even a small step [S5]. Interface translation: show *what moved today*
  (a node activated, an artifact accepted, a review batch cleared), not a
  vanity counter. Strength: **moderate** (rich observational + diary
  data, not experimental).
- **Goal gradients are real:** effort accelerates as a reward is
  approached (Kivetz, Urminsky & Zheng 2006, *J. Marketing Research* —
  *known-literature*; API rate-limited this session). Nunes & Drèze's
  *endowed progress effect* was verified via Semantic Scholar: an
  *artificial* head start (pre-checked car-wash cards) increases
  persistence, 279 citations [S7]. Both are fidelity-relevant: they show
  progress bars **work**, and that **fake head starts work too** — which
  is exactly why endowed-progress mechanics are manipulative when applied
  to learning claims. Real progress bars over real state (node state,
  evidence count) are honest; any synthetic advancement is a deceptive
  pattern. Strength: **moderate**.
- **Streaks: the strongest evidence is that they retain users and that
  breaking them demotivates.** Duolingo's own product post (best
  first-party data available) says streaks run on early-portion excitement
  and later on **loss aversion** — "Even on your laziest days … you'll be
  reminded to complete a lesson so as not to lose your hard-earned
  progress" — and admits a broken streak "can have the opposite effect,
  and actually feel quite de motivating" [S8]. Their countermeasure is
  *flexibility* (streak freezes), which measurably increased daily
  actives (+0.38%) rather than encouraging days off; learners reaching
  a 7-day streak are "3.6 times more likely to complete their course"
  [S8]. This is retention engineering, not learning science, and the
  loss-aversion mechanic is the classic manipulative core. SkillTrace has
  no streaks; the honest residue is the *flexibility principle*: never
  let a missed day read as failure of the learner (missed reviews create
  overdue items, never demotion — SkillTrace's model already guarantees
  this). Strength: **moderate for retention effects, weak for learning
  benefit**.
- **Fashions to reject:** XP, leaderboards, coins — none appear in the
  learning-science literature as learning interventions; SDT's reward
  literature (below) predicts extrinsic rewards can crowd out intrinsic
  motivation [S4]. Position-and-mastery displays (per-topic mastery,
  skill maps) are the defensible form of progress salience (R1: Duolingo
  replaced its tree with a path; RemNote's headline feature is per-topic
  mastery).

### 2.2 Friction placement

- **Fogg Behavior Model (B=MAP):** "Behavior happens when Motivation,
  Ability, and a Prompt come together at the same time. When a behavior
  does not occur, at least one of those three elements is missing" [S3].
  The design corollary: for a target behavior, raise *ability* —
  simplicity — and make the prompt obvious. Translation: **starting or
  resuming a session should be one obvious prompt with maximal
  simplicity** (one click from the home/today view). Strength:
  **moderate** (widely referenced practitioner framework — the site
  claims 1,900+ academic citations — not a tested theory).
- **Deliberate friction at acceptance is a *design choice*, justified by
  the domain rather than by a friction study.** The evidence base supports
  *desirable difficulty* for the **learning act** (retrieval, spacing,
  interleaving [S2][S9]) — it does not legitimize friction in
  confirmation dialogs. SkillTrace's pass/mastery confirmations stay
  explicit because they are acceptance moments under the safety rules
  (nothing passes without explicit human acceptance; asserted progress
  never demotes) — the honest-communication requirement (§2.6), not
  learning science, is the warrant. Practical form: one unambiguous,
  well-labeled action that *states the consequence* ("this records pass
  on <node>; evidence X, Y attached") — friction as clarity, not as a
  maze. Strength: **strong by repo constraint; moderate as general UX
  evidence**.
- **Anti-pattern: friction *inside* the review loop.** Anki's manual
  models the opposite: question → one key shows the answer (Space) → one
  key grades (Space = Good); "Most people find it convenient to answer
  most cards with Space and keep one finger on 1 for when they forget"
  [S10]. Review UI friction should be zero except grading itself.

### 2.3 Cognitive load & density

- **Definition and target:** "the cognitive load imposed by a user
  interface is the amount of mental resources that is required to operate
  the system"; designers should eliminate **extraneous** load —
  "processing that takes up mental resources, but doesn't actually help
  users understand the content" — while keeping intrinsic load, which is
  the learning itself [S11]. Working-memory limits are among the most
  replicated results in cognitive psychology, and working-memory capacity
  correlates with literacy and numeracy outcomes [S12]. Strength:
  **strong**.
- **NN/g prescriptions, directly applicable to a server-rendered desktop
  UI [S11]:**
  - *Avoid visual clutter* — "redundant links, irrelevant images, and
    meaningless typography flourishes slow users down."
  - *Build on existing mental models* — labels/layouts users already
    know. For SkillTrace: tables, plain headings, standard link styling —
    consistent with R1's "deliberately non-gamified, technical" tone.
  - *Offload tasks* — "can you show a picture, re-display previously
    entered information, or set a smart default?"
- **Progressive disclosure:** "Initially, show users only a few of the
  most important options. Offer a larger set of specialized options upon
  request" — making applications "easier to learn and less error-prone"
  (Nielsen, 2006) [S13]. Caveat from the same source: staged disclosure
  needs a task analysis; over-splitting tasks "bogs users down by excess
  navigation" [S13]. Translation: the session surface shows the current
  item + counts; evidence detail, gate receipts, and analytics live
  behind links. Strength: **strong** (30+ years of consistent usability
  practice; R1 found every healthy product converges on one screen, one
  default action).
- **Chunking** follows from working-memory limits (Miller 7±2; modern
  estimates nearer 4 chunks — Cowan — *known-literature*; capacity
  correlations summarized in [S12]). One idea per panel, one queue per
  screen. Strength: **strong** for the limit; **moderate** for the
  "4 vs 7" number.

### 2.4 Feedback timing

- **Retrieval practice / testing effect — the strongest result in this
  ticket.** Rowland's meta-analysis of the testing effect (*Psychological
  Bulletin*, 2014, 971 citations) confirms testing beats restudy for
  retention [S14]; the Bjork lab states it plainly: "When information is
  successfully retrieved from memory, its representation in memory is
  changed such that it becomes more recallable in the future … often
  greater than the benefit resulting from additional study" [S2].
  Strength: **strong**. Underwrites a *retrieval-first* review session
  (question shown before answer — never the answer exposed alongside the
  question).
- **Delayed feedback can be a feature, not a bug.** Delayed feedback is
  listed among desirable difficulties: it "might slow down learning
  initially" while improving long-term performance; the achievability
  requirement is that "the task must be able to be accomplished — too
  difficult a task may dissuade the learner" [S9]. For a review UI: it is
  fine — and more honest — that a wrong answer's repair shows up as a
  *rescheduled review* rather than an instant correction celebration.
  Immediate correctness feedback at reveal is standard and fine; do not
  add instant commentary that short-circuits retrieval. Strength:
  **moderate** (timing studies are mixed; Hattie & Timperley: feedback
  "can be either positive or negative" depending on type, with timing
  among the "typically thorny issues" [S15]).
- **Failure framing in review:** Anki's manual is the best practitioner
  model — `Again` means "incorrect or couldn't recall," with explicit
  honesty norms ("if it counts as a fail in a real-life context … then
  it counts as a fail in Anki as well"), and the expected distribution is
  Again ~5–20%, Good ~80–95% — i.e. **failure during review is a normal,
  expected event with its own button, not an alarm** [S10]. FSRS framing
  reinforces it: forgetting drives the schedule; Anki's docs caution
  against over-reading retention on young cards and note the
  retention-vs-time tradeoff is non-linear ("to increase our retention by
  5 percentage points, we would have to study 35% more frequently")
  [S16]. Strength: **strong for the norm structure; moderate for the
  numbers**.
- **SuperMemo's remarks** (Wozniak's *20 rules*): supermemo.com and
  supermemo.guru were 403/404 this session — *known-literature*. Rules
  relevant here: *minimum information principle* (small, simple items
  fail less), *do not learn if you do not understand*, *build upon the
  basics*. These bind SkillTrace's **artifact specs and gates** (what
  counts as evidence) — a curriculum-authoring concern, not UI.

### 2.5 Motivation architecture

- **SDT (autonomy / competence / relatedness):** "Conditions supporting
  the individual's experience of autonomy, competence, and relatedness
  are argued to foster the most volitional and high quality forms of
  motivation and engagement … including enhanced performance,
  persistence, and creativity"; need-thwarting contexts have "a robust
  detrimental impact on wellness" [S4]. For a **single-user tool**,
  relatedness has no social surface; its honest local translation is
  *connection to purpose* (why this node matters, what it unlocks), not
  social features. Strength: **strong** as a framework (large literatures
  in education and health domains).
- **Autonomy:** never nag with fake urgency; recommendations reorder and
  warn (SkillTrace's advisory-policy principle matches SDT's
  autonomy-supportive vs controlling distinction). Controlling mechanics
  — must-do-today banners, guilt copy — are the anti-pattern [S4].
- **Competence:** optimal challenge + visible per-topic mastery (R1's
  position-and-mastery finding) [S4][S2].
- **Implementation intentions — the best-evidenced single intervention
  here for *follow-through*.** Gollwitzer & Sheeran's meta-analysis (94
  studies) found d ≈ 0.65 on goal attainment (*known-literature*: paper
  unreadable this session; corroborated via the Wikipedia article's
  citation apparatus [S1]; the implementationintention.com project page
  was unreachable). Mechanism: an if-then plan ("If it is 9am Monday,
  then I start the session for node X") delegates initiation to a cue,
  repairing the intention–behavior gap ("intentions account for only
  20% to 30% of the variance in behavior" [S1]). Moderators: stronger
  for difficult goals and scarce opportunities; documented limitation —
  negative effect for socially-prescribed perfectionists (Powers,
  Koestner & Topciu 2005) [S1]. **Interface translation:** an optional,
  learner-initiated *planning prompt before a session* ("when will you
  work on this, and what will you produce?") stored as a note — never a
  blocking modal, never auto-generated pressure. Strength: **strong**
  (meta-analytic), with a **moderate** caveat on universality.
- **Proximal goals:** goal-proximity effects (Bandura & Schunk 1981,
  cited in [S1]) support breaking a node into visible next steps —
  SkillTrace's Mentor section already carries "Do this next" as a
  canonical heading.

### 2.6 Trust & honesty (the evidence-gated model)

- **The gate should be shown, not hidden and not celebrated over.** The
  honest interface states the rule on every relevant surface: *passed*
  requires accepted evidence by a non-AI authority; *mastered* requires a
  later confirmed review; nothing demotes. Concretely: a node view's
  state line should carry the *reason* ("passed — 2 gate-run receipts,
  evidence accepted 2026-05-01"), and when a pass is refused by a gate
  the refusal names the missing evidence. This is the same transparency
  move as Anki exposing Desired Retention plus interval previews on its
  answer buttons [S10][S16], and it matches SkillTrace's existing
  honesty-banner convention for portfolio exports.
- **Celebration without false claims:** celebrate *events that happened*
  (evidence accepted, node passed, review batch cleared) with factual
  copy ("Evidence record #12 accepted — node 42 is now passed"), never
  forward-looking or comparative claims ("you're ahead of 90% of
  learners!", "your memory is now 95% strong!"). The deceptive-patterns
  taxonomy maps the adjacent failure modes precisely — *fake social
  proof*, *fake urgency*, *fake scarcity*, *confirmshaming*, and the
  newer **Addictive Design** category ("design exploits psychological
  vulnerabilities to foster compulsive behaviour") [S17]. None of these
  require deception about the *learner's own data* to fire — which is
  why SkillTrace's rule is: **every displayed number must be derived from
  repo state** (derived readiness computed from the graph; asserted
  progress from the store).
- **Loss-framing of progress is the bright line.** Duolingo's streak
  mechanics are honest *about what they are* (a consistency counter with
  loss aversion attached [S8]); SkillTrace's equivalent pressure surface
  (retention pressure, overdue reviews) must attach loss framing to the
  **memory**, never to a metronome: "3 reviews are overdue; forgetting
  is expected — they'll still be there tomorrow" rather than "you broke
  your streak." Asserted progress never demotes (repo invariant) — the
  UI must never imply it did.

### 2.7 The review moment (SRS-specific)

- **One decision per screen, retrieval-first, keyboard-first.** Anki's
  flow is the de-facto standard: question only → `Show Answer` (Space) →
  grade with 1–4, where each button **previews the interval it will
  produce** ("Each answer button shows the next time a card will be
  reviewed again if you select that button" [S10]). Interval preview is
  the strongest verified *honesty* device in SRS UI: it converts grading
  from a judgment into an informed scheduling choice. Strength:
  **strong practitioner consensus; moderate research**.
- **Self-grading norms must be stated in the UI.** Anki's manual spells
  out what each button means and warns toward strictness on partial
  answers [S10]. A review UI that hides grading semantics trains noisy
  data — and SkillTrace's retention analytics depend on honest grading.
- **10-second rule:** "if you can't answer within about 10 seconds, it's
  probably better to move on and show the answer than keep struggling to
  remember" [S10] — a practitioner norm, worth surfacing as guidance
  copy, not enforcement. Strength: **weak/practitioner**.
- **The schedule owns the pressure, transparently.** FSRS-era practice
  exposes the one policy knob (Desired Retention, default 0.9), a
  *Help Me Decide* helper, and a simulator [S16]; the FSRS project
  frames the deal as scheduling "according to the FSRS algorithm" with
  parameters fit to *your* review history [S18]. SkillTrace carries
  retention pressure via review scheduling; the honest surface is
  **counts + next-interval previews + "why this is due"**, never
  emotional urgency. Retention dashboards should carry the same caution
  Anki's docs do about young-card noise [S16].
- **Backlog mercy:** Anki's *Falling Behind* behavior — prioritize
  longest-waiting cards, fold the delay into scheduling, "you don't have
  to start anew and can just start back from where you left" [S10] — is
  the concrete model for SkillTrace's overdue surface: never an
  ever-growing shame counter; always a *resumable* queue.

## 3. Candidate-preferences table

Direct input to G-Preferences (apply / reject / defer). Each row is an
interface-preference statement; "Evidence" grades the underlying claim,
not the fit.

| # | Candidate preference | Evidence | Sources |
|---|---|---|---|
| P1 | **Starting today's focus takes one click from the home view** — one obvious primary action ("start session"). | Moderate (Fogg framework) + consistent product practice | [S3], R1 |
| P2 | **Review UI is retrieval-first and keyboard-first:** question before answer; one key reveals; one key grades; zero friction inside the loop. | Strong (testing effect + practitioner consensus) | [S2], [S10], [S14] |
| P3 | **Grading buttons preview the interval they produce** and state grading semantics (incl. strictness on partial answers) inline. | Moderate | [S10], [S16] |
| P4 | **Failure during review is framed as a normal scheduling event** (Again ~5–20% expected), never alarm or shaming; wrong answers reschedule, they don't scold. | Strong (norm structure) | [S9], [S10] |
| P5 | **Progress salience = position-and-competence** (node state, per-topic mastery map, "what moved today"), derived entirely from repo state. No XP, no leaderboards. | Moderate | [S4], [S5], R1 |
| P6 | **No streaks, no loss-framed metronomes.** Overdue pressure attaches to memory ("reviews are waiting"), never to a broken-run counter; missed days never read as learner failure. | Moderate (streaks show both the retention effect and the break-and-quit failure mode) | [S8], [S17] |
| P7 | **Any synthetic progress advancement (endowed progress, pre-checked bars, fake head starts) is prohibited** as a deceptive pattern. | Moderate + taxonomy | [S7], [S17] |
| P8 | **Acceptance moments (pass/mastery) are explicit, single, self-explanatory actions that state their consequence** ("records pass on node X; evidence A, B attached"); friction = clarity, not maze. | Moderate UX + strong repo constraint | §2.2, CONTEXT.md |
| P9 | **Session surface shows one item + counts; everything else (evidence detail, gate receipts, analytics) behind progressive disclosure.** Whitespace, one idea per panel, standard mental-model layouts. | Strong | [S11], [S12], [S13] |
| P10 | **Optional pre-session planning prompt** ("when will you do this / what will you produce?") — learner-initiated, stored, never blocking, never auto-nagging. | Strong (meta-analytic d≈0.65, perfectionism caveat) | [S1] |
| P11 | **State lines carry reasons**: every node view states why it holds its state ("passed — evidence accepted <date>; 2 receipts"); every refusal names the missing evidence. | Moderate (transparency as trust device) + strong repo fit | §2.6, [S10], [S16] |
| P12 | **Overdue is resumable, never a shame counter**: longest-waiting first, delay folded into scheduling, copy says "start back where you left." | Moderate | [S10] |
| P13 | **Celebration copy is factual** ("evidence accepted — node now passed"), never comparative or predictive ("you're ahead of…", "your memory is 95%"). | Strong (follows from deceptive-pattern taxonomy + repo honesty rules) | [S17], §2.6 |
| P14 | **Retention-pressure surfaces show counts, next-interval preview, and "why due"; retention dashboards warn against reading young-card noise.** | Moderate | [S10], [S16], [S18] |
| P15 | **Relatedness rendered as connection-to-purpose** (what this node unlocks, what it's for) rather than social features. | Speculative (SDT extension to single-user tools; no direct study found) | [S4] |
| P16 | **~10-second recall guidance surfaced as advisory copy** in review help, not enforcement. | Weak/practitioner | [S10] |
| P17 | **SuperMemo-derived constraint on gates/artifact specs**: evidence should test minimum, understood units; do not gate on what was never understood. | *known-literature* (blocked source; curriculum-side concern, not UI) | §2.4 |

**Fashionable-but-unsupported (explicit rejects for G-Preferences to
confirm):** XP/points, leaderboards, coins, streak counters, fake urgency
("only 2 hours left today!"), synthetic head-start bars, confetti over
predicted (rather than accepted) outcomes, motivational copy implying
demotion risk on missed days.

## 4. Sources

All URLs accessed 2026-09-14.

- [S1] Implementation intention (Wikipedia; cites Gollwitzer 1999,
  Gollwitzer & Sheeran 2006 meta-analysis, Powers et al. 2005):
  https://en.wikipedia.org/wiki/Implementation_intention
- [S2] Bjork Learning and Forgetting Lab — research overview (testing
  effect, spacing, metacognitive biases): https://bjorklab.psych.ucla.edu/research/
- [S3] Fogg Behavior Model (B=MAP quotes): https://behaviormodel.org/
- [S4] Self-Determination Theory overview: https://selfdeterminationtheory.org/theory/
- [S5] Amabile & Kramer, "The Power of Small Wins," HBR May 2011:
  https://hbr.org/2011/05/the-power-of-small-wins
- [S6] Fogg Behavior Model — Ability/Prompt pages: https://behaviormodel.org/ability/
- [S7] Nunes & Drèze, "The Endowed Progress Effect: How Artificial
  Advancement Increases Effort" (2006), Semantic Scholar record
  (DOI 10.1086/500480, 279 citations):
  https://api.semanticscholar.org/graph/v1/paper/search?query=endowed+progress+effect
- [S8] Duolingo, "The habit-building research behind your Duolingo
  streak" (2022): https://blog.duolingo.com/how-duolingo-streak-builds-habit/
- [S9] Desirable difficulty (Wikipedia; Bjork 1994; delayed feedback,
  retrieval practice, achievability requirement):
  https://en.wikipedia.org/wiki/Desirable_difficulty
- [S10] Anki Manual — Studying (question/answer flow, Again/Hard/Good/Easy
  semantics and honesty norms, interval previews on buttons, falling
  behind, shortcuts): https://docs.ankiweb.net/studying.html
- [S11] Whitenton (NN/g), "Minimize Cognitive Load to Maximize Usability"
  (2013): https://www.nngroup.com/articles/minimize-cognitive-load/
- [S12] Working memory (Wikipedia; capacity limits, Daneman & Carpenter
  1980, academic-achievement correlations):
  https://en.wikipedia.org/wiki/Working_memory
- [S13] Nielsen (NN/g), "Progressive Disclosure" (2006):
  https://www.nngroup.com/articles/progressive-disclosure/
- [S14] Rowland 2014, "The effect of testing versus restudy on retention:
  a meta-analytic review of the testing effect," *Psychological Bulletin*
  (Semantic Scholar record, 971 citations):
  https://api.semanticscholar.org/graph/v1/paper/DOI:10.1037/a0037559
- [S15] Hattie & Timperley 2007, "The Power of Feedback," *Review of
  Educational Research* (Semantic Scholar record with abstract):
  https://api.semanticscholar.org/graph/v1/paper/DOI:10.3102/003465430298487
- [S16] Anki Manual — Deck Options (FSRS, Desired Retention,
  retention-vs-time tradeoff, young-card caution):
  https://docs.ankiweb.net/deck-options.html
- [S17] Brignull et al., Deceptive Patterns — type taxonomy incl.
  Addictive Design, fake urgency/scarcity, confirmshaming:
  https://www.deceptive.design/types
- [S18] FSRS4Anki (open-spaced-repetition):
  https://github.com/open-spaced-repetition/fsrs4anki
- [S19] gwern, "Spaced Repetition for Efficient Learning" (secondary
  literature review; testing-effect and spacing references):
  https://gwern.net/spaced-repetition

*known-literature (unverified this session, never load-bearing):*
Gollwitzer & Sheeran 2006 meta-analysis (d≈0.65, 94 studies); Kivetz,
Urminsky & Zheng 2006 goal-gradient; van der Kleij et al. 2015 feedback
meta-analysis; Wozniak, "Twenty rules of formulating knowledge"
(supermemo.com / supermemo.guru returned 403/404);
characterlab.org "Plans are not wishes" (404; site restructure).
