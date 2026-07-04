# ADR 0003 — Evidence acceptance is frozen at submission; supersession and annotation are derived, never mutations

Date: 2026-07-03
Status: accepted

## Context

Evidence records are immutable (safety rule: corrections supersede, never
edit/delete), and acceptance has exactly two authorities: an objective gate
command exiting 0, or learner manual review. Those two facts collide on a
timeline question: if a learner submits an artifact and acceptance happens
*later*, recording that acceptance means mutating the record.

Three models were considered:

1. **Acceptance decided at submission and frozen into the record.** No
   pending state; a rejected record stays rejected forever; a new try is a
   new record.
2. **A separate Acceptance record** referencing a pending evidence record —
   allows "submit now, judge later" at the cost of a second record type and
   a pending state.
3. **A mutable status field** defined as outside the immutability guarantee
   — rejected outright: it makes "immutable" a lie with a footnote and is a
   hand-edit magnet.

## Decision

Model 1. `skilltrace evidence submit` performs the judgment: it runs the
node's objective gate command (exit 0 → accepted, non-zero → rejected
record; a command that cannot run at all is an error and writes nothing —
inability to judge is not a judgment), or, on manual-review nodes, requires
the learner to state `--accept` or `--reject` explicitly. No verdict is
ever defaulted. The verdict, authority, and a content hash of the artifact
as submitted are frozen into the record at creation.

Two companions keep immutability absolute with zero exceptions:

- **Superseded is a derived status.** The correcting record carries
  `supersedes` + reason; the old record is never touched. Corrections form
  a chain with one live head, target the same artifact spec, and are judged
  on their own merits.
- **Advisory commentary is a separate append-only annotation record** that
  names an evidence record (structure settled; not implemented until an
  AI-review workflow exists). No commentary field ever rides on the record.

## Consequences

- Submitting *is* the act of judgment, which keeps the single learner
  accountable to it and deters false reporting — the design intent.
- There is no pending state and no later un-accepting; the regret path is a
  superseding record with a required reason, which removes eligibility but
  never revokes an asserted pass (warning surfaced instead).
- Pass eligibility is pure arithmetic over records on file; `eligibility`
  and `pass` never execute gate commands, so they are deterministic on any
  machine. Post-acceptance regression is the Review mechanism's concern
  (the frozen content hash makes drift detectable as a warning).
- One record per submission — no join between evidence and acceptance rows.
- If a multi-reviewer future ever demands "submit now, judge later", moving
  to model 2 means migrating every record written under this semantic. That
  cost is accepted: SkillTrace is single-learner by design (decision 20),
  so the workflow model 2 serves has no user.
