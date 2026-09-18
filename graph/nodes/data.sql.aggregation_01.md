---
id: data.sql.aggregation_01
title: Summarize groups with GROUP BY
summary: Compute per-group counts and averages with aggregate functions.
domain: data
track: foundational
estimated_effort:
  min_minutes: 30
  max_minutes: 60
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: true
  requires_long_block: false
tags:
- sql
- data
- aggregation
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Summarize groups with GROUP BY

## What this skill is

Collapse many rows into per-group summaries — counts and averages by group — with aggregate functions and GROUP BY.

## Why this skill

Per-group summaries are the daily bread of exploratory data work: how many per department, what average per category. This is the move that turns raw rows into statements about the world.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.data.sql.aggregation`); Evidence is checked by running your submission against its objective gate. The body does not restate them.

## How to work on it

Work aggregate-and-group drills in the interactive lessons, predicting the number of result rows (one per group) before running each query. Seed estimate: 30–60 minutes.

## Resources

- sqlbolt (registry)
- select-star-sql (registry)
- sqlite-docs (registry)

## Notes

Aligned to the canonical node skeleton, 2026-09.
