---
id: data.sql.select_basics_01
title: Query rows and columns with SELECT
summary: Retrieve specific columns from a table with a basic SELECT statement.
domain: data
track: foundational
estimated_effort:
  min_minutes: 20
  max_minutes: 45
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: true
  requires_long_block: false
tags:
- sql
- data
- select
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Query rows and columns with SELECT

## Learning target

Read data out of a relational table by naming the columns you want. The
objective gate runs your query against a fixed two-table dataset:

- `employees(id, name, department_id, salary, hire_year)`
- `departments(id, name, location)`

with eight employees across three departments.

Write one SQL statement that returns the `name` and `salary` of every employee.
Save it at `evidence/artifacts/data/sql_select_basics_solution.sql` and submit.

## Study pointers

SQLBolt lessons 1–2 (sqlbolt.com) for `SELECT` and column projection, done in
the browser against a live table; Mode's SQL Tutorial "Basic SQL → SELECT" for
the same idea with worked examples.

## Notes

Objective-gated: the shipped checker runs your statement against a seeded
in-memory SQLite database and compares the returned rows (order-insensitive) to
the expected `(name, salary)` for all eight employees.
