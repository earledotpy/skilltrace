---
id: programming.python.modules_imports_01
title: Use the standard library through imports
summary: Import and use standard-library modules to accomplish tasks without writing everything by hand.
domain: programming
track: foundational
estimated_effort:
  min_minutes: 30
  max_minutes: 75
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: true
  requires_long_block: false
tags:
- python
- modules
- standard-library
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Use the standard library through imports

## Learning target

Reach for the right standard-library module instead of reinventing it. For the
objective gate, define three functions in your solution script with exactly this
behavior, each backed by a standard-library module:

- `days_between(date1, date2)` — given two `"YYYY-MM-DD"` strings, return the
  whole number of days between them (use `datetime`).
- `sqrt_floor(n)` — return the integer part of the square root of `n` (use `math`).
- `most_common_char(s)` — return the single most frequent character in `s` (use
  `collections.Counter`).

Save your script at `evidence/artifacts/programming/python_modules_imports_solution.py`
and submit it.

## Study pointers

The Python Tutorial §6 "Modules" for `import` mechanics
(docs.python.org/3/tutorial/modules.html); browse the library reference entries
for `datetime`, `math`, and `collections` (docs.python.org/3/library/) to find
the function each task needs.

## Notes

Objective-gated: each stated result is impractical without the right module, so
the checker's assertions stand in for "used the standard library".
