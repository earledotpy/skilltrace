---
id: agents.frameworks.pydanticai_01
title: Ship a typed agent with PydanticAI tools and test-model evals
summary: Build a typed agent with structured output, test it with the built-in test model, and run one eval.
domain: agents
track: foundational
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 1-2
  roadmap_topic: PydanticAI (typed agents, tools, testing, evals)
  source_role: reference_only
source_metadata:
  primary_source: PydanticAI documentation
  canonical_url: https://pydantic.dev/docs/ai/
  source_version: V2.0 stable 2026-06-23 (PyPI 2.40.0 observed 2026-09-05, re-pin); verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources: []
regeneration_key: pydanticai-v2/typed-agent-evals-01
section_provenance:
- source: PydanticAI documentation
  section: Agents, dependencies, and structured output
- source: PydanticAI documentation
  section: Function tools and toolsets
- source: PydanticAI documentation
  section: Testing (built-in test model, no API key)
- source: PydanticAI documentation
  section: Evals (pydantic-evals, pytest-style)
estimated_effort:
  min_minutes: 90
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- pydanticai
- typing
- evals
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Ship a typed agent with PydanticAI tools and test-model evals

## Learning target

Build a PydanticAI agent with typed dependencies, one function tool, and
structured output validated by a Pydantic model; drive it first with the
built-in `test` model (no API key), then against one real provider via the
string-swap models overview; and run one `pydantic-evals` pytest-style eval
showing a pass. Write a half-page note: what the type boundary caught that a
dict-passing agent would have let through.

## Study pointers

The agents/dependencies/structured-output pages for the typed core; the tools
and toolsets pages for the function tool; the testing page for the `test`
model loop; the evals pages for the pytest-style eval. MCP, instructions,
hooks, and durable execution are pointers, not built here. Observe the V1 to
V2 upgrade guide if any example you meet still speaks V1.

## Source provenance

Primary: PydanticAI documentation, https://pydantic.dev/docs/ai/ — agents,
tools, testing, evals. Regeneration key: `pydanticai-v2/typed-agent-evals-01`.
The PyPI pin must be re-verified at spec time. All references
`reference_only`.

## Notes

Type-safety node of the slice and the second framework-comparison soft edge
(with the OpenAI SDK node): harness-first typed agents versus the
delegation-first SDK. Hard prerequisite is the fundamentals node only.
Framework is MIT OSS; Logfire observability and provider tokens are separate
costs, not pinned here.
