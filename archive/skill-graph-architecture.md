Phase 1: The Discovery Interview — COMPLETE.

All four design dimensions have been confirmed. The following consensus parameters govern the framework:

Dimension	Confirmed Parameter	
Scope	Core: DL, NLP, Classical ML (prerequisite). Expansion: RL, CV. Mandatory Adjacent: Math, SE, Ethics. Optional: MLOps, Hardware.	
Competency	4-level spectrum (Emerging → Developing → Proficient → Mastered) with binary "Proficient" gateway. Atomic micro-skills clustered into capability modules. Tier-specific evidence portfolios.	
Analytics	70% automated diagnostic / 30% self-assessment with divergence flagging. Hybrid quantitative dashboard + qualitative narrative. Prescriptive engine with learner override.	
Environment	Consumer laptop (8–16 GB RAM, no dGPU). Cloud offloading (Colab/Kaggle). Python-native, minimal dependencies. Linux/WSL2. Fragmented scheduling; offline-capable where possible.	

---

Phase 2: The 5-Pillar Framework

AXIOM: Adaptive Competency eXchange & Integrated Ontology for Mastery

A Skill Graph Architecture for Self-Directed Proficiency in Artificial Intelligence

---

Pillar 1: Architectural Paradigm (The Skill Graph)

1.1 Theoretical Foundation

Traditional syllabi impose a linear, time-bound progression that violates two well-established principles of learning science: Mastery Learning (Bloom, 1968), which holds that achievement levels are contingent on the quality of instruction and time-on-task rather than fixed time allocations; and Constructivism, which posits that knowledge is built via the active integration of new concepts into existing mental schemas. A linear timeline cannot model the non-uniform, recursive, and prerequisite-dependent nature of technical skill acquisition.

The proposed alternative is a dependency-aware Skill Graph, formally defined as a directed acyclic graph G = (V, E) where:

- V represents the set of skill nodes (atomic competencies).
- E represents the set of directed edges (prerequisite relationships).

This architecture transitions the learner from a passive recipient of a scheduled curriculum to an active traverser of a competency landscape, where progression is gated by demonstrated proficiency rather than calendar elapsed time.

1.2 Node Taxonomy

Each node v \in V is typed to reflect the epistemic nature of the competency:

Node Type	Symbol	Definition	Example	
Knowledge Node	K	Declarative understanding; "knowing that"	K{LA.3.2}: "Eigenvalues and eigenvectors of symmetric matrices"	
Procedural Node	P	Operational competence; "knowing how"	P{DL.2.1}: "Implementing backpropagation for a fully-connected layer from scratch"	
Contextual Node	C	Situational judgment; "knowing when and why"	C{ETH.1.4}: "Analyzing a facial recognition deployment for disparate impact"	
Portfolio Node	\Pi	Synthesis artifact; integrative demonstration	\Pi{CAP.1}: "End-to-end NLP pipeline with bias audit report"	

1.3 Edge Semantics & Prerequisite Logic

Edges e \in E are not uniform. They carry semantic weight that governs traversal rules:

Edge Type	Notation	Semantics	Graph Effect	
Hard Prerequisite	v_i \rightarrow v_j	Mastery of v_i is mandatory before v_j may be activated.	v_j state remains Locked until v_i \geq \text{Proficient}.	
Soft Prerequisite	v_i \dashrightarrow v_j	Recommended but not mandatory; learner may override with documented rationale.	v_j state is Available (Recommended); override triggers audit log entry.	
Co-requisite	v_i \leftrightarrow v_j	Simultaneous engagement is pedagogically optimal.	Both nodes may enter Active concurrently; mastery of one cannot be finalized until the other reaches \geq \text{Developing}.	
Remediation Edge	v_j \leftarrow v_i	Dynamically generated reverse edge triggered by diagnostic failure.	If v_j assessment reveals a gap in v_i, a temporary remediation path is instantiated.	

1.4 Adaptive Sequencing & Remediation

The system employs a modified topological traversal with dynamic path recalculation. The initial learning path is computed via Kahn's algorithm on the static prerequisite graph. However, as the learner interacts with the system, the path is adaptively modified:

1. Prerequisite Leakage Detection: If a learner attempts node v_j and fails assessments in a pattern consistent with a deficiency in upstream node v_i (e.g., chain-rule errors in backpropagation indicating a calculus gap), the system instantiates a remediation edge v_j \leftarrow v_i and suspends v_j until v_i is revalidated.
2. Spaced Reinforcement Triggers: Nodes that have been mastered but are prerequisite to newly accessed nodes are queued for micro-reviews (spaced repetition intervals: 1, 3, 7, 14, 30 days) to mitigate decay.
3. Learner Override Protocol: The prescriptive engine may recommend suspension, but the learner retains an explicit Force Advance capability. This action is logged and triggers a risk acknowledgment narrative (e.g., "You are proceeding to Convolutional Networks without confirmed mastery of Tensor Operations. Historical data indicates a 62% probability of remediation within 3 sessions.").

1.5 Node Lifecycle State Machine

Each node traverses a finite state machine:

```
Locked → Available → Active → Under Review → Mastered
            ↑                ↓
            └──── Remediation ──┘
```

- Locked: Prerequisite conditions unsatisfied.
- Available: Prerequisites met; learner may activate.
- Active: Learner has engaged with resources and/or assessments.
- Under Review: Assessment evidence submitted; awaiting validation (automated or portfolio review).
- Mastered: Mastery threshold achieved; node unlocks downstream dependencies.

---

Pillar 2: Domain Curation & Curriculum Mapping

The curriculum is partitioned into four tiers, reflecting a progression from necessary conditions (mathematics, software engineering) to sufficient conditions (core AI technical skills) to contextual integration (ethics, communication) and systems expansion (deployment, MLOps).

2.1 Tier I: Foundational / Mathematical

This tier consists of hard prerequisites for all downstream technical nodes. Mastery is defined as derivational fluency and novel application.

Domain	Micro-Skill Cluster	Primary Resources	Evidence Requirement	
Linear Algebra	Vectors, matrices, eigen-decomposition, SVD	3Blue1Brown Essence of Linear Algebra; MIT OCW 18.06 (Gilbert Strang); Interactive Linear Algebra (Brown University); Paul's Online Math Notes	Derive SVD from first principles; solve a novel transformation problem using NumPy	
Multivariate Calculus	Partial derivatives, gradients, Jacobians, chain rule	3Blue1Brown Essence of Calculus; MIT OCW 18.02; Khan Academy	Compute gradients for a custom loss function manually; verify with SymPy	
Probability & Statistics	Random variables, distributions, MLE, Bayesian updating	Harvard Stat 110 (Blitzstein & Hwang, free text + lectures); Seeing Theory (Brown University, interactive); MIT OCW 18.05	Derive MLE for a Poisson distribution; perform Bayesian updating on a synthetic dataset	
Software Engineering	Python fluency, Git, basic architecture, debugging	Python Official Tutorial; Automate the Boring Stuff with Python (Sweigart, free); Corey Schafer (YouTube); Pro Git (free); freeCodeCamp	Build a modular Python package with unit tests; maintain version history on GitHub	

2.2 Tier II: Core Technical

This tier is bifurcated into Classical Machine Learning (prerequisite to Deep Learning) and Modern Deep Learning / NLP (the primary target domain).

Domain	Micro-Skill Cluster	Primary Resources	Evidence Requirement	
Classical ML	Regression, classification, regularization, validation, tree-based methods	Andrew Ng Machine Learning Specialization (Coursera, audit/free); An Introduction to Statistical Learning with Python (James et al., free PDF); scikit-learn documentation	Implement linear regression from scratch (NumPy only); build a full classification pipeline with cross-validation	
Deep Learning	Neural nets, backpropagation, CNNs, optimization, regularization	fast.ai Practical Deep Learning for Coders (free); Neural Networks and Deep Learning (Nielsen, free online); Dive into Deep Learning (d2l.ai, free); MIT 6.S191	Implement a 2-layer MLP with manual backprop; train a CNN on CIFAR-10 using PyTorch (CPU)	
Natural Language Processing	Tokenization, embeddings, RNNs/Transformers, fine-tuning	Hugging Face NLP Course (free); Speech and Language Processing (Jurafsky & Martin, free draft 3rd ed.); NLTK Book (free)	Build a sentiment classifier from scratch; fine-tune a BERT model on a custom dataset using Hugging Face Transformers	

2.3 Tier III: Systems / Deployment (Expansion Tier)

Activated only after Tier II core nodes reach Proficient. This tier is optional per the confirmed scope.

Domain	Micro-Skill Cluster	Primary Resources	Evidence Requirement	
MLOps & Deployment	Model serving, API design, monitoring, CI/CD for ML	Made With ML (free course); Google ML System Design materials; freeCodeCamp DevOps	Deploy a model via Streamlit or Gradio; set up a GitHub Actions pipeline for automated testing	
Cloud & Compute	Colab/Kaggle optimization, resource management, data versioning	Google Colab documentation; Kaggle Notebooks; DVC documentation (free)	Optimize a training notebook for TPU/GPU free tier; use DVC for dataset versioning	

2.4 Tier IV: Adjacent / Contextual

Mandatory for analytical proficiency, but assessed via contextual judgment rather than procedural implementation.

Domain	Micro-Skill Cluster	Primary Resources	Evidence Requirement	
AI Ethics & Safety	Fairness, accountability, transparency, risk analysis	AI Safety Fundamentals (BlueDot Impact, free); Fairness and Machine Learning (Barocas et al., free draft); EU AI Act (public); ACM Code of Ethics	Conduct a bias audit on a provided dataset; write a 1,500-word policy brief on a deployment scenario	
Technical Communication	Research synthesis, documentation, peer explanation	MIT Communication Labs (free guides); freeCodeCamp Technical Writing; "How to Write a Technical Paper" (various university guides)	Produce a technical blog post explaining a model architecture to a non-expert audience	

2.5 Build-First Integration Strategy

To prevent the "lecture trap" (passive consumption without transfer), the framework enforces a Build-First Constraint: for every K-type node, the learner must produce a corresponding P-type artifact within two sessions. For example, after engaging with the theory of gradient descent, the learner must implement it from scratch before accessing the next node. This aligns with Constructionism (Papert, 1980), which emphasizes learning through the construction of public artifacts.

---

Pillar 3: Competency Assessment & Validation Engine

3.1 Assessment Typology

Type	Function	Frequency	Modality	
Formative (Diagnostic)	Provide real-time feedback during learning; identify misconceptions	Continuous	Embedded quizzes, code checkpoints, confidence calibration prompts	
Summative (Gateway)	Validate mastery for node state transition	Per node completion	Structured examinations, portfolio submissions, reproducible code projects	
Interstitial (Spaced)	Prevent decay of mastered nodes	1, 3, 7, 14, 30 days post-mastery	Micro-assessments (5–10 minutes), "explain it like I'm five" prompts	

3.2 Automated Grading Architecture

Given the constraint of zero budget for API consumption and limited local hardware, the assessment engine employs a tiered automation strategy:

- Procedural Nodes (Code): Automated via pytest harnesses and nbgrader (Jupyter notebook validation). Learners submit notebooks or `.py` files; the system executes tests in an isolated environment (locally or on Colab) and returns pass/fail with stack traces.
- Knowledge Nodes (Mathematics): Partially automated via SymPy for symbolic verification of derivations. Where symbolic verification is intractable (e.g., geometric intuition), structured self-assessment rubrics are used, with the system requiring the learner to articulate their reasoning in writing. Local lightweight LLMs (e.g., Phi-3 or Gemma 2B via Ollama) may be used for surface-level coherence checking of explanations, but final validation defaults to human-in-the-loop (self-assessment with mandatory confidence calibration).
- Contextual Nodes (Ethics/Case Studies): Automated evaluation is currently unreliable for nuanced ethical reasoning. The system employs structured rubrics (e.g., identification of stakeholders, application of fairness criteria, proposal of mitigations) with AI-assisted pre-screening (local LLM flags missing rubric dimensions) followed by mandatory learner self-assessment against the rubric.

3.3 Mastery Threshold Logic: The Pragmatic Bayesian-Consecutive Hybrid (PBCH)

A pure Bayesian Knowledge Tracing (BKT) model (Corbett & Anderson, 1994) is theoretically ideal but requires parameter estimation datasets unavailable for a single learner. Conversely, a naive "3 correct in a row" heuristic fails to account for guess/slip probabilities and contextual diversity.

The PBCH algorithm is proposed as follows:

For each micro-skill node n, maintain a latent mastery probability P(L_n) \in [0, 1], initialized at 0.1.

Update Rule:
- On correct application in a novel context:

  P(L_n) \leftarrow P(L_n) + (1 - P(L_n)) \cdot \alpha{correct}

  where \alpha{correct} = 0.25.
- On incorrect application:

  P(L_n) \leftarrow P(L_n) \cdot \alpha{incorrect}

  where \alpha{incorrect} = 0.6.

Mastery Declaration:

Node n is declared Mastered when:
1. P(L_n) \geq 0.85, AND
2. The learner has demonstrated the skill in at least 3 distinct problem contexts (to prevent rote memorization of a single problem type), AND
3. A confidence-calibrated self-assessment rating of \geq 4/5 is recorded (cross-validation condition).

Forgetting Decay:

If no interaction with node n occurs for t > 30 days, apply:

P(L_n) \leftarrow P(L_n) \cdot e^{-\lambda t}

where \lambda = 0.02. If P(L_n) drops below 0.70, the node reverts to Available for micro-review.

3.4 Evidence Portfolio Requirements

Mastery of higher-order Portfolio Nodes (\Pi) requires the submission of a reproducible artifact repository containing:
1. Source code with `README.md` and `requirements.txt`.
2. A `METHODS.md` document explaining architectural decisions.
3. A `REFLECTION.md` document analyzing limitations and ethical considerations.
4. Evidence of version control (Git commit history).
5. A 5-minute screencast or written walkthrough demonstrating functionality.

---

Pillar 4: Automated Analytics & Diagnostic Modeling

4.1 Data Collection Architecture

To ensure interoperability and future extensibility, the system adheres to the xAPI (Experience API / Tin Can API) specification for learning record statements. However, to respect the minimal-dependency constraint, the implementation uses a lightweight SQLite-backed LRS rather than a full Learning Locker deployment.

Schema (Simplified):

Field	Type	Description	
`statement_id`	UUID	Unique identifier	
`timestamp`	ISO 8601	Event time	
`actor`	JSON	Learner identifier	
`verb`	JSON	`attempted`, `completed`, `passed`, `failed`, `remediated`, `interacted`	
`object`	JSON	Node ID or resource URL	
`result`	JSON	Score, duration (ms), response text	
`context`	JSON	Prerequisite states, platform (local/Colab), session ID	

Data Sources:
- Assessment Events: pytest results, notebook execution metadata, self-assessment form submissions.
- Behavioral Traces: Time-on-task (measured via session tracking in the Streamlit dashboard), video watch percentages (self-reported), code commit timestamps.
- Environmental Metadata: Hardware context (local vs. Colab), dependency versions.

4.2 The Four-Layer Analytics Model

Layer	Question Answered	Technique	Output	
Descriptive	What happened?	SQL aggregation; Pandas summaries; time-series bar charts	Weekly progress reports; node completion velocity; time-on-task distributions	
Diagnostic	Why did it happen?	Error pattern clustering (k-means on error type vectors); prerequisite leakage correlation matrices	Misconception reports (e.g., "Errors in Node DL.2.1 correlate 0.78 with weaknesses in Node CALC.1.3"); root-cause narratives	
Predictive	What will happen?	Linear regression / ARIMA on weekly velocity; survival analysis for node completion times	Projected mastery dates per tier; at-risk node flags (predicted stall >14 days)	
Prescriptive	What should I do next?	Rule-based expert system; graph traversal with weighted heuristics	Remediation path queues; optimal next-node recommendations; schedule optimization for 8–10 hr/week constraint	

4.3 Diagnostic Modeling & Root Cause Analysis

Diagnostic modeling is selectively applied to nodes where the learner has recorded two or more consecutive failures or where the self-assessment / automated diagnostic divergence exceeds one proficiency level.

The Diagnostic Protocol:
1. Error Vector Extraction: Decompose each failure into a vector of error types (e.g., conceptual, procedural, notational, transfer).
2. Prerequisite Correlation: Compute Pearson correlation between error vectors and historical performance on all upstream nodes.
3. Root Cause Hypothesis Generation: If correlation with an upstream node v_i exceeds 0.65, generate a Diagnostic Narrative: "Your errors in implementing batch normalization suggest a fundamental misunderstanding of population statistics (Node PROB.2.1). Remediation is recommended."
4. Intervention Assignment: Queue the identified upstream node for focused remediation (bypassing the full curriculum sequence).

4.4 Learner Dashboard Specification

The dashboard is implemented as a local Streamlit application with two primary views:

View A: Quantitative Navigation (The Skill Graph)
- Interactive network visualization (via `pyvis` or `networkx` + `plotly`) where nodes are color-coded by state.
- Sidebar metrics: Weekly velocity (nodes mastered / week), current streak, at-risk nodes.
- Time-series charts: Cumulative mastery curve, actual vs. predicted progress.

View B: Qualitative Diagnostic Panel
- Narrative summaries of the last 5 diagnostic events.
- Active remediation paths with estimated time to resolution.
- Confidence calibration charts (self-assessed vs. demonstrated proficiency).

---

Pillar 5: Operational Stack & Implementation Roadmap

5.1 Technology Stack Recommendation

All components prioritize Python-native, free, open-source, and self-hostable/local-first operation.

Layer	Technology	Justification	
Backend API	FastAPI (Python)	Lightweight, async-native, automatic OpenAPI documentation, minimal boilerplate.	
ORM / Validation	SQLAlchemy 2.0 + Pydantic v2	Industry standard; robust type safety; SQLite-compatible.	
Database (MVP)	SQLite	Zero-configuration, file-based, single-user optimal, requires no server.	
Database (Advanced)	PostgreSQL	Migration path for concurrent analytics, full-text search, and JSONB for xAPI statements.	
Analytics Engine	Pandas / Polars + custom Python modules	No external BI tool dependencies; fully programmable.	
Dashboard Frontend	Streamlit	Pure Python; rapid prototyping; ideal for single-user local analytics; offline-capable.	
Skill Graph Viz	PyVis (NetworkX wrapper) + Plotly	Interactive graph rendering within Streamlit.	
Assessment Runner	pytest + nbgrader (Jupyter)	Standard Python testing; notebook validation.	
Symbolic Math Check	SymPy	Native Python; verifies derivations and algebraic manipulations.	
Version Control	Git + GitHub/GitLab (free tier)	Essential for portfolio evidence; cloud backup of code artifacts.	
Cloud Compute	Google Colab (free tier) + Kaggle	GPU/TPU access for model training; zero local hardware burden.	
Local LLM (Optional)	Ollama + Phi-3 / Gemma 2B	Privacy-preserving; runs on CPU with 8–16 GB RAM for lightweight rubric pre-screening.	
Credentialing	Open Badges 3.0 (JSON-LD) via custom issuer	No proprietary platform lock-in; badges are cryptographically verifiable and learner-owned.	

5.2 Phased Implementation Roadmap

The roadmap assumes the learner is simultaneously building the system and learning the content. System assembly is treated as a meta-learning activity (Tier II: Software Engineering) to prevent overhead from displacing domain study.

Phase 1: Minimum Viable Product (Weeks 1–8)
- Objective: Operationalize the Skill Graph and begin Tier I study.
- System Tasks:
  - Design SQLite schema for nodes, edges, assessments, and xAPI statements.
  - Build a FastAPI backend with CRUD endpoints for node state management.
  - Deploy a Streamlit dashboard with static Skill Graph visualization and manual state updates.
  - Implement the PBCH mastery tracker (simplified: threshold + context counter).
- Content Tasks: Begin Tier I (Linear Algebra, Calculus, Python, Git) using curated resources.
- Analytics: Descriptive layer only (completion tracking, time logging).

Phase 2: Intermediate Automation (Weeks 9–20)
- Objective: Automate assessment and introduce diagnostic analytics.
- System Tasks:
  - Integrate `pytest` harnesses for procedural node validation.
  - Build the automated grading pipeline (code submission → test execution → PBCH update).
  - Implement the diagnostic correlation engine (error vector extraction + prerequisite correlation).
  - Deploy the prescriptive recommendation engine (rule-based next-node suggestions).
  - Add Open Badges 3.0 issuance upon tier completion.
- Content Tasks: Complete Tier I; begin Tier II (Classical ML, Deep Learning).
- Analytics: Descriptive + Diagnostic layers active.

Phase 3: Advanced Adaptive Features (Weeks 21–36+)
- Objective: Full predictive modeling and adaptive sequencing.
- System Tasks:
  - Migrate database to PostgreSQL if analytics latency degrades.
  - Implement predictive layer (ARIMA / linear regression on velocity data).
  - Add spaced-repetition micro-review queue with automated scheduling.
  - Integrate local LLM (Ollama) for contextual node pre-screening and rubric assistance.
  - Build the learner override workflow with risk acknowledgment narratives.
- Content Tasks: Complete Tier II; activate Tier III (Systems/Deployment) and Tier IV (Ethics, Communication) in parallel.
- Analytics: All four layers (Descriptive, Diagnostic, Predictive, Prescriptive) active.

5.3 Digital Credentialing

The framework employs Open Badges 3.0 to issue cryptographically verifiable, learner-owned credentials.

- Badge Tiers: Aligned with curriculum tiers (e.g., "Foundational Mathematical Proficiency," "Core Deep Learning Practitioner," "AI Ethics & Governance Analyst").
- Issuance Logic: Triggered automatically upon completion of all mandatory nodes within a tier AND submission of the tier's Portfolio Node (\Pi).
- Storage: Badges are issued as JSON-LD files stored in the learner's GitHub repository and optionally uploaded to a public badge backpack (e.g., Badgr free tier or self-hosted Badgr Server).

5.4 Privacy & Data Sovereignty

All learning records, assessment data, and behavioral traces are stored locally in the SQLite database by default. Cloud services (Colab, Kaggle) are used only for ephemeral compute; no persistent learner data is stored on third-party platforms except version-controlled code artifacts on GitHub/GitLab. The system is designed to be air-gap capable for offline study sessions, with synchronization deferred until connectivity is restored.

---

Conclusion

This framework abandons the rigid, anachronistic structure of the time-bound syllabus in favor of a dynamic, evidence-based Skill Graph that respects the cognitive architecture of the learner and the operational constraints of the environment. By integrating dependency-aware sequencing, granular competency tracking, automated diagnostic analytics, and a minimal-dependency open-source stack, the AXIOM framework provides a rigorous, falsifiable, and self-directed pathway from foundational mathematical fluency to deep analytical proficiency in Artificial Intelligence.

The system is designed to be built as it is used, ensuring that the infrastructure of learning becomes itself an object of mastery—an instantiation of the constructivist principle that knowledge is most durable when it is actively constructed.