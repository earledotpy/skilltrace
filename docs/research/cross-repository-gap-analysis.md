# Cross-repository gap analysis for SkillTrace

**Research date:** 2026-09-03
**Scope:** Official GitHub repositories, repository source code, tests, and first-party documentation only.
**Evidence labels:** **Verified** means directly stated or implemented in an inspected primary source. **Inference** means a design implication for SkillTrace, not a claim made by the external project.

## Repository discovery

| Named repository | Canonical repository inspected | Relevance |
|---|---|---|
| Engram | [nagisanzenin/engram](https://github.com/nagisanzenin/engram) | Evidence-based learning, receipts, FSRS review |
| Anki | [ankitects/anki](https://github.com/ankitects/anki) | Mature spaced-repetition engine |
| Numo | [cashubtc/Numo](https://github.com/cashubtc/Numo) | **Not a learning project**; Android Cashu point-of-sale application |
| learn-faster-kit | [hluaguo/learn-faster-kit](https://github.com/hluaguo/learn-faster-kit) | AI coaching, syllabi, active practice, reviews |
| vimhjkl | [S-Sigdel/vimhjkl](https://github.com/S-Sigdel/vimhjkl) | CLI procedural practice with real Vim verification |
| Skill-Anything | [SYuan03/Skill-Anything](https://github.com/SYuan03/Skill-Anything) | Source material to study packs and agent skills |
| Mnemosyne | [mnemosyne-proj/mnemosyne](https://github.com/mnemosyne-proj/mnemosyne) | Mature flashcards, schedulers, plugins, sync |
| Drill | [rr-/drill](https://github.com/rr-/drill) | Simple CLI SRS with decks, tags, JSON, reports |
| developer-roadmap | [nilbuild/developer-roadmap](https://github.com/nilbuild/developer-roadmap) | Markdown-backed roadmap graph/content model |
| urnote | [urnote/urnote](https://github.com/urnote/urnote) | Markdown-native note review workflow |

---

## SkillTrace baseline used for the comparison

The comparison treats the following as already covered, rather than gaps:

- five node states, derived readiness, asserted progress, and immutable
  progress semantics (`CONTEXT.md:14-67`);
- objective-gate or learner-manual acceptance, immutable/superseding evidence,
  and explicit learner-only pass/master commands (`CONTEXT.md:131-178`);
- sessions, blockers, remediation, reviews, and advisory policies
  (`CONTEXT.md:244-353`);
- event-log analytics v1 and FSRS retention analytics, with adaptive sequencing
  still planned for v2.1 (`CONTEXT.md:355-399`,
  `docs/POST_V1_ROADMAP.md:29-50`).

**Inference:** A feature is ranked below only when the external projects expose
additional behavior or a contract that these baseline documents do not clearly
specify. “Not clearly discussed” is therefore narrower than “not implemented.”

## Executive summary

The closest comparators are **Engram**, **vimhjkl**, **Drill**, and **urnote**.
Engram most directly overlaps SkillTrace’s evidence-gated learning direction:
it combines a tutor, blind assessor, on-disk grading receipts, and
deterministic FSRS scheduling ([README.md lines 18-18](https://github.com/nagisanzenin/engram/blob/main/README.md#L18);
[README.md lines 119-128](https://github.com/nagisanzenin/engram/blob/main/README.md#L119-L128)).
`vimhjkl` demonstrates a particularly strong pattern for procedural skills:
authored challenges are machine-verified against real Vim, and learner attempts
are graded on correctness and efficiency ([README.md lines 14-18](https://github.com/S-Sigdel/vimhjkl/blob/main/README.md#L14-L18);
[engine.py lines 26-53](https://github.com/S-Sigdel/vimhjkl/blob/main/src/vimhjkl/engine.py#L26-L53)).
`Drill` and `urnote` demonstrate low-friction terminal workflows and
human-readable persistence ([Drill README.md lines 1-12](https://github.com/rr-/drill/blob/master/README.md#L1-L12);
[U rnote README.md lines 21-36](https://github.com/urnote/urnote/blob/master/README.md#L21-L36)).

Anki and Mnemosyne establish the depth of the spaced-repetition feature space, but their core abstractions are cards and schedulers rather than prerequisite graphs, evidence records, or explicit learner assertions. `developer-roadmap` provides a useful content/repository convention—one Markdown file per roadmap topic with stable node identifiers—but does not provide learner-state or evidence semantics. `learn-faster-kit` and Skill-Anything show how AI can generate syllabi, exercises, quizzes, and study packs, but they also reinforce SkillTrace’s distinction between generated/advisory content and authoritative learner progress.

Numo is a verified repository-name mismatch: the inspected project is a Cashu merchant POS Android application, not a learning system. It should not influence SkillTrace’s product roadmap except as a reminder that repository-name matching needs explicit canonical-repository verification.

---

## Findings by repository

### 1. Engram

**Verified facts**

- Engram describes itself as a human learning system with a tutor, blind assessor, and on-disk grading receipts.
  Source: [README.md lines 18-18](https://github.com/nagisanzenin/engram/blob/main/README.md#L18)
- It exposes learning and review workflows, including `/learn`, `/review`, and `/coach`.
  Source: [README.md lines 161-169](https://github.com/nagisanzenin/engram/blob/main/README.md#L161-L169)
- It uses deterministic FSRS-4.5 scheduling.
  Source: [README.md lines 119-128](https://github.com/nagisanzenin/engram/blob/main/README.md#L119-L128)

**Implications for SkillTrace**

- **Inference:** Engram validates the product value of keeping assessment receipts as durable artifacts rather than treating a review score as the only record of learning.
- **Inference:** SkillTrace should preserve its stronger authority boundary: an objective command or learner manual review may accept evidence, but an assessor or AI workflow must not directly assert `passed` or `mastered`.
- **Inference:** FSRS is a plausible future retention implementation, but it should remain an advisory scheduling layer over SkillTrace’s existing immutable evidence and permanent mastery semantics.

### 2. Anki

**Verified facts**

- The repository contains the source code for Anki’s computer version.
  Source: [README.md lines 7-8](https://github.com/ankitects/anki/blob/main/README.md#L7-L8)
- Anki is explicitly described as a spaced-repetition program.
  Source: [README.md lines 10-12](https://github.com/ankitects/anki/blob/main/README.md#L10-L12)

**Implications for SkillTrace**

- **Inference:** Anki demonstrates that a mature scheduler can be a deep subsystem in its own right; SkillTrace should avoid prematurely reimplementing a full card scheduler inside the graph/evidence engine.
- **Inference:** Anki’s card-centric model is complementary rather than equivalent. A SkillTrace node can eventually produce review prompts, but card scheduling should not replace node readiness, evidence eligibility, or explicit state assertion.
- **Gap:** The inspected README does not by itself establish a portable CLI, Markdown source-of-truth model, prerequisite graph, or evidence-gated pass workflow.

### 3. Numo

**Verified facts**

- The inspected `cashubtc/Numo` repository is an Android point-of-sale application for receiving Cashu ecash payments via tap-to-pay.
  Source: [README.md lines 7-10](https://github.com/cashubtc/Numo/blob/main/README.md#L7-L10)
- Its documented features include Cashu/NDEF tap-to-pay, Lightning BOLT11 invoices, catalogs, baskets, and payment history.
  Source: [README.md lines 23-35](https://github.com/cashubtc/Numo/blob/main/README.md#L23-L35)

**Implications for SkillTrace**

- **Verified conclusion:** This repository is unrelated to learning or skill graphs.
- **Inference:** No feature should be adopted from Numo for SkillTrace.
- **Gap:** “Numo” is ambiguous as a project name. A future comparison should confirm whether a different learning repository was intended before drawing product conclusions.

### 4. learn-faster-kit

**Verified facts**

- The project presents itself as an AI-powered learning coach using personalized syllabi, spaced repetition, active practice, and progress tracking.
  Source: [README.md lines 7-20](https://github.com/hluaguo/learn-faster-kit/blob/main/README.md#L7-L20)
- It supports four learning modes and commands such as `/learn`, `/review`, and `/progress`.
  Source: [README.md lines 160-177](https://github.com/hluaguo/learn-faster-kit/blob/main/README.md#L160-L177)
- The repository integrates with Claude Code and provides project-local learning tools and agent instructions.
  Source: [README.md lines 7-20](https://github.com/hluaguo/learn-faster-kit/blob/main/README.md#L7-L20)

**Implications for SkillTrace**

- **Inference:** Mode-specific study protocols—balanced, exam preparation, theory-focused, and practical—could be represented as seed policy values or recommendation preferences, not engine mechanics.
- **Inference:** Auto-generated exercises and teach-back prompts are promising inputs to `ArtifactSpec` and `AssessmentAttempt`, but generated content must not count as accepted evidence without an explicit gate or learner judgment.
- **Inference:** Agent integration is useful as an advisory interface around the CLI, provided the agent cannot invoke guarded state transitions implicitly.
- **Repository ambiguity:** The inspected repository is `hluaguo/learn-faster-kit`, while its installation examples reference another GitHub owner. This should be treated as a provenance question rather than assumed equivalence.

### 5. vimhjkl

**Verified facts**

- `vimhjkl` contains 66 skills and 230 challenges, with every challenge machine-verified against real Vim.
  Source: [README.md lines 14-18](https://github.com/S-Sigdel/vimhjkl/blob/main/README.md#L14-L18)
- It provides Learn, Blind, Practice, Grind, and Review modes.
  Source: [README.md lines 45-67](https://github.com/S-Sigdel/vimhjkl/blob/main/README.md#L45-L67)
- Skill progression uses Leitner scheduling and unlocks.
  Source: [README.md lines 81-93](https://github.com/S-Sigdel/vimhjkl/blob/main/README.md#L81-L93)
- Curriculum generation replays challenges in real Vim and refuses to write generated skill data if verification fails.
  Source: [`build/generate.py` lines 1-7 and 34-96](https://github.com/S-Sigdel/vimhjkl/blob/main/build/generate.py)
- Its engine has explicit difficulty gates, maintenance scheduling, and mastery summaries.
  Source: [`src/vimhjkl/engine.py` lines 26-53, 60-83, and 265-332](https://github.com/S-Sigdel/vimhjkl/blob/main/src/vimhjkl/engine.py)
- Learner progress is persisted by skill ID, including boxes, passes, failures, ease, and last-seen data.
  Source: [`src/vimhjkl/store.py` lines 120-180](https://github.com/S-Sigdel/vimhjkl/blob/main/src/vimhjkl/store.py)

**Implications for SkillTrace**

- **Inference:** Real-environment verification is the strongest external pattern for procedural evidence. SkillTrace could support artifacts whose objective gate runs a reproducible command in a controlled working directory.
- **Inference:** Challenge generation should be a build-time or curriculum-validation concern, while learner evidence acceptance remains a separate runtime concern.
- **Inference:** The project’s “correct and within a bounded efficiency threshold” model could inspire optional rubric fields for procedure artifacts, but score thresholds should remain curriculum data rather than hard-coded engine rules.
- **Important difference:** `vimhjkl` directly updates a skill mastery/progression model from repetitions. SkillTrace intentionally separates derived readiness from asserted progress and forbids automatic `pass` or `master` transitions.

### 6. Skill-Anything

**Verified facts**

- Skill-Anything converts source material into study packs and optionally AI-tool-compatible skills.
  Source: [README.md lines 182-195](https://github.com/SYuan03/Skill-Anything/blob/main/README.md#L182-L195)
- It uses section-aware map-reduce processing, per-section quiz/card quotas, concurrency, and disk caching.
  Source: [README.md lines 35-44](https://github.com/SYuan03/Skill-Anything/blob/main/README.md#L35-L44)

**Implications for SkillTrace**

- **Inference:** A curriculum-import pipeline could generate candidate nodes, artifact specifications, resources, and assessment prompts from source material.
- **Inference:** Section-level provenance and cache keys are important if generated curriculum is regenerated over time; SkillTrace should preserve source references and avoid silently rewriting immutable node history.
- **Inference:** Generated study packs should enter the repository as proposed curriculum/evidence fixtures, requiring validation before becoming canonical seed data.
- **Risk:** LLM-generated quizzes and skills can be plausible but incorrect. They should be advisory or unaccepted until an objective gate or learner review establishes authority.

### 7. Mnemosyne

**Verified facts**

- Mnemosyne is an open-source spaced-repetition flashcard program and a research project into long-term memory.
  Source: [README.md lines 3-7](https://github.com/mnemosyne-proj/mnemosyne/blob/master/README.md#L3-L7)
- Documented features include bidirectional device sync, desktop and Android clients, rich-media cards, plugins, external scripting, multiple schedulers, browser review, cramming, and a reusable core library.
  Source: [README.md lines 9-22](https://github.com/mnemosyne-proj/mnemosyne/blob/master/README.md#L9-L22)

**Implications for SkillTrace**

- **Inference:** Plugin and scripting seams are valuable future architecture, especially for custom objective gates and import/export adapters.
- **Inference:** A “cram” or temporary review mode could be useful as an advisory review view that does not alter regular review scheduling.
- **Inference:** Multi-device sync is not currently compatible with SkillTrace’s local-first single-repository boundary. If introduced later, it would require explicit conflict semantics for immutable records and asserted progress.
- **Risk:** Rich media, browser review, Android clients, and multiple schedulers are high-surface-area features with limited core value for SkillTrace’s evidence-gated graph.

### 8. Drill

**Verified facts**

- Drill is a CLI spaced-repetition program with multiple decks, tags, JSON import/export, and HTML reports.
  Source: [README.md lines 1-12](https://github.com/rr-/drill/blob/master/README.md#L1-L12)
- Its review workflow adjusts a card score; the score maps to a fixed delay ladder from immediate review through four months.
  Source: [README.md lines 41-65](https://github.com/rr-/drill/blob/master/README.md#L41-L65)
- The scheduler implements the score-to-delay table directly.
  Source: [`drillsrs/scheduler.py` lines 6-18 and 28-40](https://github.com/rr-/drill/blob/master/drillsrs/scheduler.py)
- The project stores deck/card/user-answer data in SQLite and supports JSON export and HTML statistics.
  Sources: [`drillsrs/db.py` lines 15-19, 24-35, and 88-114](https://github.com/rr-/drill/blob/master/drillsrs/db.py); [`drillsrs/cmd/export.py` (export command)](https://github.com/rr-/drill/blob/master/drillsrs/cmd/export.py); [`drillsrs/cmd/stats.py` (stats command)](https://github.com/rr-/drill/blob/master/drillsrs/cmd/stats.py)

**Implications for SkillTrace**

- **Inference:** Drill is a useful benchmark for low-friction CLI ergonomics and explicit import/export.
- **Inference:** JSON interchange could be a practical adapter for importing flashcards into a SkillTrace review layer, while keeping Markdown/YAML as SkillTrace’s source of truth.
- **Important difference:** Drill’s score and due date are the central progress model; SkillTrace needs evidence records, gates, attempts, blockers, remediation, and non-revocable assertions in addition to review scheduling.
- **Risk:** A simple score ladder is easy to implement but may conflict with the richer retention analytics already planned for SkillTrace.

### 9. developer-roadmap

**Verified facts**

- The project describes interactive roadmaps whose nodes open topic content.
  Source: [readme.md lines 25-27](https://github.com/nilbuild/developer-roadmap/blob/master/readme.md#L25-L27)
- Roadmap content is stored as one Markdown file per topic using the pattern `roadmaps/<roadmap-slug>/content/<topic-slug>@<node-id>.md`.
  Source: [readme.md lines 148-166](https://github.com/nilbuild/developer-roadmap/blob/master/readme.md#L148-L166)
- Stable node IDs in filenames link topic content to roadmap nodes, and merged changes synchronize to the website.
  Source: [readme.md lines 148-166](https://github.com/nilbuild/developer-roadmap/blob/master/readme.md#L148-166)

**Implications for SkillTrace**

- **Inference:** The filename-plus-stable-ID convention is a good external precedent for human-readable, Git-friendly curriculum content.
- **Inference:** SkillTrace should continue separating node content from relationship data, because the roadmap repository demonstrates that topic content can be edited independently from the visual graph.
- **Important difference:** `developer-roadmap` is a content and navigation repository, not a learner-progress engine. It does not establish evidence acceptance, pass eligibility, or asserted mastery.
- **Potential integration:** A roadmap importer could create `reference_only` anchors and candidate resources without allowing the external roadmap to control locking or recommendation.

### 10. urnote

**Verified facts**

- Urnote reviews Markdown notes by recognizing headings ending in `?`; `note commit` adds those sections to a review plan.
  Source: [README.md lines 21-36](https://github.com/urnote/urnote/blob/master/README.md#L21-L36)
- It creates daily review tasks under `TASK/`.
  Source: [README.md lines 21-36](https://github.com/urnote/urnote/blob/master/README.md#L21-L36)
- It models ordinary, planned, due, and paused review states with marker-based transitions.
  Source: [README.md lines 38-64](https://github.com/urnote/urnote/blob/master/README.md#L38-L64)

**Implications for SkillTrace**

- **Inference:** Urnote demonstrates a compelling “files are the interface” workflow: the learner can inspect and edit Markdown without surrendering source ownership to a database.
- **Inference:** A lightweight review-plan representation could complement SkillTrace’s more formal review records, especially for notes or optional prompts attached to a node.
- **Important difference:** Marker changes are sufficient for note review but do not provide immutable evidence, acceptance authority, artifact hashes, or guarded state transitions.
- **Risk:** Embedding too much operational state directly in curriculum Markdown would violate SkillTrace’s curriculum/progress separation.

---

## Ranked feature matrix

Scores are relative to SkillTrace’s current architecture.
Every row below is an **external delta**, not a claim that the whole capability
is absent. “Gap” means the external pattern is not clearly specified in the
baseline, or is only present in a narrower form. For example, SkillTrace has
objective gates and evidence fingerprints already; the open question is the
reproducible execution and receipt contract around them.

| Rank | Candidate feature | External precedent | Core value | Effort | Risk | Recommendation |
|---:|---|---|:---:|:---:|:---:|---|
| 1 | Reproducible objective procedure gates | `vimhjkl` real-Vim challenge verification | High | Medium | Medium | Prioritize as an extension of `ValidationGate`; capture command, environment, exit status, output summary, and artifact hash |
| 2 | Durable grading/verification receipts | Engram receipts; `vimhjkl` verification pipeline | High | Medium | Low | Extend existing immutable evidence fingerprints with structured execution receipt metadata; never make receipts state transitions |
| 3 | Review-scheduler data contract beyond shipped FSRS analytics | Engram, Anki, Mnemosyne | Medium/High | Medium/High | Medium | Specify how stability/difficulty, due dates, and review outcomes feed recommendations while never changing asserted mastery |
| 4 | Procedure-specific artifact rubrics | `vimhjkl` correctness/efficiency grading | High | Medium | Medium | Add optional rubric dimensions as seed data; avoid hard-coded domain assumptions |
| 5 | Markdown-native curriculum import/export | `developer-roadmap`, Urnote | High | Low/Medium | Low | Preserve stable IDs, source provenance, and separate relationship/state files |
| 6 | Flashcard/review interoperability | Drill, Anki, Mnemosyne | Medium/High | Medium | Medium | Build adapters, not a second source of truth; imported cards should remain review material |
| 7 | Generated candidate study packs | Skill-Anything | Medium/High | Medium | High | Permit proposal generation with provenance and validation; never auto-accept generated evidence |
| 8 | Mode-specific study policies | learn-faster-kit | Medium | Low | Medium | Represent as advisory seed policy values or session templates |
| 9 | Teach-back and active-practice prompts | learn-faster-kit | Medium | Medium | Medium | Generate prompts and candidate artifacts; require learner/objective acceptance |
| 10 | Plugin/external-script API | Mnemosyne | Medium | High | High | Defer until gate and import seams stabilize; define a narrow subprocess contract first |
| 11 | Cramming mode | Mnemosyne | Low/Medium | Low/Medium | Medium | Add only if users need temporary review without modifying normal schedule |
| 12 | Rich media/browser/mobile clients | Mnemosyne | Low for core | High | High | Do not prioritize for local-first CLI-first v1.x |
| 13 | Multi-device synchronization | Mnemosyne | Medium later | Very High | High | Out of scope while single-repository local-first semantics remain governing |
| 14 | Numo payment/catalog features | Numo | None | N/A | N/A | Exclude; repository is unrelated to learning |

### Recommended sequencing

1. Extend objective gates for reproducible commands and capture receipts.
2. Add procedure-oriented artifact/rubric metadata.
3. Specify the boundary between shipped FSRS analytics and any future adaptive
   review scheduler; keep all scheduling advisory.
4. Add Markdown curriculum import/export with stable IDs and provenance.
5. Add optional flashcard adapters.
6. Add generated study-pack proposals only behind explicit validation and acceptance boundaries.
7. Defer plugins, mobile/browser clients, and synchronization.

---

## Architecture gaps exposed by the comparison

### Evidence and execution

External projects are strongest where they execute or replay a concrete task:

- `vimhjkl` replays authored solutions in a real editor
  ([build/generate.py lines 34-96](https://github.com/S-Sigdel/vimhjkl/blob/main/build/generate.py#L34-L96)).
- Engram records grading receipts
  ([README.md lines 18-18](https://github.com/nagisanzenin/engram/blob/main/README.md#L18)).
- Drill records answer outcomes but not artifact-level proof
  ([review.py lines 37-120](https://github.com/rr-/drill/blob/master/drillsrs/cmd/review.py#L37-L120)).

**Gap for SkillTrace:** the current gate model can run a verification command, but a mature procedure-evidence contract still needs decisions about:

- command working directory;
- environment and dependency capture;
- timeout and resource limits;
- stdout/stderr retention;
- exit-code-only versus structured verdicts;
- nondeterministic commands;
- sandboxing and network access;
- whether a successful command creates evidence automatically or only permits learner submission.

### Retention and mastery

Anki, Mnemosyne, Drill, Engram, and `vimhjkl` all treat review scheduling as
central, but they differ in complexity from simple score ladders to FSRS and
Leitner boxes (Anki: [README.md lines 10-12](https://github.com/ankitects/anki/blob/main/README.md#L10-L12);
Mnemosyne: [README.md lines 9-22](https://github.com/mnemosyne-proj/mnemosyne/blob/master/README.md#L9-L22);
Drill: [scheduler.py lines 6-40](https://github.com/rr-/drill/blob/master/drillsrs/scheduler.py#L6-L40);
Engram: [README.md lines 119-128](https://github.com/nagisanzenin/engram/blob/main/README.md#L119-L128);
`vimhjkl`: [README.md lines 81-93](https://github.com/S-Sigdel/vimhjkl/blob/main/README.md#L81-L93)).

**Gap for SkillTrace:** define how scheduled reviews coexist with permanent `mastered` state. A failed later review must create a failure record and recommendation pressure without demoting mastery, consistent with SkillTrace’s existing domain rules.

### Generated curriculum

Skill-Anything and learn-faster-kit show source-to-syllabus and
source-to-exercise generation (Skill-Anything:
[README.md lines 35-44](https://github.com/SYuan03/Skill-Anything/blob/main/README.md#L35-L44);
learn-faster-kit:
[README.md lines 7-20](https://github.com/hluaguo/learn-faster-kit/blob/main/README.md#L7-L20)).

**Gap for SkillTrace:** define the provenance chain:

```text
source material
  -> generated candidate node/prompt/resource
  -> human or objective validation
  -> canonical curriculum/evidence specification
  -> learner submission
  -> accepted EvidenceRecord
```

Generated text should remain distinguishable from canonical curriculum and accepted evidence.

### Graph/content separation

`developer-roadmap` demonstrates stable node-linked Markdown content
([readme.md lines 148-166](https://github.com/nilbuild/developer-roadmap/blob/master/readme.md#L148-L166)),
while SkillTrace’s own architecture separately stores edges and progress.

**Gap for SkillTrace:** establish an import contract that maps external node identifiers to immutable SkillTrace node IDs without allowing external roadmap ordering to override hard prerequisites or recommendation policy.

### Interoperability

Drill and Anki establish demand for import/export, but their data models are
card-centric (Drill: [README.md lines 1-12](https://github.com/rr-/drill/blob/master/README.md#L1-L12);
Anki: [README.md lines 7-12](https://github.com/ankitects/anki/blob/main/README.md#L7-L12)).

**Gap for SkillTrace:** decide whether imported cards become:

1. review prompts attached to an existing SkillNode;
2. optional ArtifactSpecs;
3. separate unverified study material;
4. a generated node proposal requiring validation.

The safest initial choice is review material attached to an existing node, never direct pass evidence.

---

## Unanswered product and architecture questions

1. **What is the minimum objective-gate execution contract?**
   Is exit code sufficient, or should gates support structured JSON verdicts, declared outputs, and test summaries?

2. **How should execution environments be represented?**
   Should an EvidenceRecord capture interpreter version, package lock hash, OS, command line, and working-tree commit?

3. **What is the security boundary for learner-supplied commands?**
   Objective gates execute local commands. Should SkillTrace provide opt-in network denial, timeout enforcement, subprocess isolation, or only document the trust model?

4. **How should procedure efficiency be modeled?**
   Should optional rubric fields support keystroke count, runtime, token count, or resource usage, and are these advisory metrics or acceptance criteria?

5. **When does generated curriculum become canonical?**
   What human review or validation is required before AI-generated nodes, quizzes, and artifact specs enter the curriculum?

6. **How should source provenance survive regeneration?**
   If a source document changes, should SkillTrace create new candidate nodes, update existing nodes in place, or require a material-redefinition/new-node decision?

7. **How should FSRS interact with permanent mastery?**
   Should FSRS schedule only reviews, or may its stability/difficulty values influence recommendations for mastered nodes without changing state?

8. **What is the flashcard interoperability boundary?**
   Which Anki/Drill fields are worth importing, and how are imported prompts linked to SkillNodes and evidence specifications?

9. **Should review prompts be first-class curriculum objects?**
   Urnote treats reviewable headings as note metadata; SkillTrace may need a distinct prompt model to avoid contaminating node content or progress state.

10. **What is the canonical procedure-artifact type?**
    Is a source file, repository commit, command transcript, test report, deployed endpoint, or signed receipt represented uniformly as an artifact, or are specialized artifact kinds needed?

11. **How should external roadmap imports map identifiers?**
    Can a stable external node ID become a `reference_only` anchor, or should imported content receive a new immutable SkillTrace node ID every time?

12. **What must be retained from objective-gate output?**
    Full logs improve auditability but increase privacy and storage risk. A digest plus bounded summary may be the right default.

13. **Should failed objective gates create AssessmentAttempts automatically?**
    This would improve failure visibility but risks conflating evidence-submission failures with deliberate learner assessment attempts.

14. **What is the smallest useful plugin seam?**
    A subprocess gate adapter may be safer than a Python plugin API, but it requires a stable protocol and versioning policy.

15. **If sync is ever added, how are immutable records merged?**
    Mnemosyne demonstrates demand for device sync, but SkillTrace must define conflict resolution for append-only evidence, supersession chains, event logs, and asserted progress before considering it.

---

## Source and method notes

- All external feature claims above use official repository README files or source files.
- Existing local research convention was inspected in `docs/research/vimhjkl-drill-vs-skilltrace.md`: titled research note, pinned sources, numbered analytical sections, explicit comparisons, and inline path/line citations.
- `docs/research/` already existed and contained that prior research note; no unrelated files were changed.
- The requested target file `C:\\skilltrace\\docs\\research\\cross-repository-gap-analysis.md` was written from this report and validated after creation.
- The repository was already dirty before this research, including existing modifications and untracked research files. No changes were made by this research pass.
