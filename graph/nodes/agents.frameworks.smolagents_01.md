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

## What this skill is

Run a smolagents `CodeAgent` end to end on a small task (model via `InferenceClientModel`, LiteLLM, local Transformers, or an OpenAI-compatible server — your choice), author one custom tool following the tools in-depth guide, rerun the agent using it, and compare `CodeAgent` with `ToolCallingAgent`.

## Why this skill

Code actions are the most composable agent style and the cheapest to prototype with. A learner who can write and use one custom tool can extend any agent in the slice, and can say which task shape favors emitting code versus calling tools.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Study the guided tour / quickstart and run the first agent; author the custom tool and rerun the agent with it. Write the half-page comparison: what each style emits as an action, and which task shape favors which. Seed estimate: 90–180 minutes.

## Resources

- hf-agents-course (registry)
- smolagents-docs (registry)
- mcp-spec (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight.

Prototyping-flavored framework node: code actions and composability first, production orchestration later (LangGraph). Hard prerequisite is the fundamentals node only — the agent/tool vocabulary is the incoherence test. MCP interop (`from_mcp`) is named here as a pointer; the protocol itself lives in its own node. Secure code execution (E2B/Modal/Docker sandboxes) is background reading here — noted, not built. Primary source: smolagents documentation — quickstart, CodeAgent vs ToolCallingAgent, tools in-depth; supporting: HF Agents Course Unit 2.1; regeneration key `smolagents-1.26.0/first-codeagent-01`. All references `reference_only`. Aligned to the canonical node skeleton, 2026-09.
