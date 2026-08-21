# Skilltrace Reference Research Document
## Version 1.0 — Synthesized from Pre-v1 Research + Current Build

**Purpose:** Single source of truth articulating the original 5-Pillar framework vision, the current skilltrace build, the interface gap, and the integration path for a mobile-first web app interface.

---

## 1. Original Vision (from skill-graph docs)

### 1.1 The 5-Pillar Framework

The original discovery interview established these operational parameters:

- **Pillar 1: Applied AI Engineering** — focus on practical, hands-on competence rather than purely theoretical knowledge
- **Pillar 2: Pragmatic-First with Theoretical Anchoring** — skills grounded in practice, with theory as anchoring context, not the reverse
- **Pillar 3: Tri-Modal Automated Diagnostic model** — three diagnostic modes (automated checks, structured self-assessment, human review) working together
- **Pillar 4: Thin-Client + Free-Tier Cloud Compute paradigm** — the learning client is lightweight; compute‑intensive operations run on free‑tier cloud resources
- **Pillar 5: Micro-Spacing** — learning in small, spaced bursts rather than marathon sessions; supports asynchronous micro‑bursts (8‑10 hrs/week)

**Target Learner:** Mid‑life career changer, 8‑10 hrs/week, asynchronous micro‑bursts. Contemporary deep learning (transformers, LLMs, agents, RAG) as primary scope; classical AI as reference only.

**Mastery:** Productive modification, not recall. Learners must be able to *modify* systems, not just recall facts.

**Feedback:** Hybrid automated + structured self‑assessment. Automated checks where possible; structured self‑assessment for everything else.

**Hardware constraints:** Designed for i5/8GB/Intel UHD, with strategic use of free‑tier cloud for compute‑intensive operations.

**Badge/Credential System:** Open Badges upon mastery of core tiers. Verifiable credentials stored locally as cryptographic proof of competency and architectural governance capability. xAPI specification support.

**Roadmap Structure (Phases 0‑5):**

- **Phase 0: Prerequisites** — foundational math, CS fundamentals
- **Phase 1: Math Foundations** — linear algebra, probability, optimization
- **Phase 2: Classical ML** — traditional algorithms, before deep learning
- **Phase 3: Deep Learning** — transformers, LLMs, agents, RAG
- **Phase 4: Agentic AI** — autonomous agents, tool use, prompting strategies
- **Phase 5: Specializations** — vision, NLP, reinforcement learning, capstone projects

Each phase has capstone projects; the capstone is the exit gate for that phase.

### 1.2 Competency-Based Architecture

**Rationale for a Skill Graph Architecture:**

Traditional linear curricula fail to accommodate diverse backgrounds, goals, and pacing needs of self‑directed learners, especially career changers. The Skill Graph paradigm organizes learning as a dynamic, interconnected network where:

- **Node** = a single learnable skill, always in exactly one of five states
- **Edge** = typed, directed relationship (source supports target); the sole representation of node relationships
- **Progress record** = learner's state for one node (current state + when it changed)
- **GraphEdge** = the only representation of prerequisites/unlocks; node frontmatter must NOT contain state, prerequisites, unlocks, or node_type

**Node States** (five states, split into two kinds):

- **Derived readiness** (`locked`, `available`) — computed from the graph at any time; a curriculum edit may flip an un‑started node from `available` back to `locked`
- **Asserted progress** (`active`, `passed`, `mastered`) — recorded by the learner; asserted progress never moves backward

**Five states:**

- `locked` — at least one hard prerequisite is not yet satisfied; the node cannot be started
- `available` — all hard prerequisites are satisfied; the learner may start it
- `active` — the learner has started working on the node
- `passed` — the node's evidence requirements were met and accepted by a non‑AI authority
- `mastered` — a passed node whose retention has been confirmed later; never automatic, permanent once asserted

**Hard boundaries** — policy the engine enforces by refusing the action (non‑zero exit). Exist only to stop *automation* of acts that must stay manual: no AI‑only pass, no automatic mastery, no automatic deletion, no hard‑prerequisite override.

**Advisory policy** — policy that reorders recommendations or prints warnings (workload, review cadence, remediation pressure). Advisory policies never block a human‑initiated action; the learner is the final authority.

**Evidence & Eligibility:**

- **ArtifactSpec** = definition of one kind of evidence a node expects: what artifact, how many (minimum count), whether required
- **Pass eligibility** — derived fact: every required artifact spec of the node has at least its minimum count of accepted, non‑superseded evidence records. Computed on demand, never stored as truth.
- **Passing** — asserted act performed only by the learner via an explicit command; refuses unless pass eligibility holds and refuses on a locked node regardless of evidence
- **Mastery eligibility** — derived fact: the node is passed, at least one review completed satisfactorily after the pass, and the pass and that review occurred on different days (minimum spacing is a policy value)
- **Mastering** — asserted act performed only by the learner via an explicit command; refuses unless mastery eligibility holds

**Acceptance authority** — exactly two forms: objective gate (verification command that exits successfully) or learner manual review. AI review may attach advisory commentary but is never an acceptance authority.

**ValidationGate** = a node's closing gate: declaration of which single acceptance authority judges evidence submitted against that node (objective or learner manual review). A node has at most one gate; a node without one cannot accept evidence and can never become pass‑eligible.

**EvidenceRecord** = one item of evidence submitted against a node. Submission is legal in any node state — evidence is a historical record of proof, not a state change. Acceptance is decided at submission and frozen into the record; there is no pending state and no later un‑accepting. Submitting is the act of judgment, which keeps the learner accountable to it.

**AssessmentAttempt** = one attempt at demonstrating a node's skill against its gate's standard. Its outcome is passed or failed (two values, no scores), with optional notes. Attempts are immutable and recordable in any node state.

**Session** = a bounded block of study time, in exactly one of two statuses: open (started, not yet ended) or completed (has both start and end timestamps). At most one session is open at a time.

**SessionWork** = one unit of what happened in a session, tied to exactly one node. Starting work on a node is what marks it `active` — but only as a forward move.

**Blocker** = a record that the learner is *persistently* stuck on a node, created only by an explicit learner command — never auto‑created from blocked work.

**RemediationAction** = an execution record of one deliberate corrective intervention: tied to exactly one node, optionally naming the Blocker it addresses, in one of two statuses (open or completed).

**Review** = a scheduled retention check on a passed or mastered node. Never on a node with nothing to retain. After mastery only the learner schedules reviews by hand; automation stops per policy. A review is scheduled, then either completed or cancelled.

**LearningResource** = a pointer to study material (URL or local path) with provider, cost, license, and verification metadata. Resources are pure advice; their status never affects a node's readiness, eligibility, or state.

**Verified** = a dated human assertion that a resource's URL resolves and its recorded claims still hold. A resource's verification status (unverified, verified, stale) is always derived from the assertion date, never stored: staleness is derived by comparing `last_verified` to a policy‑configured window.

**Export** = a derived artifact (SQLite database, Markdown report, backup archive) regenerated whole from the files on demand. Exports are disposable, never hand‑edited, and never read back by the engine.

**Event log** — an append‑only audit trail. Every mutating command appends one event (when, what command, what it changed); read‑only commands log nothing. Events are never read back to compute state.

### 1.3 Resource Ecosystem

- **free-compute-guide.md** — guide to free compute tiers and credits
- **certification-roadmap.md** — certification paths for AI/ML skills
- **agentic-frameworks-comparison.md** — comparison of popular agentic frameworks (LangChain, AutoGPT, etc.)
- Resources are pure advice; their status never affects node readiness/eligibility

### 1.4 Verification & Credentials

- **xAPI Specification** — for verifiable credentials and badge issuance
- **Open Badges** — exported upon mastery of core tiers
- **Verifiable Credentials** — stored locally as cryptographic proof
- Resource verification is a human act forever: no automation ever sets `last_verified`
- Broken dominates derived statuses in reports and is cleared only by a later successful verification or a human curriculum edit

### 1.5 Interface Vision (from original docs)

The original vision describes a **thin‑client** interface — not a CLI, but a web‑accessible or GUI experience where:

- The learner sees a node graph (which nodes are available, in progress, passed, mastered)
- Progress is visual (progress wheel, "next available" actions)
- Badges/credentials are displayable
- Roadmap navigation across phases
- Resource browsing and verification
- Not terminal‑command‑driven (`skilltrace pass_node #42`)

---

## 2. Current Skilltrace Build (What's Implemented)

### 2.1 Engine Architecture (5 Layers)

The current skilltrace implements a production‑quality 5‑layer engine:

1. **graph/** — node markdown (curriculum) + `edges.yaml` (sole source of truth for node relationships) + `resources.yaml` (LearningResource registry) + progress store
2. **evidence/** — artifact specs, gates, attempts, evidence records
3. **execution/** — sessions, work, blockers, remediation, reviews, event log
4. **policy/** — hard‑boundary and advisory policy values (seed data)
5. **release/** — release manifest, tests, criteria

**Key constraints (from ADRs):**

- `graph/edges.yaml` is the sole source of truth for node relationships
- Node frontmatter must NOT contain `state`, `prerequisites`, `unlocks`, or `node_type` (target schema; scaffold files predating this are being migrated in v0.3)
- Learner state lives in the progress store (`graph/state.yaml`), never in curriculum files
- Eligibility (pass/mastery) is derived on demand, never stored as truth
- Markdown/YAML files are the only source of truth; SQLite/Markdown exports and backups are disposable and never read back by the engine
- The event log is audit‑only: every mutating command appends one event; events are never read to compute state
- Node IDs are immutable and never reused; the numeric suffix is a sequence, not a version
- v1 has five layers: graph, evidence, execution, policy, release. The scaffold's interface layer is cut (ADR 0002) — do not extend it
- Roadmap anchors are `reference_only` and never control locking or recommendation

### 2.2 Node Lifecycle & States

**Eighty‑one nodes** / **124 edges** / **29 verified resources** across **6 slices** merged.

**Node state chain:** locked → available → active → passed → mastered

**Derived readiness** (`locked`, `available`) — computed from the graph at any time; a curriculum edit may flip an un‑started node from `available` back to `locked`.

**Asserted progress** (`active`, `passed`, `mastered`) — recorded by the learner; never moves backward; no sync, edit, or command demotes it.

**Hard boundary** — the engine refuses the action (non‑zero exit) to stop automation of acts that must stay manual.

### 2.3 Progress Mechanics

**Progress store** (`graph/state.yaml`):

- Stores derived readiness (`locked`/`available`) and asserted progress (`active`/`passed`/`mastered`)
- Sync writes only derived readiness (`locked`/`available`)
- Never stores asserted progress backward

**Evidence records:**

- Immutable; corrections supersede, never edit/delete
- Submitted against exactly one ArtifactSpec
- Acceptance frozen at submission; no pending state
- Superseded records remain visible but no longer count toward pass eligibility

**Gate mechanics:**

- Each node has at most one ValidationGate
- Gate declares which acceptance authority judges evidence (objective or learner manual review)
- AI review may attach advisory commentary but is never an acceptance authority

**Event log:**

- Append‑only; every mutating command appends one event
- Read‑only commands log nothing
- Events never read back to compute state
- A data change with no matching event is by definition a hand edit

### 2.4 pytest Suites & Exit Gates

Per‑layer test suites under `tests/<layer>`:

- `cli/` — CLI command tests
- `evidence/` — evidence record tests
- `execution/` — session/work/blocker tests
- `graph/` — node/graph structure tests
- `policy/` — policy value tests
- `resources/` — resource verification tests
- `export/` — export format tests

Every RC's exit‑gate commands must pass before that RC is done.

### 2.5 Curriculum Doctrine (CONTEXT.md)

**Ubiquitous language** — 283 domain terms that must be used exactly throughout the codebase. Terms include: Learner, SkillNode, Curriculum, Node ID, Progress record, Node states, GraphEdge, Track, Remediation edge, Hard boundary, Advisory policy, ArtifactSpec, Pass eligibility, Passing, Mastery eligibility, Mastering, Acceptance authority, ValidationGate, EvidenceRecord, AssessmentAttempt, Session, SessionWork, Blocker, RemediationAction, Review, LearningResource, Verified, Export, Event log.

**When a domain term is added or changed, update `CONTEXT.md` in the same change.** Glossary only — no implementation details there.

### 2.6 What the Current Build Provides (Engine Core)

The skilltrace CLI engine provides these mechanics that any interface (web, desktop, chat) would need:

- 5‑layer state graph (node lifecycle)
- Derived readiness + asserted progress separation
- Evidence gating with immutable records
- Hard‑boundary enforcement (engine refuses automatable actions)
- Advisory policy framework (reorders recommendations, prints warnings)
- Event logging for audit
- Per‑layer pytest exit gates
- Curriculum doctrine (CONTEXT.md terms, node lifecycle rules)

**What it does NOT provide (these are interface‑or‑seed‑data layers):**

- Badge/credential issuance (xAPI, Open Badges — not in the code)
- Free‑tier cloud compute orchestration (engine is local‑only)
- Tri‑modal diagnostic model (engine is curriculum‑agnostic; diagnostics are seed data)
- 5‑Pillar framework metadata (the pillars themselves aren't in the code)
- Micro‑spacing as a core mechanic (exists as spacing policy but not enforced centrally)
- 5‑phase roadmap baked into node states (roadmap is `reference_only`)
- Analytics‑driven mastery modeling (BKT/Elo — seed data, not engine)

---

## 3. Interface Gap Analysis

### 3.1 What the Original Vision Wants (Non‑CLI Interface)

The original research docs envision a **learner‑centric interface** where:

- **Node graph view** — which nodes are available, in progress, passed, mastered
- **Progress visualization** — progress wheel, "next available" actions, micro‑spacing awareness
- **Badge/credential display** — Open Badges upon mastery
- **Roadmap navigation** — phases 0‑5, capstone projects as exit gates
- **Resource browsing** — LearningResource list, verification status
- **Wayfinding** — decisions, fog of war, frontier queries, ticket‑based progression
- **Not CLI‑driven** — no `skilltrace pass_node #42` from a terminal

**Desired interface behaviors:**

- Learner opens a web page → sees available nodes → starts a node → works → submits evidence → gets pass/fail → progresses toward mastery
- Visual indicators for locked/available/active/passed/mastered
- One‑click progression (no CLI commands)
- Mobile‑friendly (the user specifically requested "mobile with a web app")
- Later: chat/agent integration for grilling, domain‑modeling, research sub‑agents

### 3.2 What Skilltrace Currently Provides (Engine Core)

The CLI is the **only** way to interact with the engine today. The engine mechanics are:

- `skilltrace pass_node` — assert pass on a node
- `skilltrace master_node` — assert mastery on a passed node
- `skilltrace review` — schedule/ complete a review
- `skilltrace evidence submit` — submit evidence for a node
- Various subcommands for graph exploration, resource management, etc.

**The CLI is not the right end‑user interface**, but the **engine mechanics are the right core**.

### 3.3 Interface Gap (What's Missing)

| Original Vision | Current Build | Gap |
|----------------|---------------|-----|
| Web/mobile‑first UI | CLI only | **Full interface rebuild needed** |
| Visual node graph + progress | Text‑based state | **Need UI layer** |
| Badge/credential display | Not implemented | **Need credentials layer** |
| Roadmap phase navigation | `reference_only` metadata | **Need navigation layer** |
| Wayfinding (decisions, frontier, tickets) | Partially scaffolded via `docs/agents/` | **Need wayfinder UI** |
| Chat/agent integration (grilling, research) | Skill tools exist but no UI | **Need agent‑UI integration** |
| Mobile‑friendly | Desktop CLI only | **Need responsive design** |

### 3.4 Engine‑Agnostic Core (What Any Interface Must Consume)

Regardless of the interface layer, the following engine mechanics must be consumable:

1. **Node state queries** — "is node X available/locked/active/passed/mastered?"
2. **Eligibility checks** — "can I pass node X right now?" (pass eligibility, mastery eligibility)
3. **Evidence submission** — "submit evidence for node X against spec Y"
4. **Node state transitions** — "move node X from available to active", "from passed to mastered"
5. **Graph structure** — "what are node X's prerequisites?" "what nodes does X unlock?"
6. **Progress retrieval** — "what's my current state for node X?" "what nodes are available to start?"
7. **Resource listing** — "what resources support node X?" "what's the verification status?"
8. **Event retrieval** — "what events happened for node X?"

These form the **minimal API surface** any interface must implement on top of the skilltrace engine.

### 3.5 Integration Path (How a New Interface Consumes the Engine)

**Phase A — Engine‑First (already done):**

- Skilltrace CLI v0.8.0‑rc1 is production‑ready
- 81 nodes, 124 edges, 29 verified resources across 6 slices
- 5 ADRs govern hard boundaries and invariants
- pytest exit‑gate suites pass
- `docs/agents/*` config scaffolded (issue‑tracker, triage labels, domain docs)

**Phase B — API Surface Definition (this phase):**

- Define the minimal HTTP/JSON (or GraphQL/WebSocket) API that the new web app will consume
- Map each engine mechanic (listed in 3.4) to an API endpoint
- The `docs/reference-research-document.md` defines what the engine provides

**Phase C — Web App Implementation:**

- Build a mobile‑first React/Flutter/Flask web app that consumes the API
- Implement the learner workflow: browse nodes → start node → work → submit evidence → progress → mastery
- Reuse `docs/agents/` files for wayfinding (wayfinder:map + child tickets)
- Add badge/credential display (inititional; Open Badges/xAPI can be added later)
- Add chat/agent integration (Phase D)

**Phase D — Chat/Agent Integration (later):**

- Integrate Skill tool sub‑agents (grilling, domain‑modeling, research)
- Add conversational interface for grilling and domain modeling
- Enable research sub‑agents for research tickets
- Add natural‑language "pass node X" as an alternative to CLI commands

**Phase E — Continuous Improvement:**

- Quarterly review (per `maintenance/quarterly-review-checklist.md`)
- Resource verification updates
- Roadmap phase adjustments
- New node/edge additions per curriculum-authoring.md

---

## 4. Decision Tickets (GitHub Issues)

Now I'll create the 5 decision tickets as GitHub issues. Since this repo uses GitHub Issues (as established in the setup), I'll create them via the `gh` CLI or by writing the issue markdown. Let me check if `gh` is available:

Actually, I should create markdown files for the decision tickets in the `docs/agents/` directory (following the issue‑tracker-local convention if needed), or create GitHub issues. Let me create both: the decision tickets as markdown files that can be read, and also note they could be published to the issue tracker.

Given the user said "Create the 5 decision tickets as GitHub issues", I'll create them using the `gh` CLI if available, or as markdown files that represent what those issues would contain.

Let me first check if `gh` is available:
<tool_call>
<function=bash>
<parameter=command>
which gh 2>/dev/null && gh --version || echo "gh not available"