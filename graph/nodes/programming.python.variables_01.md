---
id: programming.python.variables_01
title: Use variables and expressions in Python
summary: Create variables, assign values, and use expressions to compute simple results.
domain: programming
track: foundational
roadmap_anchors:
- phase: phase_1
  phase_label: Programming Fundamentals
  month_range: 5-12
  roadmap_topic: Python Foundations
  source_role: reference_only
estimated_effort:
  min_minutes: 30
  max_minutes: 90
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: true
  requires_long_block: false
tags:
- python
- variables
created_at: 2026-06-28
updated_at: 2026-07-06
---

# Use variables and expressions in Python

## Learning target

Create variables, assign values, and compute results with expressions. For the
objective gate, define three module-level variables in your solution script,
each the result of an expression:

- `seconds_per_day` — the number of seconds in a day (`24 * 60 * 60` → `86400`).
- `total_cost` — for a price of `4.90`, quantity `5`, and tax `2.00`, the total
  `price * quantity + tax` (`26.5`).
- `average` — the mean of `10`, `20`, and `30` (`20.0`).

Save your script at `evidence/artifacts/programming/python_variables_solution.py`
and submit it.

## Study pointers

The Python Tutorial §3.1.1 "Numbers" and §3.1.3 "Using Python as a Calculator"
(docs.python.org/3/tutorial/introduction.html); Real Python's "Variables in
Python" for naming and assignment.

## Notes

Objective-gated: `evidence/checks/programming.python.variables_check.py` imports
the solution and asserts each variable holds the stated value.
