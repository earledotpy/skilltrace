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

## What this skill is

Take a small, messy CSV — missing values, stray whitespace, wrong types — and produce a clean version, deciding for each problem whether to drop, fill, or coerce, and writing down why.

## Why this skill

‘Clean’ is a judgment call, so the rationale is part of the deliverable: which imputation, whether to drop a row, and why.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.data.csv.clean_simple_dataset`); Evidence is judged by learner manual review. The body does not restate them.

## How to work on it

Study the missing-data options first, then make one cleaning pass over a real messy file, recording each drop, fill, or coerce decision as you go. Seed estimate: 60–180 minutes.

## Resources

- pandas-docs (registry)
- automate-the-boring-stuff (registry)

## Notes

Manual-gated by design: ‘clean’ is a judgment call, so the gate reads the script and the rationale rather than comparing to one blessed output. Aligned to the canonical node skeleton, 2026-09.
