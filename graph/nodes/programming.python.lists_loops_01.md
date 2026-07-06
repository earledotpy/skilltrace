---
id: programming.python.lists_loops_01
title: Use lists and loops in Python
summary: Represent repeated values and process them with loops.
domain: programming
track: foundational
roadmap_anchors:
- phase: phase_1
  phase_label: Programming Fundamentals
  month_range: 5-12
  roadmap_topic: Python Foundations
  source_role: reference_only
estimated_effort:
  min_minutes: 60
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- python
- lists
- loops
created_at: 2026-06-28
updated_at: 2026-07-06
---

# Use lists and loops in Python

## Learning target

Hold repeated values in a list and process them with a loop. For the objective
gate, define three functions in your solution script with exactly this behavior:

- `sum_list(nums)` — return the total of the numbers (`0` for an empty list).
- `count_evens(nums)` — return how many of the numbers are even.
- `squares_up_to(n)` — return `[1, 4, 9, ..., n*n]` for `1` through `n`.

Save your script at `evidence/artifacts/programming/python_lists_loops_solution.py`
and submit it.

## Study pointers

The Python Tutorial §4.2–4.3 "for Statements" and "range", and §5.1 on lists
(docs.python.org/3/tutorial/controlflow.html); Real Python's "Python for Loops"
for accumulation patterns.

## Notes

Objective-gated: `evidence/checks/programming.python.lists_loops_check.py` asserts
each function over sample inputs, including the empty-list edge case.
