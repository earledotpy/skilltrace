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

## What this skill is

Take one small CSV and move it through three tools that see data differently: read the rows, load them into SQL and answer a question with a query, then answer the same question in Pandas — and check that the two results match.

## Why this skill

The skill is seeing that a CSV, a SQL table, and a DataFrame are three views of the same tabular data, and that a filter-group-aggregate question has one answer regardless of which tool asks it. Agreement between the paths is the evidence the question was really answered.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.consolidation.data_roundtrip`); Evidence is judged by learner manual review. The body does not restate them.

## How to work on it

Keep the dataset tiny (about a dozen rows) so the agreement can be verified by hand; use the SQL lessons for one leg and the Pandas comparison-with-SQL page for the other. Seed estimate: 60–120 minutes.

## Resources

- sqlbolt (registry)
- pandas-docs (registry)

## Notes

Soft-edged from the CSV, SQL, and Pandas bands it weaves — prior fluency passes it directly. Whether the two paths were made to genuinely agree, and discrepancies understood, is judgment. Aligned to the canonical node skeleton, 2026-09.
