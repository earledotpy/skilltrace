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

## Learning target

Diagnose and fix the environment failures that stop work before any real code
runs: `ModuleNotFoundError` for a package you thought you installed, running the
wrong Python, a virtual environment that isn't activated, and PATH confusion on
Windows. The rescue skill is *locating* the problem — asking which interpreter
and which environment is actually running (`where python`, `python -c "import
sys; print(sys.executable)"`, `pip show`) — rather than reinstalling blindly.

## Study pointers

- Real Python's guides to virtual environments and to `pip`/`PATH` on Windows;
  the Python Tutorial's "Modules" and "Virtual Environments" chapters for how
  import resolution finds (or fails to find) a package.
- Reproduce one failure on purpose (activate no venv, then import a venv-only
  package) so the diagnosis steps become muscle memory.

## Notes

A remediation node homed in the Python domain and narrower than the
`environment_01` setup node: this is a troubleshooting drill for when the
environment breaks, surfacing on a blocker or repeated failure. Its role lives
in its `remediation` edges and `track: remediation` (weight 0.5). Rescues the
setup, imports, and library-dependent data nodes. Manual-gated.
