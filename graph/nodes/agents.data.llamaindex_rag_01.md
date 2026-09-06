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

## Learning target

Ingest a small document set (a dozen pages is plenty) into a LlamaIndex
index, query it through a retriever plus query engine pair, and show one
retrieval-augmented answer with its cited chunks. Then take one agentic turn:
let a ReAct or function-calling agent over the same index decide when to
retrieve. Write a half-page note comparing the plain pipeline answer with the
agentic turn — what the agent decided that the pipeline could not.

## Study pointers

LlamaIndex framework docs for documents/nodes/indices and ingestion; the RAG
pipeline pages for retrievers and query engines; the agents pages for the
agentic turn; HF Agents Course Unit 2.2 for framework framing and Unit 3 for
the agentic-RAG use-case shape. LlamaCloud (Parse/Extract/Index) is a
commercial pointer only — the pipeline here runs on the free OSS framework.

## Source provenance

Primary: LlamaIndex framework documentation,
https://developers.llamaindex.ai/python/framework/ — ingestion, RAG pipeline,
agents. Supporting: HF Agents Course Units 2.2 and 3. Regeneration key:
`llamaindex-0.14.16/rag-pipeline-01`. All references `reference_only`.

## Notes

Data-centric node of the slice. Hard prerequisite is the fundamentals node
only. The MCP tool package (`llama-index-tools-mcp`) is named as a pointer
from the protocol node; it is not built here.
