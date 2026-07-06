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

## Learning target

Stage a change and record it as a commit with a message. For the objective gate,
build a Git repository at `evidence/artifacts/git_repo/`: initialize it, add a
file, and commit it with a real message. Submit the repository (point
`--location` at `evidence/artifacts/git_repo/`).

The gate asks Git whether `HEAD` resolves to a commit that carries a message and
tracks a file — the mechanical result of the workflow, not that a `.git` folder
merely exists.

## Study pointers

Pro Git chapter 2.2 "Recording Changes to the Repository" (git-scm.com/book/en/v2)
for `git add`, `git status`, and `git commit`; GitHub Docs "Committing and
reviewing changes to your project" for the same in practice.

## Notes

Objective-gated: `evidence/checks/tooling.git.commit_workflow_check.py` interrogates
the repository artifact with `git rev-parse`, `git log`, and `git ls-tree`.
