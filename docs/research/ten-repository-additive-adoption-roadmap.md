# Ten-Repository Additive Adoption Roadmap

**Research date:** 2026-09-03  
**SkillTrace baseline:** local checkout at
[`61f54164a50ed76b2481f270cb6abc2841e26265`](https://github.com/earledotpy/skilltrace/tree/61f54164a50ed76b2481f270cb6abc2841e26265).

## Decision

Adopt only narrow patterns that strengthen the existing five-layer engine:
clearer operational analytics, validated seed-graph authoring, durable
derived exports, and advisory review ordering. Do not import another
repository's state machine, card store, or authority model.

This is an additive roadmap, not a proposal to reopen the version-slot
sequence. v1.5 already supplies a read-time, exponential-decay retention
overlay; it derives from completed reviews and a pass-date fallback, then
never writes state ([Tier 2 spec, sections 1.1-1.4](../spec-tier2-retention-analytics.md);
[`retention_model.py:1-28,103-187`](../../src/skilltrace/policy/retention_model.py)).
v1.6 is the active, separately scoped operational-analytics release: velocity,
blockers, review completion, and evidence coverage derive from the primary
YAML records, not `execution/events.yaml`
([v1.6 spec, sections 0-2](../spec-v1.6-event-log-analytics.md);
[`derive.py:1-20,274-428`](../../src/skilltrace/analytics/derive.py)).

The planned work below therefore leaves v1.5's retention formula intact and
does not turn v1.6 into predictive, prescriptive, or diagnostic analytics.
Those are expressly outside v1.6 ([v1.6 spec, section 0](../spec-v1.6-event-log-analytics.md)).

## Candidate corpus

The ten candidates are the ordered local shortlist in
[`docs/resources/learning-engines-comparison.md:13-23`](../resources/learning-engines-comparison.md).
The earlier Cashu merchant-POS repository is not a candidate: the third
candidate is **`mohaneddz/Numo`**, a language-learning curriculum engine.
All upstream citations below are commit-pinned primary repository sources.

| Candidate | Verified transferable observation | Adoption disposition |
|---|---|---|
| [`nagisanzenin/engram@0590eb8`](https://github.com/nagisanzenin/engram/tree/0590eb8f008680acbfb5aaa4dbc73bf63ca643dd) | It documents local grading receipts and deterministic FSRS scheduling ([`README.md:18-20,93-127`](https://github.com/nagisanzenin/engram/blob/0590eb8f008680acbfb5aaa4dbc73bf63ca643dd/README.md#L18-L20)). | Reuse the receipt/report idea in v2.0; do not replace the shipped retention model. |
| [`ankitects/anki@20c475f`](https://github.com/ankitects/anki/tree/20c475f110c44899b91546906ce876976d9a52d7) | Its Rust core mutates card queue, due date, interval, and type as part of review scheduling ([`rslib/src/scheduler/reviews.rs:22-80`](https://github.com/ankitects/anki/blob/20c475f110c44899b91546906ce876976d9a52d7/rslib/src/scheduler/reviews.rs#L22-L80)). | Use only as a complexity boundary: no card scheduler or mutable memory state in the graph core. |
| [`mohaneddz/Numo@9569c4d`](https://github.com/mohaneddz/Numo/tree/9569c4d27329981c7bf537de36e4776095d6c27e) | It defines an explicit skill graph and fails a build on an unclassified curriculum token ([`skillGraph.ts:63-255,282-290`](https://github.com/mohaneddz/Numo/blob/9569c4d27329981c7bf537de36e4776095d6c27e/src/services/curriculum/skillGraph.ts#L63-L255)). Its mastery store also changes mastery after outcomes ([`masteryStore.ts:21-45,142-186`](https://github.com/mohaneddz/Numo/blob/9569c4d27329981c7bf537de36e4776095d6c27e/src/services/curriculum/masteryStore.ts#L21-L45)). | Reuse fail-loudly seed validation and transparent advisory ranking inputs; reject mutable computed mastery as learner progress. |
| [`hluaguo/learn-faster-kit@c0168f3`](https://github.com/hluaguo/learn-faster-kit/tree/c0168f30f87e488b5230dbd387fe2904f7fdf538) | Its installer creates a project-local learning workspace and copies scripts/templates ([`installer.py:196-258`](https://github.com/hluaguo/learn-faster-kit/blob/c0168f30f87e488b5230dbd387fe2904f7fdf538/src/learn_faster/cli/installer.py#L196-L258)). Its review scheduler is a fixed interval ladder ([`review_scheduler.py:12-16,63-113`](https://github.com/hluaguo/learn-faster-kit/blob/c0168f30f87e488b5230dbd387fe2904f7fdf538/src/learn_faster/templates/shared/scripts/review_scheduler.py#L12-L16)). | Later, borrow advisory prompt/protocol output only; do not regress v1.5 to a fixed ladder or vendor opaque scripts. |
| [`S-Sigdel/vimhjkl@501762f`](https://github.com/S-Sigdel/vimhjkl/tree/501762feecd0aa1c2f04089ba2f94177159b730e) | It verifies real-Vim procedure results from observable buffer/cursor/register/output state ([`grader.py:429-500`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/grader.py#L429-L500)). | Reuse as the model for a bounded objective-gate receipt, not automatic skill progression. |
| [`SYuan03/Skill-Anything@4c83b8e`](https://github.com/SYuan03/Skill-Anything/tree/4c83b8e73dccd897db6cecc1d5e6bbd987baf80a) | It turns sources into structured `SkillPack` outputs, including sections, exercises, flashcards, and learning paths ([`models.py:62-83,143-153,186-211`](https://github.com/SYuan03/Skill-Anything/blob/4c83b8e73dccd897db6cecc1d5e6bbd987baf80a/skill_anything/models.py#L62-L83)). | Reuse the proposed-content/provenance pattern for seed authoring; never treat generated content as accepted evidence. |
| [`mnemosyne-proj/mnemosyne@ff4f61e`](https://github.com/mnemosyne-proj/mnemosyne/tree/ff4f61e84bea0d6928c29b7798f0f88b90938a0a) | Its scheduler explicitly separates rebuild/invalidation, next-card selection, grading, counts, and projections ([`scheduler.py:65-119`](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/scheduler.py#L65-L119)). | Reuse the separation-of-concerns discipline for a future advisory queue; do not import a second scheduler or sync model. |
| [`rr-/drill@a3ba4a6`](https://github.com/rr-/drill/tree/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0) | Its CLI has explicit JSON export and HTML statistics surfaces ([`cmd/export.py:20-48`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/export.py#L20-L48); [`cmd/stats.py:81-120`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/stats.py#L81-L120)). | Reuse portable, derived reporting conventions only. |
| [`nilbuild/developer-roadmap@82441f9`](https://github.com/nilbuild/developer-roadmap/tree/82441f97180f9a36f11b1fe348c65010978c9156) | Topic Markdown is named with a stable node identifier and synchronized separately from roadmap content ([`readme.md:148-166`](https://github.com/nilbuild/developer-roadmap/blob/82441f97180f9a36f11b1fe348c65010978c9156/readme.md#L148-L166)). | Reuse stable external references as `reference_only` anchors, never as relationships or priority. |
| [`urnote/urnote@f22e7d4`](https://github.com/urnote/urnote/tree/f22e7d4b755bc2fac2ea22a425ca17265ac07073) | It identifies reviewable Markdown headings and creates local daily tasks ([`README.md:21-36,38-64`](https://github.com/urnote/urnote/blob/f22e7d4b755bc2fac2ea22a425ca17265ac07073/README.md#L21-L36)). | Later, permit non-authoritative prompt extraction; do not encode review state in curriculum Markdown. |

## Additive sequence

The sequence follows the slots already locked in
[`docs/POST_V1_ROADMAP.md:29-50`](../POST_V1_ROADMAP.md). It adds no new
version slot and does not move v1.7, v1.8, or v1.9 work into v1.6.

### Near-term core improvements

### 1. Complete v1.6 with named, denominator-correct operational metrics

**Target:** v1.6 only; finish the active scope rather than layering on a new
analytics product.

- **Value:** Makes velocity, blockers, review completion, and evidence coverage
  decision-useful without overstating what the data proves. Mnemosyne records
  scheduler/repetition facts separately from its reporting surfaces
  ([`SQLite_logging.py:29-58,98-111`](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/databases/SQLite_logging.py#L29-L58));
  Drill exposes derived exports rather than making reports its data model
  ([`cmd/export.py:20-48`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/export.py#L20-L48)).
- **Likely implementation seam:** retain the pure
  `derive_analytics()` composition in
  [`src/skilltrace/analytics/derive.py:274-428`](../../src/skilltrace/analytics/derive.py).
  Before release, make the evidence metric's label match its current rule:
  a gap is a required spec with zero accepted live records
  (`derive.py:347-393`), whereas pass eligibility requires each required
  spec to reach its `minimum_count`
  ([`src/skilltrace/evidence/submission.py:103-120`](../../src/skilltrace/evidence/submission.py)).
  If a pass-readiness metric is desired later, add it under a distinct name
  and exact denominator; do not silently change v1.6 coverage.
- **Safety boundary preserved:** analytics remains read-only over primary
  YAML; it neither reads the audit event log for state nor transitions nodes
  ([`docs/spec-v1.6-event-log-analytics.md:34-57`](../spec-v1.6-event-log-analytics.md);
  [`tests/analytics/test_derive.py:1-14`](../../tests/analytics/test_derive.py)).
- **Candidate basis:** Mnemosyne, Drill.

### 2. Use fail-loudly, provenance-carrying seed authoring for v1.8 and v1.9

**Target:** v1.8/v1.9 seed-graph delivery, after v1.7's deliberately narrow
manual resource verification work.

- **Value:** Gives the ML and agentic seed graphs reproducible source
  attribution and a reviewable generation path while keeping curriculum
  content Git-friendly. Numo refuses an unclassified source token
  ([`skillGraph.ts:282-290`](https://github.com/mohaneddz/Numo/blob/9569c4d27329981c7bf537de36e4776095d6c27e/src/services/curriculum/skillGraph.ts#L282-L290));
  Skill-Anything demonstrates structured source-to-pack output
  ([`engine.py:35-55,101-145`](https://github.com/SYuan03/Skill-Anything/blob/4c83b8e73dccd897db6cecc1d5e6bbd987baf80a/skill_anything/engine.py#L35-L55));
  developer-roadmap demonstrates stable node-addressable Markdown
  ([`readme.md:148-166`](https://github.com/nilbuild/developer-roadmap/blob/82441f97180f9a36f11b1fe348c65010978c9156/readme.md#L148-L166)).
- **Likely implementation seam:** make an offline authoring/import tool emit
  proposed node Markdown, `edges.yaml` entries, resources, and source
  metadata; accept output only after the existing node/edge/resource
  validators. Anchor external source IDs as `reference_only`, relying on the
  existing behavioral guarantee that anchors neither lock nor reorder nodes
  ([`tests/graph/test_roadmap_anchor.py:1-54`](../../tests/graph/test_roadmap_anchor.py)).
  Keep relationships solely in `graph/edges.yaml`, as required by the
  application roadmap
  ([`docs/skilltrace-application-roadmap.md:29-45`](../skilltrace-application-roadmap.md)).
- **Safety boundary preserved:** generated material is proposed curriculum,
  not learner evidence. It cannot create or demote asserted progress, and it
  cannot introduce an alternate relationship authority.
- **Candidate basis:** Numo, Skill-Anything, developer-roadmap.

### 3. Prepare a bounded objective-gate receipt contract, but defer its runner

**Target:** design/fixture work alongside procedural seed content; ship a
general runner only when a concrete v1.8/v1.9 artifact needs it.

- **Value:** A structured receipt lets a learner inspect why an objective gate
  accepted or rejected a procedural artifact. `vimhjkl` shows the high-value
  evidence shape: observable final state plus bounded efficiency information
  ([`grader.py:429-500`](https://github.com/S-Sigdel/vimhjkl/blob/501762feecd0aa1c2f04089ba2f94177159b730e/src/vimhjkl/grader.py#L429-L500)).
- **Likely implementation seam:** extend the object built by
  `plan_submit()` only after defining a small, immutable receipt schema:
  normalized command identity, root-relative declared inputs, exit class,
  tool/version when available, artifact hash, and bounded diagnostic summary.
  Today the planner already creates one accepted/rejected record from the
  gate exit code and artifact hash
  ([`src/skilltrace/evidence/submission.py:147-217`](../../src/skilltrace/evidence/submission.py));
  the gate schema is deliberately only `manual` or `objective`
  ([`src/skilltrace/evidence/gates.py:24-115`](../../src/skilltrace/evidence/gates.py)).
- **Safety boundary preserved:** an exit code may decide the submitted
  `EvidenceRecord` verdict, but never invoke `pass_node` or `master_node`.
  An unrunnable command remains no judgment and writes no record; acceptance
  stays frozen at submission
  ([ADR 0003](../adr/0003-acceptance-frozen-at-submission.md);
  [`tests/evidence/test_gates.py:36-63`](../../tests/evidence/test_gates.py)).
- **Candidate basis:** vimhjkl, Engram.

## Later optional features

### 4. v2.0: derived portfolio and evidence-receipt exports

- **Value:** Make evidence, accepted-gate verdicts, review timeline, and
  v1.6 aggregates shareable as a human-readable project report. Engram's
  on-disk receipts ([`README.md:18-20`](https://github.com/nagisanzenin/engram/blob/0590eb8f008680acbfb5aaa4dbc73bf63ca643dd/README.md#L18-L20))
  and Drill's JSON/HTML exports ([`cmd/export.py:20-48`](https://github.com/rr-/drill/blob/a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0/drillsrs/cmd/export.py#L20-L48))
  validate the output value.
- **Likely implementation seam:** build on the existing one-way
  `ExportData` gatherer
  ([`src/skilltrace/export_data.py:1-80`](../../src/skilltrace/export_data.py))
  and analytics renderers
  ([`src/skilltrace/analytics/export.py:1-87`](../../src/skilltrace/analytics/export.py)).
  The receipt view should link record IDs and hashes, not duplicate or
  normalize them into a new store.
- **Safety boundary preserved:** it is a disposable derived artifact, never
  an engine input. Markdown/YAML remain truth; exports do not change
  eligibility, acceptance, state, or event semantics
  ([application roadmap, decision 12](../skilltrace-application-roadmap.md);
  [`tests/analytics/test_export.py:62-93`](../../tests/analytics/test_export.py)).
- **Candidate basis:** Engram, Drill.

### 5. v2.1: advisory sequencing overlay bound to v1.5 and v1.6 inputs

- **Value:** Offer an explainable mixed study/review ordering that can use
  retention suggestions, overdue reviews, operational workload, and existing
  remediation pressure. Mnemosyne's explicit separation of queue rebuilding
  from selection/grading ([`scheduler.py:65-119`](https://github.com/mnemosyne-proj/mnemosyne/blob/ff4f61e84bea0d6928c29b7798f0f88b90938a0a/mnemosyne/libmnemosyne/scheduler.py#L65-L119))
  and Numo's deterministic, rationale-bearing session planning
  ([`sessionPlanner.ts:100-122,182-207`](https://github.com/mohaneddz/Numo/blob/9569c4d27329981c7bf537de36e4776095d6c27e/src/services/curriculum/sessionPlanner.ts#L100-L122))
  are useful precedents.
- **Likely implementation seam:** enrich the pure `recommend()` ranking
  inputs rather than add a queue database or a scheduler. It already admits
  injected advisory factors and only ranks `available`/`active` nodes
  ([`src/skilltrace/graph/recommendation.py:204-276`](../../src/skilltrace/graph/recommendation.py)).
  Feed it read-time results from `derive_memory_states()` and the completed
  v1.6 derivation; retain candidate reasons and stable tie-breaking.
- **Safety boundary preserved:** retention and analytics may reorder or warn,
  never block a learner action. The overlay cannot surface locked nodes,
  satisfy a hard prerequisite, mutate `graph/state.yaml`, or demote
  `passed`/`mastered`
  ([`tests/graph/test_recommendation.py:45-75`](../../tests/graph/test_recommendation.py);
  [`CONTEXT.md:30-49,90-108`](../../CONTEXT.md)).
- **Candidate basis:** Anki, Mnemosyne, Numo, Engram.

### 6. Post-v2.1 only: advisory practice profiles and Markdown prompt extraction

- **Value:** Let the learner select a bounded protocol (for example focused,
  mixed, or review) and surface note-derived questions without making an AI
  tutor or a second persistence model mandatory. learn-faster-kit exposes
  mode-specific workflows ([`README.md:160-177`](https://github.com/hluaguo/learn-faster-kit/blob/c0168f30f87e488b5230dbd387fe2904f7fdf538/README.md#L160-L177));
  Urnote shows a small Markdown-to-review-task convention
  ([`README.md:21-36`](https://github.com/urnote/urnote/blob/f22e7d4b755bc2fac2ea22a425ca17265ac07073/README.md#L21-L36)).
- **Likely implementation seam:** policy values and read-only output
  renderers only; model protocols as opaque session-template or advisory
  policy values, not engine states. Keep extracted prompts separate from
  node frontmatter and from the progress store.
- **Safety boundary preserved:** prompts and AI commentary are advisory. They
  cannot become a gate authority, accepted evidence, or an implicit
  pass/master action
  ([`CONTEXT.md:118-178`](../../CONTEXT.md);
  [`src/skilltrace/evidence/gates.py:24-30`](../../src/skilltrace/evidence/gates.py)).
- **Candidate basis:** learn-faster-kit, Urnote.

## Explicitly avoid

| Do not adopt | Why it is incompatible |
|---|---|
| A full Anki/Mnemosyne/Drill card scheduler, card database, or due-date state as graph truth | v1.5 is already a pure, read-time retention overlay; SkillTrace’s node readiness, evidence eligibility, and asserted progress have distinct semantics. |
| Numo-style computed mastery as the node state | Numo updates its mastery estimate after outcomes ([`masteryStore.ts:142-186`](https://github.com/mohaneddz/Numo/blob/9569c4d27329981c7bf537de36e4776095d6c27e/src/services/curriculum/masteryStore.ts#L142-L186)); SkillTrace asserted progress never moves backward ([`CONTEXT.md:30-49`](../../CONTEXT.md)). |
| Auto-pass, auto-master, AI acceptance, or a gate that asserts progress | The automation prohibitions are engine constants, not configurable preferences ([ADR 0004](../adr/0004-hard-boundaries-are-engine-constants.md)); accepted evidence and learner assertion remain separate. |
| Generated curriculum or AI prompts treated as accepted evidence | Candidate-generation outputs are curriculum proposals. An `EvidenceRecord` requires its existing objective or learner-manual authority at submission ([ADR 0003](../adr/0003-acceptance-frozen-at-submission.md)). |
| External-roadmap ordering as prerequisites or recommendation weights | Anchors are `reference_only`, and tests prove they do not lock or suppress recommendation ([`tests/graph/test_roadmap_anchor.py:1-54`](../../tests/graph/test_roadmap_anchor.py)). |
| Plugin systems, remote/multi-device sync, mobile clients, or cloud analytics in this sequence | They introduce alternate writers and conflict semantics. The established roadmap keeps cloud sync out of scope and keeps v1.6 network-independent ([`docs/POST_V1_ROADMAP.md:66-76`](../POST_V1_ROADMAP.md); [`docs/spec-v1.6-event-log-analytics.md:26-44`](../spec-v1.6-event-log-analytics.md)). |
| A revived interface registry or a parallel UI vocabulary | The interface layer was explicitly cut by ADR 0002 to prevent drift. The reintroduced web-only interface sublayer ([ADR 0007](../adr/0007-reintroduce-interface-layer.md)) derives its vocabulary from the live CLI dispatcher registry (`src/skilltrace/dispatch.py:91`) rather than a hand-declared YAML, and validates at import time. CLI and Serve continue to call real engine seams; the sublayer is a reflection, not a parallel source. |

## Adoption gate

Implement a listed item only in its existing slot and only with regression
tests proving that it preserves: learner-only pass/master assertion,
no hard-prerequisite override, immutable/superseding evidence, `edges.yaml`
as the sole relationship source, and derived-only exports/analytics. This is
the narrow route by which the candidate patterns add value without changing
SkillTrace’s governing model.
