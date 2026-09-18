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

## What this skill is

Define agent, tool, and action loop; contrast CodeAgents with tool-calling agents, with a one-line example of a task each style suits.

## Why this skill

The agent vocabulary is the entry ticket to the whole agentic slice: every framework and protocol node downstream assumes the tool/action-loop distinction. A learner who can say what makes an agent more than a bare LLM call can follow delegation, guardrails, and tool-use discussions without getting lost.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Study the syllabus and concepts units, then practice in writing: one paragraph on what makes an agent more than a bare LLM call, the two agent styles with an example task each, and two tools with what each observes or changes. Seed estimate: 60–120 minutes.

## Resources

- hf-agents-course (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight. Aligned to the canonical node skeleton, 2026-09.
