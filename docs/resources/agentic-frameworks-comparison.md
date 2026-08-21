# Agentic Frameworks Comparison

**Last Verified:** August 2026  
**Purpose:** Reference for choosing and learning agentic frameworks across roadmap phases

---

## Framework Comparison Matrix

| Framework | Repo | Docs | Paradigm | Best For | Learning Curve | Production Ready | HF Course Coverage |
|-----------|------|------|----------|----------|----------------|------------------|-------------------|
| **smolagents** | https://github.com/huggingface/smolagents | https://huggingface.co/docs/smolagents/ | CodeAgent (Python), ToolCallingAgent (JSON), minimal (~1000 lines) | Learning, prototyping, HF ecosystem integration | **Low** | Medium | **Agents Course Unit 2.1** (Primary) |
| **LangGraph** | https://github.com/langchain-ai/langgraph | https://docs.langchain.com/oss/python/langgraph/ | Graph-based orchestration, stateful, durable, cycles | Production agents, complex workflows, human-in-loop | Medium-High | **High** | **Agents Course Unit 2.3** |
| **LlamaIndex** | https://github.com/run-llama/llama_index | https://developers.llamaindex.ai/ | RAG, agents over data, workflows, indexes | Document agents, data-centric apps, agentic RAG | Medium | High | **Agents Course Unit 2.2** |
| **DSPy** | https://github.com/stanfordnlp/dspy | https://dspy.ai/ | Declarative signatures, modules, teleprompters, optimization | RAG pipelines, prompt optimization, agent loops | Medium-High | High | **DL.AI Short Course** |
| **CrewAI** | https://github.com/crewAIInc/crewAI | https://docs.crewai.com/ | Role-based crews, Flows (event-driven), high-level abstraction | Multi-agent collaboration, business processes | Low-Medium | Medium | Referenced in Agents Course |
| **Microsoft Agent Framework** | https://github.com/microsoft/agent-framework | https://learn.microsoft.com/en-us/agent-framework/ | Graph-based workflows, typed, enterprise-ready | New projects, production multi-agent (AutoGen successor) | Medium | High | Migration guide only |
| **AutoGen** | https://github.com/microsoft/autogen | https://microsoft.github.io/autogen/ | Event-driven, multi-agent chat | **⚠️ MAINTENANCE MODE** — migrate to Agent Framework | — | Legacy only | Legacy only |

---

## Recommended Learning Path (Phase 4 Order)

### 1. Start: smolagents (Weeks 1–2)
- **Why:** Simplest mental model (CodeAgent writes Python), HF-native, teaches fundamentals
- **Primary Resource:** HF Agents Course Unit 2.1 (Sergio Paniego)
- **Key Concepts:** CodeAgent vs ToolCallingAgent, multi-agent delegation, Gradio UI
- **Project:** Rebuild Alfred agent + custom tool

### 2. Production Orchestration: LangGraph (Weeks 3–4)
- **Why:** Stateful, durable, human-in-loop, cycles, streaming — production standard
- **Primary Resource:** HF Agents Course Unit 2.3 (Joffrey Thomas) + LangGraph Quickstart
- **Key Concepts:** StateGraph, Functional API, Checkpointers (SqliteSaver/PostgresSaver), Interrupts, Streaming
- **Project:** Customer support agent with approval workflow

### 3. Data-Centric Agents: LlamaIndex (Weeks 5–6)
- **Why:** Best for RAG, document processing, structured data, workflows
- **Primary Resource:** HF Agents Course Unit 2.2 (David Berenstein) + LlamaIndex Starter Tutorial
- **Key Concepts:** Indexes (VectorStore, Summary, KnowledgeGraph), Workflows, Agentic RAG, LlamaParse
- **Project:** Enterprise knowledge agent with hybrid search + reranking

### 4. Optimization: DSPy (Weeks 7–8)
- **Why:** Programmatic optimization (signatures → modules → teleprompters), compiles prompts
- **Primary Resource:** DL.AI "DSPy: Build and Optimize Agentic Apps" (Chen Qian) + DSPy tutorials
- **Key Concepts:** Signatures, Modules (ChainOfThought, ReAct), Teleprompters (MIPROv2, COPRO, BootstrapFewShot), Compilation
- **Project:** Auto-optimize RAG pipeline or agent prompts

### 5. Enterprise/Teams: CrewAI or Microsoft Agent Framework (Optional)
- **CrewAI:** Role-based, Flows for event-driven control, MIT license
- **Microsoft Agent Framework:** Typed, graph-based, enterprise support, AutoGen migration path

---

## Framework Deep-Dives

### smolagents (Learning + Prototyping)

| Aspect | Details |
|--------|---------|
| **Core Abstraction** | `CodeAgent` (writes Python code) / `ToolCallingAgent` (JSON tool calls) |
| **Model Support** | Any HF model, OpenAI, Anthropic, local (Ollama, Transformers) |
| **Tools** | Python functions with type hints → auto-schema |
| **Memory** | `Memory` class (short-term) + custom long-term |
| **Multi-Agent** | `ManagedAgent` for delegation |
| **UI** | Built-in Gradio (`launch_gradio()`), CLI (`smolagent`, `webagent`) |
| **MCP** | Native client (`MCPClient`) + server support |
| **Limitations** | No built-in persistence, no cycles, limited streaming |
| **Best For** | Learning, rapid prototyping, HF Spaces demos, education |

**Key Resources:**
- Guided Tour: https://huggingface.co/docs/smolagents/guided_tour
- API Reference: https://huggingface.co/docs/smolagents/api_reference
- Examples: https://github.com/huggingface/smolagents/tree/main/examples

---

### LangGraph (Production Orchestration)

| Aspect | Details |
|--------|---------|
| **Core Abstraction** | `StateGraph` (nodes + edges + state) / Functional API (`@entry_point`, `@task`) |
| **State** | TypedDict / Pydantic — full type safety |
| **Persistence** | `SqliteSaver`, `PostgresSaver`, `MemorySaver` — checkpointing |
| **Cycles** | Native support (loops, retries, reflection) |
| **Human-in-Loop** | `interrupt()` + `Command(resume=...)` |
| **Streaming** | Token streaming (`.stream()`), progress streaming (`.astream_events()`) |
| **Subgraphs** | Modular composition (parent → child graphs) |
| **MCP** | `langchain-mcp-adapters` + native tool calling |
| **Observability** | LangSmith (free tier), custom callbacks |
| **Best For** | Production systems, complex workflows, audit trails, multi-turn |

**Key Resources:**
- Quickstart: https://docs.langchain.com/oss/python/langgraph/quickstart
- Concepts: https://docs.langchain.com/oss/python/langgraph/concepts
- How-to: https://docs.langchain.com/oss/python/langgraph/how_to
- Persistence: https://docs.langchain.com/oss/python/langgraph/persistence

---

### LlamaIndex (Data-Centric Agents)

| Aspect | Details |
|--------|---------|
| **Core Abstraction** | `Index` (VectorStore, Summary, Tree, KnowledgeGraph) + `QueryEngine` + `Agent` |
| **Workflows** | Event-driven (`@step`), branching, concurrency, error handling, human-in-loop |
| **RAG** | Advanced: hybrid search, reranking, query decomposition, recursive retrieval |
| **LlamaParse** | 10k free credits/mo — PDF parsing (tables, images, charts) |
| **Agents** | `FunctionCallingAgent`, `ReActAgent`, `WorkflowAgent` |
| **MCP** | Native MCP client + server support |
| **Evaluation** | RAGAS integration, custom evaluators |
| **Best For** | Document-heavy apps, knowledge bases, structured data, agentic RAG |

**Key Resources:**
- Starter Tutorial: https://developers.llamaindex.ai/docs/getting_started/starter_tutorial
- Workflows: https://developers.llamaindex.ai/docs/workflows
- Agentic RAG: https://developers.llamaindex.ai/docs/agentic_rag
- LlamaParse: https://developers.llamaindex.ai/docs/parsing

---

### DSPy (Optimization)

| Aspect | Details |
|--------|---------|
| **Core Abstraction** | `Signature` (input/output spec) → `Module` (logic) → `Teleprompter` (optimizer) |
| **Programming Model** | Declarative: define signatures, compose modules, optimize |
| **Teleprompters** | MIPROv2 (instruction + few-shot), COPRO (instruction only), BootstrapFewShot |
| **Optimization Target** | Any metric (accuracy, F1, custom, LLM-as-judge) |
| **Compilation** | Optimized program = frozen weights + prompts (fast inference) |
| **MCP** | `pip install dspy[mcp]` — tool integration |
| **Evaluation** | `dspy.Evaluate` + custom metrics |
| **Best For** | Prompt optimization, RAG pipeline tuning, agent loop optimization |

**Key Resources:**
- Docs: https://dspy.ai/
- Tutorials: https://dspy.ai/tutorials/
- Teleprompters: https://dspy.ai/teleprompters/
- DL.AI Course: "DSPy: Build and Optimize Agentic Apps" (Chen Qian)

---

### CrewAI (Role-Based Multi-Agent)

| Aspect | Details |
|--------|---------|
| **Core Abstraction** | `Agent` (role, goal, backstory) + `Task` + `Crew` (orchestration) |
| **Flows** | Event-driven control (`@listen`, `@router`, `@start`) — separate from Crews |
| **Memory** | Short-term (conversation), Long-term (vector), Entity memory |
| **Tools** | Built-in + custom (LangChain tools compatible) |
| **MCP** | Supported via LangChain adapters |
| **Enterprise** | CrewAI AMP Suite (paid) |
| **Best For** | Business process automation, role-based collaboration, non-technical stakeholders |

**Key Resources:**
- Docs: https://docs.crewai.com/
- Flows: https://docs.crewai.com/concepts/flows
- Memory: https://docs.crewai.com/concepts/memory

---

### AutoGen → Microsoft Agent Framework (Migration)

| Status | Details |
|--------|---------|
| **AutoGen** | **Maintenance mode** — no new features, community-managed, security patches only |
| **Migration** | https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/ |
| **Agent Framework** | Graph-based, typed, enterprise-ready, Azure integration |
| **When to Use** | New projects only; existing AutoGen → migrate |
| **Learning** | Not in HF Agents Course; separate Microsoft Learn path |

---

## Framework Selection Guide

| If Your Project Needs... | Choose |
|--------------------------|--------|
| Simplest start, Python-native agents | **smolagents** |
| Production durability, human approval, cycles | **LangGraph** |
| Document-heavy, RAG, structured data | **LlamaIndex** |
| Prompt/pipeline optimization, compilation | **DSPy** |
| Role-based business processes | **CrewAI** |
| Enterprise Azure, typed, AutoGen migration | **Microsoft Agent Framework** |

**Most Projects Use Multiple:**
- smolagents for prototyping → LangGraph for production
- LlamaIndex for RAG + LangGraph for orchestration
- DSPy to optimize prompts for any framework

---

## Phase 4 Integration (HF Agents Course)

| Week | Framework | Course Unit | Certificate Progress |
|------|-----------|-------------|---------------------|
| 1–2 | smolagents | Unit 2.1 | Agents Fundamentals |
| 3–4 | LangGraph | Unit 2.3 | Agents Completion (part) |
| 5–6 | LlamaIndex | Unit 2.2 | Agents Completion (part) |
| 7–8 | DSPy | DL.AI Short Course | — |
| 9–10 | Integration | Units 3–4 + GAIA | Agents Completion |
| 11–13 | MCP + Context | MCP Course + Context Course | 4 more certificates |

---

## Common Patterns Across Frameworks

| Pattern | smolagents | LangGraph | LlamaIndex | DSPy |
|---------|------------|-----------|------------|------|
| **Tool Use** | `@tool` decorator | `ToolNode` | `FunctionTool` | `dspy.Tool` |
| **Memory** | `Memory` class | Checkpointer | `Memory` module | Custom |
| **Multi-Agent** | `ManagedAgent` | Subgraphs | `AgentWorkflow` | Modules |
| **Streaming** | `stream()` | `.stream()` / `.astream_events()` | `.astream()` | N/A |
| **MCP Client** | `MCPClient` | `langchain-mcp-adapters` | Native | `dspy[mcp]` |
| **Evaluation** | Custom | LangSmith + custom | RAGAS + custom | `dspy.Evaluate` |

---

## Decision: Start with smolagents → LangGraph → LlamaIndex

This mirrors the HF Agents Course structure and builds from simplest to most production-ready. DSPy adds optimization layer on top of any framework.

**Capstone Mapping:**
- Capstone 1: smolagents
- Capstone 2: LangGraph
- Capstone 3: LlamaIndex or DSPy