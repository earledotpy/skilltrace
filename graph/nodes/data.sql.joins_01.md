---
id: data.sql.joins_01
title: Combine tables with an inner join
summary: Join two related tables on a key to combine their columns.
domain: data
track: foundational
estimated_effort:
  min_minutes: 45
  max_minutes: 90
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- sql
- data
- joins
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Combine tables with an inner join

## What this skill is

Combine two related tables with an inner join, matching a shared key so each row pairs columns from both tables.

## Why this skill

Real data arrives normalized across tables; the join turns those tables back into one analysis-ready view. Matching on the key — rather than pairing every row with every row — is the whole discipline.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.data.sql.joins`); Evidence is checked by running your submission against its objective gate. The body does not restate them.

## How to work on it

Practice inner joins on live tables, each time naming the key columns on both sides before writing the ON clause. Seed estimate: 45–90 minutes.

## Resources

- sqlbolt (registry)
- select-star-sql (registry)
- sqlite-docs (registry)

## Notes

Aligned to the canonical node skeleton, 2026-09.
