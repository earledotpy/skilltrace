---
id: ml.trees.ensembles_01
title: Train tree ensembles and control overfitting
summary: Train decision trees, random forests, and gradient boosting with sklearn and explain the overfitting controls.
domain: ml
track: foundational
roadmap_anchors:
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 5-6
  roadmap_topic: Decision trees, random forests, gradient boosting
  source_role: reference_only
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 5-6
  roadmap_topic: ML Specialization Course 2 (trees, ensembles, boosting)
  source_role: reference_only
source_metadata:
  primary_source: Google ML Crash Course (2024 refresh)
  canonical_url: https://developers.google.com/machine-learning/crash-course
  source_version: 2024-11-12 refresh; verified 2026-08-08 per docs/roadmap/phase-2-classical-ml.md
  supporting_sources:
  - Andrew Ng Machine Learning Specialization (Python) — https://www.coursera.org/specializations/machine-learning-introduction
  - ISLP Python edition — https://www.statlearning.com/
  - Kaggle Learn Intermediate Machine Learning — https://www.kaggle.com/learn/intermediate-machine-learning
regeneration_key: mlcc-2024-11-12/trees-ensembles-01
section_provenance:
- source: Google ML Crash Course
  section: Decision Trees + Ensembles modules (splits, bagging, boosting intuition)
- source: Andrew Ng Machine Learning Specialization (Python)
  section: Course 2 (decision trees, random forests, boosting in Python/sklearn)
- source: ISLP (Python edition)
  section: "Chapter 8 (tree-based methods labs — trees, forests, boosting in Python)"
- source: Kaggle Learn
  section: Intermediate Machine Learning (XGBoost exercise, categorical handling)
estimated_effort:
  min_minutes: 90
  max_minutes: 240
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- ml
- trees
- random-forest
- boosting
- sklearn
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Train tree ensembles and control overfitting

## Learning target

On one tabular dataset, train a decision tree, a random forest, and a gradient
boosting model (sklearn), compare validation scores, and explain — with the
depth/learning-rate/ subsample knobs you actually set — how each ensemble
controls the bias-variance tradeoff you diagnosed in
`ml.evaluation.validation_metrics_01`.

## Study pointers

Google MLCC Trees + Ensembles modules for split/bagging/boosting intuition; Ng
MLS Course 2 for the sklearn-level practice; ISLP Chapter 8 Python labs for the
statistical reading (pruning, bagging, random forests, boosting); Kaggle Learn
Intermediate XGBoost exercise for the competition-grade defaults.

## Source provenance

Primary: Google ML Crash Course — Trees + Ensembles modules. Regeneration key:
`mlcc-2024-11-12/trees-ensembles-01`. Supporting: Ng MLS Course 2; ISLP
Chapter 8; Kaggle Learn Intermediate. All references `reference_only`.

## Notes

Tabular-data workhorse for the Phase 2 competitions; direct prerequisite of
both practice nodes. No fast.ai dependency — v1.8 sources are the locked four
only (fast.ai stays in `docs/roadmap/phase-2-classical-ml.md` as curriculum
background, not a v1.8 seed source).
