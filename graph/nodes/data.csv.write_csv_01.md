---
id: data.csv.write_csv_01
title: Write rows to a CSV file
summary: Write a list of records to a well-formed CSV with the csv module.
domain: data
track: foundational
estimated_effort:
  min_minutes: 30
  max_minutes: 60
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: true
  requires_long_block: false
tags:
- data
- csv
- writing
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Write rows to a CSV file

## Learning target

Turn in-memory records into a CSV another program can read back. For the
objective gate, define one function in your solution script:

- `write_rows(path, rows)` — write `rows` (a list of dicts that share the same
  keys) to a CSV at `path`, with the keys as a header row.

Save your script at `evidence/artifacts/data/csv_write_csv_solution.py` and
submit. The gate round-trips your output back through `csv.DictReader`, so a
missing header row or a mangled delimiter is caught.

## Study pointers

The Python `csv` module docs (docs.python.org/3/library/csv.html) for
`csv.writer` / `csv.DictWriter` and the `newline=""` file argument that avoids
blank rows on Windows; Real Python's "Reading and Writing CSV Files in Python"
for worked writer examples.

## Notes

Objective-gated: the checker writes with your function, reads the file back with
the standard library, and asserts it recovers exactly the rows written.
