---
id: data.sql.aggregation_01
title: Summarize groups with GROUP BY
summary: Compute per-group counts and averages with aggregate functions.
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
- sql
- data
- aggregation
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Summarize groups with GROUP BY

## Learning target

Collapse many rows into per-group summaries — the daily bread of exploratory
data work — against the same seeded dataset:

- `employees(id, name, department_id, salary, hire_year)`
- `departments(id, name, location)`

Write one SQL statement that returns, for each department, its `department_id`,
the number of employees in it, and their average salary. Save it at
`evidence/artifacts/data/sql_aggregation_solution.sql` and submit.

## Study pointers

SQLBolt lessons 6–7 (sqlbolt.com) for aggregate functions and `GROUP BY`;
Mode's SQL Tutorial "Intermediate SQL → Aggregate functions / GROUP BY" for
`COUNT`, `AVG`, and grouping with worked queries.

## Notes

Objective-gated: the checker compares the three per-department summary rows
(order-insensitive). A missing `GROUP BY` collapses to one row and rejects; so
does the wrong aggregate (e.g. `SUM` for `AVG`).
