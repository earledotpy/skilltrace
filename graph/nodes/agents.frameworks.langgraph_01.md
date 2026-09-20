---
id: agents.frameworks.langgraph_01
title: Orchestrate a stateful graph with LangGraph and persistence
summary: Build a small stateful graph with reducers, add checkpointing, and run the prebuilt ReAct agent.
domain: agents
track: foundational
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 1-2
  roadmap_topic: LangGraph (stateful graphs, persistence, orchestration)
  source_role: reference_only
source_metadata:
  primary_source: LangGraph documentation
  canonical_url: https://docs.langchain.com/oss/python/langgraph/overview
  source_version: 1.2.11 (PyPI 2026-08-11); 1.0 is LTS; verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources:
  - Hugging Face Agents Course Unit 2.3 — https://huggingface.co/learn/agents-course/unit0/introduction
regeneration_key: langgraph-1.2.11/stateful-graph-01
section_provenance:
- source: LangGraph documentation
  section: Graphs, state, and reducers (core graph model)
- source: LangGraph documentation
  section: Persistence and checkpointing (sqlite/postgres checkpointer)
- source: LangGraph documentation
  section: Prebuilt ReAct agent
- source: Hugging Face Agents Course
  section: Unit 2.3 (LangGraph framework unit)
estimated_effort:
  min_minutes: 120
  max_minutes: 240
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- langgraph
- orchestration
- state
- persistence
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Orchestrate a stateful graph with LangGraph and persistence

## What this skill is

Build a small LangGraph graph — two or more nodes plus an edge — over explicit state with a reducer, rerun it from a sqlite checkpointer so a second invocation resumes rather than restarts, and run the prebuilt ReAct agent on one task with one tool.

## Why this skill

Stateful orchestration is the production backbone of the agentic slice: every multi-step agent eventually needs state, reducers, and persistence. A learner who can checkpoint and resume a graph can reason about what survives between runs — the question deployment and debugging both turn on.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Study the overview pages for graphs, state, and reducers, then build the small graph and rerun it from a checkpointer; finish with the prebuilt ReAct agent run. Write a half-page note: what the checkpointer remembers between runs, and where you would insert a human-in-the-loop step (streaming and Studio are pointers, not built here). Seed estimate: 120–240 minutes.

## Resources

- hf-agents-course (registry)
- langgraph-docs (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight.

Production-orchestration node of the slice and one of the two hard-prerequisite lineages into the capstone (the other is the Docker-primer node). Hard prerequisite is the fundamentals node only. Library scope is the MIT-licensed OSS graph library; `langgraph-api` server / Platform hosting terms are commercial and are never part of acceptance here. Platform deployment (APIs, threads, cron) and LangSmith evals stay background pointers. Primary source: LangGraph documentation — graphs/state, persistence/checkpointing, prebuilt ReAct agent; supporting: HF Agents Course Unit 2.3; regeneration key `langgraph-1.2.11/stateful-graph-01`. All references `reference_only`. Aligned to the canonical node skeleton, 2026-09.
