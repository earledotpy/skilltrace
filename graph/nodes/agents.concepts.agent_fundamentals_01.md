---
id: agents.concepts.agent_fundamentals_01
title: Explain what an AI agent is and how tools extend an LLM
summary: Define agent, tool, and action loop; contrast CodeAgents with tool-calling agents.
domain: agents
track: foundational
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 1-2
  roadmap_topic: HF Agents Course Units 0-1 (what agents are, tools, CodeAgents)
  source_role: reference_only
source_metadata:
  primary_source: Hugging Face Agents Course (2025 edition)
  canonical_url: https://huggingface.co/learn/agents-course/unit0/introduction
  source_version: 2025 edition, Units 0-4 + Bonus 1-3; verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources: []
regeneration_key: hf-agents-2025/agent-fundamentals-01
section_provenance:
- source: Hugging Face Agents Course
  section: Unit 0 (Welcome, syllabus, learning paths)
- source: Hugging Face Agents Course
  section: Unit 1 (Introduction to Agents — concepts, LLMs recap, tools, CodeAgents vs tool-calling)
estimated_effort:
  min_minutes: 60
  max_minutes: 120
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- fundamentals
- tools
- code-agents
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Explain what an AI agent is and how tools extend an LLM

## Learning target

Given a task description, state in one paragraph what makes an agent more than
a bare LLM call (perception via tools, action loop, memory), name the two
agent styles from the course — CodeAgent (actions as code) versus
tool-calling agent (actions as structured calls) — with a one-line example of
a task each style suits, and list two tools an agent might use with what each
one observes or changes.

## Study pointers

HF Agents Course Unit 0 for the syllabus and learning paths; Unit 1 for the
agent definition, the LLMs recap, the tools vocabulary, and the CodeAgents
versus tool-calling comparison. The Unit 1 fundamentals certificate quiz is a
good self-check that the vocabulary stuck.

## Source provenance

Primary: Hugging Face Agents Course (2025 edition),
https://huggingface.co/learn/agents-course/unit0/introduction —
Unit 0 (Welcome/syllabus/paths) + Unit 1 (Introduction to Agents).
Regeneration key: `hf-agents-2025/agent-fundamentals-01`. All references are
`reference_only` roadmap anchors; they never control locking or recommendation.

## Notes

Entry node of the v1.9 Phase 3 chain. Every framework and protocol node in
this slice lists it as a hard prerequisite: without the agent/tool/action-loop
vocabulary those targets are incoherent. Learner-manual gate expected
(conceptual judgment needs human review; AI is never an acceptance authority).
