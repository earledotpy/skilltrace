# SkillTrace — Ubiquitous Language

Glossary of domain terms. Definitions only — no implementation details.

**Learner** — the single person whose curriculum and progress a SkillTrace
repository holds. SkillTrace is single-learner by design: one clone is one
learner's identity; no record carries a user field. A second learner forks
the curriculum without the progress store.

## Node lifecycle

**SkillNode** — a single learnable skill in the skill graph. A node is always in
exactly one of five states.

**Curriculum** — the shared definition of skills: nodes, edges, gates,
artifact specs, resources. Contains no learner progress and can be
regenerated or shared without it.

**Node ID** — an immutable, never-reused identifier. The numeric suffix is a
sequence distinguishing sibling nodes in a topic, not a version. Minor edits
to a node happen in place and never invalidate progress; a material
redefinition of the skill is a *new* node with its own ID and edges, while
the old node's history remains true forever. Minor-vs-material is a human
judgment.

**Progress record** — the learner's state for one node (its current node
state plus when it changed). Progress belongs to the learner, not the
curriculum.

**Node states** — `locked → available → active → passed → mastered`.
The five states split into two kinds:

- **Derived readiness** (`locked`, `available`) — computed from the graph at
  any time. A curriculum edit (e.g., adding a hard prerequisite) may flip an
  un-started node from `available` back to `locked`.
- **Asserted progress** (`active`, `passed`, `mastered`) — recorded by the
  learner. Asserted progress never moves backward; no graph edit, sync, or
  automated process may revoke it.

- **locked** — at least one hard prerequisite is not yet satisfied. The node
  cannot be started or recommended as available.
- **available** — all hard prerequisites are satisfied; the learner may start it.
- **active** — the learner has started working on the node.
- **passed** — the node's evidence requirements were met and accepted by a
  non-AI authority. Passing is distinct from mastery.
- **mastered** — a passed node whose retention has been confirmed later.
  Never automatic, and permanent once asserted: a badly-failed later review
  creates failure records and remediation pressure, but never demotes the
  state.

**Failure** — not a node state. A failed assessment is recorded as a failed
**AssessmentAttempt**; being stuck is recorded as a **Blocker**. Either may
activate remediation edges, but the node itself stays in its current state.

## Engine vs. curriculum

**Engine** — SkillTrace's curriculum-agnostic mechanics: states, edges,
gates, policies as *mechanisms*. The engine never hardcodes rules from any
particular curriculum or study protocol.

**Seed data** — a particular curriculum expressed as nodes, edges, resources,
and policy *values* (e.g., a 3-failed-attempt remediation threshold). The
learner's AI Learning Roadmap contributes seed data and default policy
values only; it never defines engine behavior.

**Roadmap anchor** — `reference_only` metadata linking a node to a phase or
month of an external roadmap. Anchors never control locking, readiness, or
recommendation.

## Edges & policy

**GraphEdge** — a typed, directed relationship between two nodes (source
supports target). Edges are the only representation of node relationships;
node definitions never carry their own prerequisite or unlock lists.

**Track** — an opaque label grouping nodes (e.g., foundational, portfolio,
consolidation). The engine attaches no meaning to track names; their
recommendation priorities are seed policy values, and an unmapped track
warns rather than fails. No engine mechanic may key off a track name.

**Remediation edge** — a directed edge from a remediation node to the skill
node it rescues. Inactive at rest; it activates when the target has an open
Blocker or reaches the policy-configured number of failed attempts without a
pass. While active it raises the remediation node's recommendation priority
only — it never locks the target or alters progress. It deactivates when the
remediation node is passed or the triggering blocker is resolved.

**Hard boundary** — a policy the engine enforces by refusing the action
(non-zero exit). Hard boundaries exist only to stop *automation* of acts
that must stay manual: no AI-only pass, no automatic mastery, no automatic
deletion, no hard-prerequisite override.

**Advisory policy** — a policy that reorders recommendations or prints
warnings (workload, review cadence, remediation pressure). Advisory policies
never block a human-initiated action; the learner is the final authority.

## Evidence & execution (partial — being refined)

**Pass eligibility** — a derived fact: the node has accepted evidence
satisfying its closing gate. Computed on demand, never stored as truth.

**Passing** — an asserted act performed only by the learner via an explicit
command; the command refuses unless pass eligibility holds. Nothing else —
gate, sync, or AI — ever passes a node.

**Mastery eligibility** — a derived fact: the node is passed, at least one
review completed satisfactorily after the pass, and the pass and that review
occurred on different days (minimum spacing is a policy value). "No mastery
from a single session" is the engine mechanism; the spacing is seed data.

**Mastering** — an asserted act performed only by the learner via an explicit
command; the command refuses unless mastery eligibility holds.

**Acceptance authority** — who may accept evidence. Exactly two forms:
an **objective gate** (a verification command that exits successfully) or
**learner manual review** (the learner judges the artifact against the
node's rubric). AI review may attach advisory commentary to evidence but is
never an acceptance authority.

**EvidenceRecord** — one item of evidence submitted against a node. Records
are never edited or deleted, by human or machine; a correction is a new
record that **supersedes** the old one (with a required reason). Superseded
records remain visible but no longer count toward pass eligibility. An
already-asserted pass is never revoked by supersession; the discrepancy is
surfaced as an advisory warning for the learner to act on.

**AssessmentAttempt** — one attempt at a validation gate for a node. Attempts
may fail; failed attempts are the canonical record of assessment failure.

**Session** — a bounded block of study time. At most one session is open at
a time; a completed session has start and end timestamps. Session templates
(micro/standard/deep) are seed presets, not distinct types.

**SessionWork** — one unit of what happened in a session, tied to exactly
one node. A session holds many work items, so interleaving several nodes in
one sitting is first-class. Starting work on a node is what marks it
`active`. Work flagged as blocked requires notes.

**Blocker** — a record that the learner is stuck on a node. Blockers are the
canonical record of being stuck; resolving one requires a resolution summary.

**Review** — a scheduled retention check on a passed node. Completing one
requires a result summary and an outcome (satisfactory or unsatisfactory).
A satisfactory review after a pass feeds mastery eligibility; an
unsatisfactory one creates failure-side pressure, never a demotion. The
first review is auto-scheduled when a node is passed (cadence values are
seed data); overdue reviews warn and raise recommendation pressure but never
block anything.

**LearningResource** — a pointer to study material (URL or local path) with
provider, cost, license, and verification metadata. Resources are pure
advice: their status never affects a node's readiness, eligibility, or
state. Resource problems are warnings in health reports only.

**Verified** — a dated human assertion that a resource's URL resolves and
its recorded claims (cost, free tier, certificate, license) still hold.
Staleness is derived by comparing `last_verified` to a policy-configured
window; a replacement candidate is just an alternative resource linked to
the same node, promoted only by a human curriculum edit.

**Export** — a derived artifact (SQLite database, Markdown report, backup
archive) regenerated whole from the files on demand. Exports are disposable,
never hand-edited, and never read back by the engine. The Markdown/YAML
files are the only source of truth.

**Event log** — an append-only audit trail. Every mutating command appends
one event (when, what command, what it changed); read-only commands log
nothing. Events are never read back to compute state — losing the log loses
history, not state. A data change with no matching event is by definition a
hand edit.
