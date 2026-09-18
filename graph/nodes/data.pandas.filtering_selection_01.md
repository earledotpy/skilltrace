---
id: data.pandas.filtering_selection_01
title: Filter rows and select columns in Pandas
summary: Subset a DataFrame with a boolean condition and pick columns.
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
- filtering
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Filter rows and select columns in Pandas

## What this skill is

Cut a DataFrame down to the rows and columns a question needs: the first move in nearly every analysis.

## Why this skill

Filtering to exactly the needed rows and columns is what turns a dataset into an answerable question.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.data.pandas.filtering_selection`); Evidence is checked by running your submission against its objective gate. The body does not restate them.

## How to work on it

Study boolean indexing and column selection first, then practise threshold-plus-columns cuts on a small fixed frame. Seed estimate: 30–60 minutes.

## Resources

- pandas-docs (registry)
- python-for-data-analysis (registry)

## Notes

An off-by-one threshold or an extra column is the skill failing, so exactness here is the point. Aligned to the canonical node skeleton, 2026-09.
