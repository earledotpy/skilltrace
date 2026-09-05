---
id: agents.optimization.dspy_01
title: Optimize a program with DSPy signatures, modules, and metrics
summary: Write a DSPy program with typed signatures, score it with a metric, and run one optimizer pass.
domain: agents
track: foundational
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 1-2
  roadmap_topic: DSPy (signatures, modules, optimization)
  source_role: reference_only
source_metadata:
  primary_source: DSPy documentation
  canonical_url: https://dspy.ai/
  source_version: 3.3.1 (PyPI 2026-08-21); verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources: []
regeneration_key: dspy-3.3.1/signatures-optimization-01
section_provenance:
- source: DSPy documentation
  section: Getting Started (Program-don't-prompt, setup, first program)
- source: DSPy documentation
  section: Signatures (including class-based and expanding signatures)
- source: DSPy documentation
  section: Modules and composing modules (including Tools with ReAct)
- source: DSPy documentation
  section: Metrics and GEPA optimization (optimizer choice)
estimated_effort:
  min_minutes: 90
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- dspy
- optimization
- prompting
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Optimize a program with DSPy signatures, modules, and metrics

## Learning target

Write a small DSPy program (`pip install dspy`) built from two composed
modules with typed signatures, define a metric that scores its outputs, and
run one optimizer pass (GEPA or a BootstrapFewShot-family optimizer) showing
before-and-after scores on a tiny evaluation set you author. Write a half-page
note in the Program-don't-prompt spirit: what moved into the program (and the
metric) versus what stayed in prose prompts.

## Study pointers

DSPy Getting Started for setup and the first program; the signatures pages for
typed and class-based signatures; the modules pages for composition and Tools
with ReAct; the metrics and optimizer pages for the optimization pass. Runtime
cost is the underlying LM API tokens — note which provider you used and why.

## Source provenance

Primary: DSPy documentation, https://dspy.ai/ — Getting Started, signatures,
modules, metrics, GEPA optimization. Regeneration key:
`dspy-3.3.1/signatures-optimization-01`. All references `reference_only`.

## Notes

Optimization-discipline node of the slice; it orders before orchestration
work (soft edge toward LangGraph) without gating it. Hard prerequisite is the
fundamentals node only. DSPy is MIT-licensed OSS; no certificate is involved.
