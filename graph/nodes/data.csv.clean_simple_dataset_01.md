---
id: data.csv.clean_simple_dataset_01
title: Clean a simple CSV dataset
summary: Handle missing or malformed values in a small CSV file.
domain: data
track: foundational
roadmap_anchors:
- phase: phase_1
  phase_label: Programming Fundamentals
  month_range: 8-12
  roadmap_topic: Data Cleaning
  source_role: reference_only
estimated_effort:
  min_minutes: 60
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- data
- csv
- cleaning
created_at: 2026-06-28
updated_at: 2026-07-06
---

# Clean a simple CSV dataset

## Learning target

Take a small, messy CSV — missing values, stray whitespace, wrong types — and
produce a clean version, deciding for each problem whether to drop, fill, or
coerce, and writing down why. The evidence is your cleaning script plus a short
note on the choices you made.

## Study pointers

The Pandas "Working with missing data" user guide
(pandas.pydata.org/docs/user_guide/missing_data.html) for `dropna` / `fillna`
and when each is appropriate; Real Python's "Pythonic Data Cleaning With pandas
and NumPy" for a worked cleaning pass over a real dataset.

## Notes

Manual-gated by design: "clean" is a judgment call — which imputation, whether
to drop a row — so the gate reads your script and your rationale rather than
comparing to one blessed output. See docs/curriculum-authoring.md (the gate
honesty rule) for why this stays manual while `read_csv` is objective.

