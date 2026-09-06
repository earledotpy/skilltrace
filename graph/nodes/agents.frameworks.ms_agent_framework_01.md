---
id: agents.frameworks.ms_agent_framework_01
title: Run an agent team with Microsoft Agent Framework workflows
summary: Build one agent with MCP tools, run a sequential workflow, and note the AutoGen migration standing.
domain: agents
track: foundational
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 1-2
  roadmap_topic: Microsoft Agent Framework (agents, workflows, AutoGen successor)
  source_role: reference_only
source_metadata:
  primary_source: Microsoft Agent Framework documentation
  canonical_url: https://learn.microsoft.com/en-us/agent-framework/overview
  source_version: Public Preview RC-1 (python-1.0.0rc2 2026-02-26); verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources: []
regeneration_key: ms-agent-framework-rc1/workflows-01
section_provenance:
- source: Microsoft Agent Framework documentation
  section: Agents overview (chat clients, including Ollama-local-free)
- source: Microsoft Agent Framework documentation
  section: Function tools + MCP servers as tools
- source: Microsoft Agent Framework documentation
  section: Workflows (sequential, concurrent, handoff, group collaboration)
- source: Microsoft Agent Framework documentation
  section: Migration guides from Semantic Kernel and from AutoGen
estimated_effort:
  min_minutes: 90
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- microsoft
- workflows
- multi-agent
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Run an agent team with Microsoft Agent Framework workflows

## Learning target

Build one agent on the framework (Ollama-local is the free-first model
choice; Azure OpenAI/OpenAI/Anthropic noted with their metered cost), give it
one function tool and one MCP server as tools, and run a two-agent sequential
workflow where the second agent consumes the first agent's output. Write a
half-page note on the succession standing: what the migration guides say
about moving from Semantic Kernel / AutoGen, and why AutoGen (maintenance
mode, community-managed, no new features) is not the v1.9 target.

## Study pointers

The agents-overview pages for chat-client setup; the tools pages for function
tools plus MCP servers as tools; the workflows pages for the sequential
pattern (concurrent, handoff, and group collaboration as background);
the migration guides for the AutoGen succession note. Session state,
middleware/filters, and observability are pointers, not built here.

## Source provenance

Primary: Microsoft Agent Framework documentation,
https://learn.microsoft.com/en-us/agent-framework/overview — agents, tools,
workflows, migration guides. Regeneration key:
`ms-agent-framework-rc1/workflows-01`. All references `reference_only`.

## Notes

Enterprise-workflow node of the slice. Hard prerequisite is the fundamentals
node only; the MCP node is a soft ordering (tools-via-MCP lands faster with
the protocol first, but the workflow runs without it). Framework is MIT
OSS; model and hosting costs sit with third parties per the docs'
Third-Party-Systems notice.
