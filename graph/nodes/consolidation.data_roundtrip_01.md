---
id: consolidation.data_roundtrip_01
title: Carry a dataset through a CSV to SQL to Pandas round-trip
summary: Load a CSV, query it with SQL, then reproduce the same answer in Pandas, and confirm the two paths agree.
domain: data
track: consolidation
estimated_effort:
  min_minutes: 60
  max_minutes: 120
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- consolidation
- data
- sql
- pandas
created_at: 2026-07-07
updated_at: 2026-07-07
---

# Carry a dataset through a CSV to SQL to Pandas round-trip

## Learning target

Take one small CSV and move it through three tools that see data differently:
read the rows, load them into SQL and answer a question with a query, then
answer the *same* question in Pandas — and check that the two results match.
The skill is seeing that a CSV, a SQL table, and a DataFrame are three views of
the same tabular data, and that a filter-group-aggregate question has one answer
regardless of which tool asks it.

## Study pointers

- SQLBolt for the SQL leg and the Pandas docs "Comparison with SQL" page for the
  Pandas leg — the latter maps each SQL clause to its DataFrame equivalent, which
  is exactly the round-trip this node asks you to make.
- Keep the dataset tiny (a dozen rows) so you can verify the agreement by hand.

## Notes

Soft-edged from the CSV, SQL, and Pandas bands it weaves — prior fluency passes
it directly. Manual-gated: whether the two paths were made to genuinely agree,
and the discrepancies understood, is judgment.
