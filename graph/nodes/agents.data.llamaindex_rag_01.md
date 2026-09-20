---
id: agents.data.llamaindex_rag_01
title: Build a small RAG pipeline with LlamaIndex retrievers
summary: Index a document set, query it through a retriever and query engine, and run one agentic-RAG turn.
domain: agents
track: foundational
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 1-2
  roadmap_topic: LlamaIndex (indexes, RAG pipeline, agentic RAG)
  source_role: reference_only
source_metadata:
  primary_source: LlamaIndex framework documentation
  canonical_url: https://developers.llamaindex.ai/python/framework/
  source_version: Core 0.14.16 (changelog 2026-03-10); verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources:
  - Hugging Face Agents Course Unit 2.2 — https://huggingface.co/learn/agents-course/unit0/introduction
  - Hugging Face Agents Course Unit 3 (Agentic RAG use case) — https://huggingface.co/learn/agents-course/unit0/introduction
regeneration_key: llamaindex-0.14.16/rag-pipeline-01
section_provenance:
- source: LlamaIndex framework documentation
  section: Documents, nodes, and indices (ingestion)
- source: LlamaIndex framework documentation
  section: RAG pipeline (retrievers, query engines)
- source: LlamaIndex framework documentation
  section: Agents (ReAct / function-calling agents over an index)
- source: Hugging Face Agents Course
  section: Unit 2.2 (LlamaIndex framework unit) + Unit 3 (Agentic RAG use case)
estimated_effort:
  min_minutes: 90
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- llamaindex
- rag
- retrieval
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Build a small RAG pipeline with LlamaIndex retrievers

## What this skill is

Ingest a small document set (a dozen pages is plenty) into a LlamaIndex index, query it through a retriever plus query engine pair, and show one retrieval-augmented answer with its cited chunks — then take one agentic turn, letting a ReAct or function-calling agent over the same index decide when to retrieve.

## Why this skill

Retrieval is how an agent's knowledge stops being whatever fits in the context window. A learner who can index, retrieve with citations, and hand the retriever to an agent can build the data half of any RAG system and tell a pipeline answer from an agentic one.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Study the documents/nodes/indices and RAG-pipeline pages, build the small pipeline, then run the agentic turn over the same index. Write a half-page note comparing the plain pipeline answer with the agentic turn — what the agent decided that the pipeline could not. Seed estimate: 90–180 minutes.

## Resources

- hf-agents-course (registry)
- llamaindex-docs (registry)
- mcp-spec (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight.

Data-centric node of the slice. Hard prerequisite is the fundamentals node only. The MCP tool package (`llama-index-tools-mcp`) is named as a pointer from the protocol node; it is not built here. LlamaCloud (Parse/Extract/Index) is a commercial pointer only — the pipeline here runs on the free OSS framework. Primary source: LlamaIndex framework documentation — ingestion, RAG pipeline, agents; supporting: HF Agents Course Units 2.2 and 3; regeneration key `llamaindex-0.14.16/rag-pipeline-01`. All references `reference_only`. Aligned to the canonical node skeleton, 2026-09.
