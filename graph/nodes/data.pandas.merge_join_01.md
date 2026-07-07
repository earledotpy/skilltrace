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

## Learning target

Bring two tables together on a shared key — the Pandas counterpart of a SQL
join, and how lookup tables get attached to a dataset. The objective gate calls
your function on the fixed `sales` DataFrame (`region, product, units, revenue`)
and a small `regions` lookup (`region, manager`):

- `attach_manager(sales, regions)` — return `sales` with each row's `manager`
  attached by matching on `region`.

Save your script at
`evidence/artifacts/data/pandas_merge_join_solution.py` and submit.

## Study pointers

The Pandas "Merge, join, concatenate and compare" user guide
(pandas.pydata.org/docs/user_guide/merging.html) for `DataFrame.merge`, the `on`
key, and `how`; the "10 minutes to pandas" Merge section for a compact example.

## Notes

Objective-gated: the checker compares the merged rows (order-insensitive) and
the column set, so a cross join (every sales row against every region) or the
wrong key is caught.
