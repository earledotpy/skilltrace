---
id: data.sql.join_mental_models_01
title: Build a mental model for SQL joins
summary: Reason about what each join type keeps and drops, so joins stop being trial-and-error — a focused rescue drill for the concept, not the full join syntax lesson.
domain: data
track: remediation
estimated_effort:
  min_minutes: 20
  max_minutes: 45
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: true
  requires_long_block: false
tags:
- remediation
- sql
- joins
created_at: 2026-07-07
updated_at: 2026-07-07
---

# Build a mental model for SQL joins

## What this skill is

Predict, before running the query, what a join returns: which rows an inner join keeps versus a left join, what a missing or duplicated join key does, and why an unintended fan-out multiplies rows. The rescue is a mental model — picturing two tables and which rows survive the match.

## Why this skill

This turns joins from permuting INNER and LEFT until the count looks right into reasoning. Learners who can write join syntax but keep getting the wrong rows are missing exactly this picture.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.data.sql.join_mental_models`); Evidence is judged by learner manual review. The body does not restate them.

## How to work on it

For each interactive join exercise, predict the row count before running it; then draw two small tables by hand and trace one inner and one left join row by row. Seed estimate: 20–45 minutes.

## Resources

- sqlbolt (registry)
- select-star-sql (registry)

## Notes

A remediation node homed in the SQL domain, narrower than the joins learning node: it rescues the concept when syntax works but rows come out wrong. Rescues the joins and subqueries nodes and the data round-trip consolidation. Aligned to the canonical node skeleton, 2026-09.
