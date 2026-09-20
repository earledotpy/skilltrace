# A Competency-Based Skill-Graph Framework for Self-Directed AI Engineering

**Design Document — Phase 2 Deliverable**
**Target archetype:** Applied AI / LLM Engineer ("build and ship"), with a deliberate first-principles spine
**Learner profile:** Mid-life career changer · 8–10 hrs/week · free/open-source preference · limited local hardware
**System intent:** A self-hosted, single-learner adaptive platform that is *also* a portfolio artifact demonstrating ed-tech systems architecture

---

## 0. Design Decision Record

This framework is not generic. Every structural choice below descends from a decision fixed during the Phase 1 interview. The Decision Record is reproduced first because it is load-bearing: each Pillar implements one or more of these rows, and any later disagreement should be resolved by amending this table, not by silently re-deriving the architecture.

| # | Dimension | Decision | Primary consequence |
|---|-----------|----------|---------------------|
| D1 | Target & contribution mode | Applied LLM Engineer; "contribute" = **build and ship** | Terminal graph nodes are shippable artifacts, not exams or publications |
| D2 | Core vs. adjacent boundary | **Safety + evals promoted into Core**; ethics/governance kept thin and applied | Adversarial robustness and evaluation are prerequisite-bearing Core nodes |
| D3 | Foundational depth | **Thin mandatory math spine + just-in-time** | Math nodes are *soft remediation* edges, not upfront *hard gates* |
| D4 | Unit of mastery | **Two-layer**: formative readiness + artifact as the real exit gate | Statistical machinery operates only where event volume is honest |
| D5 | Grading authority | **Objective gates primary/mandatory-where-possible; AI grading advisory only** | A node without an objective gate is a node whose author skipped the highest-value rep |
| D6 | Analytics scope | **Descriptive + Diagnostic + Prescriptive real; Predictive = labelled heuristic** | Only the structurally-grounded layers carry decision authority |
| D7 | Environment | **Cloud-first learning; local-first single-user SQLite MVP; deployment deferred** | The MVP is buildable at the learner's *current* skill level |

A single tension governs the whole design and is named explicitly so it can be defended against continuously: **the learner is building the platform with skills acquired through the platform.** Every choice that inflates the MVP's prerequisites inverts that dependency and converts the platform from a launchpad into a blocker. The architecture below is biased, everywhere, toward the minimum apparatus that does honest work for *n = 1*.

---

## Pillar 1 — Architectural Paradigm: The Skill Graph

### 1.1 From timeline to dependency structure

The orthodox syllabus is a total order over time. It fails the self-directed learner in two specific ways: it cannot represent that two skills are independent (parallelizable), and it cannot represent that a failure downstream implies a deficiency upstream. Both are central to mastery-based progression.

The framework replaces the timeline with a **directed acyclic graph (DAG)** in which:

- **Nodes** are *competencies* — the smallest unit that can be independently mastered and independently proven (D4).
- **Directed edges** are *prerequisite relations* — "B requires A" means the learner cannot productively attempt B's artifact without A's competence.

The theoretical grounding is deliberate, per the formatting constraint against motivational language:

- **Mastery Learning (Bloom).** Progression is gated by demonstrated competence, not elapsed time. A node does not close because its material was consumed; it closes because mastery was *proven* (Pillar 3).
- **Knowledge Space Theory (Doignon & Falmagne).** Prerequisite relations between knowledge components are a formal object; the set of "masterable next states" is computable from the graph and the learner's current mastery vector. This is precisely what makes adaptive sequencing tractable for one learner without population data.
- **Constructivism (Papert's constructionism in particular).** Knowledge is built by building public artifacts. This is why terminal nodes are *shipped things* (D1), not recall checks.

### 1.2 Node schema

The schema is the contract every other Pillar reads from. It is intentionally small.

```json
{
  "id": "rag.retrieval_quality",
  "title": "Retrieval quality for RAG",
  "tier": 1,
  "type": "core_technical",
  "prerequisites": ["embeddings.cosine_similarity", "data.chunking"],
  "remediation_targets": {
    "embeddings.cosine_similarity": "math.vectors_dot_product"
  },
  "knowledge_components": [
    "kc.recall_precision_tradeoff",
    "kc.chunk_overlap_effects",
    "kc.reranking_role"
  ],
  "formative_checks": "checks/rag_retrieval/*.yaml",
  "artifact_spec": "specs/rag_retrieval_eval.md",
  "validation": {
    "type": "objective_eval",
    "gate": "evals/rag_retrieval_suite/"
  },
  "mastery_state": "not_started",
  "credential": "badge.tier1.rag"
}
```

Two fields deserve emphasis because they are where Pillars 3–5 plug in:

- `validation.type` is an enum — `objective_eval | ai_advisory | human_review` (D5). The engine's *close* logic branches on this value, so authority to close a node is encoded in the node itself.
- `remediation_targets` maps a *weak prerequisite* to the *upstream node that repairs it*. This is the data the diagnostic layer (Pillar 4) traverses, and it is what makes D3's "just-in-time math" mechanical rather than aspirational.

### 1.3 Edge taxonomy

The thin-spine decision (D3) requires two distinct edge types, not one:

| Edge type | Semantics | Behaviour | Applies to |
|-----------|-----------|-----------|------------|
| **Hard prerequisite** | Node is *locked* until the source is mastered | Blocks forward traversal | Most Core Technical → Systems dependencies |
| **Soft remediation / co-requisite** | Node is *attemptable*; source is pulled in *reactively* on failure | Activated only when a diagnostic trace implicates it | The entire math spine, and most Foundational content |

The default traversal direction is therefore *forward into building*. The math nodes are not a wall the learner climbs first; they are repair stations the diagnostic engine routes to when an applied node fails. This directly instantiates the "remediation path" requirement and resolves the most common career-changer failure mode (months lost in front-loaded math at high dropout risk).

### 1.4 Adaptive sequencing

Two operations, both cheap, both library-provided (see Pillar 5, `networkx`):

1. **Next-node recommendation = topological sort over the unmet-prerequisite frontier.** Given the mastery vector, the set of nodes whose hard prerequisites are all satisfied is the "fringe." Ordering the fringe (by tier, then by downstream leverage) yields the recommendation. *This is also the entire Prescriptive analytics layer* (D6) — it falls out of graph structure and needs no separate model.

2. **Remediation routing on failure.** When an artifact fails its gate (Pillar 3), the diagnostic layer (Pillar 4) maps the failure to one or more `knowledge_components`, then to the `remediation_targets` upstream node, and *re-injects that node into the fringe with priority*. The learner is not told "you failed"; they are told "attempt `math.vectors_dot_product`, then re-attempt."

### 1.5 The floating-node problem

Contextual nodes (D2 — governance literacy, communication-as-output) frequently have **no clean prerequisite edges**: "AI governance literacy" does not depend on backpropagation. Admitting many such nodes degrades the DAG into "a DAG plus a bag of unattached nodes," which a topological sequencer cannot order.

Resolution: gate floating nodes on **progress milestones** rather than skill prerequisites. "Complete OWASP LLM Top 10 literacy" is unlocked by *"reaching Tier 1 completion,"* not by any specific skill. This keeps the contextual band present (D2 keeps it thin, which is the second reason to do so) without corrupting the dependency structure. Milestone edges are a third, *non-prerequisite* edge type the engine treats as pure unlock conditions.

---

## Pillar 2 — Domain Curation & Curriculum Mapping

### 2.1 Tier architecture

Four tiers, reconfigured per D2 (safety + evals promoted *into* Core; governance kept thin):

| Tier | Name | Role | Edge default |
|------|------|------|--------------|
| **T0** | Foundational | Thin math spine + JIT remediation pool | Soft (D3) |
| **T1** | Core Technical | Applied LLM engineering **incl. safety + evals** | Hard within tier |
| **T2** | Systems / Deployment | Serving, demos, observability under free-tier constraints | Hard from T1 |
| **T3** | Contextual | Governance literacy + communication-as-output | Milestone-gated |

### 2.2 Curated resources

All entries below are free or free-to-audit, open where possible, and were verified current as of mid-2026. The resource layer is the **most time-sensitive** part of this document; the platform should treat resource URLs as data, not as hard-coded constants, so they can be refreshed without touching the engine.

**T0 — Foundational (thin spine only; everything else is JIT)**

| Skill | Resource | Why this one |
|-------|----------|--------------|
| Vectors, dot product, cosine similarity | 3Blue1Brown, *Essence of Linear Algebra* | Intuition-first, no proof overhead — exactly the spine, nothing past it |
| Probability / sampling / softmax | Khan Academy (probability & statistics) | Free, granular, good for reactive remediation pulls |
| Gradient intuition + first NN from scratch | Karpathy, *Neural Networks: Zero to Hero* (micrograd → GPT) | Bridges T0→T1; builds understanding *by building*, satisfying constructivism |

**T1 — Core Technical (the spine of the curriculum)**

| Cluster | Resource | Notes |
|---------|----------|-------|
| LLM engineering roadmap + Colab notebooks | **mlabonne/llm-course** (GitHub) | Already structured as roadmaps with dependency ordering — the single best scaffold to *seed your graph from* |
| NLP / LLM / Agents foundations | Hugging Face **LLM, NLP, and Agents courses** | Free, actively maintained, runs on free tiers |
| Practical DL, top-down | fast.ai *Practical Deep Learning* | Build-first pedagogy aligned with D1 |
| RAG + agents, applied | Cohere LLM University; Microsoft *Generative AI for Beginners* | Free end-to-end RAG/agent tutorials |
| **Safety (now Core, D2)** | OWASP **LLM Top 10**; `garak` (red-team scanner); Giskard *Red Teaming LLM Applications* | Treat prompt injection / jailbreak / output validation as an attack surface, not an ethics seminar |
| **Evals (now Core, D2)** | Evidently AI *LLM evaluation for AI builders* (10 code tutorials); Inspect AI (UK AISI) | Writing the eval *is* the differentiating skill — see Pillar 3 |

**T2 — Systems / Deployment (cloud-first, free-tier-shaped, D7)**

| Skill | Resource | Constraint as pedagogy |
|-------|----------|------------------------|
| Run small/quantized models | Ollama; Hugging Face Hub | Free-tier ceilings *teach* quantization and checkpointing — production discipline you need anyway |
| Demos / sharing | Gradio / Streamlit on Hugging Face Spaces | Zero-cost public artifacts (doubles as portfolio) |
| Burst compute | Google Colab / Kaggle free tiers; Modal free tier | Session limits force small, checkpointed experiments |
| Observability | Langfuse (self-hostable tracing) | Feeds Pillar 4 honestly without enterprise infra |

**T3 — Contextual (thin, applied, milestone-gated)**

| Node | Resource | Depth |
|------|----------|-------|
| Governance literacy | NIST AI RMF overview; EU AI Act summary | Awareness only |
| Adversarial robustness literacy | OWASP LLM Top 10 (reused from T1) | Reinforcement, not new study |
| Communication **as output** | Writing a clean PR, a reproducible issue, a trustworthy README | Graded as artifacts, not as a soft skill |

### 2.3 Theory ↔ build balance

The curriculum is build-first with a first-principles spine, not build-only. The operational test for whether a theoretical node belongs in the graph at all: *does its absence cause silent, hard-to-diagnose failures downstream?* Cosine-similarity intuition passes this test (its absence makes retrieval tuning cargo-cult). Eigendecomposition proofs fail it for this archetype and are therefore *not* nodes — they are JIT material pulled only if a specific downstream node ever implicates them.

---

## Pillar 3 — Competency Assessment & Validation Engine

### 3.1 The two-layer model

A naïve combination of D1 (artifacts as mastery) and the brief's requested threshold logic (BKT/Elo) is **incoherent**: BKT and Elo require many small graded interactions per skill, and one shipped RAG app is *n = 1* — there is nothing to trace. The framework resolves this rather than choosing a side:

| Layer | Instrument | Frequency | Role | Feeds |
|-------|-----------|-----------|------|-------|
| **Formative (readiness)** | Auto-gradable knowledge-component checks | High | Establishes *readiness to attempt the artifact* — **does not** mark mastery | BKT/Elo + analytics stream |
| **Summative (mastery)** | The shipped artifact vs. a rubric/eval | Low | The **actual exit gate** that closes the node | Diagnostic + credential issuance |

Mastery is therefore: *readiness signal clears threshold → build the artifact → artifact passes its gate → node closes.* The small-*n* statistical machinery is confined to the formative layer, where event volume makes it honest. This is what rescues BKT/Elo from being "dashboard theatre."

> **Explicit caveat (D4).** The formative layer's honest justification, for a single learner, is partly *"to give the platform something to measure."* If the platform ever stops being a goal and the objective becomes purely learning AI, the formative layer is the **first** thing to cut.

### 3.2 Validation-type matrix

Per D5, grading authority is keyed to artifact type. The `validation.type` enum from §1.2 drives this:

| Type | Authority to close a node | Use when | Cost |
|------|--------------------------|----------|------|
| **`objective_eval`** | **Primary — auto-closes the node** | The artifact has checkable outputs (most Core nodes) | Writing the eval (this is the lesson, not overhead) |
| **`ai_advisory`** | **Never sole authority** — attaches feedback + provisional score | Genuinely fuzzy dimensions: README clarity, code idiom, design soundness | LLM-judge unreliability; mitigations below |
| **`human_review`** | Aspirational top stamp / override | Capstones; a real merged PR or maintainer comment | Unschedulable; not required to close |

**Curriculum-design constraint (the sharp one):** nodes are to be *authored* so their artifacts are objectively checkable wherever possible. "Let the AI grade it" is tempting precisely because writing the eval is hard — but **writing the objective eval is the single highest-value rep in the entire curriculum** (evals are promoted Core, D2). The discipline is the point. Encode it as an invariant: *a node without an objective gate is a node whose author skipped the most important work.*

**AI-advisory mitigations** (when `ai_advisory` is unavoidable): grade against an explicit rubric demanding cited evidence ("quote the line that does X"); run the judge 2–3× and check agreement; use a *different* model family than the one that produced the artifact. This is not paranoia — current open-source eval frameworks themselves report LLM judges at roughly 85–92% agreement with human raters and recommend human review on a 5–10% sample. The mitigation mirrors industry practice.

### 3.3 Mastery-threshold logic

- **Formative threshold:** a **BKT** mastery-probability cutoff (e.g. P(known) ≥ 0.95 across a node's knowledge components), or a simpler consecutive-correct heuristic when a node has too few items for BKT to be meaningful. Optionally an **Elo** rating where items and learner share a scale, useful for adaptive item selection. All three are confined to the formative layer by design.
- **Summative threshold:** binary-ish — the artifact's `objective_eval` gate passes, or it does not. No probabilistic dressing on a single build.

### 3.4 Grading harness

The objective-gate spine is built on existing open-source eval frameworks rather than hand-rolled:

| Need | Tool | License / note |
|------|------|----------------|
| pytest-native metric gates in CI | **DeepEval** | Apache-2.0; fails the "build" on threshold breach |
| Red-team / adversarial gate (Safety nodes) | **Promptfoo** | MIT; now under OpenAI stewardship — vendor-neutrality is a documented open question, weigh it for non-OpenAI judge models |
| Agent / tool-use evaluation | **Inspect AI** | MIT (UK AI Security Institute) |
| RAG-specific metrics | **Ragas** | Open-source |
| Benchmark-style reproducible evals | `lm-evaluation-harness` / OpenAI Evals | Open-source |

The harness is the same machinery a professional ships — so building it *is* curriculum, not scaffolding.

---

## Pillar 4 — Automated Analytics & Diagnostic Modeling

### 4.1 Data architecture — adopt the vocabulary, not the enterprise

The brief requests xAPI and a Learning Record Store. The honest *n = 1* position:

- **Adopt the xAPI statement *shape*** — `actor · verb · object` (e.g., *learner · attempted · rag.retrieval_quality*) — as the event schema. It is a clean, extensible vocabulary worth inheriting.
- **Do not deploy a full LRS.** A multi-service Learning Record Store (e.g., Learning Locker) for one learner is enterprise telemetry guarding a footpath. Store xAPI-shaped statements as rows in **SQLite** (D7). If a deployed, queryable LRS later becomes a *portfolio* goal, it is a deferred roadmap phase — labelled as such.

### 4.2 The four layers — three real, one labelled

The brief presents four co-equal layers. Three derive their power from **graph structure** (and therefore work at *n = 1*); one needs **population data** (and therefore cannot do honest inference for one learner). This is stated plainly per D6:

| Layer | Question | Status here | Mechanism | Authority |
|-------|----------|-------------|-----------|-----------|
| **Descriptive** | What happened? | **Real** | Aggregate over the event stream | Full |
| **Diagnostic** | Why? | **Real, high-value** | Rule-based root-cause tracing over the DAG (§4.3) | Full |
| **Prescriptive** | What next? | **Real** | Topological sort over the unmet-prereq fringe (§1.4) | Full |
| **Predictive** | What will happen? | **Labelled heuristic only** | Transparent extrapolation ("~3 sessions, based on recent pace") | **None over decisions** |

> **Predictive containment (D6).** The Predictive layer is the most *impressive-looking* and the least *honest* at *n = 1*; any "model" over one sparse stream is a moving average in a lab coat. It is retained, if at all, for **demonstration value** — explicitly walled off, visibly labelled "heuristic projection, not inference," and **forbidden from influencing sequencing**. The failure mode being prevented: a novice rearranging his study life around noise about his own learning. Demoting Predictive also removes the *only* component that would have justified a separate ML pipeline — a real Pillar 5 simplification.

### 4.3 Diagnostic modeling — selectively applied

Diagnosis is where the graph earns its cost. It is **not** statistical; it is structural, which is exactly why it works for one learner:

1. An artifact fails its `objective_eval` gate.
2. The failed assertions map to specific `knowledge_components` on the node.
3. Those map via `remediation_targets` to upstream node(s).
4. Those node(s) are re-injected into the fringe with priority (§1.4).

"Why did RAG fail?" resolves to a concrete answer — *weak cosine-similarity intuition* or *missed chunking edge case* — and an action, not a dashboard reading. Diagnosis is applied *selectively*: only on failure, only along implicated edges, never as a blanket scan.

---

## Pillar 5 — Operational Stack & Implementation Roadmap

### 5.1 Technology stack — Python, minimal dependencies, local-first (D7)

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Language | **Python** | Brief constraint; matches the domain being learned |
| Graph engine | **NetworkX** | DAG, topological sort, prerequisite traversal are built-in — Pillar 1 is mostly *configuration* of this library |
| Persistence | **SQLite** | One file; serves event store, mastery state, and xAPI-shaped statements; no server to operate |
| Schema / validation | **Pydantic** | The node schema (§1.2) becomes typed models; validation is free |
| API | **FastAPI** | Thin, async, minimal; teaches a production-relevant skill |
| Front end | Jinja2 templates or HTMX (avoid SPA complexity for MVP) | Lowest prerequisite burden; defer React |
| Grading harness | **DeepEval / Promptfoo / Inspect AI** (Pillar 3.4) | The objective-gate spine; professional-grade |
| Formative modeling | `pyBKT` (BSD) for BKT; ~30 lines for Elo | Confined to the formative layer (Pillar 3.3) |
| Descriptive dashboards | Plotly or Matplotlib | Reads SQLite directly; no extra service |
| Credentialing | Open Badges **2.0 baking** → **3.0** deferred (§5.3) | Minimal first, future-proof later |

Everything above runs **as a single Python process on the learner's current machine**, started when studying and off otherwise. There is no container orchestration, no message bus, no LRS service in the MVP. This is the concrete form of D7's anti-inversion principle: the MVP is buildable *before* the curriculum has taught deployment.

### 5.2 Implementation roadmap

Phased from a genuine MVP to advanced adaptive features. Each phase is shippable and useful on its own — and each phase is *itself* a portfolio artifact.

| Phase | Deliverable | Builds on curriculum | Key risk retired |
|-------|-------------|---------------------|------------------|
| **P0 — Seed** | Hand-author ~15 T1 nodes in JSON/YAML using mlabonne/llm-course as the skeleton; no code | none | Proves the *graph model* before writing software |
| **P1 — MVP** | NetworkX graph + SQLite state + CLI: "what's my next node?" (topological sort) and manual mastery marking | basic Python | Proves Prescriptive layer with zero ML |
| **P2 — Validation** | Wire DeepEval objective gates; node auto-closes on gate pass; formative checks added | Core: evals | Proves D4/D5 two-layer mastery |
| **P3 — Diagnostics** | `remediation_targets` traversal; failure routes to upstream node | graph algorithms | Proves Diagnostic layer — the graph's main payoff |
| **P4 — Analytics** | xAPI-shaped event logging; Descriptive dashboards; Predictive as a *labelled* heuristic widget | data handling | Proves Pillar 4 honestly |
| **P5 — Formative modeling** | `pyBKT` mastery probabilities over knowledge components | probabilistic ML | Makes formative thresholds principled |
| **P6 — Credentialing** | Open Badges 2.0 baking on tier completion | (light) | Tier completion becomes portable |
| **P7 — Deferred / portfolio** | FastAPI + web UI; deployed instance; optional OB 3.0 / deployed LRS | deployment (T2) | *Only if* a live URL is a portfolio goal — never on the MVP path |

The ordering is not arbitrary: each phase requires only skills the learner has plausibly acquired by that point. P7 deliberately collects every component that would otherwise have inverted the dependency, and quarantines it behind an explicit "this is for the portfolio, not for learning" decision.

### 5.3 Digital credentialing

- **MVP (P6): Open Badges 2.0 with badge baking.** OB 2.0 remains the most widely supported version in 2026; verification is a hosted JSON assertion, and metadata is *baked* directly into a PNG/SVG. For a single issuer issuing to a single learner, this is a few dozen lines and zero infrastructure.
- **Deferred (P7): Open Badges 3.0.** Finalized by 1EdTech in June 2024 and aligned with the W3C Verifiable Credentials data model, OB 3.0 adds cryptographic proofs, wallet portability, and DID-based identity. It is the more impressive and more future-proof story — and correspondingly more engineering. Open-source issuers worth evaluating if/when this phase is reached include **Badge Engine** (Digital Promise, OB 3.0) and **Badgr** (self-hostable, with a Pathways feature, though under post-acquisition organizational uncertainty).
- Badges align to nodes via the `credential` field (§1.2) and to skill frameworks via OB's `alignment` property, so a completed tier emits a verifiable, externally legible credential.

---

## Closing — Standing Failure Modes

A competency framework that does not name its own failure modes is incomplete. Three are structural to *this* design and should be watched continuously, not assumed away:

1. **The dependency inversion (the platform as blocker).** Every feature pulled forward from P7 raises the skill floor required to start. The countermeasure is the roadmap's strict phase ordering and the single-process MVP — defend them against scope creep.

2. **Dashboard theatre.** Three analytics layers are real because they are structural; the Predictive layer is decorative for one learner. If its heuristic output ever begins steering real study decisions, it has failed its containment and should be removed.

3. **Rigor-as-avoidance.** For a build-and-ship target, time in the math tier past the thin spine is frequently procrastination wearing the costume of "being thorough" — measurable, comfortable, and a hiding place from the more exposing act of shipping something public and imperfect. The just-in-time edge structure (D3) exists partly to make this avoidance visible: if the learner is repeatedly pulling math nodes that no downstream failure implicated, that is the signal.

The framework's coherence rests on one discipline above all: **build the artifact, write the eval, ship it, and let an objective gate — not a model, not a dashboard, and not the learner's own untrained judgment — decide whether the node is closed.**
