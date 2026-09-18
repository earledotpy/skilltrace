---
id: data.pandas.merge_join_01
title: Merge two DataFrames on a key
summary: Combine two DataFrames by matching a shared column.
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
- data
- pandas
- merge
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Merge two DataFrames on a key

## What this skill is

Bring two tables together on a shared key: the Pandas counterpart of a SQL join, and how lookup tables get attached to a dataset.

## Why this skill

Attaching reference data by key is how isolated tables become one analyzable frame.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.data.pandas.merge_join`); Evidence is checked by running your submission against its objective gate. The body does not restate them.

## How to work on it

Study the merge guide’s key and join-type handling first, then practise attaching a small lookup table to a fixed frame. Seed estimate: 45–90 minutes.

## Resources

- pandas-docs (registry)
- python-for-data-analysis (registry)

## Notes

A cross join or the wrong key is the skill failing, so key discipline is the point. Aligned to the canonical node skeleton, 2026-09.
