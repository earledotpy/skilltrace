---
id: programming.python.functions_01
title: Define and call Python functions
summary: Write reusable functions with parameters and return values.
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
- functions
created_at: 2026-06-28
updated_at: 2026-07-06
---

# Define and call Python functions

## Learning target

Write reusable functions with parameters and return values. For the objective
gate, define three functions in your solution script with exactly this behavior:

- `rectangle_area(width, height)` — return the area (`width * height`).
- `celsius_to_fahrenheit(c)` — return the Fahrenheit temperature (`c * 9/5 + 32`).
- `greet(name)` — return the string `"Hello, <name>!"` for the given name.

Save your script at `evidence/artifacts/programming/python_functions_solution.py`
and submit it; the gate runs the shipped checker against these three functions.

## Study pointers

The Python Tutorial §4.7–4.8 "Defining Functions" (docs.python.org/3/tutorial/controlflow.html)
for parameters and return values; Real Python's "Defining Your Own Python Function"
for worked examples with runnable code.

## Notes

Objective-gated: the checker `evidence/checks/programming.python.functions_check.py`
imports the solution and asserts each function's stated return value.
