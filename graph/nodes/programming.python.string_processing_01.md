---
id: programming.python.string_processing_01
title: Clean and process text with string methods
summary: Normalize, split, and measure strings with Python's string methods.
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
- strings
- text
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Clean and process text with string methods

## Learning target

Reach for the right string methods to clean and summarize text — the daily work
of preparing raw data. For the objective gate, define three functions in your
solution script with exactly this behavior:

- `normalize(s)` — return `s` with surrounding whitespace stripped and lower-cased.
- `initials(full_name)` — return dotted, upper-case initials
  (`"Ada Lovelace"` → `"A.L."`), one initial per whitespace-separated name.
- `count_vowels(s)` — return the number of vowels (`a e i o u`, either case) in `s`.

Save your script at `evidence/artifacts/programming/python_string_processing_solution.py`
and submit it.

## Study pointers

The Python Tutorial §3.1.2 "Strings" for slicing and the string-methods table in
the library reference (docs.python.org/3/library/stdtypes.html#string-methods);
Real Python's "Strings and Character Data in Python" for worked transformations.

## Notes

Objective-gated: `evidence/checks/programming.python.string_processing_check.py`
imports the solution and asserts each transformation.
