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

## Learning target

Compute a new column from existing ones — the everyday shape of feature
engineering. The objective gate calls your function on the same fixed `sales`
DataFrame (`region, product, units, revenue`):

- `add_unit_price(df)` — return the DataFrame with a new `unit_price` column
  equal to `revenue / units`, leaving the existing columns unchanged.

Save your script at
`evidence/artifacts/data/pandas_transform_columns_solution.py` and submit.

## Study pointers

The "10 minutes to pandas" Operations section and the Pandas "Indexing and
selecting data → Setting" notes (pandas.pydata.org/docs) for assigning a new
column from a vectorized expression; Real Python's "pandas: How to Add Columns"
for worked variants including `assign`.

## Notes

Objective-gated: the checker compares every row's `unit_price` against
`revenue / units`. The seed numbers divide cleanly, so a correct answer never
fails on floating-point noise; a wrong formula does.
