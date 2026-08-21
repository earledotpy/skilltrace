# Capstone Projects — 3 Deployed Agentic Applications

**Timeline:** Ongoing (starts during Phase 5, continues post-roadmap)  
**Prerequisites:** Phases 0–5 complete  
**Last Verified:** August 2026

---

## Objective

Build and deploy **three distinct agentic applications** demonstrating mastery across frameworks, deployment, and evaluation. Each capstone is a portfolio-grade project for AI Engineer roles.

---

## Capstone Requirements (All Three)

| Requirement | Details |
|-------------|---------|
| **Problem** | Solves a real, non-trivial task (not "hello world") |
| **Framework** | Different primary framework each (smolagents, LangGraph, LlamaIndex/DSPy) |
| **Agentic** | Multi-step reasoning, tool use, memory, self-correction |
| **MCP** | Includes at least one custom MCP server (tools/resources) |
| **Evaluation** | Quantitative (accuracy, latency, cost) + Qualitative (LLM-as-judge, user study) |
| **Guardrails** | Input/output validation, PII detection, failure modes documented |
| **Deployment** | Live on Hugging Face Spaces (ZeroGPU) + Render (API) |
| **Documentation** | README, architecture diagram, API docs, blog post |
| **Code Quality** | Type hints, tests (pytest), CI/CD (GitHub Actions), requirements.lock |

---

## Capstone 1: smolagents-Based (CodeAgent Paradigm)

### Suggested Problems (Choose One)
| Problem | Description | Tools Needed |
|---------|-------------|--------------|
| **Research Analyst** | Deep research on topic → web search → synthesize → cited report | Web search, PDF parse, code execution, file write |
| **Code Migration Assistant** | Analyze legacy codebase → propose modernization → generate diffs | Git, AST parse, LSP, code execution |
| **Data Science Agent** | Load dataset → explore → clean → model → explain → report | Pandas, sklearn, plotting, Jupyter execution |
| **Travel Planner** | Constraints → search flights/hotels → optimize itinerary → book | Web search, API calls, calendar, optimization |

### Technical Spec
- **Framework:** smolagents (CodeAgent primary, ToolCallingAgent for APIs)
- **MCP Server:** Custom tools (e.g., `web_search`, `code_exec`, `file_ops`)
- **Memory:** Conversation history + long-term fact store (SQLite/Chroma)
- **Evaluation:** GAIA-style benchmark on domain tasks + custom metrics
- **Deployment:** HF Space (Gradio) + MCP server on separate HF Space

### Deliverables
```
capstone-smolagents/
├── agent/
│   ├── main.py              # CodeAgent setup
│   ├── tools/               # Custom tools (MCP-compatible)
│   ├── prompts/             # System prompts, few-shots
│   └── memory/              # Short + long term memory
├── mcp-server/
│   ├── server.py            # FastMCP server
│   ├── tools/               # Exposed tools
│   └── Dockerfile
├── eval/
│   ├── benchmark.json       # Test cases
│   ├── metrics.py           # Evaluation functions
│   └── results/
├── deployment/
│   ├── hf-space-gradio/     # Gradio app
│   ├── hf-space-mcp/        # MCP server
│   └── render-api/          # FastAPI fallback
├── tests/
├── .github/workflows/       # CI/CD
├── requirements.txt
├── requirements.lock
├── README.md
├── ARCHITECTURE.md
└── BLOG_POST.md
```

---

## Capstone 2: LangGraph-Based (Stateful Orchestration)

### Suggested Problems (Choose One)
| Problem | Description | Why LangGraph |
|---------|-------------|---------------|
| **Customer Support Agent** | Multi-turn → classify → retrieve → act → escalate → follow-up | Human-in-loop, persistence, state |
| **Code Review Bot** | PR → analyze → comment → suggest fixes → re-review on push | Cycles, checkpointing, streaming |
| **Financial Report Generator** | Query → SQL → analyze → chart → narrative → review → publish | Branching, parallel nodes, durable |
| **Legal Document Assistant** | Upload → chunk → index → query → cite → draft → verify | Subgraphs, human approval, audit trail |

### Technical Spec
- **Framework:** LangGraph (StateGraph, Functional API)
- **Persistence:** SqliteSaver / PostgresSaver (Render free Postgres)
- **Human-in-Loop:** Interrupt + resume for approvals
- **Streaming:** Token-by-token + progress updates
- **MCP Server:** External tools (database, API, file system)
- **Evaluation:** End-to-end success rate + step-level accuracy + latency
- **Deployment:** Render (FastAPI + LangGraph server) + HF Space (Gradio frontend)

### Deliverables
```
capstone-langgraph/
├── graph/
│   ├── state.py             # TypedState definition
│   ├── nodes/               # Node functions
│   ├── edges/               # Routing logic
│   └── graph.py             # Compiled graph
├── persistence/
│   ├── checkpointer.py      # SqliteSaver setup
│   └── migrations/
├── human-in-loop/
│   ├── interrupts.py        # Interrupt definitions
│   └── resume-handler.py
├── mcp-server/
│   └── ...                  # Custom MCP tools
├── api/
│   ├── main.py              # FastAPI + LangGraph server
│   ├── schemas.py           # Pydantic models
│   └── streaming.py         # SSE/WS streaming
├── frontend/
│   └── gradio-app/          # HF Space deployment
├── eval/
│   ├── test-cases.yaml
│   ├── harness.py
│   └── reports/
├── deployment/
│   ├── render.yaml
│   ├── docker-compose.yml
│   └── hf-space/
├── tests/
├── .github/workflows/
├── requirements.txt
├── requirements.lock
├── README.md
├── ARCHITECTURE.md
└── BLOG_POST.md
```

---

## Capstone 3: LlamaIndex or DSPy-Based (Data-Centric / Optimization)

### Option A: LlamaIndex (Data-Centric Agent)

#### Suggested Problems
| Problem | Description |
|---------|-------------|
| **Enterprise Knowledge Agent** | Ingest Confluence/Notion/PDFs → agentic RAG → cite → update docs |
| **Financial Analyst** | SEC filings → extract tables → compute ratios → compare → memo |
| **Technical Docs Assistant** | Codebase + docs → answer "how to" → generate examples → PR docs |

#### Technical Spec
- **Framework:** LlamaIndex (Workflows, Agentic RAG, LlamaParse)
- **Indexing:** Hybrid (dense + sparse), semantic chunking, reranking (Cohere/Jina)
- **Workflow:** Event-driven with branching, error handling, human checkpoints
- **MCP Server:** Document ingestion, query, update tools
- **Evaluation:** RAGAS (faithfulness, relevance, context precision) + custom
- **Deployment:** HF Space (Gradio) + Render (API + Postgres for index metadata)

### Option B: DSPy (Optimization-Focused)

#### Suggested Problems
| Problem | Description |
|---------|-------------|
| **Auto-Prompt Optimizer** | Task → DSPy signatures → MIPRO/COPRO → optimized prompts → deploy |
| **RAG Pipeline Optimizer** | Retrieval + generation → joint optimization → eval → deploy |
| **Agent Workflow Compiler** | Agent logic → DSPy modules → teleprompter → compiled program |

#### Technical Spec
- **Framework:** DSPy (Signatures, Modules, Teleprompters)
- **Optimization:** MIPROv2 / COPRO / BootstrapFewShot
- **MCP:** `dspy[mcp]` for tool integration
- **Evaluation:** DSPy Evaluate + custom metrics + LLM-as-judge
- **Deployment:** Compiled program as FastAPI endpoint + HF Space demo

### Deliverables (Choose A or B)
```
capstone-llamaindex/  OR  capstone-dspy/
├── pipeline/           # Indexing, retrieval, generation, workflow
├── optimization/       # DSPy: teleprompters, compiled programs
├── mcp-server/
├── eval/
│   ├── ragas/          # RAGAS metrics
│   ├── custom/
│   └── reports/
├── deployment/
├── tests/
├── .github/workflows/
├── requirements.txt
├── requirements.lock
├── README.md
├── ARCHITECTURE.md
└── BLOG_POST.md
```

---

## Evaluation Framework (All Capstones)

### Quantitative Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Task Success Rate** | ≥80% | GAIA-style or custom benchmark |
| **Latency (p50)** | <10s | End-to-end per interaction |
| **Latency (p95)** | <30s | End-to-end per interaction |
| **Cost per Task** | <$0.10 | API + compute (track via LangSmith) |
| **Hallucination Rate** | <5% | LLM-as-judge on outputs |
| **Citation Accuracy** | ≥90% | RAGAS context precision / recall |

### Qualitative Assessment
- **User Study:** 5+ users complete 3 tasks; SUS score ≥70
- **Failure Analysis:** Document 10+ failure modes + mitigations
- **Guardrail Effectiveness:** Inject 20 adversarial inputs; measure block rate

---

## Deployment Checklist (Each Capstone)

- [ ] **HF Space (Gradio):** ZeroGPU enabled, 2+ spaces used
- [ ] **MCP Server:** Deployed on HF Space (separate) or Render
- [ ] **FastAPI/Render:** API endpoint with health checks, auto-deploy on push
- [ ] **Monitoring:** LangSmith/Phoenix free tier + custom logs
- [ ] **CI/CD:** GitHub Actions → test → build → deploy (HF Space / Render)
- [ ] **Secrets:** HF_TOKEN, API keys in GitHub Secrets / Render env vars
- [ ] **Documentation:** README + ARCHITECTURE.md + API docs (OpenAPI)

---

## Blog Post Template (Each Capstone)

```markdown
# Building [Capstone Name]: An Agentic [Domain] System

## Problem & Motivation
Why this problem? Who is it for? What makes it agentic?

## Architecture
- Framework choice rationale
- System diagram (Mermaid)
- Key components

## Implementation Highlights
- Novel technique / pattern used
- MCP integration
- Evaluation approach

## Results
- Quantitative metrics (table)
- Qualitative findings
- Failure modes + fixes

## Lessons Learned
- What worked
- What didn't
- What I'd do differently

## Links
- Live Demo: [HF Space URL]
- API: [Render URL]
- Source: [GitHub URL]
- MCP Server: [HF Space URL]
```

---

## Timeline Suggestion

| Week | Activity |
|------|----------|
| 1–2 | Capstone 1: Design + core agent + MCP |
| 3–4 | Capstone 1: Eval + Deploy + Document |
| 5–6 | Capstone 2: Design + graph + persistence |
| 7–8 | Capstone 2: Human-in-loop + Deploy + Document |
| 9–10 | Capstone 3: Design + pipeline/optimization |
| 11–12 | Capstone 3: Eval + Deploy + Document |
| 13 | **Portfolio Polish:** Cross-link, index, blog posts |
| 14 | **Certificate Completion:** HF Context Engineering, etc. |

---

## Post-Roadmap: Continuing Growth

| Direction | Resources |
|-----------|-----------|
| **Open Source** | Contribute to smolagents, LangGraph, LlamaIndex, DSPy (good first issues) |
| **Certifications** | AWS AI Practitioner → AWS ML Engineer Associate |
| **Specialization** | Deep-dive into chosen capstone domain |
| **Community** | HF Discord, LangChain Discord, DSPy Discord, local meetups |
| **Job Search** | Portfolio = 3 deployed agents + 6 HF certs + blog posts + GitHub history |

---

## Final Portfolio Structure (GitHub)

```
ai-engineering-portfolio/
├── phase-0-prerequisites/
├── phase-1-math-foundations/
├── phase-2-classical-ml/
├── phase-3-deep-learning/
├── phase-4-agentic-ai/
├── phase-5-specializations/
├── capstone-smolagents/
├── capstone-langgraph/
├── capstone-llamaindex/  (or capstone-dspy/)
├── certificates/
│   ├── hf-agents-*.png
│   ├── hf-mcp-*.png
│   ├── hf-context-*.png
│   ├── cs50p.png
│   └── kaggle-*.png
├── blog-posts/           # Mirror of BLOG_POST.md files
└── README.md             # Master index with links to all
```

---

## Success Criteria (Roadmap Complete)

- [ ] All 6 phase checkpoints passed
- [ ] 3 capstones deployed and documented
- [ ] 6+ Hugging Face certificates earned
- [ ] CS50P + 6+ Kaggle certificates earned
- [ ] GitHub portfolio with 20+ repos, green contribution graph
- [ ] 10+ technical blog posts published
- [ ] AWS AI Practitioner certified (optional, $100)
- [ ] Ready for AI Engineer applications