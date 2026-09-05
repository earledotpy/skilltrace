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

## Learning target

Produce a `kaggle-titanic/` folder with a first submission, then a second
submission adding 3+ engineered features (e.g. family size, title, deck —
per `docs/roadmap/phase-2-classical-ml.md`), each submission committed with a
message explaining what changed, plus a one-page score comparison naming which
feature moved the metric and why.

## Study pointers

Kaggle Learn Intro + Intermediate for the notebook/pipeline mechanics and the
Titanic competition pages for the submission loop; Google MLCC workflow for
framing-to-evaluation discipline; ISLP classification labs for reading the
model honestly.

## Source provenance

Primary: Kaggle Learn (Intro + Intermediate) + Titanic competition.
Regeneration key: `kaggle-2026-08/titanic-baseline-01`. Supporting: Google MLCC
end-to-end workflow; ISLP Chapters 4–5 labs. All references `reference_only`.

## Notes

First half of the Phase 2 Kaggle checkpoint (Titanic ≥ 0.78 accuracy threshold
lives in the roadmap doc, not in this node — the node records the submission
discipline, not the score gate). Portfolio track: the folder is the evidence
artifact.
