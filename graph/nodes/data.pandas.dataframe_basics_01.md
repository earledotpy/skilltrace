---
id: data.pandas.dataframe_basics_01
title: Use basic Pandas DataFrame operations
summary: Load, inspect, filter, and summarize tabular data with Pandas.
domain: data
track: foundational
roadmap_anchors:
- phase: phase_1
  phase_label: Programming Fundamentals
  month_range: 9-12
  roadmap_topic: Pandas
  source_role: reference_only
estimated_effort:
  min_minutes: 60
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- data
- pandas
created_at: 2026-06-28
updated_at: 2026-07-06
---

# Use basic Pandas DataFrame operations

## Learning target

Inspect, summarize, and filter a DataFrame — the DataFrame basics every later
Pandas skill builds on. The objective gate calls three functions on a fixed
six-row `sales` DataFrame (columns `region, product, units, revenue`):

- `column_names(df)` — return the column labels as a list.
- `total_revenue(df)` — return the sum of the `revenue` column.
- `region_rows(df, region)` — return the rows whose `region` equals `region`.

Save your script at
`evidence/artifacts/data/pandas_dataframe_basics_solution.py` and submit.

## Study pointers

The "10 minutes to pandas" tutorial (pandas.pydata.org/docs/user_guide/10min.html)
for constructing, viewing, selecting, and summarizing a DataFrame; the Pandas
"Essential basic functionality" guide for `sum`, `columns`, and boolean masks.

## Notes

Objective-gated: the checker asserts each function's result on the fixed frame
(row order not required for `region_rows`). Retrofitted from a manual gate —
each of these operations has one correct result, so exit-0 is honestly the
skill; it also anchors the Pandas hard-chain that follows.

