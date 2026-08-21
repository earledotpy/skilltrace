# Safety Boundaries

SkillTrace enforces hard safety rules that no command, sync, automation, or AI
review can bypass. These are engine-level invariants, not policy preferences.

## No automated pass or mastery

Passing and mastering are explicit learner commands only. No gate, sync process,
AI review, or automated workflow may assert `passed` or `mastered` on a node.
The commands `skilltrace pass` and `skilltrace master` refuse unless the
learner has met all eligibility requirements and issued the command themselves.

**What this prevents:** An AI, script, or automated process silently advancing
a node's state without the learner's conscious decision.

## No automated deletion

Evidence records are immutable. No command may delete an evidence record.
Corrections use the supersede model: a new record with `supersedes` and
`supersede_reason` links to the record it replaces. The original record remains
in the trail.

**What this prevents:** Loss of audit history, silent removal of evidence that
a decision was based on.

## Asserted progress never demotes

Once a node is asserted as `active`, `passed`, or `mastered`, no sync, edit,
command, or automated process may move it backward to a lesser state. Derived
readiness (`locked`/`available`) may change, but asserted progress is
permanent.

**What this prevents:** A data sync or policy recalculation undoing work the
learner has already completed.

## Hard prerequisites are never overridden

A `hard_prerequisite` edge locks its target until the source node is passed.
No command, policy, or override may bypass this lock. The only way to unlock a
node is to pass its hard prerequisites.

**What this prevents:** Studying material the learner is not ready for, which
would produce unreliable evidence and broken learning sequences.

## AI review is never acceptance authority

AI-generated review commentary may attach to evidence records as advisory
notes, but it may never serve as the acceptance authority for a gate. Only
`objective_gate` (command exit code) or `learner_manual` (explicit learner
verdict) may accept evidence.

**What this prevents:** An AI model's judgment replacing the learner's own
assessment of their work.

## Files are the sole source of truth

Markdown and YAML files in the repo are the only authoritative data. SQLite
databases, Markdown exports, and backups are disposable derived artifacts
regenerated from the source files. No engine code path reads from SQLite or
exports to compute state.

**What this prevents:** Derived artifacts diverging from source truth, or the
engine depending on a snapshot that may be stale.

## Single learner by design

One repo is one learner. There are no user fields, no multi-user
authentication, and no shared progress stores. A second learner forks the
curriculum without the progress store.

**What this prevents:** Accidental data sharing, confused progress attribution,
and the complexity of multi-learner concurrency in a local-first system.
