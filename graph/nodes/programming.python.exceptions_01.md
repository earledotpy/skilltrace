---
id: programming.python.exceptions_01
title: Handle errors with try/except
summary: Catch expected exceptions and return a sensible fallback instead of crashing.
domain: programming
track: foundational
estimated_effort:
  min_minutes: 30
  max_minutes: 60
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: true
  requires_long_block: false
tags:
- python
- exceptions
- error-handling
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Handle errors with try/except

## Learning target

Wrap an operation that might fail in `try`/`except`, catch the specific error,
and return a fallback rather than letting the program crash. For the objective
gate, define two functions in your solution script with exactly this behavior:

- `safe_divide(a, b)` — return `a / b`, or `None` when `b` is `0` (catch
  `ZeroDivisionError`).
- `parse_int(s)` — return `int(s)`, or `None` when `s` is not a valid integer
  (catch `ValueError`).

Save your script at `evidence/artifacts/programming/python_exceptions_solution.py`
and submit it.

## Study pointers

The Python Tutorial §8 "Errors and Exceptions", especially §8.3 "Handling
Exceptions" (docs.python.org/3/tutorial/errors.html); Real Python's "Python
Exceptions: An Introduction" for catching specific error types.

## Notes

Objective-gated: the checker calls the happy path *and* the failing path, so a
function that lets the exception escape (or returns the wrong fallback) is
rejected — catching is the substance the gate verifies.
