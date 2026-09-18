---
id: programming.python.environment_troubleshooting_01
title: Troubleshoot Python environment and path problems
summary: Diagnose the environment failures that block beginners — wrong interpreter, module not found, activation and PATH confusion — a focused rescue drill, not first-time setup.
domain: programming
track: remediation
estimated_effort:
  min_minutes: 20
  max_minutes: 45
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: true
  requires_long_block: false
tags:
- remediation
- python
- environment
created_at: 2026-07-07
updated_at: 2026-07-07
---

# Troubleshoot Python environment and path problems

## What this skill is

Diagnose and fix the environment failures that stop work before any real code runs: a missing module, the wrong interpreter, an inactive virtual environment, and PATH confusion. The rescue skill is locating the problem — asking which interpreter and environment is actually running — rather than reinstalling blindly.

## Why this skill

These failures stop everything before any code runs, so locating the cause quickly is what unblocks the real work.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.programming.python.environment_troubleshooting`); Evidence is judged by learner manual review. The body does not restate them.

## How to work on it

Study how import resolution and virtual environments work first, then reproduce one failure on purpose so the diagnosis steps become muscle memory. Seed estimate: 20–45 minutes.

## Resources

- python-tutorial (registry)
- missing-semester (registry)

## Notes

A remediation node homed in the Python domain and narrower than the environment-setup node: a troubleshooting drill for when the environment breaks, surfacing on a blocker or repeated failure. Its role lives in its remediation edges and track label. Aligned to the canonical node skeleton, 2026-09.
