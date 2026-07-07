---
id: data.csv.read_csv_01
title: Read a CSV file with Python
summary: Load a simple CSV file and inspect rows and columns.
domain: data
track: foundational
roadmap_anchors:
- phase: phase_1
  phase_label: Programming Fundamentals
  month_range: 8-12
  roadmap_topic: CSV and Data Handling
  source_role: reference_only
estimated_effort:
  min_minutes: 45
  max_minutes: 120
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- data
- csv
- python
created_at: 2026-06-28
updated_at: 2026-07-06
---

# Read a CSV file with Python

## Learning target

Open a CSV file and turn its rows into records you can work with. For the
objective gate, define one function in your solution script:

- `read_rows(path)` — open the CSV at `path` and return its data rows as a list
  of dicts, each keyed by the header, in file order.

A three-row `people.csv` (columns `name, age, city`) ships at
`evidence/checks/data/datasets/people.csv` — read that same file while you
develop. Save your script at
`evidence/artifacts/data/csv_read_csv_solution.py` and submit.

## Study pointers

The Python `csv` module docs (docs.python.org/3/library/csv.html) for
`csv.reader` / `csv.DictReader` and the `newline=""` file argument; Real
Python's "Reading and Writing CSV Files in Python" for the header-as-keys
pattern with worked examples.

## Notes

Objective-gated: the checker runs `read_rows` on the shipped `people.csv` and
asserts it returns one header-keyed dict per data row (values stay strings, as
`csv` reads them). Retrofitted from a manual gate — reading a CSV into records
has one correct result, so exit-0 is honestly the skill.

