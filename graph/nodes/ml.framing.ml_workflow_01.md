---
id: ml.framing.ml_workflow_01
title: Frame an ML task and split data without leakage
summary: Frame a supervised task, choose train/validation/test splits, and name two leakage patterns to avoid.
domain: ml
track: foundational
roadmap_anchors:
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 1-2
  roadmap_topic: ML workflow, framing, data prep
  source_role: reference_only
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 1-2
  roadmap_topic: ML Specialization Course 1 Week 1 (supervised learning, regression/classification framing)
  source_role: reference_only
source_metadata:
  primary_source: Google ML Crash Course (2024 refresh)
  canonical_url: https://developers.google.com/machine-learning/crash-course
  source_version: 2024-11-12 refresh; verified 2026-08-08 per docs/roadmap/phase-2-classical-ml.md
  supporting_sources:
  - Andrew Ng Machine Learning Specialization (Python) — https://www.coursera.org/specializations/machine-learning-introduction
  - ISLP Python edition — https://www.statlearning.com/
  - Kaggle Learn Intro to Machine Learning — https://www.kaggle.com/learn/intro-to-machine-learning
regeneration_key: mlcc-2024-11-12/ml-workflow-01
section_provenance:
- source: Google ML Crash Course
  section: Framing + Data Prep modules (ML problem framing, data preparation)
- source: Andrew Ng Machine Learning Specialization (Python)
  section: Course 1 Week 1 (supervised vs unsupervised, regression vs classification)
- source: ISLP (Python edition)
  section: Chapter 1 (Introduction; supervised vs unsupervised)
- source: Kaggle Learn
  section: Intro to Machine Learning, lesson 1 (how models work, basic data exploration)
estimated_effort:
  min_minutes: 60
  max_minutes: 120
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- ml
- framing
- data-split
- leakage
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Frame an ML task and split data without leakage

## Learning target

Given a tabular problem statement, state whether it is supervised (regression or
classification) or unsupervised, propose a train/validation/test split with a
one-line justification for keeping the test set sacred, and name two leakage
patterns (e.g. target-derived features, pre-split imputation/normalization) with
a one-line fix for each.

## Study pointers

Google ML Crash Course Framing + Data Prep modules for the workflow vocabulary;
Ng ML Specialization Course 1 Week 1 for supervised/unsupervised framing; ISLP
Chapter 1 for the statistical framing; Kaggle Learn Intro lesson 1 for the
notebook-level workflow.

## Source provenance

Primary: Google ML Crash Course (2024 refresh),
https://developers.google.com/machine-learning/crash-course —
Framing + Data Prep modules. Regeneration key:
`mlcc-2024-11-12/ml-workflow-01`. Supporting sections: Ng MLS Course 1 Week 1;
ISLP Chapter 1; Kaggle Learn Intro lesson 1. All references are
`reference_only` roadmap anchors; they never control locking or recommendation.

## Notes

Entry node of the v1.8 Phase 2 chain. Learner-manual gate expected (framing
judgment needs human review; AI is never an acceptance authority).
