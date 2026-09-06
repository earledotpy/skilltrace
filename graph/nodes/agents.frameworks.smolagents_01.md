---
id: agents.frameworks.smolagents_01
title: Build a first CodeAgent with smolagents and one custom tool
summary: Run a CodeAgent and a ToolCallingAgent; author one custom tool and compare the styles.
domain: agents
track: foundational
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 1-2
  roadmap_topic: smolagents (CodeAgent, tools, first agent)
  source_role: reference_only
source_metadata:
  primary_source: smolagents documentation
  canonical_url: https://huggingface.co/docs/smolagents
  source_version: 1.26.0 (PyPI + GitHub release 2026-05-29); verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources:
  - Hugging Face Agents Course Unit 2.1 — https://huggingface.co/learn/agents-course/unit0/introduction
regeneration_key: smolagents-1.26.0/first-codeagent-01
section_provenance:
- source: smolagents documentation
  section: Guided tour / quickstart (first CodeAgent run)
- source: smolagents documentation
  section: CodeAgent vs ToolCallingAgent (code actions, composability)
- source: smolagents documentation
  section: Tools in-depth guide (authoring a custom tool)
- source: Hugging Face Agents Course
  section: Unit 2.1 (smolagents framework unit)
estimated_effort:
  min_minutes: 90
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- smolagents
- code-agent
- tools
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Build a first CodeAgent with smolagents and one custom tool

## Learning target

Run a smolagents `CodeAgent` end to end on a small task (model via
`InferenceClientModel`, LiteLLM, local Transformers, or an OpenAI-compatible
server — your choice), then author one custom tool following the tools
in-depth guide and rerun the agent using it. Write a half-page comparison of
`CodeAgent` versus `ToolCallingAgent`: what each one emits as an action, and
which task shape favors which style.

## Study pointers

smolagents guided tour / quickstart for the first run; the CodeAgent versus
ToolCallingAgent pages for the style comparison; the tools in-depth guide for
authoring the custom tool; HF Agents Course Unit 2.1 for the framework-level
framing. Secure code execution (E2B/Modal/Docker sandboxes) is background
reading here — noted, not built.

## Source provenance

Primary: smolagents documentation, https://huggingface.co/docs/smolagents —
quickstart, CodeAgent vs ToolCallingAgent, tools in-depth. Supporting: HF
Agents Course Unit 2.1. Regeneration key:
`smolagents-1.26.0/first-codeagent-01`. All references `reference_only`.

## Notes

Prototyping-flavored framework node: code actions and composability first,
production orchestration later (LangGraph). Hard prerequisite is the
fundamentals node only — the agent/tool vocabulary is the incoherence test.
MCP interop (`from_mcp`) is named here as a pointer; the protocol itself lives
in its own node.
