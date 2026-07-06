---
id: programming.python.comprehensions_01
title: Transform sequences with comprehensions
summary: Use list and dictionary comprehensions to map and filter data concisely.
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
- comprehensions
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Transform sequences with comprehensions

## Learning target

Map and filter a sequence into a new list or dict with a comprehension. For the
objective gate, define three functions in your solution script with exactly this
behavior:

- `evens(nums)` — return a list of the even numbers from `nums`, in order.
- `square_map(nums)` — return a dict mapping each number to its square.
- `long_words(words, min_len)` — return a list of the words whose length is at
  least `min_len`, in order.

Save your script at `evidence/artifacts/programming/python_comprehensions_solution.py`
and submit it.

## Study pointers

The Python Tutorial §5.1.3 "List Comprehensions" and §5.5 for dict
comprehensions (docs.python.org/3/tutorial/datastructures.html); Real Python's
"When to Use a List Comprehension in Python" for the map/filter mental model.

## Notes

Objective-gated: the checker asserts behavior, not syntax — but each stated
result is the natural product of a comprehension over the input.
