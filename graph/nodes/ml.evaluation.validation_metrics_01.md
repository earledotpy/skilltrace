---
id: ml.evaluation.validation_metrics_01
title: Validate models and diagnose bias-variance
summary: Run train/validation/test discipline, read validation curves, and apply regularization against overfitting.
domain: ml
track: foundational
roadmap_anchors:
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 4-5
  roadmap_topic: Model evaluation, validation, bias-variance, regularization
  source_role: reference_only
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 4-5
  roadmap_topic: ML Specialization Course 2 Week 3 (bias/variance, regularization, evaluation)
  source_role: reference_only
source_metadata:
  primary_source: Google ML Crash Course (2024 refresh)
  canonical_url: https://developers.google.com/machine-learning/crash-course
  source_version: 2024-11-12 refresh; verified 2026-08-08 per docs/roadmap/phase-2-classical-ml.md
  supporting_sources:
  - Andrew Ng Machine Learning Specialization (Python) — https://www.coursera.org/specializations/machine-learning-introduction
  - ISLP Python edition — https://www.statlearning.com/
  - Kaggle Learn Intermediate Machine Learning — https://www.kaggle.com/learn/intermediate-machine-learning
regeneration_key: mlcc-2024-11-12/validation-metrics-01
section_provenance:
- source: Google ML Crash Course
  section: Evaluation + Validation modules (metrics, test-set discipline, representation)
- source: Andrew Ng Machine Learning Specialization (Python)
  section: Course 2 Week 3 (bias/variance diagnosis, regularization, train/dev/test methodology)
- source: ISLP (Python edition)
  section: "Chapter 5 (resampling — cross-validation, bootstrap; Python labs)"
- source: Kaggle Learn
  section: Intermediate Machine Learning (missing values, categoricals, pipelines, cross-validation, XGBoost intro)
estimated_effort:
  min_minutes: 90
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- ml
- validation
- metrics
- bias-variance
- regularization
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Validate models and diagnose bias-variance

## What this skill is

On a provided overfit/underfit learning-curve pair, diagnose bias versus variance, prescribe the matching fix (more data, simpler model, L1/L2, early stopping, cross-validation), and state when to use accuracy versus F1 versus ROC-AUC versus RMSE with one real example each.

## Why this skill

Evaluation discipline decides whether every later model comparison means anything; a mis-diagnosed curve or a leaked metric wastes the whole chain downstream. A learner who can diagnose and prescribe can trust — and defend — their numbers.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Study the Evaluation + Validation modules for test-set discipline and metrics, and the bias/variance material for the diagnosis. Practice the curve diagnosis, then use the ISLP cross-validation and bootstrap labs and the Kaggle Learn Intermediate lessons for pipeline-level validation practice. Seed estimate: 90–180 minutes.

## Resources

- mlcc-crash-course (registry)
- ng-ml-specialization-python (registry)
- islp-python-edition (registry)
- kaggle-learn-ml (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight.

Direct home of the Phase 2 conceptual checkpoint items (bias-variance curve, overfitting signs, test-set sacredness, leakage examples, metric choice). Primary source: Google ML Crash Course — Evaluation + Validation modules; supporting: Ng MLS Course 2 Week 3, ISLP Chapter 5, Kaggle Learn Intermediate; regeneration key `mlcc-2024-11-12/validation-metrics-01`. All references `reference_only`. Aligned to the canonical node skeleton, 2026-09.
