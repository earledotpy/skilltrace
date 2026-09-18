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

## What this skill is

Wrap an operation that might fail in try/except, catch the specific error, and return a fallback rather than letting the program crash.

## Why this skill

Programs that crash on the first bad input never ship; catching the specific error is what makes them robust.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.programming.python.exceptions`); Evidence is checked by running your submission against its objective gate. The body does not restate them.

## How to work on it

Study the exception-handling form first, then practise the happy path and the failing path side by side until catching is automatic. Seed estimate: 30–60 minutes.

## Resources

- python-tutorial (registry)
- runestone-py4e (registry)

## Notes

The gate exercises the happy path and the failing path, so letting the exception escape or returning the wrong fallback is rejected. Aligned to the canonical node skeleton, 2026-09.
