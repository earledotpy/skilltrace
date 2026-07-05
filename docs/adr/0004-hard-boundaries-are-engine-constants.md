# ADR 0004 — Hard boundaries are engine constants; the policy file must agree

Date: 2026-07-04
Status: accepted

## Context

The repo layout declares `policy/` to be seed data: values the engine reads,
never engine code. The policy layer (v0.6) makes those files load-bearing for
the first time — and one of them, `automation_boundary.yaml`, declares which
actions automation may perform, including the safety-critical forbidden list:
`pass_node`, `master_node`, `delete_record`.

If that file were genuinely authoritative, the safety rules CLAUDE.md calls
"never violate, never work around" would be exactly as hard as one line of
YAML: edit `pass_node` to `allowed` and the boundary is gone. A boundary that
a text editor can soften is not a hard boundary; it is a default.

Three models were considered:

1. **Engine constants, YAML must agree.** The forbidden list is hardcoded.
   The YAML still declares it, and `validate policy` fails if the file ever
   disagrees with the constants.
2. **YAML is authoritative.** Purest reading of "policy values are seed
   data"; the engine enforces whatever the file says. The safety rule becomes
   a convention about file contents, not an engine guarantee.
3. **Engine only, no YAML rules.** Drop the declarations from the file
   entirely; `check-automation` answers from constants alone.

## Decision

Model 1. The forbidden automations — `pass_node`, `master_node`,
`delete_record` — are constants in the engine, not configurable values.
`automation_boundary.yaml` continues to declare them, for two reasons: it is
the human-readable statement of the boundary alongside the other policy
files, and it is the surface `skilltrace check-automation` reads back and
`skilltrace validate policy` cross-checks. A file that disagrees with the
constants makes the repo *invalid* (validation failure, non-zero exit); it
never makes the boundary *soft*.

This carves a deliberate exception into "policy files are seed data": every
other policy file carries genuinely tunable values (thresholds, weights,
cadences); this one file's forbidden list is a mirror the engine holds up to
its own constants. Alongside this, the permission model collapses to two
levels — `allowed` / `forbidden` — answering one question: may this action
fire as a side effect of another command? The former
`allowed_with_confirmation` tier is dropped: in a single-learner CLI every
explicit command already is the confirmation.

## Consequences

- Tampering with `automation_boundary.yaml` is detected, not obeyed: the
  repo fails validation until the file again matches the constants.
- `check-automation` stays an honest query — file and constants can never
  answer differently for long, because validation forces reconciliation.
- The safety rules are enforceable in tests against code, not data: no
  fixture, seed variant, or migration can produce a repo where automation of
  pass/master/delete is permitted.
- The cost is purity: `policy/` is no longer uniformly seed data, and this
  ADR is the record of why that one file is subordinate to code.
- If a future curriculum genuinely needed a different automation boundary,
  it would require an engine change and a revisit of this ADR — that
  friction is the point.
