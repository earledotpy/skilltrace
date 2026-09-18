---
id: data.pandas.groupby_aggregation_01
title: Aggregate a DataFrame with groupby
summary: Split a DataFrame by a key and compute a per-group summary.
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
- aggregation
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Aggregate a DataFrame with groupby

## What this skill is

Collapse rows into per-group summaries: the split-apply-combine pattern at the heart of exploratory analysis.

## Why this skill

Grouping plus aggregation is how raw rows become the per-category numbers every report is built from.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.data.pandas.groupby_aggregation`); Evidence is checked by running your submission against its objective gate. The body does not restate them.

## How to work on it

Study the split-apply-combine guide first, then practise group-by-region-and-sum shapes on a small fixed frame. Seed estimate: 45–90 minutes.

## Resources

- pandas-docs (registry)
- python-for-data-analysis (registry)

## Notes

The grouping and the sum are the skill; index order is not. Aligned to the canonical node skeleton, 2026-09.
