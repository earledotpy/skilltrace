---
id: ml.capstone.house_prices_integration_01
title: Integrate the Phase 2 chain on Kaggle House Prices (capstone)
summary: Deliver a full CSV-to-submission pipeline on House Prices reusing framing, regression, validation, and ensembles.
domain: ml
track: portfolio
roadmap_anchors:
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 6-8
  roadmap_topic: Kaggle House Prices competition (capstone integration)
  source_role: reference_only
- phase: phase_2
  phase_label: Classical Machine Learning
  month_range: 5-8
  roadmap_topic: ML Crash Course + ISLP regression/validation applied end to end
  source_role: reference_only
source_metadata:
  primary_source: Kaggle Learn
  canonical_url: https://www.kaggle.com/learn
  source_version: 2026 track contents; verified 2026-08-08 per docs/roadmap/phase-2-classical-ml.md
  supporting_sources:
  - Google ML Crash Course (2024 refresh) — https://developers.google.com/machine-learning/crash-course
  - Andrew Ng Machine Learning Specialization (Python) — https://www.coursera.org/specializations/machine-learning-introduction
  - ISLP Python edition — https://www.statlearning.com/
regeneration_key: kaggle-2026-08/house-prices-capstone-01
section_provenance:
- source: Kaggle Learn
  section: Intermediate Machine Learning + House Prices competition (pipelines, XGBoost, 3+ submissions discipline)
- source: Google ML Crash Course
  section: Linear Regression + Evaluation/Validation + Trees/Ensembles modules (loss, metrics, boosting)
- source: Andrew Ng Machine Learning Specialization (Python)
  section: Courses 1–2 (regularized regression, bias/variance diagnosis, trees/ensembles)
- source: ISLP (Python edition)
  section: Chapters 3 + 5 + 8 (linear regression, resampling, tree-based methods labs)
estimated_effort:
  min_minutes: 240
  max_minutes: 480
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- ml
- kaggle
- capstone
- integration
- portfolio
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Integrate the Phase 2 chain on Kaggle House Prices (capstone)

## Learning target

Deliver a `kaggle-house-prices/` folder that integrates the whole Phase 2
chain on the House Prices competition: CSV load and clean, leakage-audited
split, regularized regression baseline, tree/gradient-boosting comparison with
cross-validated metric choice (RMSE, log scale), 3+ submissions with
commit-message discipline, and a best-model analysis naming which source's
technique (MLCC, Ng MLS, ISLP, Kaggle) moved the score at each step.

## Study pointers

Kaggle Learn Intermediate + House Prices pages for the competition loop; Google
MLCC Regression/Evaluation/Trees modules for loss, metrics, and boosting; Ng
MLS Courses 1–2 for regularization and bias/variance diagnosis; ISLP Chapters
3/5/8 Python labs for the regression/resampling/trees reading.

## Source provenance

Primary: Kaggle Learn + House Prices competition. Regeneration key:
`kaggle-2026-08/house-prices-capstone-01`. Supporting sections: Google MLCC
(Regression, Evaluation/Validation, Trees/Ensembles); Ng MLS Courses 1–2; ISLP
Chapters 3, 5, 8. All references `reference_only` — this node *integrates*
four sources without any anchor controlling locking.

## Capstone integration identification

This node is the v1.8 ≥ 1 / ≥ 2-sources capstone. Prerequisites cite two
source lineages (the Kaggle-anchored `ml.practice.titanic_baseline_01` chain
and the MLCC/Ng/ISLP-anchored `ml.trees.ensembles_01` chain), and its
supporting LearningResources cite three of the four v1.8 sources
(`kaggle-learn-ml`, `islp-python-edition`, `mlcc-crash-course` — plus
`ng-ml-specialization-python` via the ensemble prerequisite's resources). See
the draft-branch note for the full criterion walk-through.

## Notes

Second half of the Phase 2 Kaggle checkpoint (House Prices RMSE discipline per
the roadmap doc). Portfolio track: the folder plus best-model analysis is the
evidence artifact. No FastAPI/Docker deployment preview — re-slotted to v1.9
per `docs/POST_V1_ROADMAP.md`.
