---
id: ml.classification.logistic_regression_01
title: Train and evaluate logistic regression classifiers
summary: Train logistic regression from scratch and with sklearn, and choose accuracy vs F1 vs ROC-AUC for a given class balance.
domain: ml
track: foundational
roadmap_anchors:
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 3-4
  roadmap_topic: Classification, logistic regression
  source_role: reference_only
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 3-4
  roadmap_topic: ML Specialization Courses 1-2 (classification, logistic loss, regularization)
  source_role: reference_only
source_metadata:
  primary_source: Google ML Crash Course (2024 refresh)
  canonical_url: https://developers.google.com/machine-learning/crash-course
  source_version: 2024-11-12 refresh; verified 2026-08-08 per docs/roadmap/phase-2-classical-ml.md
  supporting_sources:
  - Andrew Ng Machine Learning Specialization (Python) — https://www.coursera.org/specializations/machine-learning-introduction
  - ISLP Python edition — https://www.statlearning.com/
  - Kaggle Learn Intro to Machine Learning — https://www.kaggle.com/learn/intro-to-machine-learning
regeneration_key: mlcc-2024-11-12/logistic-regression-01
section_provenance:
- source: Google ML Crash Course
  section: Logistic Regression + Classification modules (sigmoid, log-loss, thresholding)
- source: Andrew Ng Machine Learning Specialization (Python)
  section: Course 1 Week 3 + Course 2 (classification, logistic regression, regularization)
- source: ISLP (Python edition)
  section: "Chapter 4 (classification labs — logistic regression, LDA/QDA in Python)"
- source: Kaggle Learn
  section: Intro to Machine Learning (categorical handling, model comparison exercises)
estimated_effort:
  min_minutes: 90
  max_minutes: 180
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- ml
- classification
- logistic-regression
- metrics
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Train and evaluate logistic regression classifiers

## Learning target

Implement logistic regression in NumPy (sigmoid, log-loss, gradient descent),
match it against a sklearn baseline, and for two given scenarios (balanced vs
10:1 imbalanced) pick the right metric — accuracy vs F1 vs ROC-AUC — with a
one-line justification each, plus a threshold-tuning note.

## Study pointers

Google MLCC Logistic Regression + Classification modules for sigmoid/log-loss;
Ng MLS Course 1 Week 3 and Course 2 for regularized logistic regression in
Python; ISLP Chapter 4 Python labs for the classification reading; Kaggle Learn
Intro for categorical-feature handling.

## Source provenance

Primary: Google ML Crash Course (2024 refresh) — Logistic Regression and
Classification modules. Regeneration key:
`mlcc-2024-11-12/logistic-regression-01`. Supporting: Ng MLS Courses 1–2; ISLP
Chapter 4; Kaggle Learn Intro. All references `reference_only`.

## Notes

Feeds the metrics half of the Phase 2 conceptual checkpoint (accuracy vs F1 vs
ROC-AUC vs RMSE). Manual or objective gate per slot-builder choice; either way
AI is never the acceptance authority.
