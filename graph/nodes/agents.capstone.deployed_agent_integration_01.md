---
id: agents.capstone.deployed_agent_integration_01
title: Deploy an agent behind FastAPI on Engine plus a ZeroGPU Space (capstone)
summary: Ship a LangGraph agent with MCP tools served by FastAPI, checked on Engine-local and hosted on Gradio ZeroGPU.
domain: agents
track: portfolio
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 3
  roadmap_topic: Agentic capstone (LangGraph + MCP + primer deploy, Engine-local + Spaces hosted)
  source_role: reference_only
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 3
  roadmap_topic: HF Agents Course Unit 4 (final project, build/test/certify on GAIA)
  source_role: reference_only
source_metadata:
  primary_source: LangGraph documentation
  canonical_url: https://docs.langchain.com/oss/python/langgraph/overview
  source_version: 1.2.11 (PyPI 2026-08-11); verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources:
  - Model Context Protocol specification — https://modelcontextprotocol.io/
  - FastAPI documentation — https://fastapi.tiangolo.com/
  - Docker Engine documentation — https://docs.docker.com/engine/
  - Hugging Face Spaces ZeroGPU docs — https://huggingface.co/docs/hub/en/spaces-zerogpu
regeneration_key: langgraph-1.2.11/deployed-agent-capstone-01
section_provenance:
- source: LangGraph documentation
  section: Graphs/state, persistence, prebuilt ReAct agent (the orchestrated core)
- source: Model Context Protocol specification
  section: Server Tools + stdio transport (the agent's tool surface)
- source: FastAPI documentation
  section: First Steps + FastAPI in Containers (the serving wrapper)
- source: Docker Engine documentation
  section: Engine 4-command acceptance (the local check)
- source: Hugging Face Spaces ZeroGPU docs
  section: 'Gradio SDK + @spaces.GPU deploy (free tier: max 2 Spaces, 5 min/day)'
estimated_effort:
  min_minutes: 240
  max_minutes: 480
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- capstone
- integration
- portfolio
- deploy
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Deploy an agent behind FastAPI on Engine plus a ZeroGPU Space (capstone)

## Learning target

Deliver a `deployed-agent/` folder that integrates the slice: a LangGraph
agent (stateful graph, checkpointer on) whose tools arrive over MCP (at least
one tool served by your own MCP server from the protocol node), wrapped in
the primer FastAPI service, checked twice — Engine-local via the 4-command
acceptance, and hosted via Gradio SDK plus `@spaces.GPU` ZeroGPU deploy (free
tier: max 2 Spaces, 5 min/day; acceptance checks the Space URL resolves plus
the ZeroGPU decorator present). Never `docker push` to Spaces (Docker Spaces
need a paid plan). Close with a best-model-style analysis naming which
source's technique (LangGraph persistence, MCP tool surface, DSPy-optimized
prompts, LlamaIndex retrieval) moved the agent's behavior at each step.

## Study pointers

LangGraph persistence and ReAct pages for the orchestrated core; the MCP
server-Tools and stdio pages for the tool surface; the FastAPI primer nodes
for the serving wrapper; the Spaces ZeroGPU pages for the hosted split
(Gradio-only compatibility, quotas, no `torch.compile`).

## Source provenance

Primary: LangGraph documentation. Supporting: MCP specification (Tools,
stdio); FastAPI docs (first steps, containers); Docker Engine docs (local
acceptance); Spaces ZeroGPU docs (hosted split). Regeneration key:
`langgraph-1.2.11/deployed-agent-capstone-01`. All references
`reference_only` — this node *integrates* sources without any anchor
controlling locking.

## Capstone integration identification

This node is the v1.9 >= 1 / >= 2-sources capstone. Prerequisites cite two
source lineages (the LangGraph-anchored `agents.frameworks.langgraph_01`
chain and the primer-anchored `agents.deploy.docker_engine_build_run_01`
chain), and its artifact cites LangGraph plus MCP (tools via MCP) plus the
primer (served by FastAPI, checked on Engine, hosted on ZeroGPU) — satisfying
>= 1 node citing >= 2 sources with the agentic deploy-via-primer flavor, in
the Engine-local plus Gradio-ZeroGPU hosted split per the locked primer
verdict. See the draft-branch note for the full criterion walk-through.

## Notes

Second half of the Phase 3 agentic checkpoint (deployed-agent discipline per
the slot row). Portfolio track: the folder plus behavior analysis is the
evidence artifact. DSPy-optimized prompts and LlamaIndex retrieval are
expected ingredients of the analysis, not extra prerequisites — the hard
parents stay exactly the two locked ones.
