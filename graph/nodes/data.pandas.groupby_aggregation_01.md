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

## Learning target

Collapse rows into per-group summaries — the split-apply-combine pattern at the
heart of exploratory analysis. The objective gate calls your function on the
same fixed `sales` DataFrame (`region, product, units, revenue`):

- `revenue_by_region(df)` — return a Series of the total `revenue` for each
  `region` (group by `region`, sum `revenue`).

Save your script at
`evidence/artifacts/data/pandas_groupby_aggregation_solution.py` and submit.

## Study pointers

The Pandas "Group by: split-apply-combine" user guide
(pandas.pydata.org/docs/user_guide/groupby.html) for `groupby` and aggregation;
the "10 minutes to pandas" Grouping section for a compact worked example.

## Notes

Objective-gated: the checker compares the result as a `{region: total}` mapping,
so the Series index order is not the skill — the grouping and the sum are.
