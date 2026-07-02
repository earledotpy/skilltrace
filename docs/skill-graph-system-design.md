# SYSTEM DESIGN DOCUMENT: AUTONOMOUS AI SYSTEMS ARCHITECTURE FRAMEWORK
## EXECUTIVE SUMMARY

This document outlines the architectural blueprint for a self-directed, competency-based learning framework. Traditional pedagogical models utilizing chronological syllabi are structurally inadequate for asynchronous, high-complexity systems engineering. Consequently, this architecture utilizes a Directed Acyclic Graph (DAG) for curriculum mapping, Constructivist theory for competency validation, and a decoupled edge-to-cloud data pipeline to monitor mastery without exhausting local compute resources.

## PILLAR 1: ARCHITECTURAL PARADIGM (THE SKILL GRAPH).

The framework Abandons the linear, time-bound syllabus in favor of a dependency-aware **Skill Graph**. This model maps knowledge as a network of interconnected nodes, optimizing for the nonlinear reality of multi-agent systems engineering and "vibe coding."

### 1.1 Node and Edge Architecture

 * **Nodes (Competencies):** Each node represents a discrete, actionable capability (e.g., "Implement Ed25519-signed agent mandates," "Quantize Llama 3 for 8GB RAM execution"). Nodes encapsulate the learning objective, required resources, and mastery criteria.
 * **Directed Edges (Prerequisites):** Edges define the strict dependencies between nodes. A learner cannot initiate an advanced node (e.g., "Fail-Closed Multi-Agent Routing") until the prerequisite nodes (e.g., "Terminal-Based State Logging," "JSON-RPC Message Parsing") reach the Mastery Threshold.
 * 
### 1.2 Adaptive Sequencing and Remediation

The graph is natively dynamic. When friction is detected during the active verification phase (detailed in Pillar 3), the system traces the directed edges backward to identify the structural deficit.
 * *Example:* If a multi-agent worktree execution fails, the diagnostic engine isolates whether the failure stems from a logic error (Core Technical node) or a misunderstanding of the underlying tensor dimensions (Mathematical node), temporarily locking the active node and routing the learner to the precise prerequisite node requiring remediation.
 * 
## PILLAR 2: DOMAIN CURATION & CURRICULUM MAPPING

The curriculum is segregated into four distinct tiers, engineered specifically for resource-constrained edge environments and terminal-centric workflows.

### 2.1 Foundational/Mathematical Tier

Prioritizes mathematical constructs essential for understanding vector embeddings, loss functions, and local model constraints.
 * **Nodes:** Algebraic expressions, simplifying radicals (bridging from current Units 11/13 proficiencies), matrices, and introductory linear algebra.
 * **Resources:** Open-source Khan Academy tracks (parsed via CLI or TTS), MIT OpenCourseWare 18.06 (Linear Algebra) specifically focusing on vector operations.
 * 
### 2.2 Core Technical Tier

Focuses on the operational fluency required to orchestrate AI architectures through command-line interfaces.
 * **Nodes:** Advanced Git submodules/worktrees, Bash scripting (Termux/Git Bash environments), lightweight text editing (Micro), and Python syntax review for code-auditing purposes.
 * **Resources:** GNU Bash Reference Manual, specific TTS-compatible historical software engineering texts, and the official Python documentation.
 * 
### 2.3 Systems & Deployment Tier

The primary vector of study. Focuses on local execution and optimization.
 * **Nodes:** Hardware-constrained Large/Small Language Model deployment, model quantization techniques (e.g., GGUF formatting), local API server hosting, and autonomous multi-agent state management.
 * **Resources:** Llama.cpp documentation, HuggingFace Transformers (quantization specific), and open-source agentic frameworks (e.g., AutoGen, LangChain) adapted for local endpoints.
 * 
### 2.4 Adjacent/Contextual Tier

Focuses on the systemic oversight, security, and governance of AI agents.
 * **Nodes:** Zero-trust architecture, autonomy-gating, verifiable code promotion, and privacy-preserving data handling.
 * **Resources:** NIST AI Risk Management Framework, cryptographic signing literature (Ed25519 application), and open-source system security protocols.
 * 
## PILLAR 3: COMPETENCY ASSESSMENT & VALIDATION ENGINE

Mastery is defined strictly by the learner's ability to govern and verify AI-generated architectures, merging systems engineering with active recall.

### 3.1 Validation Mechanisms

 * **Formative Validation (The Promotion Gate):** Code is evaluated via localized health-check scripts (analogous to the Axiom Forge pipeline). If an agent-generated architecture passes the syntax, memory, and logic checks within the 8GB RAM constraint, formative validation is achieved.
 * **Summative Validation (The AI Debrief):** Following a successful build, the learner initiates a terminal-based debrief with a local SLM or API-gated model. The model interrogates the learner on the system's architecture, fail-states, and governance mandates.
 * 
### 3.2 Automated Grading & Mastery Threshold Logic

The system evaluates the AI Debrief transcript against a predefined rubric. Mastery is not binary; it is calculated using a modified Bayesian Knowledge Tracing (BKT) algorithm. Let P(L_t) represent the probability that the learner has mastered the node at time t:
$$ P(L_t) = P(L_{t-1}) + \frac{P(T) \cdot P(L_{t-1}) \cdot (1 - P(S))}{P(L_{t-1}) \cdot (1 - P(S)) + (1 - P(L_{t-1})) \cdot P(G)} $$
Where:
 * P(T) = Probability of learning transition.
 * P(S) = Probability of a slip (successful build, but poor explanation).
 * P(G) = Probability of a guess (AI agent wrote the code, learner does not understand it).
The Mastery Threshold is achieved when P(L_t) \ge 0.95, triggering the unlocking of adjacent nodes on the graph.

## PILLAR 4: AUTOMATED ANALYTICS & DIAGNOSTIC MODELING

Data collection must occur continuously without imposing administrative friction on the learner or computational load on the local environment.

### 4.1 Data Architecture (Telemetry)

The system leverages a decoupled Learning Record Store (LRS) paradigm. Telemetry is gathered passively through Git hooks and Bash history parsers. When a health-check script resolves or a worktree is committed, an automated JSON payload formatted to xAPI standards is pushed to a private GitHub repository.

### 4.2 The Four Layers of Analytics

 1. **Descriptive (What occurred):** Automated aggregation of terminal logs, commit frequency, and time-on-task within specific worktrees.
 2. **Diagnostic (Why it occurred):** AI-driven semantic analysis of the Debrief transcripts to identify conceptual gaps (e.g., distinguishing whether a failure to deploy a model is due to a Bash syntax error or a misunderstanding of VRAM allocation).
 3. **Predictive (What will occur):** By analyzing the BKT probabilities, the CI/CD pipeline forecasts which upcoming nodes possess a high probability of failure due to decaying mastery in foundational tiers.
 4. **Prescriptive (Next steps):** The system dynamically generates and injects remediation mandates—such as a specific algebraic review cycle or a targeted TTS-compatible reading assignment—into the learner's active queue.
 5. 
## PILLAR 5: OPERATIONAL STACK & IMPLEMENTATION ROADMAP

The infrastructure relies exclusively on open-source, decoupled tools, ensuring the local compute remains dedicated to model execution.

### 5.1 Technology Stack

 * **Graph Visualization & Interface:** Obsidian (Local). Markdown-based graph rendering, operating offline with minimal RAM overhead.
 * **Telemetry & CI/CD Engine:** Git / GitHub Actions (Cloud). Operates as the serverless backend. Webhooks trigger Python-based analytic scripts upon every commit.
 * **Database:** Flat-file JSON / SQLite (Cloud). Stored within the GitHub repository, updated asynchronously by the CI/CD pipeline.
 * **Verification Agent:** Claude CLI or Antigravity (Local/API). Executed within Termux/Git Bash for summative debriefs.
 * 
### 5.2 Phased Implementation Roadmap

**Phase 1: Minimum Viable Graph (Days 1-14)**
 * Initialize the Obsidian vault.
 * Draft the primary nodes in Markdown and establish the prerequisite edges.
 * Begin manual tracking of progress by updating YAML frontmatter in the node files.

**Phase 2: Telemetry Integration (Days 15-30)**
 * Deploy custom Git hooks within the local development environment.
 * Write the Python scripts required to format terminal logs and health-check outputs into xAPI payloads.
 * Configure GitHub Actions to ingest the payloads and automatically update the Obsidian YAML frontmatter via automated pull requests.

**Phase 3: Active Verifier Deployment (Days 31-45)**
 * Develop the system prompt and strict rubric for the AI Debrief Agent.
 * Integrate the agent into the terminal workflow.
 * Script the CI/CD pipeline to parse the debrief transcripts and execute the BKT probability calculations, fully automating the Mastery Threshold logic.

**Phase 4: Cryptographic Credentialing (Days 46+)**
 * Implement a system to generate Ed25519-signed Open Badges upon the mastery of core tiers.
 * Store these verifiable credentials locally as cryptographic proof of competency and architectural governance capability.
