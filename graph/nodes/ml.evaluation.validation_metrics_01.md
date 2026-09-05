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

## Learning target

On a provided overfit/underfit learning-curve pair, diagnose bias vs variance,
prescribe the matching fix (more data, simpler model, L1/L2, early stopping,
cross-validation), and state when to use accuracy vs F1 vs ROC-AUC vs RMSE with
one real example each — the Phase 2 conceptual checkpoint wording.

## Study pointers

Google MLCC Evaluation + Validation modules for test-set discipline and
metrics; Ng MLS Course 2 Week 3 for bias/variance diagnosis and regularization;
ISLP Chapter 5 Python labs for cross-validation and bootstrap; Kaggle Learn
Intermediate for pipeline-level validation practice.

## Source provenance

Primary: Google ML Crash Course — Evaluation + Validation modules.
Regeneration key: `mlcc-2024-11-12/validation-metrics-01`. Supporting: Ng MLS
Course 2 Week 3; ISLP Chapter 5; Kaggle Learn Intermediate. All references
`reference_only`.

## Notes

Direct home of the Phase 2 conceptual checkpoint items (bias-variance curve,
overfitting signs, test-set sacredness, leakage examples, metric choice).
