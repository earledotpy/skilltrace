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

## Learning target

Starting from the minimal-app node, write the from-scratch Dockerfile
(official Python image, `WORKDIR /code`, copy `requirements.txt` first for
layer cache, `pip install --no-cache-dir --upgrade -r`, copy `./app` last,
exec-form `CMD ["fastapi", "run", "app/main.py", "--port", "80"]`), then pass
the Engine 4-command acceptance on stock CI (`ubuntu-24.04`, preinstalled
Client+Server 28.0.4; `docker --version` recorded as evidence only), fixed
mapping `-p 80:80`, all exit 0: `docker build -t <primer-image> .`,
`docker run -d --name <primer-container> -p 80:80 <primer-image>`,
`curl -f http://localhost:80/` (body `{"message": "Hello World"}`),
`curl -f http://localhost:80/docs` (HTTP 200, Swagger UI). No Compose, no
Buildx, no push/registry in acceptance.

## Study pointers

FastAPI's Docker deployment page for the canonical Dockerfile; Engine install
docs for the daemon/CLI shape; the Desktop-license page for why Desktop stays
non-default (paid subscription above 250 employees or $10M revenue — the
free-first default is Engine, never Desktop). Alternates advisory note
(single note, inside this node, never multiplied acceptance): commands map to
`podman build/run`; Rancher Desktop / Finch / Colima run the same Dockerfile
via their Docker-compatible path. Engine is the only checked target.

## Source provenance

Primary: Docker Engine documentation, https://docs.docker.com/engine/ —
install, architecture, license gates. Supporting: FastAPI in Containers,
https://fastapi.tiangolo.com/deployment/docker/. Regeneration key:
`docker-engine-28.0.4/primer-build-run-01`. All references `reference_only`.

## Notes

Second half of the primer hard chain and one of the two hard-prerequisite
lineages into the capstone (the other is LangGraph). Portfolio track: the
Dockerfile plus the four-command exit-0 transcript is the evidence artifact.
The single hard edge out of the primer is this node to the capstone.
