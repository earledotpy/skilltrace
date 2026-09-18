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

## What this skill is

Write data to a text file and read it back in Python, so what one function writes the other recovers exactly.

## Why this skill

File round-trips underlie CSV work, artifacts, and every later skill that persists data to disk.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.programming.python.files`); Evidence is checked by running your submission against its objective gate. The body does not restate them.

## How to work on it

Study the open-and-with pattern and the read/write methods first, then practise a write-then-read round-trip until the pair agrees exactly. Seed estimate: 45–120 minutes.

## Resources

- python-tutorial (registry)
- automate-the-boring-stuff (registry)

## Notes

A mismatched newline or encoding choice between the two halves is the skill failing, so agreement is the point. Aligned to the canonical node skeleton, 2026-09.
