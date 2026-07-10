---
id: data.sql.filtering_sorting_01
title: Filter and sort query results
summary: Restrict rows with WHERE and order them with ORDER BY.
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
- filtering
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Filter and sort query results

## Learning target

Narrow a result set to the rows that matter and put them in a useful order,
against the same seeded dataset as the other SQL nodes:

- `employees(id, name, department_id, salary, hire_year)`
- `departments(id, name, location)`

Write one SQL statement that returns the `name` of every employee earning more
than 90000, ordered so the highest salary comes first. Save it at
`evidence/artifacts/data/sql_filtering_sorting_solution.sql` and submit.

## Study pointers

SQLBolt lessons 2–3 (sqlbolt.com) for `WHERE` predicates and `ORDER BY`; Mode's
SQL Tutorial "Intermediate SQL → WHERE / ORDER BY / LIMIT" for comparison and
sort operators with runnable examples.

## Notes

Objective-gated: both the filter and the sort are the skill, so the checker
compares the returned names in order — a missing `ORDER BY` or the wrong
direction rejects.
