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

## What this skill is

Given a tabular problem statement, state whether it is supervised (regression or classification) or unsupervised, propose a train/validation/test split that keeps the test set sacred, and name two leakage patterns with a one-line fix for each.

## Why this skill

Framing decides everything downstream: the wrong task definition or a leaked split makes every later model comparison meaningless. A learner who can frame cleanly and split without leakage can trust their evaluation before spending time on models.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Study the framing and data-prep vocabulary, then practice on a small tabular problem: write the task type, sketch the split with one line on why the test set stays untouched, and list two leakage patterns with fixes. Seed estimate: 60–120 minutes.

## Resources

- mlcc-crash-course (registry)
- ng-ml-specialization-python (registry)
- islp-python-edition (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight. Aligned to the canonical node skeleton, 2026-09.
