---
id: ml.practice.titanic_baseline_01
title: Ship a Kaggle Titanic baseline with feature engineering
summary: Submit a Titanic baseline, then improve it with three engineered features and a written score comparison.
domain: ml
track: portfolio
roadmap_anchors:
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 6-8
  roadmap_topic: Kaggle Titanic competition (feature engineering, submissions)
  source_role: reference_only
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 6-8
  roadmap_topic: ML Crash Course end-to-end workflow applied to Kaggle data
  source_role: reference_only
source_metadata:
  primary_source: Kaggle Learn
  canonical_url: https://www.kaggle.com/learn
  source_version: 2026 track contents; verified 2026-08-08 per docs/roadmap/phase-2-classical-ml.md
  supporting_sources:
  - Google ML Crash Course (2024 refresh) — https://developers.google.com/machine-learning/crash-course
  - ISLP Python edition — https://www.statlearning.com/
regeneration_key: kaggle-2026-08/titanic-baseline-01
section_provenance:
- source: Kaggle Learn
  section: Intro + Intermediate Machine Learning (notebook flow, pipelines, XGBoost); Titanic competition pages (3+ submissions each per Phase 2 checkpoint)
- source: Google ML Crash Course
  section: End-to-end workflow (framing to evaluation) applied to the Titanic split
- source: ISLP (Python edition)
  section: Classification labs (Chapters 4–5) informing the feature/readout discipline
estimated_effort:
  min_minutes: 180
  max_minutes: 360
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- ml
- kaggle
- titanic
- feature-engineering
- portfolio
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Ship a Kaggle Titanic baseline with feature engineering

## What this skill is

Run the Kaggle Titanic loop end to end: a first baseline submission, then a second submission adding engineered features, with a written comparison naming which feature moved the metric and why.

## Why this skill

Titanic is the first place where workflow discipline meets a public scoreboard: framing, features, and honest score reading in one loop. A learner who can ship a baseline, improve it deliberately, and say what moved the score is ready for larger practice datasets.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Work the notebook-to-submission loop twice on the Titanic data: baseline first with a commit message explaining what changed, then a second pass with additional engineered features and a one-page score comparison. Seed estimate: 180–360 minutes.

## Resources

- kaggle-learn-ml (registry)
- mlcc-crash-course (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight. Aligned to the canonical node skeleton, 2026-09.
