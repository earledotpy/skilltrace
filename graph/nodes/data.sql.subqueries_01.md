---
id: data.sql.subqueries_01
title: Filter against a subquery
summary: Use a nested SELECT to compute a threshold you filter against.
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
- subqueries
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Filter against a subquery

## Learning target

Compute a value with one query and filter another query against it — the move
behind "above average", "more than the median", and countless real questions.
Against the same seeded dataset:

- `employees(id, name, department_id, salary, hire_year)`
- `departments(id, name, location)`

Write one SQL statement that returns the `name` of every employee who earns more
than the company-wide average salary, computing that average with a subquery
rather than hardcoding it. Save it at
`evidence/artifacts/data/sql_subqueries_solution.sql` and submit.

## Study pointers

Mode's SQL Tutorial "Advanced SQL → Subqueries" for a nested `SELECT` in a
`WHERE` clause with worked examples; the SQLite `SELECT` documentation
(sqlite.org/lang_select.html) for how a scalar subquery evaluates.

## Notes

Objective-gated: the checker compares the four names above the company average
(order-insensitive). The gate can only observe the returned rows, so a hardcoded
threshold that happens to match is accepted — the honesty rule governs the
author shipping no proxy, not adversarial-proofing a single honest learner.
