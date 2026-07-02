---
id: 1
title: Installable skilltrace package with subcommand dispatcher
milestone: v0.3.0-rc1
labels: [cli, foundation]
status: done
depends_on: []
---

## Outcome (2026-07-02)

Done. Installable `skilltrace` package under `src/skilltrace/` with a
`skilltrace` console-script entry point (`pip install -e .` verified on
Windows; `skilltrace --help` exits 0 and lists `validate`, `sync`, `next`).
The argparse dispatcher (`cli.py` + `dispatch.py`) is the single chokepoint:
mutating commands append exactly one audit event to `execution/events.yaml`
(timestamp, command, args, records_touched); read-only commands append none.
The automation boundary is code-authoritative — `pass_node`/`master_node`/
`delete_record` are refused unconditionally in `automation.py`, independent of
the policy file, which can only *add* forbidden actions. The three v0.3
commands are registered with placeholder handlers; real logic lands in
issues #5 (validate graph), #6 (sync), #7 (next). `compiler/` untouched.
Tests: `tests/cli/` (21 passing).

## Context

Decision 13: one `skilltrace` CLI from v0.3 so every later RC builds on the
final interface. The dispatcher is also the single chokepoint for the two
cross-cutting rules: mutating commands append exactly one audit event, and
automation boundaries are checked before dispatch.

## Scope

- `pyproject.toml` with a `skilltrace` console-script entry point;
  editable install works on Windows.
- `src/skilltrace/` package layout; `compiler/` stays untouched as
  throwaway reference.
- Subcommand dispatcher (argparse) with the v0.3 surface: `validate graph`,
  `sync`, `next`. Commands register as read-only or mutating.
- Mutating commands append one event to `execution/events.yaml` (timestamp,
  command, args, records touched); read-only commands append nothing.
- `skilltrace --help` lists all registered subcommands.

## Acceptance

- Fresh clone → `pip install -e .` → `skilltrace --help` exits 0.
- Test: a registered mutating command appends exactly one event; a
  read-only command appends none.
- Test: dispatcher refuses an action registered as automation-forbidden
  (placeholder wiring for `pass_node`/`master_node`/`delete_record`).
