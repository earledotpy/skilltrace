# ADR 0001 — Learner progress lives in a separate store, not in node files

Date: 2026-07-02
Status: accepted

## Context

The v0.1 scaffold stores `state:` in each node's markdown frontmatter, so one
file mixes curriculum definition (title, competency dimensions, gates),
derived readiness (rewritten by `sync_readiness`), and the learner's journal
sections. Readiness syncs would rewrite curriculum files, a bad write could
corrupt frontmatter, and the seed curriculum could never be shared or
regenerated without carrying personal progress along.

## Decision

Node markdown files are pure curriculum definition and contain no `state:`
field. All learner state (derived readiness and asserted progress, with
timestamps) lives in a single progress store owned by the tools
(`graph/state.yaml`, keyed by node ID). Sync may only write derived readiness
(`locked`/`available`); asserted progress (`active`/`passed`/`mastered`) is
never written by any automated process.

Journal sections in the node body remain for the learner's own use; tools do
not parse them.

## Consequences

- `sync_readiness` and mutation commands touch exactly one file, giving the
  "no hidden mutation" policy a crisp enforcement point.
- The v0.8 seed graph can be regenerated or shared without merging progress.
- `skilltrace node <id>` must join two sources (node file + progress store)
  instead of reading one self-contained file.
- Scaffold node files with `state:` in frontmatter must be migrated; the v0.3
  loader should reject the field to prevent drift.
