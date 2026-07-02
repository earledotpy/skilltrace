Competency-Based AI Skill Graph Framework

A Self-Directed, Analytics-Driven Architecture for Deep Proficiency

Document Version 1.0 – Research-Ready Technical Report
Target Learner: Mid-life career changer, 8–10 hrs/week, asynchronous micro-bursts
Architectural Principle: Mastery Learning (Bloom) + Bayesian Knowledge Tracing (Corbett & Anderson) + Constructivist Project-Based Application

---

Abstract

This document presents a complete design for a personalized, self-directed learning system aimed at developing deep proficiency in modern artificial intelligence. The system is tailored to an individual with limited hardware (i5-10210U, 8 GB RAM, 128 MB iGPU, ~96 GB storage), a fragmented schedule of 8–10 hours per week, and a preference for asynchronous micro-learning bursts of 15–30 minutes. It enforces mastery learning through a directed acyclic skill graph, Bayesian knowledge tracing, and automated project-based assessment, while providing a layered analytics engine that diagnoses, predicts, and prescribes learning activities. All heavy computation is offloaded to free cloud GPU resources; local operations are restricted to lightweight inference and data management. The architecture integrates open-source tools (Miniconda, Streamlit, FastAPI, Ollama, Celery, PostgreSQL) and open educational resources, ensuring the entire pipeline is cost-free and self-hostable. This document details every subsystem: the skill graph topology, adaptive sequencing, curriculum tiers, automated grading pipelines, mastery threshold logic, analytics layers, and a phased implementation roadmap.

---

Table of Contents

1. Introduction and Binding Constraints
2. Pillar 1: Architectural Paradigm – The Skill Graph
      2.1 Node Definition
      2.2 Directed Edges and Topology
      2.3 Adaptive Sequencing and Remediation
3. Pillar 2: Domain Curation and Curriculum Mapping
      3.1 Tier 0 – Foundational & Mathematical
      3.2 Tier 1 – Core Technical (Classical ML to Modern DL)
      3.3 Tier 2 – Systems & Deployment (Adjacency 2/5)
      3.4 Tier 3 – Ethics, Governance, Communication (Adjacency 4/5)
4. Pillar 3: Competency Assessment and Validation Engine
      4.1 Formative vs. Summative Assessment
      4.2 Automated Grading Architectures
      4.3 Mastery Threshold Logic: Fixed, Project-Based, and BKT
5. Pillar 4: Automated Analytics and Diagnostic Modeling
      5.1 Data Collection (xAPI-Compliant LRS)
      5.2 The Four Layers of Analytics
      5.3 Selective Diagnostic Triggers
6. Pillar 5: Operational Stack and Implementation Roadmap
      6.1 Technology Stack
      6.2 Hardware Adaptation Strategies
      6.3 Phased Implementation Plan
7. Conclusion and Future Evolution
8. References

---

1. Introduction and Binding Constraints

The goal of this system is to guide a learner from foundational mathematics through modern deep learning, deployment, and responsible AI, culminating in the ability to make substantive contributions to the field. The design is governed by the following immutable constraints derived from the learner’s environment and preferences:

· Hardware: Intel Core i5-10210U, 8 GB RAM, Intel UHD Graphics (128 MB shared), ~96 GB total internal storage (with significant free space constraints). Local deep training is infeasible; all heavy model training and large-scale inference must execute on free cloud platforms (Google Colab with T4 GPU, Kaggle).
· Operating System: Windows 11 Pro; WSL2 is leveraged for Docker and Linux-native tooling.
· Time: 8–10 hours per week, distributed across multiple days in 15–30 minute micro-bursts, with one weekly 2‑hour reserved block for summative project work.
· Learning Preferences: Self-directed, asynchronous, visual and hands-on; requires immediate feedback and demonstrable progress.
· Mastery Tolerances: Differentiated thresholds:
  · Math: fixed heuristic (5 consecutive ≥90% on randomized problem generators) → 0% false-positive tolerance.
  · Implementation projects: summative grade ≥85/100 on automated rubric → ≤3% false-positive tolerance.
  · Research/Ethics essays: Bayesian Knowledge Tracing posterior P(L) > 0.92, with a cap of 3 remediation attempts before manual override → 10% false-negative tolerance.
· Adjacency Weighting: Tier 2 (Systems & Deployment) weighted at 2/5; Tier 3 (Ethics, Governance, Communication) weighted at 4/5. Core Technical (Tier 1) carries full weight.

All design decisions flow from these constraints; every component is evaluated for memory footprint, disk usage, and execution time.

---

2. Pillar 1: Architectural Paradigm – The Skill Graph

The curriculum is modeled as a directed acyclic graph (DAG) where vertices represent atomic competencies (nodes) and directed edges encode prerequisite relationships. This graph is the central data structure that drives sequencing, remediation, and analytics.

2.1 Node Definition

Each node  v  is a tuple:

v = \langle \text{ID}, \text{Title}, \text{Tier}, \text{Effort} (\text{min}), \text{Prerequisites} (List[ID]), \\
\text{Resources} (List[URL]), \text{Formative\_Quiz} (Set), \text{Summative\_Gate} (Project|Essay|Exam) \rangle

· ID: Unique alphanumeric identifier (e.g., LA_01, CNN_03).
· Tier: {0,1,2,3} as defined in Section 3.
· Effort: Estimated completion time in minutes. All theory/quiz nodes are ≤25 minutes; implementation nodes are decomposed into sub-steps of ≤15 minutes each, forming a chain of micro-nodes that share the same parent summative gate.
· Prerequisites: Ordered list of prerequisite node IDs. A node becomes available only when all prerequisites are passed.
· Resources: Curated list of open-access URLs (videos, interactive pages, textbook sections), tagged with media type and estimated duration.
· Formative Quiz: A set of auto-generated low-stakes items (MCQ, fill-in-the-blank, code tracing) used for self-assessment and as triggers for the BKT update. Each item is linked to one or more knowledge components (KCs).
· Summative Gate: A high-stakes evaluation that unlocks downstream nodes upon passing. The type depends on the tier (project for Tier 1 & 2, essay for Tier 3, fixed-problem-generator for Tier 0).

2.2 Directed Edges and Topology

Edges  e = (u, v)  belong to one of two classes:

· Strict (hard prerequisite):  u  must be mastered before  v  can be attempted. Example: Matrix Multiplication → Backpropagation.
· Soft (recommended):  v  may be explored in parallel, but a warning is shown if  u  is not mastered. Example: Python Generators → PyTorch Datasets. The learner can override soft edges, but the system records the bypass event for later diagnostic analysis.

The graph is manually curated to reflect logical dependencies and pedagogical order. A small excerpt:

```
Linear_Algebra_01 → Linear_Algebra_02 → Eigendecomposition → PCA
Calculus_01 (Partial Derivatives) → Gradient_Descent → Backpropagation
Probability_01 (Bayes Theorem) → Naive_Bayes_Classifier
```

Topological sorting yields valid learning paths. The system maintains an adjacency list and caches reachability queries.

2.3 Adaptive Sequencing and Remediation

Sequencing is a state-space search over the DAG. Each node has a state ∈ {Locked, Available, InProgress, Passed, Failed}. The daily session builder uses a priority heuristic: 3 theory nodes + 1 implementation sub-step, selected from the set of Available nodes ranked by tier priority (Tier 0 > Tier 1 > Tier 2 > Tier 3) and then by a “learning velocity” score that favors nodes with high predicted success.

Remediation – Fault-Isolation Routine:

When a node  v  fails its summative gate (or formative score drops below a tunable threshold), the system executes the following algorithm:

```
def fault_isolation(node v):
    for u in strict_prerequisites(v):
        recency_score = bayesian_posterior(u)  # or recent quiz average
        if recency_score < mastery_threshold(u.tier):
            redirect_to_remediation(u)   # alternate resource + fresh formative set
            return
    # All prerequisites healthy → novel misconception
    bridge = generate_bridge_node(v.concept_title, v.failed_components)
    insert_node_into_dag(bridge, prerequisites=[v])
    set_priority(bridge, HIGH)
    alert_learner("New micro-exercise generated for targeted practice.")
```

The generate_bridge_node function uses a templated LLM prompt (via local Ollama or Colab-hosted model) to create 2–3 targeted micro-exercises, each with a short explanation and a code or multiple-choice check. The bridge node is inserted as a temporary prerequisite for retaking the original node’s summative gate.

Node Weights and Scheduler:
Weights are assigned per tier: w(Tier0)=4, w(Tier1)=5, w(Tier2)=2, w(Tier3)=4, consistent with the adjacency weighting. The scheduler maximizes total weight completed per session subject to the 25-minute budget. Implementation sub-nodes are treated as separate lightweight items.

---

3. Pillar 2: Domain Curation and Curriculum Mapping

The curriculum is organized into four tiers. The selection and depth of topics directly reflect the adjacency weights (2/5 for systems deployment, 4/5 for ethics/governance) and the mastery thresholds.

3.1 Tier 0 – Foundational & Mathematical

Goal: Solidify the mathematical underpinnings required for all subsequent machine learning.

Topics:

· Linear Algebra: Vectors, matrices, matrix multiplication, determinants, eigenvalues/eigenvectors, singular value decomposition (SVD), principal component analysis (PCA).
· Calculus: Functions, limits, derivatives, partial derivatives, the chain rule, gradients, Hessians, vector calculus for optimization.
· Probability & Statistics: Basic probability, Bayes’ theorem, random variables, probability distributions (Gaussian, Bernoulli, categorical), expectation, variance, maximum likelihood estimation (MLE), maximum a posteriori (MAP).
· Information Theory: Entropy, cross-entropy, Kullback-Leibler divergence, mutual information.

Primary Resources (all free):

· 3Blue1Brown YouTube series: Essence of Linear Algebra, Essence of Calculus – for geometric intuition.
· Khan Academy: Multivariable Calculus, Statistics and Probability – drill exercises with step-by-step feedback.
· immersivemath.com: Interactive linear algebra book.
· Mathematics for Machine Learning (free PDF, Deisenroth et al.) – supplementary reading for formal definitions.

Mastery Gate: Fixed heuristic – the learner must solve 5 consecutive problems from a randomized generator without error, scoring ≥90% on each. Problem types include computing matrix decompositions, applying the chain rule to composite functions, and calculating entropy. The generator pool is large enough to prevent memorization. Because this threshold demands perfection (5/5 at ≥90%), the false-positive rate is effectively zero.

3.2 Tier 1 – Core Technical

Goal: Achieve hands-on, project-verified proficiency in classical machine learning and modern deep learning architectures.

Topics:

· Classical ML: Linear regression, logistic regression, support vector machines, decision trees, random forests, gradient boosting (XGBoost/LightGBM), k-means clustering, dimensionality reduction.
· Deep Learning Foundations: Multilayer perceptrons, activation functions, backpropagation, regularization (dropout, L1/L2), batch normalization.
· Convolutional Neural Networks: Convolution arithmetic, pooling, architectures (LeNet, AlexNet, VGG, ResNet, Inception), transfer learning.
· Sequence Models: Recurrent neural networks, LSTMs, GRUs, sequence-to-sequence, attention mechanism, Transformers (self-attention, multi-head attention, positional encoding), vision transformers.
· Generative Models: Variational autoencoders (VAEs), generative adversarial networks (GANs), diffusion models (DDPM), large language model concepts (pretraining, fine-tuning, RLHF conceptually).
· Optimization: SGD, momentum, Adam, learning rate schedules, mixed-precision training (conceptual).
· Practical Skills: PyTorch/TensorFlow basics, data loading, writing training loops, debugging gradients, experiment tracking (Weights & Biases free tier, or local CSV logging).

Resources:

· d2l.ai (Dive into Deep Learning) – interactive Jupyter notebooks covering everything from linear regression to transformers and GANs.
· fast.ai (Practical Deep Learning for Coders) – top-down, project-first approach; excellent for motivation and rapid prototyping.
· Stanford CS231n lecture notes (Convolutional Neural Networks for Visual Recognition) and CS224n (NLP with Deep Learning) – for theoretical depth.
· PyTorch official tutorials and “Deep Learning with PyTorch” (free 60-minute blitz).
· “Attention Is All You Need” and “An Image is Worth 16x16 Words” original papers, with guided reading questions.

Mastery Gates: Each major architecture family has a project-based gate. The learner receives a Colab starter notebook containing a dataset and skeleton code. The project must be completed during a weekly 2‑hour block. Automated grading is described in Section 4.2. A passing score of ≥85/100 is required, ensuring a false-positive rate ≤3% (validated by rubric design and calibration with human experts on a small sample).

Example projects:

· MLP: Build a digit classifier (MNIST) from scratch in NumPy, then with PyTorch.
· CNN: Fine-tune a ResNet on a custom 10-class image dataset (e.g., from Kaggle).
· Transformer: Train a small transformer (6 layers) on a next-word prediction task with a tiny Shakespeare dataset.
· Diffusion: Implement a basic DDPM sampling loop in Colab using a pretrained U-Net.

3.3 Tier 2 – Systems & Deployment (Adjacency 2/5)

Goal: Provide operational competence for taking a model from notebook to production-like environment, but only to a foundational level (2/5 depth).

Topics:

· Model serialization: ONNX export, TorchScript, saving/loading state dicts.
· Inference APIs: Building a REST API with FastAPI, request/response schemas, handling concurrency.
· Containerization: Docker basics, writing Dockerfiles, running a containerized API on local Windows/WSL2.
· Performance basics: Benchmarking inference time, understanding FLOPs vs latency, conceptual CUDA profiling.
· Quantization: Introduction to post-training quantization (dynamic/static), using ONNX Runtime or PyTorch quantized modules to reduce model size.

Resources:

· Hugging Face Transformers documentation (model inference and serialization).
· Full Stack Deep Learning (free online course) – Deployment chapter.
· FastAPI official tutorial.
· Docker’s “Get Started” guide.
· Practical guides on quantizing BERT (e.g., by Hugging Face).

Mastery Gate: A single integrated project: the learner must deploy a quantized BERT-base model (converted to ONNX) as a REST API inside a Docker container on their Windows machine (CPU-only). The API must correctly handle concurrent requests (tested via pytest with requests library) and return sentiment prediction. The project is assessed with the automated rubric used for Tier 1 but with additional criteria for Dockerfile quality and API latency. Passing score ≥85.

3.4 Tier 3 – Adjacent & Contextual: Ethics, Governance, Communication (Adjacency 4/5)

Goal: Develop a strong, critical understanding of the societal implications of AI, capable of authoring model cards, compliance memos, and engaging in technical communication at a near-expert level (4/5 depth).

Topics:

· Fairness: Definitions (demographic parity, equalized odds, equal opportunity), sources of bias (data, label, algorithmic), fairness-aware metrics.
· Explainability: Post-hoc methods (LIME, SHAP, Integrated Gradients), inherently interpretable models vs black-box explanations, feature attribution.
· Privacy: Differential privacy basics, federated learning concept, data minimization.
· Regulatory Frameworks: EU AI Act (risk categories, requirements), NIST AI Risk Management Framework, GDPR implications for AI.
· Documentation & Accountability: Model Cards (Mitchell et al.), Datasheets for Datasets, FactSheets.
· Technical Communication: Writing clear documentation, presenting complex ideas to non-technical stakeholders, peer review.

Resources:

· Fairness and Machine Learning (Barocas, Hardt, Narayanan) – free online book (fairmlbook.org).
· Google’s Responsible AI Practices (PAIR guidebook).
· AI Now Institute reports and policy briefs.
· EU AI Act text and official summaries.
· NIST AI RMF 1.0.
· Original paper on Model Cards, plus examples from Hugging Face.

Mastery Gate: Bayesian Knowledge Tracing (BKT)-driven essay series. The learner writes two types of documents:

1. Model Card for a real-world ML system (e.g., a resume screening tool). The system provides a dataset description and model performance metrics; the learner must identify fairness concerns, document intended use and limitations.
2. Regulatory Compliance Memo for the same system under the EU AI Act, addressing risk categorization, conformity assessment, and required documentation.

Essays are graded via an automated pipeline (Section 4.2). Mastery is declared when the BKT model’s posterior probability of knowing all KCs exceeds 0.92. The 10% false-negative tolerance means the system allows up to 3 remediation cycles (new essay prompts) before alerting the learner to seek external feedback, balancing rigor with learner bandwidth.

---

4. Pillar 3: Competency Assessment and Validation Engine

4.1 Formative vs. Summative Assessment

· Formative (Low-stakes): Every node includes a short quiz generated from a question bank mapped to its KCs. Questions are delivered immediately after resource consumption. Feedback with hints is provided after the second incorrect attempt. Formative data feed the BKT model and the diagnostic analytics.
· Summative (High-stakes): The gates described per tier. Summative assessments are timed, proctored only by code/essay submission tracking, and are the sole means of unlocking downstream nodes.

4.2 Automated Grading Architectures

Code Projects (Tier 1 & 2):
A multi-stage evaluation pipeline:

1. Functional Correctness: A pytest suite checks model output shape, accuracy on a hidden test set, inference speed limits, and adherence to specified APIs. All tests must pass.
2. Static Analysis: Complexity metrics (e.g., cyclomatic complexity ≤10 per function) and style checks via Flake8 with customized rules.
3. LLM-as-a-Judge: The submitted code is anonymized and sent to an LLM (local quantized Mistral-7B via Ollama, or GPT-4o-mini with privacy guardrails if local RAM is insufficient). The LLM evaluates the code against 7 criteria on a 1–5 Likert scale:
   · Code clarity and naming
   · Appropriate use of library functions
   · Documentation (docstrings and comments)
   · Error handling and edge cases
   · Efficiency (algorithmic choices, vectorization)
   · Reproducibility (seed setting, environment file)
   · Modularity and separation of concerns
   The weighted sum of these scores (equal weights) forms the LLM quality score  S_{LLM} \in [1,5] . The final project score is:
   \text{Score} = 0.6 \times \text{Functional\_Pass\_Ratio} \times 100 + 0.4 \times \left( \frac{S_{LLM} - 1}{4} \times 100 \right)
   This gives heavy emphasis to functionality (60%) but rewards good engineering (40%). The threshold is 85.
4. False-positive control: The rubric and LLM prompt are calibrated on a small set of human-graded projects. The LLM’s inter-rater reliability is measured; if agreement with the human standard is <90%, the criteria weights are adjusted. The ≤3% false-positive tolerance is maintained by setting the decision boundary conservatively based on a calibration curve.

Essays and Memos (Tier 3):
Essays are evaluated using an ensemble of three signals:

· Semantic Similarity: The learner’s text is encoded (using Sentence-BERT all-MiniLM-L6-v2, run locally) and compared against a gold-standard reference embedding via cosine similarity. This score (normalized to [0,1]) captures overall topical coverage.
· Rubric Coverage: A predefined list of key entities (e.g., “identified bias source”, “proposed mitigation”, “cited relevant regulation”) is checked via a keyword and dependency parser. Each detected entity adds to a coverage score.
· Argumentative Coherence: Lexical chain density (measured by identifying repeated noun phrases and their taxonomic relations) and discourse structure (via a simple Rhetorical Structure Theory parser) yield a coherence metric.

Final grade = 0.4 × similarity + 0.3 × coverage + 0.3 × coherence. The result is mapped to a 0–100 scale. The threshold for a single essay is not fixed; instead, the scores are fed into the BKT model as evidence.

4.3 Mastery Threshold Logic

Tier 0 – Fixed Heuristic:
The sliding window of the last 5 attempts all must have a score ≥90%. This rule is checked automatically; any reset condition (e.g., long inactivity >7 days) triggers a fresh window. No false positives because the requirement is logically strict.

Tier 1 & 2 – Project-Based:
Project score ≥85 → node Passed. The false-positive tolerance ≤3% is ensured by calibration and by requiring that the functional tests are deterministic and critical; a student cannot pass by chance.

Tier 3 – Bayesian Knowledge Tracing (BKT):
We implement a standard BKT model per knowledge component (KC) per student. Each KC is associated with a set of essay requirements (e.g., “KC_Fairness_Def”, “KC_Regulation_Knowledge”). The model has four parameters:

·  P(L_0) : initial probability of knowing the KC.
·  P(T) : probability of transitioning from unlearned to learned after an opportunity.
·  P(G) : guess probability (producing correct answer without knowledge).
·  P(S) : slip probability (producing incorrect answer despite knowledge).

After each essay submission, the evidence is the essay’s coverage of that KC (normalized to [0,1]). We treat the continuous coverage as a soft observation: the likelihood of observing score  x  if the student knows the KC is  1 - P(S) , and if they don’t know it is  P(G) . However, to handle continuous scores, we binarize at 0.7: a KC is considered “correct” if coverage ≥0.7. Then standard BKT update equations apply:

P(L_{t} | \text{obs}_t) = \frac{P(L_{t}^{-}) \cdot (1-P(S))}{P(L_{t}^{-}) \cdot (1-P(S)) + (1-P(L_{t}^{-})) \cdot P(G)} \quad \text{if correct}

P(L_{t} | \text{obs}_t) = \frac{P(L_{t}^{-}) \cdot P(S)}{P(L_{t}^{-}) \cdot P(S) + (1-P(L_{t}^{-})) \cdot (1-P(G))} \quad \text{if incorrect}

where  P(L_{t}^{-})  is the prior before the observation, computed as  P(L_{t-1}) + (1 - P(L_{t-1})) \cdot P(T) .

We set initial parameters from literature:  P(L_0)=0.3, P(T)=0.1, P(G)=0.2, P(S)=0.1 . These can be tuned later with real data.

Advancement for the essay series happens when for all KCs,  P(L) > 0.92 . If after 3 remediation attempts the threshold is not reached, the system flags a manual mentor override, honoring the 10% false-negative tolerance (the learner might actually be competent but the automated evaluation fails to capture it, so we limit forced retries).

---

5. Pillar 4: Automated Analytics and Diagnostic Modeling

5.1 Data Collection (xAPI-Compliant LRS)

All interactions are recorded as xAPI statements stored in a local PostgreSQL database (with JSONB for statement flexibility). A Python service (pyrx or a custom FastAPI middleware) captures events:

Statement Schema (simplified):

```json
{
  "actor": {"mbox": "mailto:learner@local"},
  "verb": {"id": "http://adlnet.gov/expapi/verbs/attempted"},
  "object": {"id": "http://local.skillgraph/node/CNN_03/quiz/3"},
  "result": {
    "score": {"scaled": 0.8},
    "duration": "PT2M30S",
    "response": "42"
  },
  "context": {
    "extensions": {
      "http://local.extension/kc_ids": ["KC_conv_arithmetic"],
      "session_battery": 0.85,
      "active_tabs": 3
    }
  },
  "timestamp": "2026-06-28T09:23:00Z"
}
```

Additional telemetry includes video replay counts, code execution times, edit distance between successive code versions, and flag events for soft-edge bypasses. Privacy is maintained by aggregating browser tab counts and device status, never recording specific URLs.

5.2 The Four Layers of Analytics

1. Descriptive (Weekly Dashboard):
      A Streamlit dashboard displays:
   · Nodes completed this week vs plan, cumulative skill graph coverage.
   · Time distribution per tier (pie chart).
   · Average formative quiz scores, project scores trend line.
   · “Learning Velocity”: nodes/hour (with rolling 7-day average).
   · Heatmap of session times/days.
2. Diagnostic (Contrastive Fault Analysis):
      When a failure occurs, the system retrieves recent scores for all direct prerequisites (and their prerequisites) and compares them to the learner’s historical norm and a synthetic baseline (based on other learners’ data, initialized with Bayesian priors). It generates a natural language report:
   “Your CNN project failed. Your Convolution Arithmetic score is 92% (strong), but your Backpropagation for Pooling Layers formative score dropped to 60%. This suggests gradient flow understanding may be the root cause. Recommended: revisit Backpropagation node, complete remediation bridge.”
   This routine uses a simple rule-based system backed by a weighted bipartite graph linking KCs to nodes.
3. Predictive (Survival Analysis):
      We maintain a Cox Proportional Hazards model to predict time-to-completion of key milestones (e.g., Transformer node). Features:
   · Average daily study minutes (last 14 days).
   · Difficulty of upcoming nodes (average of historical failure rates from similar learners on the node’s prerequisite chain).
   · Recent quiz score slope (trend of scores on last 5 quizzes).
   · Number of soft-edge bypasses and remediation flags in past 2 weeks.
   The model is trained on synthetic data initially (generated from a stochastic process matching expected learner behavior) and updated as the learner’s own data accumulate. The dashboard shows predicted completion week with 80% confidence interval. If the drop-off probability (probability that milestone not reached by target date) exceeds 40%, an alert is triggered.
4. Prescriptive (Learning Vector Recommendations):
      Each Sunday night, the system computes an optimal sequence for the coming week using a constrained optimization:
   · Objective: maximize total node weight completed subject to predicted success probabilities (from predictive model) and time budget (10 hours).
   · Constraint: must include at least one summative project if a project gate is ready.
   · The solver uses a greedy algorithm over topologically sorted available nodes, weighted by priority and predicted success.
   If a stagnation risk is predicted, the planner may insert an “interest booster” – an applied case study or a playful competition (e.g., a Kaggle kernel to reproduce a result) that is topically related but lower cognitive load, to rebuild momentum.

5.3 Selective Diagnostic Triggers

To conserve compute and reduce notification fatigue, deep diagnostic routines (full Bayesian network inference, LLM-based causal explanation) are executed only when:

· A node is failed twice consecutively.
· A project score falls below 60/100.
· The learner’s predicted drop-off probability crosses 40%.
  All other analytics run on a scheduled batch basis (daily at 2 AM local time) using Celery tasks.

---

6. Pillar 5: Operational Stack and Implementation Roadmap

6.1 Technology Stack

Component Chosen Tool Justification
Local Python Env Miniconda + VS Code (WSL2) Lightweight; WSL2 enables Docker without Hyper-V; Conda isolates environments within 8 GB RAM.
Web Backend FastAPI Async, efficient; handles REST endpoints for quiz submission, project upload, analytics queries.
Web Frontend Streamlit Rapid development of dashboard and progress pages; runs locally on port 8501.
Database (LRS) PostgreSQL (Docker) Robust, handles JSONB for xAPI statements; fits within available storage (database size estimate ~50 MB after months).
Task Queue Celery + Redis (Docker) Manages asynchronous Colab submissions, LLM grading jobs, nightly analytics; Redis used as broker and result backend.
Local LLM Inference Ollama with Phi-3-mini (4‑bit quantized) ~2.5 GB RAM footprint; runs on CPU; started only during grading windows. Optionally, GPT-4o-mini API if RAM too tight, with data anonymization.
Cloud GPU Google Colab (free T4) Notebooks automatically uploaded via nbconvert and executed using Colab’s runtime API; results downloaded via gdown.
Storage Offload External SSD (USB-C) or Kaggle Datasets API Internal storage is limited; all large datasets and model checkpoints reside on external SSD; Colab/Kaggle provide ephemeral 50 GB+ for training.
Credentialing Open Badges 3.0 (pybadges) Tier completions issue verifiable badges with baked-in criteria; stored locally.
Version Control Git (local) + optional private GitHub All code, notes, and project artifacts are versioned.

6.2 Hardware Adaptation Strategies

· RAM Management:
  · Set a fixed 4 GB swap file on the external SSD.
  · Ollama runs a 3B model (Phi-3-mini) at q4_0 quantization, limiting RAM usage to ~2.5 GB; the server is stopped when not grading.
  · Streamlit, FastAPI, Celery workers are configured with conservative memory limits; total resident set size of all services ~2 GB.
  · During heavy local coding, recommend closing all non-essential applications, using Edge efficiency mode.
· Storage:
  · System files, conda envs, and database occupy ~20 GB.
  · All project datasets (e.g., CIFAR-10, Shakespeare text) are kept on external SSD or downloaded on-demand in Colab/Kaggle.
  · Automated cleanup scripts remove temporary Colab outputs older than 7 days.
· Browser & Tools:
  · Dedicate one browser profile to the learning dashboard, with aggressive tab discarding.

6.3 Phased Implementation Plan

Phase 0 – Foundation (Week 1):

· Set up WSL2, Miniconda, Docker Desktop.
· Deploy PostgreSQL and Redis containers.
· Create a Streamlit page that displays a hardcoded skill tree and lets the user check off nodes manually.
· Install all Python dependencies.
· Deliverable: Static resource tracker with local DB logging.

Phase 1 – MVP (Weeks 2–4):

· Implement the skill graph data model in a Python library (networkx-based).
· Build formative quiz engine: store questions in DB, serve via FastAPI, record answers as xAPI statements.
· Implement project submission endpoint: upload .ipynb → convert to Colab-compatible format → submit via colab-cli or HTTP trigger → retrieve output and parse scores.
· Develop weekly descriptive dashboard with basic charts (Plotly).
· Deliverable: Interactive skill graph, quiz functionality, automated Colab grading, and descriptive analytics.

Phase 2 – Analytics (Weeks 5–8):

· Integrate xAPI tracking fully; enrich statements with KC tags and context.
· Implement BKT model in Python (custom or using pyBKT) with database persistence.
· Build fault-isolation logic; connect it to remediation redirects.
· Deploy survival analysis model (using lifelines library) with synthetic data.
· Create the prescriptive weekly scheduler as a Celery task.
· Deliverable: Adaptive remediation, mastery tracking with BKT, predictive/prescriptive reports.

Phase 3 – Advanced Adaptive (Weeks 9–12):

· Integrate LLM-as-a-Judge: set up Ollama pipeline, craft prompts, implement rubric scoring.
· Develop dynamic bridge node generation using prompt engineering; integrate into fault-isolation.
· Finalize Open Badges issuance for Tier completions.
· Build the cumulative Capstone project: fine-tune a small transformer (e.g., DistilBERT) on a custom dataset entirely in Colab, with the entire workflow orchestrated by the system.
· Deliverable: Fully autonomous, self-improving learning co-pilot.

---

7. Conclusion and Future Evolution

This design translates pedagogical best practices into a practical, fully autonomous framework tailored to extreme individual constraints. By externalizing heavy computation, employing efficient local tooling, and embedding rigorous mastery checks, the system guarantees that every hour of study results in measurable, verifiable skill acquisition. The layered analytics not only track progress but actively adapt the curriculum to the learner’s cognitive state, turning potential frustration into targeted remediation.

Future enhancements could include:

· Federated anonymized sharing of BKT parameters to bootstrap cold-start for new learners.
· Integration with a spaced-repetition module for concept retention.
· A peer-matching system to pair learners working on similar nodes for virtual accountability.
· A lightweight VS Code extension for real-time code telemetry.

The architecture is intentionally modular; each pillar can be upgraded independently as open-source tools improve or as the learner’s hardware constraints evolve.

---

8. References

1. Bloom, B. S. (1968). Learning for Mastery. Evaluation Comment, 1(2), 1–12.
2. Corbett, A. T., & Anderson, J. R. (1995). Knowledge tracing: Modeling the acquisition of procedural knowledge. User Modeling and User-Adapted Interaction, 4(4), 253–278.
3. Deisenroth, M. P., Faisal, A. A., & Ong, C. S. (2020). Mathematics for Machine Learning. Cambridge University Press. (free online)
4. Zhang, A., Lipton, Z. C., Li, M., & Smola, A. J. (2021). Dive into Deep Learning. d2l.ai.
5. Howard, J., & Gugger, S. (2020). Deep Learning for Coders with fastai and PyTorch. O’Reilly Media. (fast.ai)
6. Mitchell, M., et al. (2019). Model Cards for Model Reporting. Proceedings of the Conference on Fairness, Accountability, and Transparency.
7. Barocas, S., Hardt, M., & Narayanan, A. (2019). Fairness and Machine Learning. fairmlbook.org.
8. European Union. (2024). Artificial Intelligence Act (Regulation 2024/1689).
9. NIST. (2023). Artificial Intelligence Risk Management Framework (AI RMF 1.0).
10. Vaswani, A., et al. (2017). Attention Is All You Need. NeurIPS.
11. Ronneberger, O., Fischer, P., & Brox, T. (2015). U-Net: Convolutional Networks for Biomedical Image Segmentation. MICCAI.
12. xAPI Specification. Advanced Distributed Learning. https://github.com/adlnet/xAPI-Spec

---