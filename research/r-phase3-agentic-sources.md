# R-Phase3Agentic — Phase 3 LLM / Agents / MCP Seed-Graph Source Survey (2026)

**Ticket:** https://github.com/earledotpy/skilltrace/issues/98
**Map:** https://github.com/earledotpy/skilltrace/issues/95
**Author:** Research subagent on `research/r-phase3-agentic-sources`
**Date:** 2026-08-27 (initial write), 2026-08-27 (primary-source re-verification)
**Scope:** Verify the 2026 state of the source materials the v1.3 roadmap slot
for "Phase 3 LLM / agents / MCP seed graph" (`docs/POST_V1_BACKLOG.md:37`),
surfacing drift from the August 2026 snapshot captured in
`docs/resources/agentic-frameworks-comparison.md`. Identify any new entrants
that should be on the list, and any that should be dropped or replaced.

This artifact is the evidence pack for ticket #98. The G-Slot (issue #100)
owns the actual v1.3 curriculum-shape call; this document only reports the
2026 state of the candidate sources.

**Primary-source verification (re-confirmed 2026-08-27 against live release
pages):** MCP spec `2026-07-28` stable
(<https://github.com/modelcontextprotocol/modelcontextprotocol/releases>),
DSPy `3.3.1` 2026-08-21 with `CodeAct`/`ProgramOfThought` deprecation and
`dspy.RLM` replacement, `dspy[deno]` hardening, GEPA 0.1.4, MCP SDK v1+v2
compat (<https://github.com/stanfordnlp/dspy/releases>), and the AutoGen
README "Maintenance Mode" banner directing new users to Microsoft Agent
Framework (<https://github.com/microsoft/autogen>) — all verified. No
material drift in the conclusions; the prior session's claims hold.

---

## TL;DR

| Source | Status (2026-08) | Verdict for v1.3 seed graph |
| --- | --- | --- |
| HF Agents Course | Active, free, evolving (mentions smolagents, LlamaIndex, LangGraph) | **Keep** as canonical entry point |
| DSPy | Very active (3.3.1, 2026-08-21), 37.6k★ | **Keep**, update to current scope (ReActV2, RLM, GEPA) |
| LangGraph | Very active (1.2.11, 2026-08-11), 40.6k★ | **Keep** |
| smolagents | Maintained but slower cadence (v1.26.0, 2026-05-29), 29k★ | **Keep** but flag for a verification pass at RC entry |
| LlamaIndex | Very active (0.14.24, 2026-08-19), 51.9k★ | **Keep** |
| MCP | **Standardized** — stable spec `2026-07-28` released; broad ecosystem support (VS Code, Cursor, ChatGPT, Claude, MAF, DSPy, smolagents, LlamaIndex, LangGraph, OpenAI Agents SDK) | **Keep** as a first-class node, not just a capstone concern |
| AutoGen | **Confirmed maintenance mode**; MS Agent Framework is the production successor (1.0, 13.2k★) | **Replace** AutoGen references with **Microsoft Agent Framework** in v1.3 |
| OpenAI Agents SDK | **New, very active** — production-ready successor to Swarm, sandbox + realtime + native MCP, ~7k★+, MIT | **Add** as an optional / enterprise-side alternate |
| PydanticAI | Very active (v2.35.1, 2026-08-26), 19.5k★, Pydantic-typed, MCP-native | **Add** as a recommended alternate for Pydantic-typed projects |
| Letta | Alive but slower (0.16.8, 2026-05-14), 24.5k★, focuses on stateful long-memory agents | **Mention** as a stateful-memory alternate; not a primary node |
| CrewAI | Very active (1.15.17, 2026-08-20), 57.7k★, role-based crews + Flows | **Keep** as the comparison doc already lists it |

---

## 1. Hugging Face Agents Course

- **Repo / docs:** https://github.com/huggingface/agents-course and
  https://huggingface.co/learn/agents-course/en/unit0/introduction
- **Status (2026-08):** **Active, free, evolving.** The course still covers
  smolagents, LlamaIndex, and LangGraph as Unit 2 frameworks. Free
  certification (Fundamentals + Completion). Maintained by Ben Burtenshaw and
  Sergio Paniego; the "this is a living project, evolving with your feedback"
  language is still on the introduction page.
- **Free / verifiable:** Yes — free, self-audit or certification, no paywall.
- **Drift vs. comparison doc:** None. The comparison doc already names this
  as the canonical entry point (Unit 2.1/2.2/2.3 mapping). No new HF agentic
  course has displaced it; HF Context Engineering and HF MCP courses are
  referenced as additional certs in `docs/roadmap/capstone-projects.md`.
- **2026 alternates:** None at the "beginner-to-expert, framework-spanning
  course with certification" tier. DL.AI short courses (DSPy, Building Agentic
  Apps) are narrower; Anthropic / OpenAI courses do not cover the same breadth.
- **Phase 3 shape implication:** Should remain the **onboarding spine** of
  the v1.3 seed graph. No replacement candidate.

## 2. DSPy (Stanford NLP)

- **Repo:** https://github.com/stanfordnlp/dspy (37.6k★)
- **Releases page:** https://github.com/stanfordnlp/dspy/releases
- **Status (2026-08):** **Very active.** v3.3.1 released 2026-08-21 by
  `@isaacbmiller`. Past 90 days saw 3.3.0 (2026-08-03), 3.3.0b1 (2026-05-28),
  and 3.2.1.
- **Free / verifiable:** Yes — Apache-2.0 (per repo).
- **Substantive drift since the comparison doc was written:**
  - **RLM replaces CodeAct / ProgramOfThought.** 3.3.1 emits a
    `DeprecationWarning` for `dspy.CodeAct` and `dspy.ProgramOfThought` and
    schedules them for removal in 3.5; the recommended replacement is
    `dspy.RLM`. v1.3 should not anchor on CodeAct.
  - **GEPA 0.1.4 is the active optimizer family** (with multi-proposal
    sampling, objective-aware frontiers, parallel candidate evaluation).
    MIPROv2 / COPRO / BootstrapFewShot still ship, but the forward-looking
    teleprompter story is GEPA.
  - **`dspy.Flex`** (3.3.0) optimises program **structure**, not just
    prompts — search over decomposition via GEPA. Worth at least one node
    in v1.3 ("DSPy optimisation frontier").
  - **Typed, provider-neutral LM boundary** (`dspy.LMRequest` / `LMResponse`)
    shipping in 3.3.0 with a public migration plan. LiteLLM is becoming
    optional at the 3.5+ horizon.
  - **MCP SDK v1 + v2 compat** (3.3.1) and structured MCP results via
    `dspy.Tool.from_mcp_tool(client, mcp_tool, result_mode="structured")`.
    Confirms DSPy as a first-class MCP consumer.
  - **Interpreter hardening** (Deno sandbox isolation, request-ID
    unpredictability, recursion-rejection) is now part of the base install
    with `dspy[deno]`. `LocalPythonExecutor`-style unsandboxed code is no
    longer the default posture.
- **2026 alternates:** None that match the "declarative signatures +
  compiled programs + automatic prompt optimisation" niche. Some overlap
  with PydanticAI on type-safe tool use, but DSPy is unique on optimisation.
- **Phase 3 shape implication:** Should keep DSPy as a node but **update the
  scope statement** to drop CodeAct/ProgramOfThought, add RLM + GEPA, and
  call out the typed LM boundary. Without the update, v1.3 learners will
  hit deprecation warnings on day one.

## 3. LangGraph

- **Repo:** https://github.com/langchain-ai/langgraph (40.6k★)
- **Releases:** https://github.com/langchain-ai/langgraph/releases
- **Status (2026-08):** **Very active.** `langgraph==1.2.11` released
  2026-08-11, `langgraph-sdk==0.4.3` 2026-08-19, `langgraph-cli==0.4.31`
  2026-07-10. Active maintenance across the SDK, CLI, and checkpoint
  packages (sqlite / postgres).
- **Free / verifiable:** Yes — MIT (per LangChain OSS posture).
- **Substantive drift:** The 1.2.x line is now a major-version release
  (post the older 0.x). New surface area in 2026:
  - `trace_policy` on `add_node` (added, reverted, re-added as tags-only).
  - `v3 stream_events` return type with native projections.
  - `omit_expired` opt-in on checkpoint reads.
  - delta-channel seed-walking bugfixes for checkpoint history.
  - The LangGraph SDK split (`langgraph-sdk`, `langgraph-checkpoint-*`) is
    stable; CLI allows `langgraph-api` versions up to 1.0.0.
- **2026 alternates:** Microsoft Agent Framework's workflow graph
  (`agent-framework` Python/.NET) is the closest semantic alternate for
  *typed graph orchestration with checkpointing*; CrewAI Flows for
  *event-driven* control; pure Python `asyncio` graphs for ad-hoc work.
  None displace LangGraph's position as the de facto stateful graph
  orchestration framework in the open-source Python agent ecosystem.
- **Phase 3 shape implication:** **Keep as-is.** The Phase 3 / Phase 4
  ordering (smolagents → LangGraph) and the LangGraph unit (Unit 2.3 of the
  HF Agents Course) are still correct. Verify the v1.3 seed graph entry
  pinpoints `langgraph>=1.2` rather than the older `0.x`.

## 4. smolagents (Hugging Face)

- **Repo:** https://github.com/huggingface/smolagents (29k★)
- **Status (2026-08):** **Maintained, but cadence is slowing.** v1.26.0
  released 2026-05-29 by `@albertvillanova`. v1.25.0 was 2026-05-14.
  The v1.23.0 (2025-11-17) → v1.24.0 (2026-01-16) → v1.25.0 (2026-05-14)
  → v1.26.0 (2026-05-29) pattern shows ~3-month gaps in 2026, vs. monthly
  cadence in 2024–2025. The project is still releasing (29k★, multiple
  PRs per month) but no longer the rapid-iteration pace of late 2024.
- **Free / verifiable:** Yes — Apache-2.0.
- **Substantive drift:** v1.25.0 added MLflow integration, removed the
  remote `WasmExecutor` in 1.26.0, hardened Docker/Modal/Wasm executors
  (loopback-only endpoints, token auth, no `allow_origin`, isolation of
  Deno cache per instance). v1.22.0 added MCP structured output and
  output schema support. v1.23.0 added Blaxel and Modal remote execution
  backends, GPT-5.1 default, and `anyOf` MCP-tool parsing.
- **2026 alternates at the "Python-native, minimal-magic agent" tier:**
  **OpenAI Agents SDK** (new), **PydanticAI** (newer, typed), and
  **CodeAct**-style patterns are now competing for the same learners.
  smolagents is still the **simplest, most HF-ecosystem-native** option
  and remains the HF Agents Course Unit 2.1 entry point.
- **Phase 3 shape implication:** **Keep**, but flag for a verification
  pass at v1.3 RC entry: a 3-month release gap is a yellow flag, not a red
  one. If smolagents shows no new release by the time v1.3 RC begins, the
  G-Slot call should consider whether **OpenAI Agents SDK** is a better
  default-first-agent-framework (more on that below). Until then, smolagents
  remains the Phase 3 first-framework by virtue of HF-course alignment.

## 5. LlamaIndex

- **Repo:** https://github.com/run-llama/llama_index (51.9k★)
- **Status (2026-08):** **Very active.** `llama-index-core==0.14.24` released
  2026-08-19 (yes, two days before this report). 0.14.23 was 2026-06-24,
  0.14.22 was 2026-05-14, 0.14.21 was 2026-04-21 — consistent monthly cadence.
- **Free / verifiable:** Yes — MIT.
- **Substantive drift:** Major 2026 themes in release notes:
  - **Multimodal synthesis** and **multimodal query engines** (0.14.22–0.14.23).
  - **AG-UI protocol integration** (0.14.24) — multi-modal user input
    (images, audio, video, documents) supported over AG-UI 0.4.0.
  - **MCP 2.x migration** in `llama-index-tools-mcp` (0.5.0) — confirms
    LlamaIndex tracks the MCP spec.
  - **Claude Sonnet 5 / Opus 5 / Gemini 3.7 Flash** provider support
    landed across 0.14.22–0.14.24.
  - Long-tail of reader / store / callback packages — LlamaIndex continues
    to invest in breadth, not just core.
- **2026 alternates:** None at the "data-centric agent with workflows +
  index abstractions" tier. LlamaIndex vs. LangGraph is the
  RAG-pipeline-first vs. orchestration-first divide; both remain canonical.
- **Phase 3 shape implication:** **Keep as-is.** The Phase 4
  weeks-5-and-6 placement is still correct. Confirm the v1.3 entry pins
  to the `0.14.x` line and notes the multimodal synthesis shift as a
  Phase 5 specialisation hook, not a Phase 3 requirement.

## 6. MCP — Model Context Protocol

- **Spec site:** https://modelcontextprotocol.io
- **Architecture doc:** https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture
- **Spec repo:** https://github.com/modelcontextprotocol/modelcontextprotocol
- **Status (2026-08):** **Standardised.** The current stable spec revision
  is **`2026-07-28`**, released 2026-07-28 as the "stable release" of that
  revision. Prior stable revisions: `2025-11-25`, `2025-06-18`,
  `2025-03-26`, `2024-11-05`.
- **Free / verifiable:** Yes — open protocol, MIT-licensed SDKs.
- **Substantive drift since the comparison doc:**
  - **Spec has stabilised through 5 revisions.** MCP is no longer "draft";
    it is a versioned, version-negotiated, cacheable protocol. Every
    request carries `io.modelcontextprotocol/protocolVersion` and
    capabilities in `_meta`; servers return `supportedVersions` in
    `server/discover`.
  - **Two transports:** `stdio` (local) and `streamable HTTP` (remote,
    OAuth-recommended). Remote MCP is now production-shaped.
  - **Primitives are stable:** server-side `tools` / `resources` / `prompts`;
    client-side `elicitation`. **`sampling` and `logging` were deprecated
    in `2026-07-28`** — servers should integrate directly with LLM provider
    APIs and log to `stderr` / OpenTelemetry respectively.
  - **Opt-in change-notification stream** via `subscriptions/listen`
    (replaces older polling). Real-time capability updates without
    reconnect.
  - **Ecosystem coverage is wide and primary-source confirmed:**
    - VS Code — MCP host (architecture doc).
    - Cursor — MCP host (architecture doc).
    - Claude / Claude Code / Claude Desktop — MCP hosts.
    - ChatGPT — MCP host (OpenAI Connectors).
    - Microsoft Agent Framework — MCP and A2A interoperability.
    - DSPy — MCP SDK v1 + v2 client, structured results (3.3.1).
    - smolagents — `MCPClient`, structured output, `anyOf` parsing.
    - LlamaIndex — `llama-index-tools-mcp` migrated to MCP 2.x in 0.14.24.
    - LangGraph — `langchain-mcp-adapters` plus native tool calling.
    - OpenAI Agents SDK — built-in MCP server tool calling.
    - PydanticAI — MCP support.
- **2026 alternates:** None. There is no serious competing "tool-use
  protocol" with this level of ecosystem buy-in.
- **Phase 3 shape implication:** **Promote MCP from "capstone concern" to a
  first-class Phase 3 node.** The comparison doc treats MCP as something
  you do at capstones; in 2026 it is the standard way agents talk to
  tools, and every Phase 3 framework now has a client for it. Without
  early MCP exposure, Phase 3 learners will misunderstand the modern
  tool-use story. The `capstone-projects.md` "MCP server" requirement
  remains correct; v1.3 should add an MCP node earlier in the spine.

## 7. AutoGen — confirmed maintenance mode; Microsoft Agent Framework is the successor

- **AutoGen repo:** https://github.com/microsoft/autogen (60.7k★)
- **AutoGen README banner (verified 2026-08-27):** "AutoGen is now in
  maintenance mode. It will not receive new features or enhancements and is
  community managed going forward. New users should start with Microsoft
  Agent Framework."
- **Migration guide:** https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/
- **MAF repo:** https://github.com/microsoft/agent-framework (13.2k★)
- **MAF status:** Microsoft Agent Framework is now at a **1.0 production
  release** with a commitment to long-term support. Python, .NET, and Go
  SDKs. Multi-provider model support, graph-based workflows (sequential,
  concurrent, handoff, group), checkpointing, streaming, human-in-loop,
  declarative agents, OpenTelemetry observability, MCP and A2A
  interop, Foundry hosted agents. Listed explicitly as the **enterprise
  successor** to both AutoGen and (via a separate migration guide)
  Semantic Kernel.
- **2026 alternates:** None at the "Microsoft-endorsed, multi-language,
  production-ready agent framework" tier.
- **Phase 3 shape implication:** **Drop AutoGen from the v1.3 seed graph.**
  The comparison doc's "MAINTENANCE MODE — migrate to Agent Framework"
  note is correct and confirmed. **Replace** with Microsoft Agent Framework
  as the enterprise / typed-graph option. If the v1.3 budget for
  enterprise-side frameworks is tight, mention MAF in a single
  comparison-style node alongside LangGraph rather than a full Phase 3
  track — the free-first doctrine still favours LangGraph for the
  primary spine, with MAF as the "if your team is on .NET / Azure /
  Foundry" alternate.

## 8. OpenAI Agents SDK — new entrant, worth adding

- **Repo / docs:** https://github.com/openai/openai-agents-python
- **Docs site:** https://openai.github.io/openai-agents-python/
- **Status (2026-08):** **Active.** "Production-ready upgrade of our previous
  experimentation for agents, Swarm" per the docs. Features include
  agents, handoffs, guardrails, function tools with auto-schema, **MCP
  server tool calling**, sessions (SQLAlchemy, Redis, MongoDB,
  encrypted), human-in-the-loop, tracing, **sandbox agents** (Docker,
  Unix local, manifest-defined files), **realtime agents** (gpt-realtime-2.1
  with voice interruption), voice pipelines.
- **Free / verifiable:** Yes — MIT, `pip install openai-agents`. Note
  "Works great out of the box, but you can customize exactly what
  happens" — the design philosophy is intentionally minimal.
- **2026 alternates:** Competes most directly with smolagents (simple
  agent), PydanticAI (typed), and LangGraph (orchestration). Distinctive
  surface area is the **first-class sandbox agents** and **realtime
  voice agents** — both currently unique at this quality bar.
- **Phase 3 shape implication:** **Add as a recommended alternate.**
  Not necessarily a primary Phase 3 node (smolagents still wins on
  HF-ecosystem alignment and free-tier breadth), but a v1.3 learner
  choosing the OpenAI ecosystem should land on the Agents SDK rather
  than the older Swarm cookbook. Mention in the comparison doc and in
  any "if your team standardised on OpenAI" branch.

## 9. PydanticAI — new entrant, worth adding

- **Repo:** https://github.com/pydantic/pydantic-ai (19.5k★)
- **Status (2026-08):** **Very active.** v2.35.1 released 2026-08-26,
  v2.35.0 2026-08-25, v2.34.0 2026-08-24 — daily-to-weekly cadence over
  August 2026. Plus v2.30.0 (2026-08-13) shipped a **security fix** for
  the local dev web chat UI (`Agent.to_web()` / `clai web`) that failed
  to validate the `Host` header, allowing DNS rebinding to reach the
  local agent. GHSA-q2xc-rrxj-58x9 fixed in 2.30.0 via `allowed_hosts`.
- **Free / verifiable:** Yes — MIT.
- **Substantive drift:** PydanticAI is now a **mature, typed, Pydantic-native
  agent framework** with first-class MCP support, model-agnostic via
  the "Any-LLM" / LiteLLM providers, Temporal and DBOS durability
  integrations, and an explicit "LangChain migration skill." In 2026 it
  is the canonical "Pydantic-typed, model-agnostic" alternative to
  OpenAI Agents SDK (which is OpenAI-typed).
- **2026 alternates:** Overlaps with OpenAI Agents SDK on type safety,
  with LangGraph on orchestration (less so), with smolagents on
  Python-native agents.
- **Phase 3 shape implication:** **Add as a recommended alternate** for
  learners who are already deep in the Pydantic ecosystem (FastAPI,
  Pydantic models, Pydantic Settings). Not a primary Phase 3 node — the
  HF Agents Course does not include it — but worth a comparison-doc entry
  and a "if Pydantic is your default" branch.

## 10. Letta — alive, narrower scope

- **Repo:** https://github.com/letta-ai/letta (24.5k★)
- **Status (2026-08):** **Maintained, slower cadence.** 0.16.8 released
  2026-05-14; 0.16.7 was 2026-03-31. ~2-month gaps. The 0.16.7 release
  notes are a **substantive self-hosting fix-pack** (default context
  window 32k → 128k, context-window-preservation fix, 21 context-window
  / compaction fixes, 10 memory / memfs fixes, security fixes). This is
  the work of a small focused team, not a plateau.
- **Free / verifiable:** Yes — MIT.
- **Substantive drift:** Letta continues to be the strongest option for
  **stateful long-memory agents** (memfs, core memory blocks, conversation
  forking, git-backed memory). Less general-purpose than the
  big-five frameworks.
- **2026 alternates:** Mem0 is a competing memory layer; AG-UI / AG-UI
  protocol work overlaps with LlamaIndex's 0.14.24 protocol integration.
- **Phase 3 shape implication:** **Mention as a stateful-memory
  alternate.** Not a primary Phase 3 node; not yet ready for a
  free-first Phase 3 track given the cadence. If the v1.3 scope grows
  into a memory / personalisation sub-track, Letta belongs there.

## 11. CrewAI — already in the comparison doc, still active

- **Repo:** https://github.com/crewAIInc/crewAI (57.7k★)
- **Status (2026-08):** **Very active.** 1.15.17 released 2026-08-20;
  1.15.16 on 2026-08-14; 1.15.10 on 2026-07-31. Roughly weekly cadence in
  August 2026. v1.15.17 added declarative conversational flows and
  declarative scaffolding under `crewai create <resource>`, with
  corresponding OpenAI Responses API fixes.
- **Free / verifiable:** Yes — MIT.
- **Phase 3 shape implication:** **Keep as already-listed.** The
  comparison doc's "optional enterprise / teams" framing is correct.
  No new framework displaces CrewAI's role-based crew + Flow paradigm
  in 2026.

---

## Free-first doctrine check

All recommended primary frameworks and the recommended alternates are free
and open source:

| Source | License | Free? |
| --- | --- | --- |
| HF Agents Course | Free | Yes |
| DSPy | Apache-2.0 | Yes |
| LangGraph | MIT | Yes |
| smolagents | Apache-2.0 | Yes |
| LlamaIndex | MIT | Yes |
| MCP | MIT SDKs | Yes |
| Microsoft Agent Framework | MIT | Yes |
| OpenAI Agents SDK | MIT | Yes |
| PydanticAI | MIT | Yes |
| Letta | MIT | Yes |
| CrewAI | MIT | Yes |

The **only paid component** in any of these is the **underlying LLM API**
(e.g., OpenAI, Anthropic, Google). DSPy, LangGraph, smolagents, and
LlamaIndex all support local / open-weight models via Hugging Face, Ollama,
vLLM, or local Transformers — so a free-first learner can complete the
entire v1.3 spine with HF Inference, Ollama, or a small HF Space ZeroGPU
allocation. The comparison doc already notes Render free Postgres and
ZeroGPU on HF Spaces, so the cost story is intact.

---

## Phase 3 shape implications (one paragraph, per ticket scope)

The **spine** of v1.3 (smolagents → LangGraph → LlamaIndex → DSPy, with
HF Agents Course as the entry point and MCP as a first-class node rather
than a capstone-only concern) remains the right 2026 shape — every
primary source on that list is still actively maintained, still free,
and still the canonical choice in its niche. The two changes the
G-Slot should consider for v1.3 are: **(1) drop AutoGen and replace
with Microsoft Agent Framework** as the enterprise / typed-graph
alternate, since the maintenance-mode banner is now confirmed at
the README level and MAF has reached 1.0 with multi-language SDKs and
explicit A2A / MCP interop; and **(2) add OpenAI Agents SDK and
PydanticAI as recommended alternates** so the seed graph reflects the
2026 typed-agent landscape rather than the 2024 comparison. Beyond
those, the only flag worth carrying is **smolagents' slowing release
cadence** — still maintained, but worth a verification pass at v1.3 RC
entry before pinning the "first agent framework" slot.

---

## Citations / primary sources

### Frameworks and libraries
- HF Agents Course introduction:
  https://huggingface.co/learn/agents-course/en/unit0/introduction
- DSPy releases:
  https://github.com/stanfordnlp/dspy/releases (3.3.1, 3.3.0, 3.3.0b1, 3.2.1)
- LangGraph releases:
  https://github.com/langchain-ai/langgraph/releases (1.2.11, sdk 0.4.3, checkpoint 4.2.0, cli 0.4.31)
- smolagents releases:
  https://github.com/huggingface/smolagents/releases (v1.26.0, v1.25.0, v1.24.0, v1.23.0)
- LlamaIndex releases:
  https://github.com/run-llama/llama_index/releases (0.14.24, 0.14.23, 0.14.22, 0.14.21)
- Microsoft Agent Framework repo:
  https://github.com/microsoft/agent-framework
- AutoGen repo (maintenance-mode banner):
  https://github.com/microsoft/autogen
- AutoGen → MAF migration guide:
  https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/
- OpenAI Agents SDK docs:
  https://openai.github.io/openai-agents-python/
- PydanticAI releases:
  https://github.com/pydantic/pydantic-ai/releases (v2.35.1, v2.35.0, v2.34.0, v2.33.0, v2.32.0, v2.30.0 with GHSA-q2xc-rrxj-58x9)
- Letta releases:
  https://github.com/letta-ai/letta/releases (0.16.8, 0.16.7, 0.16.6, 0.16.5)
- CrewAI releases:
  https://github.com/crewAIInc/crewAI/releases (1.15.17, 1.15.16, 1.15.15, 1.15.14, 1.15.13, 1.15.12, 1.15.11, 1.15.10, 1.15.9, 1.15.8)

### MCP
- MCP architecture overview:
  https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture
- MCP spec releases (modelcontextprotocol/modelcontextprotocol):
  https://github.com/modelcontextprotocol/modelcontextprotocol/releases (2026-07-28 stable, 2025-11-25 stable, 2025-06-18, 2025-03-26, 2024-11-05-final, 2024-11-05, 2024-10-07)
- MCP spec landing:
  https://modelcontextprotocol.io/

### Local SkillTrace references
- `docs/POST_V1_BACKLOG.md:37` — v1.3 = "Phase 3 LLM/agents/MCP seed graph"
- `docs/roadmap/capstone-projects.md` — references DSPy, MCP, LlamaIndex, LangGraph, smolagents
- `docs/resources/agentic-frameworks-comparison.md` — the August 2026 comparison snapshot this research re-validates
- `graph/resources.yaml` — SkillTrace LearningResource registry (the consumer of these sources)
