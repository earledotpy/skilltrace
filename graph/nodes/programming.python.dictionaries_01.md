---
id: programming.python.dictionaries_01
title: Store and look up data with Python dictionaries
summary: Build, index, and transform key-value dictionaries.
domain: programming
track: foundational
estimated_effort:
  min_minutes: 45
  max_minutes: 90
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- python
- dictionaries
- data-structures
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Store and look up data with Python dictionaries

## Learning target

Create dictionaries, read and write values by key, and build one up from data.
For the objective gate, define three functions in your solution script with
exactly this behavior:

- `word_count(text)` — return a dict mapping each whitespace-separated word to
  the number of times it appears (`"a b a"` → `{"a": 2, "b": 1}`).
- `get_or_default(d, key, default)` — return `d[key]` if the key is present,
  otherwise `default`.
- `invert(d)` — return a new dict with keys and values swapped.

Save your script at `evidence/artifacts/programming/python_dictionaries_solution.py`
and submit it.

## Study pointers

The Python Tutorial §5.5 "Dictionaries" (docs.python.org/3/tutorial/datastructures.html)
for the core operations; Real Python's "Dictionaries in Python" for building and
iterating dicts with runnable examples.

## Notes

Objective-gated: `evidence/checks/programming.python.dictionaries_check.py` imports
the solution and asserts each function's stated result.
