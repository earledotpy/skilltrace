---
id: 12
title: skilltrace evidence submit
milestone: v0.4.0-rc1
labels: [evidence, cli]
status: done
depends_on: [10]
---

## Outcome (2026-07-03)

Implemented as a pure `plan_submit` planner (`evidence/submission.py`) over
already-loaded data with injected gate-runner and hasher seams, plus a thin
`evidence submit` handler (`commands/submit.py`) binding the real subprocess
gate run, artifact hash, and record append. A rejected record (manual or a
failing objective gate) is a written, audited submit (exit 0, one event); only
refusals and an unrunnable objective gate exit non-zero and write nothing.
Objective gates run `shell=False` so `OSError` (unable to run) is distinct from
a non-zero exit (rejection verdict). The supersede-drops-eligibility warning is
scoped to an asserted *pass* (`passed`/`mastered`) per ADR 0003. Covered by
`tests/evidence/test_submission.py` (planner) and `test_submit_command.py`
(wired CLI + audit).

## Context

ADR 0003: submitting is the act of judgment. Acceptance is decided at
submission and frozen; no pending state; no defaulted verdict.

## Scope

```bash
skilltrace evidence submit <node_id> [--spec <spec_id>] --location <path-or-url>
    [--note "..."] [--accept | --reject]
    [--supersedes <record_id> --reason "..."]
```

- `--spec` optional when the node has exactly one artifact spec; with
  several, omitting it refuses and lists them.
- Manual-authority node: `--accept` or `--reject` is mandatory — absence
  refuses. Objective-authority node: those flags are refused, not ignored;
  the gate command runs loudly (print command + exit code); exit 0 →
  accepted, non-zero → **rejected record is written**; command unable to
  run at all → error, nothing written.
- Gateless node: refuse (no authority exists to judge).
- Any node state is legal; warn when the node is locked.
- Supersede rules enforced at submit: target exists, same spec, no existing
  successor, reason required.
- Record written with artifact content hash; ID allocated per #10.
- Submit-time warning when a supersede drops eligibility under an asserted
  pass (pass stands).
- One event appended via the dispatcher.

## Acceptance

- Tests: manual without verdict refuses; objective with `--accept` refuses;
  failing gate command yields a rejected record; unrunnable command yields
  no record; locked-node warning; gateless refusal; each supersede-rule
  violation refuses; hash recorded; exactly one event per successful
  submit; records never mutated.
