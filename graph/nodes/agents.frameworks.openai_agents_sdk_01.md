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

## What this skill is

Build two SDK agents where the first hands off to the second, add one guardrail that visibly fires on a hostile input, and give one agent a function tool plus an MCP-backed tool with tracing on.

## Why this skill

Delegation plus guardrails is the core safety pattern for multi-agent work: handoffs split the task, guardrails bound what the model alone would allow. A learner who can trace a handoff decision and show a guardrail firing can build small agent teams without flying blind.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Study the quickstart, handoffs, guardrails, and tools/tracing material, then practice the delegation-and-safety loop on a small task and write a half-page note on what the trace shows and what the guardrail blocked. Seed estimate: 90–180 minutes.

## Resources

- openai-agents-sdk (registry)
- mcp-spec (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight. Aligned to the canonical node skeleton, 2026-09.
