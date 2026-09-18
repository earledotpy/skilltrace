---
id: agents.deploy.docker_engine_build_run_01
title: Containerize the primer app and pass the Engine smoke check
summary: Write the from-scratch Dockerfile, build and run on Docker Engine, and curl / and /docs to exit 0.
domain: agents
track: portfolio
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 2-3
  roadmap_topic: Deployment primer (Dockerfile, Engine 4-command acceptance)
  source_role: reference_only
source_metadata:
  primary_source: Docker Engine documentation
  canonical_url: https://docs.docker.com/engine/
  source_version: Stable channel; stock CI ubuntu-24.04 preinstalls Client+Server 28.0.4; verified 2026-09-05 per research/v19-primer-toolchain-findings.md
  supporting_sources:
  - FastAPI in Containers (Docker) — https://fastapi.tiangolo.com/deployment/docker/
regeneration_key: docker-engine-28.0.4/primer-build-run-01
section_provenance:
- source: FastAPI documentation
  section: FastAPI in Containers — Docker (official Python image, WORKDIR /code, requirements-first layer cache, exec-form CMD)
- source: Docker Engine documentation
  section: Engine install and architecture (dockerd daemon, API, docker CLI)
- source: Docker Engine documentation
  section: Desktop license gates (why Desktop is not the default)
estimated_effort:
  min_minutes: 60
  max_minutes: 120
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- docker
- deploy
- primer
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Containerize the primer app and pass the Engine smoke check

## What this skill is

Containerize a minimal app from scratch: write the Dockerfile, build and run it on Docker Engine, and confirm the app answers on its routes.

## Why this skill

Container packaging is the deployment prerequisite for everything downstream: the capstone assumes the learner can build an image and run it reproducibly. A learner who can write a small Dockerfile and verify the running container stops debugging "works on my machine" and starts shipping.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Practice from the minimal-app starting point: write the Dockerfile from scratch, build the image, run the container with a fixed port mapping, and curl the app routes to confirm they answer. The Engine command sequence here is practice direction, not a pass bar. Seed estimate: 60–120 minutes.

## Resources

- docker-engine-docs (registry)
- fastapi-docs (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight. Aligned to the canonical node skeleton, 2026-09.
