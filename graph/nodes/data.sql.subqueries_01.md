---
id: data.sql.subqueries_01
title: Filter against a subquery
summary: Use a nested SELECT to compute a threshold you filter against.
domain: data
track: foundational
estimated_effort:
  min_minutes: 45
  max_minutes: 90
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- sql
- data
- subqueries
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Filter against a subquery

## What this skill is

Compute a value with one query and filter another query against it — the move behind ‘above average’ and countless real questions — using a nested SELECT rather than a hardcoded number.

## Why this skill

Composing queries lets each question build on the last instead of freezing a number that will go stale. A threshold computed live stays honest as the data changes; a hardcoded one silently rots.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.data.sql.subqueries`); Evidence is checked by running your submission against its objective gate. The body does not restate them.

## How to work on it

Work nested-SELECT-in-WHERE drills, each time computing the threshold inside the query and checking the result against a hand-computed expectation. Seed estimate: 45–90 minutes.

## Resources

- sqlbolt (registry)
- sqlite-docs (registry)

## Notes

Aligned to the canonical node skeleton, 2026-09.
