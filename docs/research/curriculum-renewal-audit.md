# Curriculum renewal audit — graph consistency and current learning resources

**Ticket:** earledotpy/skilltrace#291 (R-CurriculumAudit), child of wayfinder map #289.
**Audited against:** the learner destination defined by G-StudyContract (#290): an
accelerated two-week evaluation contract (6–8 h/week over several study days,
beginner foundations baseline; intermediate/advanced situations deferred to
separate branches). #290 explicitly says the old AI engineering roadmap is
**not** assumed authoritative — curriculum relevance is judged against the
clarified learner capability destination, once the contract resolves.
**Status:** planning decision aid only. Not a verdict; substantive verdicts
require learner review. No Curriculum, progress store, or verification
assertions were edited.
**Worktree:** `research/curriculum-renewal-audit` at commit 6dafd42 (main HEAD
at audit time). Repo snapshot: 100 node files, 157 active edges
(57 `hard_prerequisite`, 81 `soft_prerequisite`, 19 `remediation`), 46
LearningResource registry entries — exactly matching the post-merge
expectation of spec-v1.9 (`docs/spec-v1.9-phase3-llm-agents-mcp-seed-graph.md:121-122`),
so the ML and agents tranches are landed, not pending.
**Method:** full programmatic cross-check of `graph/` and `evidence/`; full
reads of representative nodes from both cohorts; doc review of
`docs/maintenance`, `docs/resources`, `docs/roadmap`,
`docs/ai-engineering-roadmap.md`, `docs/curriculum-authoring.md`,
spec-v1.8/v1.9; and dated primary-source verification (official docs and
release pages fetched 2026-09-17) of volatile claims. HTTP-success and
Last-Verified labels were treated as insufficient per the ticket.

---

## 1. Graph structural consistency — KEEP (clean)

Checked against AGENTS.md invariants and the target node schema:

- **Frontmatter separation (PASS):** 0 of 100 node files contain forbidden
  keys `state`, `prerequisites`, `unlocks`, or `node_type`. Learner state
  lives solely in the progress store (`graph/state.yaml`), per ADR 0001.
- **Progress store (PASS):** `graph/state.yaml` holds exactly the 100 node
  states, all legal states (`locked`/`available` — the learner has asserted
  no `active`/`passed`/`mastered` yet), no extras. One cosmetic note: mixed
  `changed_at` formats (date-only and full ISO timestamps).
- **edges.yaml (PASS):** all edge source/target IDs resolve to existing
  node files; no duplicate IDs; no inactive edges; no isolated nodes.
  Edges remain the sole source of truth for node relationships.
- **Registry integrity (PASS):** all 46 resources' `supports` IDs resolve
  to existing nodes; no node lacks a resource; no duplicate URLs.
- **Spec→graph (PASS):** every node ID cited in spec-v1.8 (11 nodes) and
  spec-v1.9 (12 nodes) exists; the 23 `ml.*`/`agents.*` nodes match the
  two tranches' union exactly.

## 2. Evidence-layer gaps — REVISE (the one substantive structural finding)

- **6 nodes declare evidence expectations the evidence layer cannot yet
  accept.** `ml.framing.ml_workflow_01`, `ml.classification.logistic_regression_01`,
  `ml.practice.titanic_baseline_01`, `agents.concepts.agent_fundamentals_01`,
  `agents.deploy.docker_engine_build_run_01`, and
  `agents.frameworks.openai_agents_sdk_01` have **no artifact spec and no
  validation gate** in `evidence/artifact_specs.yaml` /
  `evidence/validation_gates.yaml`, while node bodies say "Learner-manual
  gate expected" (`ml.framing.ml_workflow_01.md:80-81`) or "the folder is
  the evidence artifact" (`ml.practice.titanic_baseline_01.md:75-78`).
  This was deliberate sequencing ("human last_verified pending … re-pin at
  spec time", per the v1.9 resource `license` strings), but against #290's
  destination — a fortnight in which evidence inspection is a day-by-day
  activity — a beginner reaching these nodes would find pass eligibility
  underivable. Otherwise the layer is 1:1: 81 artifact specs ↔ 81 gates,
  checkers for 22 objective gates.
- **Two sources of truth risk for "what passing requires":** ~32
  math/foundations nodes have spec+gate while their bodies never mention a
  gate (e.g., `math.algebra.variables_expressions_01.md`); generic
  "problem-set evidence, minimum_count 3" specs
  (`artifact_specs.yaml:3-14`). Revise: declare one canonical surface
  (spec/gate registry) and stop the divergence before the contract runs.
- **Revise candidate (soft):** normalize `changed_at` in `state.yaml`.

## 3. Cohort comparison (foundations vs ML/agents additions)

- **Schema:** three cohorts — bare foundations schema; foundations with
  `roadmap_anchors` (43 nodes); v1.8/v1.9 nodes with `source_metadata` +
  `regeneration_key` + section provenance. No schema violations in any
  cohort. KEEP.
- **Grain:** both cohorts use `micro_session_fit` with `can_fit_15_min:
  false`; estimated spans 20–300 min (foundations) vs 60–480 min (ML/agents
  capstone). Both are multi-block, consistent with
  `docs/curriculum-authoring.md:17-19` ("smallest skill independently
  evidenced by one artifact, ~30–90 minutes" — the capstone and stats
  simulation exceed this and are legitimately portfolio-grain). KEEP.
- **Register/titles:** foundations use plain imperative skill titles; ML/agents
  add tool/version framing and a "(capstone)" suffix. Parallel summaries.
  KEEP — the divergence is content maturity (several foundations bodies are
  empty stubs, e.g., `math.algebra.variables_expressions_01.md:34-36`),
  not schema drift.
- **REVISE candidate:** fill the empty foundations stub bodies before the
  fortnight; a beginner on the #290 contract reads these as the study text.

---

## 4. Resource currency — dated primary-source verification

Fetched 2026-09-17 from official sources:

| Registry claim | Primary source finding | Leaning |
|---|---|---|
| `hf-spaces-zerogpu` "free tier max 2 Spaces, 5 min/day" (resources.yaml:466) | **Accurate.** ZeroGPU tiers page: free account 5 min/day GPU quota, max 2 ZeroGPU Spaces for free personal accounts (verified email, account >30 days); PRO 40 min/day, 10 Spaces. GPU hardware now NVIDIA RTX Pro 6000 Blackwell. | KEEP |
| `docker-engine-docs` "Desktop paid above 250 employees or $10M revenue" (resources.yaml:458) | **Imprecise.** Docker Desktop license: free for fewer than 250 employees AND less than $10M revenue; paid for professional use in larger organizations. Engine OSS license unchanged. | REVISE (AND, not "or") |
| `openai-agents-sdk` pin `openai-agents-0.22.0` (resources.yaml:435) | **Stale pin.** Latest release v0.22.3 (17 Sep 2026). SDK MIT, free; per-token API cost claim accurate. | REVISE (re-pin at spec time, as designed) |
| `pydanticai-docs` "V2.0 stable 2026-06-23", URL `pydantic.dev/docs/ai` (resources.yaml:439-442) | Canonical docs live at `ai.pydantic.dev` (the pydantic.dev path redirects); V2 line confirmed stable; docs surface has since grown substantially (Harness, Capabilities, guardrails). Pinned section list still exists. | REVISE (canonical URL) / KEEP (content) |
| `ms-agent-framework` "Public Preview RC-1" (resources.yaml:428) | **Stale.** Microsoft Agent Framework overview (updated 2026-08-25) presents the framework as current (only the Go port is public preview); confirmed successor to Semantic Kernel and AutoGen. | REVISE (status label) |
| `fastapi-docs` pin `fastapi-0.141.1` (resources.yaml:449) | Plausible and consistent with FastAPI's 0.x semver; sections cited (Tutorial, /docs, Docker) all live. | KEEP (re-pin at spec time) |
| `certification-roadmap.md:78` "AIF-C01 $100 USD … ~$18k salary uplift reported" | **Unverified.** The AWS AI Practitioner exam page fetched 2026-09-17 does not state the fee or salary figure in page text; the $18k uplift has no cited source and traces to the retired v0.1 scaffold research (archive/scaffold-v0.1/research/ai-engineering-agentic-roadmap-research.md:236). | REVISE (remove or source the claim) |
| `certification-roadmap.md` AWS ML Specialty | **Materially stale.** AWS ML Specialty (MLS-C01) is **retiring** — last exam delivery March 31, 2026 (AWS cert page, 2026-09-17). Its successor is AWS Certified Machine Learning Engineer – Associate (MLA-C01), which also recertifies the AI Practitioner. | REPLACE (rewrite cert recommendations around MLA-C01) |
| `free-compute-guide.md` Render spin-down 15 vs 30 min (internal contradiction, :135 vs :148) | **Contradiction confirmed as real.** Render's "Deploy for Free" docs (2026-09-17) confirm free instances exist only for web services, Postgres, Key Value, static sites — background workers/cron are excluded — and free Postgres expires after 30 days; the docs page's spin-down idle figure must be read from its current section (the two in-repo numbers cannot both be right). | REVISE (re-verify and reconcile) |

Foundations resources (Khan Academy, 3Blue1Brown, OpenIntro, Seeing Theory):
free access and stable URLs; content currency not in question at this grain.
KEEP.



---

## 5. Documentation layer

- **`docs/curriculum-authoring.md`** — KEEP with one REVISE: its namespace
  inventory (:265-272) predates and omits the `ml.*` and `agents.*` bands
  landed in v1.8/v1.9.
- **`docs/maintenance/quarterly-review-checklist.md`** — REVISE: its
  verification bar is URL-200-OK / `curl -I` (:22, :28), exactly the bar
  #291 declares insufficient; it never checks content currency beyond
  checkbox assertions. Last run August 2026; no overdue mechanism exists
  for the checklist itself (Overdue review semantics apply to nodes, not
  docs).
- **`docs/ai-engineering-roadmap.md`** — consistent with doctrine
  (`reference_only` anchors, 43 nodes carry them; anchors never control
  locking or recommendation). Two structural notes, not anchor misuse:
  roadmap Phase 3 (deep learning) is a stated prerequisite to the agents
  phase but has zero graph nodes, while the graph's agents tranche was
  seeded under spec-v1.9's "Phase 3" label — a phase-numbering collision
  (`spec-v1.9` vs `roadmap/phase-3-deep-learning.md` / `phase-4-agentic-ai.md`).
  REVISE (reconcile naming), not replace: the roadmap is background
  reference, not the structure the graph must transcribe.
- **Revision-versus-rebuild weighting:** the node set and 9-source agent
  list were human-locked decisions with provenance (spec-v1.8 "additions
  only", locked source list; spec-v1.9 9-source list, HF Context
  Course/CrewAI explicitly out of scope). Per CONTEXT.md, a material
  redefinition of a skill is a *new* Node ID; old history stays true. So
  graph-level replacements are expensive and must cite material change
  since lock (none found: every verified claim above is either accurate or
  a label/pin drift, both in-place revisions). Docs and resource annexes
  were never locked by a spec — revision there is cheap and sufficient.

## 6. Keep / Revise / Replace summary

| Candidate | Leaning | Key evidence |
|---|---|---|
| Whole graph structure (frontmatter, edges, registry, progress-store separation) | **KEEP** | §1 — zero invariant violations |
| Foundations cohort (math.*, python.*, data.*, tooling.*, consolidation.*) | **KEEP / REVISE** (fill empty bodies) | §3 |
| v1.8 ML / v1.9 agents node sets and locked source lists | **KEEP** (in-place updates only) | §5 — no material change since lock; verified claims are label/pin drift |
| Evidence coverage for 6 ML/agents nodes | **REVISE** (spec gates or declare pending) | §2 |
| Canonical-surface rule for "what passing requires" | **REVISE** | §2 |
| resources.yaml agent-stack claims (MS AF status, OpenAI SDK pin, PydanticAI URL, Docker AND-clause) | **REVISE** (in place, at re-pin time) | §4 table |
| certification-roadmap.md | **REVISE/REPLACE** (AWS ML Specialty retired; replace with MLA-C01; source or drop the $18k claim and unverified fees) | §4 table |
| free-compute-guide.md | **REVISE** (resolve 15/30-min contradiction; re-verify quotas) | §4 table |
| quarterly-review-checklist.md verification bar | **REVISE** (raise from HTTP-200 to content-currency checks) | §5 |
| curriculum-authoring.md namespace inventory | **REVISE** (add ml.*/agents.*) | §5 |
| ai-engineering-roadmap Phase 3 numbering vs spec-v1.9 "Phase 3" | **REVISE** (naming reconciliation only) | §5 |
| Phase 3 deep-learning nodes (absent from graph) | **GAP — flag to #290 contract resolution, not this audit's verdict** | §5 |

## 7. Residual uncertainty

1. The **learner capability destination itself is unresolved** (#290 is the
   locked study contract in flight); every relevance judgment here is
   provisional against the old roadmap's declared non-authority.
2. `fastapi-0.141.1`, PydanticAI "V2.0 stable 2026-06-23", Khan/3B1B content
   currency, and AIF-C01 fee were not directly pinned to a dated release
   record within this audit's fetch budget; fee figures especially must be
   read from AWS's current exam pages before any payment decision.
3. The Render spin-down idle duration is not stated in the fetched extract;
   only the internal contradiction is confirmed.
4. Whether the 6 gate-less nodes are intentionally sequenced to a later slot
   (spec-time re-pin) vs an oversight needs learner confirmation against the
   roadmap slot plan.
5. Hour estimates in nodes (e.g., 120–300 min for the stats simulation) are
   seed-data estimates, never measured; #290 forbids claiming learning time
   from simulation.

## Sources (all fetched 2026-09-17)

- https://huggingface.co/docs/hub/en/spaces-zerogpu — ZeroGPU usage tiers & hosting limits
- https://docs.docker.com/subscription/desktop-license/ — Docker Desktop license agreement
- https://github.com/openai/openai-agents-python/releases — latest v0.22.3
- https://ai.pydantic.dev/ — canonical PydanticAI docs
- https://learn.microsoft.com/en-us/agent-framework/overview (page updated 2026-08-25)
- https://aws.amazon.com/certification/certified-machine-learning-specialty/ — MLS-C01 retirement (last delivery 2026-03-31)
- https://aws.amazon.com/certification/certified-ai-practitioner/ — AIF-C01 page (no fee stated in page text)
- https://render.com/docs/free — Render free instances, service-type limits, 30-day Postgres expiry
