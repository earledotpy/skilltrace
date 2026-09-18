---
id: programming.python.reading_errors_01
title: Read a Python traceback to locate a failure
summary: Given a failing program, read its traceback to name the error type, find the failing line, and form the next debugging step — a focused rescue drill, not a general debugging course.
domain: programming
track: remediation
estimated_effort:
  min_minutes: 20
  max_minutes: 45
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: true
  requires_long_block: false
tags:
- remediation
- python
- debugging
created_at: 2026-07-07
updated_at: 2026-07-07
---

# Read a Python traceback to locate a failure

## What this skill is

Given a program that raises, read the traceback from the bottom up: name the exception type, identify the exact line and call that raised it, and state the one next thing to check.

## Why this skill

The narrow skill here is reading the message the interpreter already gave instead of guessing, which is what turns being stuck into a next step.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.programming.python.reading_errors`); Evidence is judged by learner manual review. The body does not restate them.

## How to work on it

Study the exception vocabulary first, then collect three tracebacks from recent real errors and practise the bottom-up read on those. Seed estimate: 20–45 minutes.

## Resources

- python-tutorial (registry)
- python-tutor (registry)

## Notes

A remediation node homed in the Python domain and deliberately narrower than the errors-debugging learning node: a traceback-reading drill that surfaces when you are stuck. Its role lives in its remediation edges and track label. Aligned to the canonical node skeleton, 2026-09.
