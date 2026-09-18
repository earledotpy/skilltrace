---
id: math.linear_algebra.matrix_multiplication_01
title: Multiply two matrices
summary: Compute a matrix-matrix product and interpret it as composing two transformations.
domain: mathematics
track: foundational
estimated_effort:
  min_minutes: 45
  max_minutes: 90
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- math
- linear-algebra
- matrix-multiplication
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Multiply two matrices

## What this skill is

Compute the product of two conformable matrices by the row-by-column rule, check dimension compatibility first, and interpret the product as applying one transformation after another.

## Why this skill

Composition of transformations is why stacked layers work, and dimension bookkeeping here prevents most later tensor-shape bugs.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.math.linear_algebra.matrix_multiplication`); Evidence is judged by learner manual review. The body does not restate them.

## How to work on it

Learn multiplication-as-composition first, then work matrix-product problems that force the compatibility check every time. Seed estimate: 45–90 minutes.

## Resources

- 3blue1brown-essence-linear-algebra (registry)
- khan-linear-algebra (registry)

## Notes

Composition of transformations is why stacked layers work; dimension bookkeeping here prevents most later tensor-shape bugs. Aligned to the canonical node skeleton, 2026-09.
