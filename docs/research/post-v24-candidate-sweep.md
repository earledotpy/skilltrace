# Post-v2.4 candidate sweep — docs/ and archive/ (R-MineDocsArchive #278)

**Branch:** `research/post-v24-candidate-sweep` · **Ticket:** #278 · Read-only sweep

This is a read-only research sweep over the archive framework documents
(`archive/skill-graph-*.md`), the existing `docs/research/` corpus, the PRD,
ADRs 0003–0005, the application roadmap, and the curriculum-authoring guide.
Its purpose is to extract candidate features or directions for **post-v2.4**
SkillTrace that are **not already captured** by shipped or planned work
(adaptive sequencing + FSRS retention overlay v2.1, gate-run receipts +
graph-impact diagnostic v2.2, polite resource sweeps v2.3, the interface
sublayer / View-Card-Command / P3 card-stack Today / NextAction /
days-practiced mirror v2.4, learner-facing diagnostic analytics, practice
profiles + prompt extraction, badge issuance, MC/PKM Tier 3 integrations,
capstone seed graphs, gate-runner/scheduler-queue, verification-sweep
scheduling, resource deep-verification, cloud sync, Elo/BKT modeling,
generative AI tutoring, auto-master/auto-pass, LLM-graded evidence,
multi-learner, portfolio export, mentor voice, overdue review, event-log
analytics). No engine, graph, or policy files were changed. Each entry records
source, idea, fit against `CONTEXT.md` language and the hard boundaries, and a
preliminary graduate/reject/defer read.

---

## archive/skill-graph-5-pillar-framework.md

- **Candidate: dynamic remedial sub-node proposals ("Adaptive Remediation Path")**
  - **Source:** §1.2 "Adaptive Sequencing and Remediation"; §4.3 diagnostic injection of targeted reading into micro-sessions.
  - **Idea:** when a node's evidence repeatedly fails, propose (advisory) remediation targets — including *authoring suggestions* for new bridge nodes homed in their natural domain.
  - **Fit:** works as an advisory policy that reorders recommendations and surfaces authoring proposals; it must never lock or auto-route. Material "injection" is fine only as a recommendation, never a mandate.
  - **Preliminary read:** **defer** — remediation edges + remediation-track nodes already exist; the genuinely new part (advisory authoring suggestions for missing remediation nodes, derived from Blockers) is small and worth a later slot.

- **Candidate: predictive velocity bottleneck warnings**
  - **Source:** §4.2 items 3–4 (predictive/prescriptive analytics on node completion times).
  - **Idea:** forecast which upcoming nodes will be slow due to weak upstream competence.
  - **Fit:** advisory-only forecasting over existing records is compatible; the doc's *prescriptive* form ("pause current progress") would be a mandate.
  - **Preliminary read:** **defer** — n=1 data volume makes prediction close to the "dashboard theatre" failure mode named in `archive/skill-graph-framework.md`; revisit only if v2.x analytics show stable patterns.

## archive/skill-graph-compentency-based.md

- **Candidate: confidence self-report as an execution fact**
  - **Source:** §4.1 data-collection list (`self_report_confidence` alongside time-on-task).
  - **Idea:** let the learner optionally record a confidence rating with session work; analytics can then show divergence between confidence and gate outcomes.
  - **Fit:** purely learner-entered execution data, advisory analytics only; no state changes. Aligns with evidence-gated honesty — divergence flags are commentary.
  - **Preliminary read:** **graduate** — cheap, additive, single-writer compatible, and it strengthens the existing learner-facing diagnostic analytics without any authority change.

- **Candidate: xAPI-shaped derived export**
  - **Source:** §5.1 xAPI-compliant LRS statements from local scripts.
  - **Idea:** an optional derived export rendering events/work/evidence coverage as xAPI-like statements.
  - **Fit:** exports are derived and never read back (roadmap invariant); no authority implications.
  - **Preliminary read:** **defer** — portfolio export is already captured; an xAPI flavor is speculative without a consuming tool.

- **REJECTED-SOURCE ideas from this doc:** federated anonymized BKT sharing (multi-learner/cloud — violates single-learner, local-first); peer-matching/accountability pairing (multi-learner by design); LLM-as-judge feeding mastery (VIOLATES BOUNDARY: AI as acceptance authority); Open Badges auto-issued on computed thresholds (badge *issuance* is captured; the automatic-on-metric trigger is rejected — issuance must follow learner pass/master, never a computed probability).

## archive/skill-graph-self-directed.md

- **Candidate: selective diagnostic tracing on a failure-rate threshold**
  - **Source:** §4.3 — diagnostic modeling applied only when formative failure exceeds 40% over 3 attempts, tracing back through prerequisites to the weakest ancestor.
  - **Idea:** a thresholded, read-only "root-cause prerequisite trace" report when a node's attempts keep failing.
  - **Fit:** read-only diagnostic over attempts + `edges.yaml`; complements the v2.2 graph-impact diagnostic (which is curriculum-edit-facing, not attempt-facing).
  - **Preliminary read:** **graduate** — a natural, boundary-safe sibling to the graph-impact diagnostic; pure derivation, advisory output.

- **REJECTED-SOURCE ideas:** BKT-driven scheduler *blocking* dependent nodes when P(Know) < 0.75 (VIOLATES BOUNDARY: advisory policies never lock; only hard prerequisites lock); consecutive-correct heuristics as automatic advancement (auto-pass — VIOLATES BOUNDARY: pass is an explicit learner command).

## archive/skill-graph-system-design.md

- **Candidate: passive telemetry from git hooks / shell history**
  - **Source:** §4.1 — git hooks and Bash-history parsers push xAPI payloads.
  - **Idea:** automatically harvest work artifacts from the learner's normal tooling.
  - **Fit:** harvesting itself is not forbidden, but auto-*recording* evidence or auto-updating node state from hooks would cross lines; a harvesting *assistant* (staging, not submitting) is conceivable.
  - **Preliminary read:** **defer** — evidence submission deliberately includes the learner's judgment act (ADR 0003); automation that removes friction here removes the accountability the design intends.

- **REJECTED-SOURCE ideas:** "temporarily locking the active node" during remediation (locks are hard-prerequisite-only); mastery threshold auto-triggering graph unlocks (VIOLATES BOUNDARY: pass/master are learner commands); Ed25519-signed badge automation (issuance captured; the automatic trigger rejected as above).

## archive/skill-graph-ai-learning-framework.md

- **Candidate: peer/community validation as an evidence flavor**
  - **Source:** competency definition (10% peer/community validation; code reviews, teaching others).
  - **Idea:** accept external human review (e.g., a real code-review comment) as *learner-manual* evidence artifacts.
  - **Fit:** fits already — a human reviewer's artifact can be attached under the existing `learner_manual` authority; no new authority is created.
  - **Preliminary read:** **defer** — no engine change needed today; this is authoring/usage doctrine (document that third-party review artifacts are valid manual-evidence artifacts), not a v2.x feature.

- **REJECTED-SOURCE ideas:** tiered percentage mastery thresholds driving tiered gates (reduces acceptance to scoring; SkillTrace gates accept/reject, learners pass); PostgreSQL/Streamlit dashboard stack (violates files-are-truth, local-first CLI posture); Elo-driven adaptive problem sets as a scheduling authority (Elo/BKT already captured and bounded to advisory).

## archive/skill-graph-framework.md

- **Candidate: "rigor-as-avoidance" visibility report**
  - **Source:** Closing, standing failure mode 3 — "if the learner is repeatedly pulling math nodes that no downstream failure implicated, that is the signal."
  - **Idea:** a read-only advisory report flagging study patterns that no downstream failure has implicated (avoidance-shaped effort).
  - **Fit:** advisory commentary over derived data; no reordering beyond existing policy weights; warns, never blocks.
  - **Preliminary read:** **graduate** — cheap, distinctive, deeply aligned with SkillTrace's "is my progress real?" problem statement.

- **REJECTED-SOURCE ideas:** auto-closing nodes when objective gates pass ("node auto-closes on gate pass" — VIOLATES BOUNDARY: explicit learner-only pass/master); predictive analytics steering decisions (the doc itself labels this dashboard theatre and calls for removal if it starts steering — adopt that containment, not the feature).

## archive/skill-graph-learning-framework.md

Nothing new. (Personalized pathways, modularity, badges, hybrid feedback,
micro-credential governance, and community/mentorship are either captured,
generic, or rejected — see the consolidated rejected list.)

## archive/skill-graph-architecture.md

- **Candidate: co-requisite edge semantics**
  - **Source:** §1.3 edge table — co-requisite (`↔`) pairs engage concurrently; mastery of one cannot finalize until the other reaches a floor.
  - **Idea:** a fourth edge type for pedagogically-paired nodes.
  - **Fit:** touches `edges.yaml` schema (deliberately pruned to three types in design decision 4) and would *gate* pass eligibility on a non-prerequisite relation — a soft lock by another name.
  - **Preliminary read:** **reject** — the minimal-locking doctrine in `docs/curriculum-authoring.md` exists precisely to keep walls rare; a co-requisite is a hidden hard edge. Soft prerequisites plus advisory nudges cover the need.

- **REJECTED-SOURCE ideas:** four-level competency spectrum (Emerging→Mastered) replacing the five node states (glossary states are settled); documented-rationale override of soft prerequisites (the pruned edge schema deliberately deleted `can_override`); learner "risk acknowledgment narratives" for overrides (normalizes hard-boundary workarounds — boundaries are not configurable, ADR 0004).

## docs/research/cross-repository-gap-analysis.md

- **Candidate: environment provenance on evidence records**
  - **Source:** §"Open questions" #2 (interpreter version, package-lock hash, OS, working-tree commit in EvidenceRecord).
  - **Idea:** optional structured environment fields captured at submission for reproducibility.
  - **Fit:** additive fields on the frozen-at-submission record (ADR 0003); immutable by construction; strengthens auditability.
  - **Preliminary read:** **graduate** — small backward-compatible schema addition, high honesty value for procedural nodes.

- **Candidate: gate execution safety policy**
  - **Source:** §"Open questions" #3 (opt-in network denial, timeout enforcement, subprocess isolation for learner-supplied gate commands).
  - **Idea:** an explicit, documented execution contract for objective gates instead of implicit subprocess behavior.
  - **Fit:** pure hardening of the existing objective-gate authority; no boundary interaction.
  - **Preliminary read:** **graduate** — gates now exist and run real commands; the trust model should be settled before more gate-runner surface ships.

- **Candidate: advisory efficiency/effort metrics in gate observations**
  - **Source:** §"Open questions" #4; corroborated by `vimhjkl-drill-vs-skilltrace.md` open question #1.
  - **Idea:** optional structured gate observations (runtime, token count, keystrokes) recorded as advisory commentary, never acceptance criteria.
  - **Fit:** safe only as commentary on evidence, not verdict inputs; freeze-at-submission keeps them honest.
  - **Preliminary read:** **graduate** — small, and answers the "portable challenge contract" question opened by the vimhjkl research.

- **Candidate: provenance policy for regenerated curriculum**
  - **Source:** §"Open questions" #6 (what happens when a source document changes).
  - **Idea:** a documented decision procedure (new node vs. in-place edit vs. material redefinition) for curriculum regeneration.
  - **Preliminary read:** **defer** — doctrine, relevant only when practice profiles + prompt extraction (captured) start producing candidates in volume.

- **Candidate: diagnostic output tiers for gate runs**
  - **Source:** §"Open questions" #12; mirrored in `evidence-provenance-and-operational-contracts.md` decision row 9.
  - **Idea:** default to summary/hash; opt-in bounded sanitized excerpt; explicit local artifact attachment.
  - **Preliminary read:** **graduate** — a privacy-and-storage contract that should land as the v2.2 receipt work matures.

- **Candidate: failure-visibility decision for failed gate runs**
  - **Source:** §"Open questions" #13 (should failed objective gates create AssessmentAttempts?).
  - **Preliminary read:** **defer** — the doc itself flags the conflation risk; needs a grilling, not a roadmap slot.

- **Candidate: minimal plugin seam as a subprocess gate adapter**
  - **Source:** §"Open questions" #14.
  - **Preliminary read:** **defer** — introduces an alternate writer; only after the gate contract above is stable.

## docs/research/ten-repository-additive-adoption-roadmap.md

- **Candidate: fail-loudly seed validation for curriculum tokens**
  - **Source:** Numo row of the candidate table ("fails a build on an unclassified curriculum token"); adoption disposition says "reuse fail-loudly seed validation."
  - **Idea:** extend graph/resource validation so unknown track/namespace/policy tokens fail validation rather than warn-and-score-0.
  - **Fit:** pure validation hardening; consistent with existing duplicate/dangling/cycle checks.
  - **Preliminary read:** **graduate** — the adoption roadmap itself endorses it; it simply hasn't been slotted.

- **Nothing else new from this doc.** Its other rows resolve to captured or
  boundary items: engram grading receipts → shipped as v2.2 gate-run
  receipts; Anki card-scheduler and Numo computed-mastery → rejected
  (complexity boundary; asserted progress never moves backward);
  learn-faster-kit mode-specific workflows + Urnote review-task convention →
  captured (practice profiles + prompt extraction); the "explicitly avoid"
  table (auto-pass/AI acceptance, anchor-driven ordering, plugin/sync/mobile,
  revived interface registry) restates engine constants (ADR 0004) and the
  Beyond list. Its adoption gate is doctrine, not a candidate.

## docs/research/top10-similarity-evidence-matrix.md

- **Candidate: atomic temp-file writes + corrupt-file quarantine for state files**
  - **Source:** engram row — atomic temp-file replacement and corrupt-JSON quarantine on its local store.
  - **Idea:** write progress/state YAML through a temp-file + atomic rename, and quarantine (rename aside, surface loudly) any state file that fails parse instead of failing a command mid-write.
  - **Fit:** pure durability hardening of the single write path; no authority or state-semantics change; quarantining never mutates or repairs records.
  - **Preliminary read:** **graduate** — small, protects the one source of truth, no boundary interaction.

## docs/research/r1-learning-app-daily-loop-uiux-trends-2023-2026.md

- **Candidate: scheduler transparency surface (interval previews + retention helper)**
  - **Source:** §1 finding 3 — Anki FSRS "Desired Retention" / "Help Me Decide" / interval-preview buttons; Mochi next-due tooltips.
  - **Idea:** make the v2.1 retention overlay's math a product surface: preview which interval a completed review will produce, and offer a read-only "help me decide" helper for the desired-retention policy value.
  - **Fit:** advisory transparency over the captured FSRS overlay; schedules advice, never flips states; no boundary risk.
  - **Preliminary read:** **graduate** — extends an existing shipped overlay with explainability, in the spirit of the `graph impact` diagnostic.

- **Already v2.4 (not candidates):** human-register translation of engine
  vocabulary (the P3.1 forbidden-vocabulary seam), today-first home with one
  continue affordance (the P3 card-stack Today), calm server-rendered visual
  direction with one analytics theme per page (v2.4 design tokens + themes).

## docs/research/r1-daily-loop-trends.md

- **Candidate: reductive mastery-level framing of the five states**
  - **Source:** C8 (Brilliant) and P3 — render states as a simple per-topic "level" language with derived percent-complete.
  - **Fit:** presentation-only, but flattens glossary semantics (locked is a wall, not a low level) and a derived percent invites dashboard theatre, which `archive/skill-graph-framework.md` names as a standing failure mode.
  - **Preliminary read:** **defer** — only as an optional label layer with strict copy rules, if ever; the state names themselves stay.

- **Already v2.4 (not candidates):** human-register copy pairing, one-CTA daily
  screen, backlog hidden behind queue/health (card-stack Today).
- **REJECTED-SOURCE ideas from this doc:** streak counters without slack
  framing (the days-practiced ruling forbids streak mechanics; return only
  via a fresh preference-table effort).

## docs/research/r2-learning-ux-preferences.md

- **Candidate: honesty display contract**
  - **Source:** §2.6 + the deceptive-patterns taxonomy [S17].
  - **Idea:** a written display rule: celebrate only events that happened (evidence accepted, node passed) with factual copy; ban fake urgency, synthetic endowed-progress bars, social proof, and forward-looking claims from every surface.
  - **Fit:** codifies "asserted progress never moves backward" and evidence honesty as a UI/display contract; touches no authority.
  - **Preliminary read:** **graduate** — cheap, distinctive, invariant-strengthening; natural v2.4 follow-up.

- **Candidate: "what moved today" progress summary**
  - **Source:** §2.1 (Amabile & Kramer progress principle).
  - **Idea:** surface what actually changed today (node activated, artifact accepted, review batch cleared) instead of vanity counters.
  - **Fit:** pure derivation from existing records; competence feedback is the validated motivator; advisory read-only.
  - **Preliminary read:** **graduate** — small learner-value addition; distinct from captured diagnostic analytics (which answers "why stuck", not "what moved").

- **Candidate: backlog mercy — non-punitive overdue re-entry**
  - **Source:** §2.7 (Anki "Falling Behind") + r1-learning-app… §1.6.
  - **Idea:** overdue surfaces prioritize longest-waiting items and read as "resume where you left," never an ever-growing shame counter or reset.
  - **Fit:** advisory pressure only; folds delay into ordering, warns not blocks; no demotion language.
  - **Preliminary read:** **graduate** — direct expression of the mirror-not-metronome ruling.

- **Candidate: stated self-grading norms (10-second rule)**
  - **Source:** §2.7 (Anki manual [S10]).
  - **Idea:** surface grading semantics and strictness guidance ("move on after ~10s") as copy, never enforcement.
  - **Fit:** protects the honesty of the review data retention analytics depend on; advisory copy only.
  - **Preliminary read:** **graduate** — tiny, practitioner-backed.

- **Candidate: delayed feedback as designed repair**
  - **Source:** §2.4 (desirable difficulty [S9]).
  - **Idea:** a wrong answer's correction resurfaces as a scheduled review rather than an instant inline fix, framed as desirable difficulty.
  - **Fit:** consistent with review-evidence and no-demotion rules; purely presentational stance.
  - **Preliminary read:** **graduate** — as design doctrine; the mechanism is the existing review schedule.

## docs/research/what-can-skilltrace-learn-from-comparable-open-sourced.md

- **Candidate: external curriculum-import provenance fields**
  - **Source:** §6 (OSMT/OpenSALT) — an `external:` metadata block (source, source_uri, source_uuid, source_commit, imported_at, mapping_policy).
  - **Idea:** when importing curriculum metadata from external frameworks, carry structured provenance fields that never imply learner state.
  - **Fit:** curriculum-side seed data only; touches nothing learner-owned; never imported as edges or gates without human review.
  - **Preliminary read:** **defer** — belongs to the captured Tier 3 multi-curriculum effort (MC-1/MC-2) when that re-opens.

- **Candidate: typed rule outcomes / explainable eligibility**
  - **Source:** §3 (Moodle) + the repo's own `reasons:` example — eligibility derived as typed outcomes with per-reason explanations (`evidence_gate: satisfied`, `hard_prerequisites: satisfied`, `asserted_pass: missing`).
  - **Fit:** read-only derivation; strengthens "eligibility is derived on demand"; the "why not eligible" surface is captured in spirit by learner-facing diagnostic analytics, but the typed rule-outcome contract itself is not.
  - **Preliminary read:** **defer** — fold into the captured diagnostic-analytics item as its explainability contract, not a separate slot.

- **REJECTED-SOURCE ideas from this doc:** Moodle-style mutable completion
  rows and instructor override (asserted progress never moves backward; no
  override authority); Open Badges/CASE/QTI as replacement state machines;
  event replay as state reconstruction (event log is audit-only); Logseq's
  database-as-authority (files-are-truth); imported associations silently
  becoming hard prerequisites.

## docs/research/mnemosyne-ankidroid-vs-skilltrace.md

- **Candidate: review-time / statistics derived views**
  - **Source:** §3 "Statistics and derived views" (Mnemosyne's per-card and per-activity statistics).
  - **Idea:** read-only statistics over review latencies and per-node review outcomes as derived views.
  - **Fit:** derived-only, never read back; feeds the existing retention model's inputs; no state writes.
  - **Preliminary read:** **defer** — overlaps v1.5/v1.6 analytics; add only if the retention overlay's consumers ask for latency breakdowns.

- **REJECTED-SOURCE ideas from this doc:** remote sync with upload/download
  conflict semantics (cloud sync stays boundary-gated); telemetry/science-log
  upload; persistent review-queue cursor (recommendation stays pure and
  explainable).

## docs/research/vimhjkl-drill-vs-skilltrace.md

- **Candidate: one-tap correction/alias choice in review grading**
  - **Source:** §1 — drill's incorrect/correct/add-alias triad; vimhjkl's retry-without-commit.
  - **Idea:** low-friction correction flow (mark incorrect / correct without recording / correct and amend) as explicit learner choices in the review loop.
  - **Fit:** corrections stay learner-actuated; evidence stays immutable (supersede, never edit).
  - **Preliminary read:** **defer** — good pattern, needs the review-record interaction shape to exist first.

- **REJECTED-SOURCE ideas from this doc:** automatic progress authority from
  graded outcomes; demotion/re-scheduling on missed answers; SQLite as
  authoritative store.

## docs/research/evidence-provenance-and-operational-contracts.md

- **Candidate: single-writer serialization contract for concurrent mutations**
  - **Source:** §3 open question 2; corroborated by the AnkiDroid one-parallelism dispatcher finding.
  - **Idea:** specify repository-scoped write serialization, reload-after-success, and stale-write refusal/diagnostics before CLI + `serve` (or any plugin) can mutate concurrently.
  - **Fit:** protects the single-writer CLI/serve write path (a holding contract in the Beyond list); asserted-progress writes still route through core dispatch; advisory diagnostics only.
  - **Preliminary read:** **graduate** — v2.4's web surface makes concurrent CLI/serve writes plausible; a hardening prerequisite, not a feature.

- **Candidate: default-deny share profile for outbound output**
  - **Source:** §3 open question 7.
  - **Idea:** an explicit field-selection share profile (default redaction of paths/free text, opt-in telemetry, retention statement) for any outbound artifact (support bundle, shared report).
  - **Fit:** serves the single-learner local-first privacy posture; does not touch acceptance authority or progress.
  - **Preliminary read:** **graduate** — prerequisite for any export/share feature, small.

- **Candidate: portable evidence locator (root-relative path + hash + external URI)**
  - **Source:** §3 open question 10.
  - **Idea:** optional root-relative artifact locator with content hash and external identifier so evidence stays interpretable after a checkout moves or machines change.
  - **Fit:** a moved artifact becomes a health warning only — never retrospective unacceptance or demotion; records immutable by construction.
  - **Preliminary read:** **graduate** — solves a real longevity problem for a years-long repo without touching state semantics.

- **Candidate: eligibility-coverage metric with explicit denominator**
  - **Source:** §3 open question 8.
  - **Idea:** rename existing coverage to "required-spec presence coverage" and add a separately named, read-only eligibility coverage with an explicit denominator and data threshold.
  - **Fit:** diagnostic naming hygiene; the doc itself insists neither metric transitions state or changes recommendations.
  - **Preliminary read:** **graduate** — small, tightens learner-facing analytics honesty.

- **Already landed in v2.2 (not candidates):** environment provenance fields,
  gate execution safety policy, advisory gate observations (runtime/token/
  keystroke commentary), and diagnostic output tiers — these §3 open
  questions are answered by the shipped gate-run receipt schema and its
  optional bounded fields; residual depth is the captured Beyond items
  (deep verification / full gate-runner).
- **REJECTED-SOURCE ideas from this doc:** retrospective unacceptance for
  missing/moved artifacts (asserted progress never moves backward); coverage
  metrics claiming pass eligibility without separate advisory-policy law.

## docs/ai-engineering-roadmap.md

- **Candidate: seed-data cadence patterns (consolidation weeks, checkpoints)**
  - **Source:** Visual Timeline / Quick-Start / Maintenance sections.
  - **Idea:** curriculum seeds may include checkpoint exercises with expected outputs, quarterly consolidation weeks, and URL-staleness review checklists — as seed/policy values only.
  - **Fit:** confirms curriculum-agnosticism; cadence values enter as advisory seed data, never engine code or schedule authority.
  - **Preliminary read:** **defer** — authoring guidance, not an engine feature; belongs to the captured seed-graph work (Phase 4/5).

- **REJECTED-SOURCE ideas from this doc:** transcribing the roadmap's phase
  structure into engine prerequisites (anchors are `reference_only`);
  certificate tracking as engine progress (certificates remain seed data /
  portfolio input).

## docs/PRD.md, docs/adr/ (0005, 0006, 0008), application roadmap, curriculum-authoring

- **Nothing new.** The PRD's non-goals are all shipped or captured. ADR 0005
  rejects restoring the retired interface registry (mining archive as input
  is exactly this sweep); ADR 0006 keeps stdlib-only serve; ADR 0008
  triple-refused the days-practiced heatmap and keeps client writes
  unconfirmed. The application roadmap's deferred v1 items all shipped or are
  captured, and its "mastery is permanent, no decay/demotion" ruling rejects
  any decay-based candidate. Curriculum-authoring's grain guidance stays
  doctrine, not validator rules (engine-enforced doctrine would violate
  curriculum-agnosticism).

## Summary

**Graduates (14), best-first:**
1. Root-cause prerequisite trace on repeated failure (self-directed doc) — boundary-safe sibling of the v2.2 graph-impact diagnostic, attempt-facing.
2. "Rigor-as-avoidance" visibility report (framework doc) — cheap, distinctive, matches the core "is my progress real?" problem statement.
3. Confidence self-report as an execution fact (competency doc) — additive execution data enabling confidence-vs-outcome analytics.
4. Single-writer serialization contract (evidence-provenance) — hardening prerequisite made plausible by v2.4's web surface.
5. Atomic temp-file writes + corrupt-file quarantine (top10 matrix) — protects the one source of truth.
6. Portable evidence locator (evidence-provenance) — longevity for a years-long repo.
7. Scheduler transparency surface for the retention overlay (r1 2023-2026) — explainability for shipped v2.1 math.
8. Honesty display contract (r2) — codifies invariants as display rules.
9. Non-punitive overdue/backlog-mercy surface (r2) — mirror-not-metronome in language.
10. Fail-loudly seed validation (ten-repository roadmap) — endorsed by the source doc, unslotted.
11. Default-deny share profile (evidence-provenance) — privacy prerequisite for any export.
12. "What moved today" summary (r2) — small validated learner-value addition.
13. Eligibility-coverage metric with explicit denominator (evidence-provenance) — analytics honesty.
14. Self-grading norms copy rule + delayed-feedback-as-repair stance (r2) — small doctrine graduates.

**Defers:** xAPI-shaped export; remediation authoring suggestions; velocity
bottleneck warnings (n=1); peer/community validation as doctrine; passive
git-hook telemetry; seed cadence patterns; external import provenance (Tier 3);
typed rule-outcome eligibility (fold into diagnostic analytics); review-time
statistics; one-tap correction; sister-card suppression; reductive
mastery-level labels; streak-with-slack (preference-table effort only).

**Rejects:** co-requisite edge semantics (hidden hard edge); BKT-driven
blocking; auto-pass/auto-master/gate-auto-close; LLM-as-judge acceptance;
federated BKT sharing; peer-matching; automatic badge triggers; mutable
completion/override authorities; event replay as state; SQLite/database
authority; remote sync conflict semantics; telemetry upload; htmx/framework
deps; hard-boundary override narratives; dashboard-theatre predictive
steering.

**Note:** several r1/r2 UI candidates were excluded as already shipped in
v2.4 (forbidden-vocabulary seam, card-stack Today, design tokens/themes);
the evidence-provenance §3 receipt items were excluded as shipped in v2.2.
No engine, graph, evidence, execution, policy, or src/ file was modified in
this sweep.



