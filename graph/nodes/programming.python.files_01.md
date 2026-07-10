---
id: programming.python.files_01
title: Read and write files in Python
summary: Use Python to read from and write to local text files.
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
- files
created_at: 2026-06-28
updated_at: 2026-07-06
---

# Read and write files in Python

## Learning target

Write data to a text file and read it back. For the objective gate, define two
functions in your solution script with exactly this behavior:

- `write_lines(path, lines)` — write each string in `lines` to the file at
  `path`, one per line.
- `read_lines(path)` — return the file's lines as a list of strings, without
  trailing newlines.

Save your script at `evidence/artifacts/programming/python_files_solution.py` and
submit it. The gate round-trips a list of lines through a temporary file using
your two functions, so they must agree: what `write_lines` writes, `read_lines`
must recover exactly.

## Study pointers

The Python Tutorial §7.2 "Reading and Writing Files"
(docs.python.org/3/tutorial/inputoutput.html) for `open`, `with`, and the read/
write methods; Real Python's "Reading and Writing Files in Python" for patterns.

## Notes

Objective-gated: the checker asserts a write→read round-trip, so a mismatched
newline or encoding choice between the two functions is rejected.
