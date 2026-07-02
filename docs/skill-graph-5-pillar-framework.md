**Phase 1 Conclusion**

The discovery interview is complete. We have established the operational parameters: a focus on **Applied AI Engineering**, assessed via **Pragmatic-First with Theoretical Anchoring**, driven by a **Tri-Modal Automated Diagnostic model**, and deployed via a **Thin-Client + Free-Tier Cloud Compute paradigm with Micro-Spacing**. 

Proceeding to Phase 2, I will now generate the comprehensive 5-Pillar Framework Design Document.

***

### PHASE 2: The 5-Pillar Framework Generation

## Pillar 1: Architectural Paradigm (The Skill Graph)

Traditional syllabi enforce artificial time-boxing (e.g., 12-week semesters), which inherently decouples learning velocity from mastery. For the mid-life career changer, operating within 8–10 hours of highly fragmented weekly availability, a linear progression model introduces excessive cognitive friction and high dropout risk. 

To resolve this, the framework utilizes a **Dynamic Dependency-Aware Skill Graph (DDSG)**. The DDSG abandons temporal constraints in favor of a Directed Acyclic Graph (DAG) architecture, where learning is strictly competency-gated.

**1.1. Nodes (Skills) and Directed Edges (Prerequisites)**
*   **Nodes:** Each node represents a discrete, atomic competency (e.g., "Implement Custom Dataset Loader in PyTorch," "Explain Self-Attention Mechanism," "Quantize LLM via bitsandbytes"). Nodes contain three internal states: *Uninitiated*, *In Progress*, and *Mastered*. 
*   **Directed Edges:** Edges define strict prerequisite dependencies. A node cannot be activated for study until all prerequisite nodes have achieved the *Mastered* state. This prevents the well-documented cognitive overload that occurs when learners attempt advanced concepts (e.g., Transformer architecture) without foundational prerequisites (e.g., Matrix Multiplication, Backpropagation).

**1.2. Adaptive Sequencing and Remediation**
The DDSG does not assume a static path. If a learner fails to achieve the Mastery Threshold on a node (e.g., fails the automated code validation for "Implement Cross-Entropy Loss"), the system triggers an **Adaptive Remediation Path**. 
*   Instead of forcing repetition of the identical material, the graph dynamically redirects the learner to a "Remedial Sub-node" (e.g., "Debugging Numpy Array Broadcasting"). 
*   Once the sub-node is mastered, the learner is routed back to the original node. This constructivist approach ensures foundational gaps are patched in real-time rather than accumulating into systemic knowledge deficits.

---

## Pillar 2: Domain Curation & Curriculum Mapping

The curriculum is structured across four distinct tiers, curated specifically for a thin-client, free-tier compute paradigm. All resources are open-source or freely accessible, prioritizing first-principles understanding paired with immediate practical application.

| Tier | Node Focus | Curated Open-Source Resources | Pragmatic Application |
| :--- | :--- | :--- | :--- |
| **Tier 1: Foundational/Mathematical** | Linear Algebra, Calculus, Probability, Python Data Stack | *Mathematics for Machine Learning* (Deisenroth et al., free PDF); *CS50's Introduction to Python*; NumPy/Pandas official docs. | Implementing gradient descent from scratch using NumPy in a Colab notebook. |
| **Tier 2: Core Technical** | Classical ML, Deep Learning Basics, Transformer Architecture | *Fast.ai* (Practical Deep Learning for Coders); *Dive into Deep Learning* (D2L.ai); Andrej Karpathy's "Neural Networks: Zero to Hero" (YouTube). | Fine-tuning a pre-trained ResNet on a novel image dataset via Kaggle Notebooks. |
| **Tier 3: Systems/Deployment** | Model Quantization, API Development, Lightweight MLOps | Hugging Face Course; FastAPI documentation; Docker basics (local CLI); Weights & Biases (free tier). | Serving a quantized LLM via a FastAPI endpoint hosted on a free-tier Render/Hugging Face Space. |
| **Tier 4: Adjacent/Contextual** | AI Ethics, Bias Mitigation, Data Privacy, Cognitive Science | *AI Ethics* (MIT Press, free PDF); Hugging Face "Ethics" documentation; NIST AI Risk Management Framework. | Writing an algorithmic impact assessment for a deployed facial recognition model. |

**Curriculum Balance Mechanism:** 
Each node within this mapping requires both a theoretical artifact (e.g., a Markdown file explaining the math) and a pragmatic artifact (e.g., a GitHub repository with functional code). This enforces the 60/40 Pragmatic-First weighting.

---

## Pillar 3: Competency Assessment & Validation Engine

Mastery is not implied by content consumption; it is proven through artifact generation and validation. To support the Tri-Modal Automated Diagnostic model, the assessment engine operates without human intervention.

**3.1. Formative vs. Summative Assessments**
*   **Formative (In-Node):** Low-stakes, automated checks occurring during the learning process. These include inline code execution via Jupyter notebooks and Socratic LLM prompts (e.g., "Explain to me why you initialized the weights with Xavier initialization").
*   **Summative (Tier-Completion):** A capstone project required to complete a Tier. For Tier 2, this might be building a custom tokenizer and training a micro-Transformer from scratch on a synthetic dataset.

**3.2. Automated Grading and Feedback**
*   **Pragmatic Output:** Utilizes GitHub Actions. When a learner pushes code to a specific node's repository, a CI/CD pipeline triggers. It spins up a container, installs dependencies, runs predefined unit tests (e.g., `assert model_output.shape == (batch_size, seq_len, vocab_size)`), and returns a pass/fail report.
*   **Theoretical Anchoring:** An open-source LLM (e.g., Llama-3-8B-Instruct via Groq API or local Ollama) is prompted with a strict rubric. The learner submits a written explanation; the LLM scores it on logical coherence, mathematical accuracy, and terminology, returning specific critiques.

**3.3. Mastery Threshold Logic**
The system utilizes **Bayesian Knowledge Tracing (BKT)**. 
Each node begins with a prior probability of mastery ($P(L_0) = 0.1$). 
*   A pass on the GitHub Actions unit test transitions the probability based on the "Learn" and "Slip" parameters. 
*   A high score on the LLM rubric further updates the posterior probability. 
A node is marked *Mastered* only when the posterior probability $P(L_n) \ge 0.95$.

---

## Pillar 4: Automated Analytics & Diagnostic Modeling

To optimize the 8–10 hours per week, the learner must minimize time spent on already-mastered concepts and maximize time on friction points. The analytics layer provides this optimization.

**4.1. Data Collection Architecture**
The system uses a lightweight **Learning Record Store (LRS)**. Using xAPI (Experience API) standards, the system logs:
*   Time spent reading documentation (via browser extension).
*   Git commit frequency and CI/CD pass/fail rates.
*   LLM assessment scores and self-reported confidence metrics.

**4.2. The Four Layers of Analytics**
1.  **Descriptive Analytics:** Dashboards displaying raw metrics—e.g., "You spent 4 hours on the Backpropagation node and made 12 Git commits."
2.  **Diagnostic Analytics:** The system identifies root causes of friction. If a learner fails the "Custom Dataset Loader" unit tests, the diagnostic engine cross-references the code errors with Tier 1 nodes and diagnoses: "Failure caused by lack of mastery in Python OOP concepts."
3.  **Predictive Analytics:** Based on historical node completion times and BKT scores, the system predicts future bottlenecks. "At your current velocity, the Transformer Architecture node will require 3x the normal time due to weak Linear Algebra mastery."
4.  **Prescriptive Analytics:** The system generates actionable directives. "Pause current progress. Spend the next 2 micro-sessions (90 minutes) completing the 'Eigendecomposition' remedial sub-node before attempting the next summative assessment."

**4.3. Diagnostic Modeling Application**
Diagnostic modeling is selectively applied to the **Theoretical Anchoring** data. By analyzing the LLM-tutor's critique logs, the system builds a semantic map of the learner's mental models. If the LLM frequently notes "confusion between stochastic and batch gradient descent," the system automatically injects targeted reading material into the learner's next micro-session.

---

## Pillar 5: Operational Stack & Implementation Roadmap

This pillar defines the concrete technology stack and the phased implementation plan to build this self-directed learning system.

**5.1. Recommended Technology Stack**
*   **Front-End / Dashboard:** **Streamlit** (Python-based, minimal dependencies, easily self-hosted or run locally).
*   **Database / LRS:** **SQLite** (local, lightweight) using a custom schema to log xAPI-like statements.
*   **Analytics Engine:** **Pandas** and **scikit-learn** (for BKT modeling and diagnostic clustering).
*   **Code Validation:** **GitHub Actions** (free CI/CD minutes for public/private repos).
*   **Compute:** **Google Colab Free Tier** / **Kaggle Notebooks** (for GPU access).
*   **AI Tutor:** **Ollama** (for local CPU inference of Llama-3) or **Groq API** (free tier for high-speed inference).

**5.2. Phased Implementation Roadmap**
*   **Phase 1: Minimum Viable Product (MVP) - Weeks 1-2**
    *   Define the Skill Graph in a JSON/YAML file structure.
    *   Set up the local SQLite database to track node status.
    *   Build the Streamlit dashboard to visualize the Skill Graph and manually update node statuses.
*   **Phase 2: Automated Pragmatic Validation - Weeks 3-4**
    *   Create template GitHub repositories for Tier 1 nodes.
    *   Implement GitHub Actions workflows with basic `pytest` suites for Python data structures and NumPy operations.
    *   Connect GitHub webhooks to the local Streamlit app to automatically update node statuses.
*   **Phase 3: AI-Assisted Theoretical Evaluation - Weeks 5-6**
    *   Integrate the Groq API or local Ollama into the Streamlit app.
    *   Engineer the Socratic Tutor prompt rubrics.
    *   Implement the text-submission interface for theoretical articulation.
*   **Phase 4: Advanced Adaptive Features - Weeks 7+**
    *   Implement the Bayesian Knowledge Tracing algorithm in Python to calculate dynamic mastery probabilities.
    *   Build the diagnostic logic that triggers remedial sub-nodes based on GitHub Actions failure logs.

**5.3. Digital Credentialing (Open Badges)**
To provide intrinsic motivation and verifiable proof of competency for a career changer, the system integrates **Open Badges v3.0** (an open standard for verifiable credentials).
*   Upon reaching the $P(L_n) \ge 0.95$ threshold for a summative Tier node, the Streamlit application automatically generates a JSON-LD Open Badge.
*   This badge contains cryptographic evidence of the mastery (links to the passing GitHub repo, the LLM rubric score, and the BKT probability).
*   These badges can be exported to platforms like LinkedIn or Badgr, providing a decentralized, self-sovereign record of your Applied AI Engineering mastery that does not rely on institutional accreditation.