---
id: data.pandas.transform_columns_01
title: Derive a new column in Pandas
summary: Add a computed column from existing ones with vectorized arithmetic.
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
- data
- pandas
- feature-engineering
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Derive a new column in Pandas

## What this skill is

Compute a new column from existing ones: the everyday shape of feature engineering.

## Why this skill

Derived columns are where domain knowledge enters the frame, and the operation recurs in every analysis.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.data.pandas.transform_columns`); Evidence is checked by running your submission against its objective gate. The body does not restate them.

## How to work on it

Study new-column assignment from a vectorized expression first, then practise one clean derived-column computation, leaving existing columns unchanged. Seed estimate: 30–60 minutes.

## Resources

- pandas-docs (registry)
- python-for-data-analysis (registry)

## Notes

Derived values are exact here, so a correct answer never fails on floating-point noise while a wrong formula does. Aligned to the canonical node skeleton, 2026-09.
