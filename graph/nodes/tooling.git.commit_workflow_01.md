---
id: tooling.git.commit_workflow_01
title: Use the basic Git commit workflow
summary: Stage, commit, and inspect changes in a local repository.
domain: tooling
track: foundational
roadmap_anchors:
- phase: phase_1
  phase_label: Programming Fundamentals
  month_range: 5-12
  roadmap_topic: Git and GitHub
  source_role: reference_only
estimated_effort:
  min_minutes: 45
  max_minutes: 120
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: false
  requires_long_block: true
tags:
- git
- commits
- tooling
created_at: 2026-06-28
updated_at: 2026-07-06
---

# Use the basic Git commit workflow

## What this skill is

Stage a change and record it as a commit with a message: the basic Git commit workflow.

## Why this skill

The commit is the unit of saved work; every later Git skill assumes staged, messaged commits.

## What passing requires

See the artifact spec and validation gate in `evidence/` for this node (`spec.tooling.git.commit_workflow`); Evidence is checked by running your submission against its objective gate. The body does not restate them.

## How to work on it

Study the record-changes flow first, then initialize a repository, add a file, and commit it with a real message. Seed estimate: 45–120 minutes.

## Resources

- pro-git-book (registry)
- github-docs (registry)

## Notes

The gate asks Git whether the history carries a messaged commit tracking a file — the mechanical result of the workflow, not that a folder merely exists. Aligned to the canonical node skeleton, 2026-09.
