---
id: data.sql.joins_01
title: Combine tables with an inner join
summary: Join two related tables on a key to combine their columns.
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
- sql
- data
- joins
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Combine tables with an inner join

## Learning target

Bring columns from two tables together by matching a shared key — the operation
that turns normalized tables back into an analysis-ready view. Against the same
seeded dataset:

- `employees(id, name, department_id, salary, hire_year)`
- `departments(id, name, location)`

Write one SQL statement that returns each employee's `name` paired with their
department's `name`, matching `employees.department_id` to `departments.id`.
Save it at `evidence/artifacts/data/sql_joins_solution.sql` and submit.

## Study pointers

SQLBolt lessons 4–5 (sqlbolt.com) for `INNER JOIN` and join keys, practiced
against live tables; Mode's SQL Tutorial "Intermediate SQL → JOINs" for the
`ON` clause and how a join expands rows.

## Notes

Objective-gated: the checker compares the eight `(employee, department)` pairs
(order-insensitive). A cross join (every name against every department) produces
the wrong row count and rejects.
