---
id: agents.frameworks.openai_agents_sdk_01
title: Delegate a task with OpenAI Agents SDK handoffs and guardrails
summary: Build two agents with a handoff, add one guardrail, and trace the run with one MCP-backed tool.
domain: agents
track: foundational
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 1-2
  roadmap_topic: OpenAI Agents SDK (agents, handoffs, guardrails)
  source_role: reference_only
source_metadata:
  primary_source: OpenAI Agents SDK (Python) documentation
  canonical_url: https://openai.github.io/openai-agents-python/
  source_version: Python openai-agents 0.22.0 (PyPI+GitHub 2026-08-19, pre-1.0 rapid 0.x); verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources:
  - OpenAI platform agents guide — https://developers.openai.com/api/docs/guides/agents
regeneration_key: openai-agents-0.22.0/handoffs-guardrails-01
section_provenance:
- source: OpenAI Agents SDK (Python) documentation
  section: Quickstart (install, API key, first agent + run)
- source: OpenAI Agents SDK (Python) documentation
  section: Agents, Runner (sync/async), handoffs (agents-as-tools, delegation)
- source: OpenAI Agents SDK (Python) documentation
  section: Guardrails (input/output)
- source: OpenAI Agents SDK (Python) documentation
  section: Function tools + MCP servers; tracing
estimated_effort:
  min_minutes: 90
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- openai
- handoffs
- guardrails
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Delegate a task with OpenAI Agents SDK handoffs and guardrails

## Learning target

Build two SDK agents (`pip install openai-agents`) where the first hands off
to the second (agents-as-tools delegation), add one input or output guardrail
that visibly fires on a hostile input, and give one agent a function tool plus
one MCP-backed tool with tracing on. Write a half-page note: what the trace
shows about the handoff decision, and what the guardrail blocked that the
model alone would have allowed.

## Study pointers

The Python SDK quickstart for install and first run; the Agents/Runner pages
for sync/async execution; the handoffs pages for delegation; the guardrails
pages for input/output checks; the tools and tracing pages for the MCP-backed
tool. Only verified Python pages are cited — the realtime API surface is JS
and is never part of this node. Per-token model billing plus metered tool
calls apply; note your spend.

## Source provenance

Primary: OpenAI Agents SDK (Python),
https://openai.github.io/openai-agents-python/ — quickstart, handoffs,
guardrails, tools, tracing. Supporting: platform agents guide,
https://developers.openai.com/api/docs/guides/agents. Regeneration key:
`openai-agents-0.22.0/handoffs-guardrails-01`. All references
`reference_only`.

## Notes

Delegation-and-safety node of the slice. Hard prerequisite is the
fundamentals node only; the MCP node is a soft ordering. SDK is MIT OSS and
free; running agents bills per-token plus metered tool calls (re-verify rates
against official pricing at spec time — no rate is pinned here).
