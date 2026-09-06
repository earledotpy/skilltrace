---
id: agents.protocol.mcp_01
title: Expose a tool through an MCP server and call it from a client
summary: Implement one MCP server tool and invoke it over stdio and Streamable HTTP from a client.
domain: agents
track: foundational
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 1-2
  roadmap_topic: MCP (protocol, servers, tools, transports)
  source_role: reference_only
source_metadata:
  primary_source: Model Context Protocol specification
  canonical_url: https://modelcontextprotocol.io/
  source_version: 2025-06-18 stable (2025-11-25 latest stable; re-pin at spec time); verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources: []
regeneration_key: mcp-2025-06-18/server-tool-01
section_provenance:
- source: Model Context Protocol specification
  section: Base protocol (JSON-RPC 2.0, lifecycle, capability negotiation)
- source: Model Context Protocol specification
  section: Server features — Tools (with Resources and Prompts as background)
- source: Model Context Protocol specification
  section: Transports (stdio, Streamable HTTP)
estimated_effort:
  min_minutes: 90
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- mcp
- protocol
- tools
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Expose a tool through an MCP server and call it from a client

## Learning target

Implement one MCP server exposing a single tool (your choice of task — e.g. a
calculator, a file lookup, a tiny search), then call it from a client over
both transports: stdio and Streamable HTTP. Show the capability negotiation in
a half-page note: what the client and server agreed on at startup, and what
broke (or warned) when you tried a mismatched expectation.

## Study pointers

The MCP base-protocol pages for JSON-RPC framing, lifecycle, and capability
negotiation; the server-features pages for the Tools surface (Resources and
Prompts as background reading); the transports pages for stdio versus
Streamable HTTP. Authorization (OAuth/OIDC) and extensions (Tasks,
Skills-over-MCP, MCP Apps) are named pointers only — not built here.

## Source provenance

Primary: Model Context Protocol specification,
https://modelcontextprotocol.io/ — base protocol, server Tools, transports.
Regeneration key: `mcp-2025-06-18/server-tool-01`. The "latest stable"
revision must be re-pinned at spec time (2025-11-25 versus the 2026-07-28
schema dir). All references `reference_only`.

## Notes

Protocol node of the slice: the shared tool vocabulary every MCP-consuming
framework node points back to (soft edges, capped per the locked shape).
Hard prerequisite is the fundamentals node only. MCP is a free open protocol
(MIT transitioning to Apache-2.0 for new spec/code, docs CC-BY-4.0); no
certificate is involved.
