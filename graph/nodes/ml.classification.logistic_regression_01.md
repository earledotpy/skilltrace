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

## What this skill is

Train logistic regression from scratch and with sklearn, and choose accuracy vs F1 vs ROC-AUC for a given class balance, with a threshold-tuning note.

## Why this skill

Classification is the first place where the default metric lies: accuracy looks fine while the model ignores the minority class. A learner who can train a simple classifier and pick the metric that matches the class balance reads model quality honestly before moving to trees and tuning.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Implement the sigmoid, log-loss, and gradient-descent loop once from scratch, compare against a library baseline, then practice metric choice on a balanced versus an imbalanced scenario with one line of justification each. Seed estimate: 90–180 minutes.

## Resources

- mlcc-crash-course (registry)
- ng-ml-specialization-python (registry)
- islp-python-edition (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight. Aligned to the canonical node skeleton, 2026-09.
