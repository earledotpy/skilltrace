---
id: portfolio.project.data_cleaning_tool_01
title: Build a data-cleaning tool portfolio project
summary: Build a small, reusable Python tool that reads a messy CSV, applies documented cleaning rules, writes a clean CSV, and ships with a README and honest write-up.
domain: programming
track: portfolio
estimated_effort:
  min_minutes: 120
  max_minutes: 300
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- portfolio
- python
- data
- git
created_at: 2026-07-07
updated_at: 2026-07-07
---

# Build a data-cleaning tool portfolio project

## Learning target

Build a command-line or importable Python tool that takes a messy CSV, applies
a set of cleaning rules you chose and can defend (which rows to drop, which
values to fill, which columns to coerce), and writes out a clean CSV. Ship it as
a small repository: working code, a README another person can follow to run it,
and a short honest write-up of the cleaning decisions and their trade-offs.

## Study pointers

- Real Python's articles on writing CLI tools and on reading/writing CSV files
  cover the mechanics; the Pandas docs are an alternative engine if you reach for
  a DataFrame.
- Decide your cleaning rules from the data, not from a template — the write-up
  is where you justify them.

## Notes

Hard-edged only from the code skills the working tool is built from (cleaning a
CSV, and the file handling that reads and writes it) — mechanically enabling.
Git, the README, and the write-up are packaging around the deliverable, so those
edges are soft. Manual-gated: working code plus a readable README plus an honest
write-up is judged, never proxied by one command.
