# Phase 4: Agentic AI Core ⭐ Emphasis Phase

**Estimated Hours:** 80  
**Weeks at 6h:** 13 | **Weeks at 8h:** 10  
**Prerequisites:** Phase 3 (Transformers, HF LLM Course, fine-tuning, RAG basics)  
**Last Verified:** August 2026

---

## Learning Objectives

By the end of this phase, you will be able to:
- Build agents using **smolagents** (CodeAgent, ToolCallingAgent, multi-agent)
- Orchestrate production workflows with **LangGraph** (stateful graphs, persistence, human-in-loop)
- Build data-centric agents with **LlamaIndex** (indexes, workflows, agentic RAG)
- Implement **Model Context Protocol (MCP)** servers and clients
- Apply **Context Engineering**: Skills, MCP, Plugins, Subagents, Hooks
- Evaluate agents systematically (GAIA benchmark, custom metrics, guardrails)
- Deploy agentic systems to Hugging Face Spaces with MCP servers
- Earn **6 free certificates** from Hugging Face (Agents 2, MCP 2, Context 2)

---

## Resource Table

### Certified Core (Required, ~70 Hours, 6 Certificates)

| Resource | URL | Format | Est. Hours | Certificates | Verified |
|----------|-----|--------|------------|--------------|----------|
| **Hugging Face Agents Course** | https://huggingface.co/learn/agents-course | 4 units + bonuses, Spaces labs | 25–30 | **Fundamentals + Completion (2)** | 2026-08-08 |
| **Hugging Face MCP Course** | https://huggingface.co/learn/mcp-course | 4 units, Anthropic partnership | 20–25 | **Fundamentals + Completion (2)** | 2026-08-08 |
| **Hugging Face Context Course** | https://huggingface.co/learn/context-course | 6 units (skills, MCP, plugins, subagents, hooks) | 25–30 | **Fundamentals + Engineering (2)** | 2026-08-08 |

### Framework Documentation (Reference)

| Framework | Docs URL | Role in Curriculum |
|-----------|----------|-------------------|
| **smolagents** | https://huggingface.co/docs/smolagents/ | Learning/prototyping (CodeAgent writes Python) |
| **LangGraph** | https://docs.langchain.com/oss/python/langgraph/ | Production orchestration (stateful, durable) |
| **LlamaIndex** | https://developers.llamaindex.ai/ | Data-centric agents, RAG, workflows |
| **DSPy** | https://dspy.ai/ | Optimization (signatures, teleprompters) |
| **CrewAI** | https://docs.crewai.com/ | Role-based multi-agent (Flows for control) |
| **Microsoft Agent Framework** | https://learn.microsoft.com/en-us/agent-framework/ | AutoGen successor (enterprise-ready) |

### Supplementary Courses (Free During Beta)

| Course | Instructor | Duration | Focus |
|--------|------------|----------|-------|
| **Building Agentic AI Systems** | Andrew Ng | ~2h | Multi-step workflows |
| **Agent Skills with Anthropic** | Elie Schoppik | 2h19m | Tool use, function calling |
| **Evaluating AI Agents** | John Gilhuly, Aman Khan | 2h36m | Systematic assessment |
| **Building and Evaluating Data Agents** | Anupam Datta, Josh Reini | 1h59m | Data-focused agents |
| **Event-Driven Agentic Document Workflows** | Laurie Voss | 1h19m | LlamaIndex workflows |
| **DSPy: Build and Optimize Agentic Apps** | Chen Qian | 59m | DSPy for agents |

---

## Recommended Learning Sequence

### 1. Hugging Face Agents Course (25h) → **2 Certificates**
```
Unit 0: Onboarding (HF account, Discord, tools)
Unit 1: Agent Fundamentals → Fundamentals Certificate
  - Tools, Thoughts, Actions, Observations
  - LLM messages, chat templates, special tokens
  - Build first agent with smolagents (Alfred)
  - Deploy to HF Spaces
Unit 2: Frameworks
  2.1 smolagents (CodeAgent, ToolCallingAgent, multi-agent)
  2.2 LlamaIndex (indexes, workflows, agents over data)
  2.3 LangGraph (stateful graphs, persistence, human-loop)
Unit 3: Use Cases (community PRs welcome)
Unit 4: Final Challenge (GAIA benchmark) → Completion Certificate
Bonus: Fine-tuning for function calling, observability, games
```

### 2. Hugging Face MCP Course (20h) → **2 Certificates**
```
Unit 1: MCP Fundamentals → Fundamentals Certificate
  - Architecture: Hosts, Clients, Servers
  - Capabilities: Tools, Resources, Prompts
  - JSON-RPC, stdio + Streamable HTTP transports
Unit 2: End-to-end MCP app (build + test locally)
Unit 3: Deployed MCP app (HF ecosystem + partners) → Completion Certificate
Unit 4: Bonus units (partner libraries)
```

### 3. Hugging Face Context Course (25h) → **2 Certificates**
```
Unit 1: Skills (portable knowledge)
Unit 2: MCP (dynamic tools/data)
Unit 3: Plugins (bundling for distribution)
Unit 4: Subagents (multi-agent workflows)
Unit 5: Hooks (observability, guardrails)
Unit 6: Nano Harness (build minimal agent from scratch)
→ Context Fundamentals Cert (Units 1-2)
→ Context Engineering Cert (Units 1-5 + capstone)
```

### 4. Framework Deep-Dives (Parallel, 10h)
- **LangGraph:** Quickstart + persistence + human-in-loop tutorial
- **LlamaIndex:** Starter tutorial (Ollama + HF embeddings) + Workflows
- **DSPy:** DL.AI short course + signatures → modules → optimizers
- **CrewAI:** Crews + Flows (event-driven) tutorials

---

## Weekly Breakdown

### At 6 Hours/Week (13 Weeks)

| Week | Focus | Resources | Deliverable |
|------|-------|-----------|-------------|
| 1 | HF Agents Course Unit 0–1 | Onboarding + Fundamentals | **HF Agents Fundamentals Cert** |
| 2 | HF Agents Course Unit 2.1 | smolagents (CodeAgent, multi-agent) | smolagents project on HF Spaces |
| 3 | HF Agents Course Unit 2.2 | LlamaIndex (indexes, workflows) | LlamaIndex RAG agent |
| 4 | HF Agents Course Unit 2.3 | LangGraph (stateful, human-loop) | LangGraph workflow with persistence |
| 5 | HF Agents Course Unit 3–4 | Use cases + GAIA challenge | **HF Agents Completion Cert** |
| 6 | HF MCP Course Unit 1 | MCP Fundamentals | **HF MCP Fundamentals Cert** |
| 7 | HF MCP Course Unit 2 | Local MCP app build + test | Local MCP server + client |
| 8 | HF MCP Course Unit 3 | Deployed MCP app | **HF MCP Completion Cert** |
| 9 | HF Context Course Unit 1–2 | Skills + MCP | **HF Context Fundamentals Cert** |
| 10 | HF Context Course Unit 3–4 | Plugins + Subagents | Plugin + multi-agent workflow |
| 11 | HF Context Course Unit 5–6 | Hooks + Nano Harness | **HF Context Engineering Cert** |
| 12 | Framework Deep-Dives | LangGraph + LlamaIndex + DSPy | 3 framework comparison project |
| 13 | **Checkpoint + Portfolio** | GAIA submission, consolidated demo | `agentic-ai-core` repo + 6 certs |

### At 8 Hours/Week (10 Weeks)

| Week | Focus | Resources | Deliverable |
|------|-------|-----------|-------------|
| 1 | HF Agents Course Complete (Units 0–4) | All units + GAIA | **2 Agents Certs** + smolagents/LlamaIndex/LangGraph projects |
| 2 | HF MCP Course Complete (Units 1–3) | Fundamentals → Deployed | **2 MCP Certs** + deployed MCP server |
| 3 | HF Context Course Complete (Units 1–6) | Skills → Nano Harness | **2 Context Certs** + capstone agent |
| 4 | Framework Deep-Dives | LangGraph, LlamaIndex, DSPy, CrewAI | Comparison matrix + 3 demos |
| 5 | DL.AI Short Courses (Pick 4) | Agent evaluation, DSPy, Data agents, etc. | Notes + applied snippets |
| 6 | **Integration Project** | Combine: smolagents + MCP + Context | Unified agentic system |
| 7 | **GAIA Benchmark Attempt** | Official GAIA evaluation | Score tracking + analysis |
| 8 | **Production Hardening** | Observability, guardrails, eval | HF Spaces deployment with monitoring |
| 9 | **Consolidation** | Re-build key components from memory | Clean implementations |
| 10 | **Checkpoint + Portfolio** | Final review, GitHub push | `agentic-ai-core` repo + 6 certs |

---

## Checkpoint Exercises (Must Pass Before Phase 5)

### smolagents (CodeAgent Paradigm)
1. **Build Alfred:** Recreate the Unit 1 Alfred agent (search + code execution) from memory
2. **Multi-Agent:** Create a CodeAgent that delegates to a ToolCallingAgent for web search
3. **Custom Tool:** Write a Python tool for a domain API (weather, stocks, custom); register with agent

### LangGraph (Production Orchestration)
1. **Stateful Graph:** Build a graph with cycles (retry logic) + checkpointing (SqliteSaver)
2. **Human-in-Loop:** Implement interrupt + resume for approval step
3. **Streaming:** Stream token-by-token output from LLM node to frontend

### LlamaIndex (Data-Centric Agents)
1. **Agentic RAG:** Ingest 20 PDFs → build index → agent that queries + synthesizes + cites
2. **Workflow:** Create a LlamaIndex Workflow with branching + error handling
3. **LlamaParse:** Use free 10k credits/mo to parse complex PDFs (tables, images)

### MCP (Model Context Protocol)
1. **MCP Server:** Build stdio server exposing 3 tools (e.g., file ops, web search, calc)
2. **MCP Client:** Connect smolagents/LangGraph agent to your MCP server
3. **Deployed MCP:** Host MCP server on HF Spaces (ZeroGPU); connect remote agent

### Context Engineering
1. **Skill:** Create a portable Skill (prompt + tools + eval) for a domain task
2. **Plugin:** Bundle Skills + MCP server as distributable Plugin
3. **Subagent:** Orchestrate 3+ subagents with different specializations
4. **Hooks:** Add observability hook (logging) + guardrail hook (PII detection)

### Evaluation & Guardrails
1. **GAIA Attempt:** Run official GAIA Level 1 questions; document success/failure patterns
2. **Custom Eval:** Build LLM-as-judge for your agent's output quality
3. **Guardrails:** Implement input/output guardrails (e.g., using Guardrails AI or custom)

---

## GitHub Portfolio Task

Repository: `agentic-ai-core` with structure:
```
agentic-ai-core/
├── hf-agents-course/
│   ├── unit1-fundamentals/
│   │   ├── alfred-agent/
│   │   └── custom-tools/
│   ├── unit2-frameworks/
│   │   ├── smolagents-project/
│   │   ├── llamaindex-agent/
│   │   └── langgraph-workflow/
│   ├── unit3-use-cases/
│   └── unit4-gaia/
│       ├── attempts/
│       └── analysis.md
├── hf-mcp-course/
│   ├── unit1-fundamentals/
│   ├── unit2-local-app/
│   │   ├── mcp-server/
│   │   └── mcp-client/
│   └── unit3-deployed/
│       ├── mcp-server-hf-spaces/
│       └── remote-agent/
├── hf-context-course/
│   ├── unit1-skills/
│   ├── unit2-mcp/
│   ├── unit3-plugins/
│   ├── unit4-subagents/
│   ├── unit5-hooks/
│   └── unit6-nano-harness/
├── framework-comparison/
│   ├── langgraph-demo/
│   ├── llamaindex-demo/
│   ├── dspy-demo/
│   └── crewai-demo/
├── certificates/
│   ├── hf-agents-fundamentals.png
│   ├── hf-agents-completion.png
│   ├── hf-mcp-fundamentals.png
│   ├── hf-mcp-completion.png
│   ├── hf-context-fundamentals.png
│   └── hf-context-engineering.png
└── README.md
```

**Deployed on HF Spaces (Required):**
- smolagents demo (Unit 1 Alfred + custom)
- LangGraph workflow with human-in-loop
- LlamaIndex agentic RAG
- MCP server (2+ tools)
- Context Engineering capstone agent

---

## Critical Notes (August 2026)

| Item | Status |
|------|--------|
| **AutoGen** | ⚠️ **Maintenance mode** — no new features. Migrate to **Microsoft Agent Framework** |
| **smolagents** | Teaching framework for HF Agents Course; CodeAgent writes Python, not JSON |
| **LangGraph** | Low-level orchestration; pair with LangChain for higher-level abstractions |
| **MCP** | Supported across all major frameworks (smolagents, LangGraph, DSPy, LlamaIndex) |
| **HF Certificates** | Free, verifiable, stackable — earn all 6 in this phase |

---

## Common Pitfalls

| Pitfall | Avoidance |
|---------|-----------|
| Skipping certificate quizzes | **Quizzes test understanding** — if you fail, re-study that unit |
| Only using one framework | **Learn all three** (smolagents, LangGraph, LlamaIndex) — each has different strengths |
| Ignoring MCP | **MCP is the standard** — 97M+ monthly SDK downloads (Feb 2026); deploy an MCP server |
| No evaluation | **GAIA + custom eval required** — agents without eval are toys |
| Not deploying | **HF Spaces ZeroGPU is free** — every project needs a live demo link |

---

## Optional Deep-Dives (If Time Permits)

| Topic | Resource | Hours |
|-------|----------|-------|
| Microsoft Agent Framework | Migration guide + quickstart | 10 |
| DSPy Teleprompters (MIPRO, COPRO) | DSPy docs + DL.AI course | 10 |
| Agent Observability (LangSmith, Arize, Phoenix) | Free tiers available | 10 |
| Multi-Agent Safety (CAISI, Red Teaming) | AI Safety Camp + BlueDot | 20 |

---

## Next Phase Preview

**Phase 5: Specializations Survey** — All three at ~20h each:
1. **LLMOps & Deployment** — MLflow, model monitoring, A/B testing, cloud deployment
2. **Multimodal AI** — Vision-language, CLIP, Stable Diffusion (fast.ai Part 2), HF Computer Vision
3. **AI Product Engineering** — FastAPI + Streamlit/Gradio, user-facing apps, eval & guardrails

**Capstone:** Build 3 deployed agentic applications (different frameworks) → publish on HF Spaces.

**Prepare:** Choose first specialization based on interest. Ensure HF Spaces + Render accounts work.