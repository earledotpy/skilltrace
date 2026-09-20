---
id: agents.deploy.fastapi_minimal_01
title: Serve a minimal FastAPI app with interactive docs
summary: Build the app/ Hello World service, run it with fastapi dev and fastapi run, and read its /docs.
domain: agents
track: portfolio
roadmap_anchors:
- phase: phase_4
  phase_label: Agentic AI Core
  month_range: 2-3
  roadmap_topic: Deployment primer (FastAPI minimal app, official first-steps floor)
  source_role: reference_only
source_metadata:
  primary_source: FastAPI documentation
  canonical_url: https://fastapi.tiangolo.com/
  source_version: 0.141.1 (PyPI 2026-07-29; 0.x semver, pin required); verified 2026-09-05 per research/v19-sources-findings.md
  supporting_sources: []
regeneration_key: fastapi-0.141.1/minimal-app-01
section_provenance:
- source: FastAPI documentation
  section: Tutorial — First Steps (first app, path operations)
- source: FastAPI documentation
  section: Automatic interactive docs (/docs Swagger UI, /redoc, /openapi.json)
- source: FastAPI documentation
  section: About FastAPI versions (0.x pinning) and manual server run (fastapi dev vs fastapi run)
estimated_effort:
  min_minutes: 60
  max_minutes: 120
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- agents
- fastapi
- deploy
- primer
created_at: 2026-09-05
updated_at: 2026-09-05
---

# Serve a minimal FastAPI app with interactive docs

## What this skill is

Build the canonical primer layout — `app/main.py` with `FastAPI()` and a root route returning a Hello World payload — plus a pinned `requirements.txt` (0.x MINOR may break, so a pin is required, not advised), serve it with `fastapi dev` and then `fastapi run`, and read its interactive docs.

## Why this skill

Every agent that leaves a notebook needs an HTTP surface, and FastAPI is the serving wrapper this slice standardizes on. A learner who can serve, document, and pin this minimal app has the floor the Docker primer and the capstone both build on.

## What passing requires

No artifact spec or validation gate exists for this node yet — nothing can be submitted or passed today. A spec and gate will be authored when this tranche enters active study (see Notes). The body states no thresholds, counts, file names, or acceptance text.

## How to work on it

Study the Tutorial first-steps pages, build the app, serve it locally with `fastapi dev`, then with `fastapi run` (the production path, Uvicorn underneath), and show both the root payload and `/docs` (Swagger UI) responding. The single-file `main.py` layout is an accepted one-line variant. Seed estimate: 60–120 minutes.

## Resources

- fastapi-docs (registry)

## Notes

Spec-pending: no artifact spec or validation gate exists yet; specs and gates are authored when this tranche enters active study. Deliberate sequencing per G-CurriculumDirection, not an oversight.

First half of the self-contained primer hard chain (this node, then the Docker build/run/smoke node). Portfolio track: the `app/` folder plus the two serve transcripts is the evidence artifact. Only new soft edges point into the primer pair; no hard edge enters from the framework nodes. Scope stops at the official first-steps plus Docker floor — no dependencies, security, background tasks, or WebSockets here.

One-line warnings, never nodes: `--proxy-headers` behind Nginx/Traefik, and the deprecated `tiangolo/uvicorn-gunicorn` base image (do not use). Primary source: FastAPI documentation — first steps, interactive docs, version pinning; regeneration key `fastapi-0.141.1/minimal-app-01`. All references `reference_only`. Aligned to the canonical node skeleton, 2026-09.
