---
id: ml.regression.linear_regression_01
title: Train and interpret linear regression
summary: Train linear regression with gradient descent intuition, read loss curves, and compare against a sklearn baseline.
domain: ml
track: foundational
roadmap_anchors:
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 2-3
  roadmap_topic: Linear regression, loss functions
  source_role: reference_only
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 2-3
  roadmap_topic: ML Specialization Course 1 (linear regression, cost, gradient descent, Python/sklearn)
  source_role: reference_only
source_metadata:
  primary_source: Google ML Crash Course (2024 refresh)
  canonical_url: https://developers.google.com/machine-learning/crash-course
  source_version: 2024-11-12 refresh; verified 2026-08-08 per docs/roadmap/phase-2-classical-ml.md
  supporting_sources:
  - Andrew Ng Machine Learning Specialization (Python) — https://www.coursera.org/specializations/machine-learning-introduction
  - ISLP Python edition — https://www.statlearning.com/
  - Kaggle Learn Intro to Machine Learning — https://www.kaggle.com/learn/intro-to-machine-learning
regeneration_key: mlcc-2024-11-12/linear-regression-01
section_provenance:
- source: Google ML Crash Course
  section: Linear Regression module (loss, gradient descent, learning rate)
- source: Andrew Ng Machine Learning Specialization (Python)
  section: Course 1 (linear regression model, cost function, gradient descent in Python)
- source: ISLP (Python edition)
  section: Chapter 3 (linear regression labs, Python)
- source: Kaggle Learn
  section: Intro to Machine Learning (model validation exercise flow)
estimated_effort:
  min_minutes: 90
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- ml
- regression
- gradient-descent
- sklearn
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Train and interpret linear regression

## What this skill is

Train linear regression in NumPy with gradient descent, compare it to a sklearn `LinearRegression` baseline on the same split, and read the loss trajectory. The learner can also say in one paragraph what learning-rate-too-high versus too-low looks like and how L1/L2 regularization changes the weights.

## Why this skill

Linear regression is the readable entry point to the whole classical-ML band: loss surfaces, gradients, and regularization all show up here in their simplest form. A learner who can train it from scratch and against a baseline can trust what every later model comparison means.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Study the loss and gradient-descent intuition, then practice: implement gradient descent in NumPy, compare to the sklearn baseline on the same split, and plot or describe the loss trajectory. The ISLP labs give the statistical reading (coefficients, residuals) and the Kaggle Learn lesson gives the train/validate loop in notebooks. Seed estimate: 90–180 minutes.

## Resources

- mlcc-crash-course (registry)
- ng-ml-specialization-python (registry)
- islp-python-edition (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight.

NumPy from-scratch implementation is the Phase 2 checkpoint skill (`ml-from-scratch` in `docs/roadmap/phase-2-classical-ml.md`). Builds on the gradient intuition from `math.calculus.gradient_intuition_01` (soft edge only). Primary source: Google ML Crash Course (2024 refresh), Linear Regression module; supporting sections: Ng MLS Course 1, ISLP Chapter 3 (Python labs), Kaggle Learn Intro; regeneration key `mlcc-2024-11-12/linear-regression-01`. All references are `reference_only` anchors. Aligned to the canonical node skeleton, 2026-09.
