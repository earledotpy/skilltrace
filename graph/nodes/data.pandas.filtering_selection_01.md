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

## Learning target

Cut a DataFrame down to the rows and columns a question needs — the first move
in nearly every analysis. The objective gate calls your function on a fixed
six-row `sales` DataFrame with columns `region, product, units, revenue`:

- `high_revenue(df)` — return the rows where `revenue` is at least 100, keeping
  only the `region`, `product`, and `revenue` columns.

Save your script at
`evidence/artifacts/data/pandas_filtering_selection_solution.py` and submit.

## Study pointers

The Pandas "Indexing and selecting data" user guide
(pandas.pydata.org/docs/user_guide/indexing.html) for boolean indexing and
column selection; the "10 minutes to pandas" tutorial's Selection section for a
quick worked run.

## Notes

Objective-gated: the checker compares the returned rows (order-insensitive) and
the exact column set, so an off-by-one threshold or an extra column is caught.
