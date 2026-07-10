---
id: programming.python.conditionals_01
title: Use conditionals in Python
summary: Use if, elif, and else statements to control program flow.
domain: programming
track: foundational
roadmap_anchors:
- phase: phase_1
  phase_label: Programming Fundamentals
  month_range: 5-12
  roadmap_topic: Python Foundations
  source_role: reference_only
estimated_effort:
  min_minutes: 45
  max_minutes: 120
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- python
- conditionals
created_at: 2026-06-28
updated_at: 2026-07-06
---

# Use conditionals in Python

## Learning target

Use `if`, `elif`, and `else` to branch on values. For the objective gate, define
three functions in your solution script with exactly this behavior:

- `classify(n)` — return `"negative"`, `"zero"`, or `"positive"` for `n`.
- `is_even(n)` — return `True` when `n` is even, else `False`.
- `larger(a, b)` — return the larger of `a` and `b`.

Save your script at `evidence/artifacts/programming/python_conditionals_solution.py`
and submit it.

## Study pointers

The Python Tutorial §4.1 "if Statements" and §4.4 on comparisons
(docs.python.org/3/tutorial/controlflow.html); Real Python's "Conditional
Statements in Python" for worked branching examples.

## Notes

Objective-gated: the checker exercises every branch of each function, so a
missed `elif` or a wrong comparison is rejected.
