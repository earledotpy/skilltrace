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
The chain is an ordering, not a mandatory itinerary: passing directly from
`available` is legal (prior learning is real); `locked` is the only wall.
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
deletion, no hard-prerequisite override. *Automation* means an action firing
as a side effect of another command (e.g. review scheduling on pass); an
explicit learner command — issued at the terminal or by confirming in a
confirmation modal — is by definition manual, so every action is either
automatable or manual-only — there is no middle "with confirmation" tier.

**Confirmation modal** — the browser form of an explicit learner command: a
dialog that presents the eligibility facts behind an intended pass or mastery
assertion and completes only on an explicit confirming click. Page load,
prefetching, or script execution never constitutes assertion. Mastery confirms
twice — the second click exists because mastery is permanent. A modal
confirmation asserts exactly what the equivalent terminal command asserts — it
informs, never adds or relaxes an engine rule.

**Advisory policy** — a policy that reorders recommendations or prints
warnings (workload, review cadence, remediation pressure). Advisory policies
never block a human-initiated action; the learner is the final authority.

## Evidence & execution (partial — being refined)

**ArtifactSpec** — the definition of one kind of evidence a node expects:
what artifact, how many (its minimum count), and whether it is required.
Every evidence record is submitted against exactly one spec. Optional specs
are slots for extra evidence — kept and shown, never counted.

**Pass eligibility** — a derived fact: every required artifact spec of the
node has at least its minimum count of accepted, non-superseded evidence
records. Computed on demand, never stored as truth. Evidence records are
the *only* input; assessment attempts never count, no matter their outcome.
Computing eligibility never executes anything — a gate's verification
command runs only at submission, and its verdict is a historical fact about
the artifact as submitted. Post-acceptance regression is the Review
mechanism's concern, not eligibility's.

**Passing** — an asserted act performed only by the learner via an explicit
command; the command refuses unless pass eligibility holds, and refuses on a
locked node regardless of evidence (no hard-prerequisite override). Being
`active` is never a precondition — it records engagement, not permission.
Nothing else — gate, sync, or AI — ever passes a node.

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
never an acceptance authority — an AI authority is not even representable in
a gate definition. A verification command that runs and fails produces a
rejected record; one that cannot run at all produces an error and no record —
inability to judge is not a judgment. On a manual-review node the learner
must state the verdict explicitly; no verdict is ever defaulted.

**ValidationGate** — a node's closing gate: the declaration of which single
acceptance authority judges evidence submitted against that node (objective
or learner manual review). A node has at most one gate; a node without one
cannot accept evidence and can never become pass-eligible — that is a
curriculum-quality warning, never an engine error. A gate never changes
node state by itself, and there is no AI gate. Distinctions like
rubric-vs-checklist are descriptive seed wording, not gate kinds.

**EvidenceRecord** — one item of evidence submitted against a node.
Submission is legal in any node state — evidence is a historical record of
proof, not a state change — with a warning when the node is locked.
Acceptance is decided at submission — by the node's objective gate or by
learner manual review — and frozen into the record; there is no pending
state and no later un-accepting. Submitting is the act of judgment, which
keeps the learner accountable to it. A rejected record stays rejected
forever; a new try is a new record. Records are never edited or deleted, by
human or machine; a correction is a new record that **supersedes** the old
one (with a required reason). Superseded is a derived status — the old
record is never touched; it means a later record names it. A correction
targets the same artifact spec as the record it corrects; corrections form
a chain with one live head (a record with a successor cannot be superseded
again); any record may be corrected regardless of how it was judged; and
the correction is judged on its own merits at its own submission.
Superseded records remain visible but no longer count toward pass
eligibility. A record fingerprints the artifact as submitted; the artifact
file drifting afterwards is surfaced as a health warning and never changes
acceptance or eligibility. An
already-asserted pass is never revoked by supersession; the discrepancy is
surfaced as an advisory warning for the learner to act on.

**Advisory annotation** — a separate append-only note that names an
evidence record; attachment is derived, and the record itself is never
touched. This is the only form advisory commentary takes — from AI review
or from the learner's own later margin notes. Annotations are displayed,
never read by engine logic, and have no effect on acceptance, eligibility,
or state. (Structure settled; no implementation before an AI-review
workflow exists.)

**AssessmentAttempt** — one attempt at demonstrating a node's skill against
its gate's standard. Its outcome is passed or failed (two values, no
scores), with optional notes. Attempts are immutable and recordable in any
node state — on a gateless node the standard lived in the learner's head,
which is a warning, not a refusal. Failed attempts are the canonical record
of assessment failure and feed remediation pressure. Attempts never feed
pass eligibility — a passing attempt justifies submitting evidence but
proves nothing by itself.

**Session** — a bounded block of study time, in exactly one of two
statuses: **open** (started, not yet ended) or **completed** (has both start
and end timestamps). At most one session is open at a time. There is no
planned session — a session records study that is happening or has
happened, never an intention. An open session older than a policy-configured
window is **stale** — a derived status that warns and never blocks; closing
a forgotten session records its honest end time, which may be in the past.
A session template (micro/standard/deep) is an optional opaque label on a
session — like a Track, the engine attaches no meaning to it; expected
durations are seed presets read only by advisory policy, and a template
with no preset warns rather than fails.

**SessionWork** — one unit of what happened in a session, tied to exactly
one node. A session holds many work items, so interleaving several nodes in
one sitting is first-class. Starting work on a node is what marks it
`active` — but only as a forward move: work on an `available` node asserts
`active`; work on an `active` node changes nothing; work on a `passed` or
`mastered` node is recorded as history without touching state (revisiting is
never a demotion). Work on a `locked` node is refused — locked is the only
wall, and "cannot be started" is literal. Work flagged as blocked requires
notes; blocked work is a session-scoped observation with no remediation
effect — it never creates a Blocker, which is a separate, deliberate act.

**Blocker** — a record that the learner is *persistently* stuck on a node,
created only by an explicit learner command — never auto-created from
blocked work. Blockers are the canonical record of persistent stuckness and
the only stuckness signal remediation edges react to. Each blocker names
its own obstacle (description required), so one node may carry several open
blockers — a second open one warns as a likely duplicate. A blocker may be
created in any node state except locked: what cannot be started cannot be
stuck. Resolving one requires a resolution summary.

**RemediationAction** — an execution record of one deliberate corrective
intervention: tied to exactly one node, optionally naming the Blocker it
addresses, in one of two statuses (open or completed; completing requires a
result summary). It is the ad-hoc counterpart to a curriculum-level
remediation edge — loggable without any remediation node existing in the
graph. It has no mechanical effect: it never resolves a blocker, never
touches state or eligibility, and never activates or deactivates a
remediation edge; advisory policy may display it as context, never read it
as a trigger.

**Review** — a scheduled retention check on a passed or mastered node —
never on a node with nothing to retain. After mastery only the learner
schedules reviews by hand; automation stops per policy. A review is
scheduled, then either completed or cancelled; cancelling is a learner-only
act with a required reason — the record stays as honest history but stops
counting as overdue and never feeds mastery eligibility. Overdue is
derived (a scheduled review past its date), never stored. Completing one
requires a result summary and an outcome (satisfactory or unsatisfactory).
A satisfactory review after a pass feeds mastery eligibility; an
unsatisfactory one creates failure-side pressure, never a demotion. The
first review is auto-scheduled when a node is passed (cadence values are
seed data); overdue reviews warn and raise recommendation pressure but never
block anything.

**Memory state** — the retention model's derived picture of how well a
passed or mastered node is currently retained. It exists only at read
time: recomputed from review history and policy values, never stored,
and never written by the engine on the learner's behalf. The core quantity
it exposes is **Retention confidence** — a single 0–1 measure of how well a
node is currently retained. Memory state may warn and reorder recommendations,
alongside retention suggestions; it never blocks anything and never moves
asserted progress.

**Retention confidence** — the retention model's derived, 0–1 measure of how
well a passed or mastered node is currently retained, where 1 means freshly
reviewed and 0 means fully faded. It is recomputed at read time from review
history and policy seed values (the decay model's half-life and multipliers),
never stored, and never written by the engine on the learner's behalf. A node
falls below the policy `attention_threshold` when roughly a half-life has
elapsed since its last contact, at which point a retention suggestion is due.
Retention confidence may warn and reorder recommendations; it never blocks
anything and never moves asserted progress.

**Retention suggestion** — a derived, never-stored recommended date for the
next retention check on a passed or mastered node, produced by the retention
model and recomputed from review history and the current date at read time
whenever the node's **Retention confidence** is below the policy
`attention_threshold`. A retention suggestion is not a Review: it creates no
record, is recomputed from review history and the current date at read time,
and becomes real only when the learner schedules a review by hand. Retention
suggestions may warn and reorder recommendations; they never block anything.

## Resource verification (v1.7)

**LearningResource** — a pointer to study material (URL or local path) with
provider, cost, license, and verification metadata. Resources are pure
advice: their status never affects a node's readiness, eligibility, or
state. Resource problems are warnings in health reports only. A resource is
part of the curriculum, identified by an immutable, never-reused ID; minor
edits happen in place, and a genuinely different resource is a new entry.
The resource names the nodes it supports (a dangling reference is a
curriculum error); a resource supporting no node is a curriculum-quality
warning, like a gateless node. Cost is a single claim — free or paid, never
both; a free tier is a claim only a paid resource can make (try before
upgrading).

**Verified** — a dated human assertion that a resource's URL resolves and
its recorded claims (cost, free tier, certificate, license) still hold.
A resource's verification status (unverified, verified, stale) is always
derived from the assertion date, never stored: staleness is derived by
comparing `last_verified` to a policy-configured window. A failed check is
not a verification: it records a dated **broken** marker with the reason —
the one stored verification fact, because it is an observation, not a
derivation. Broken dominates the derived statuses in reports and is cleared
only by a later successful verification or a human curriculum edit; like
all resource problems it warns and never blocks. Positive verification is a
human act forever: no automation ever sets `last_verified`, because claims
like a live free tier or an unchanged license need human judgment, and
half-verification is not verification. Automation may at most *flag* — an
automated check that fails is an objective observation and may set the
broken marker, but a bot can never assert that a resource is good.

**Web check** — an automated test of a resource URL's reachability. A failed
web check may record a dated broken marker, but a successful web check never
sets `last_verified`, clears `broken`, or asserts that the resource's claims
remain valid.

**Retired resource** — a resource no longer used in active resource flows but
preserved as curriculum history. Its replacement relationship and retirement
date remain visible for audit, and retirement never changes learner progress
or node state.

**Replacement candidate** — an alternative LearningResource linked to one or
more of the same nodes as a resource being retired. It becomes the replacement
only through a human curriculum edit and must itself satisfy the registry's
resource-verification requirements.

**Replacement** — a human-confirmed operation that retires one resource and
transfers its supported-node coverage to a replacement candidate. Replacement
preserves the retired resource and its broken-marker history; it never changes
learner progress, graph relationships, or evidence.

**Export** — a derived artifact (SQLite database, Markdown report, static
HTML report, backup archive) regenerated whole from the files on demand.
Exports are disposable, never hand-edited, and never read back by the
engine. The Markdown/YAML files are the only source of truth. A static HTML
report reviews where everything stood at generation time and says so on its
face — it is a review snapshot, never a daily view.

**Event log** — an append-only audit trail. Every mutating command appends
one event (when, what command, what it changed); read-only commands log
nothing. Each event also carries its provenance — whether the command was
issued from the terminal or through Serve. Events are never read back to
compute state — losing the log loses history, not state. A data change with
no matching event is by definition a hand edit.

**Serve** — the live local web surface (`skilltrace serve`, alias `st ui`)
through which the learner reads daily views and issues explicit commands
outside the terminal. It renders straight from the truth files at each
request and keeps no copy of its own, so what it shows is always current;
its writes are the same explicit, confirmed learner commands as the CLI's,
never a second path. Serve shows truth but is never a source of it, and
nothing it renders is ever read back by the engine — unlike an Export,
it is a view onto truth, not a copy of it.

## Event-log analytics (v1.6)

**Study velocity** — a derived operational metric counting work items
logged and forward node progress (nodes moving from a lower to a higher
asserted state) within a rolling window. Measured in work items per week.
Advisory policy warns when the rate falls below the target in
`policy/analytics.yaml`. Study velocity is read-only and advisory — it
never blocks a command or alters state.

**Blockers by domain** — a derived operational metric grouping open and
recently-resolved Blockers by track or node ID prefix, over a rolling
window. Advisory policy warns when the count of active blockers exceeds
the threshold in `policy/analytics.yaml`. Blockers by domain is read-only
and advisory — it never alters a Blocker record or state.

**Review completion** — a derived operational metric measuring the ratio
of completed reviews to scheduled-plus-overdue reviews, with prominent
overdue highlighting, over a rolling window. Advisory policy warns when
the completion ratio falls below the target in `policy/analytics.yaml`.
Review completion is read-only and advisory — it never schedules,
completes, or cancels a review.

**Evidence coverage** — a derived operational metric reporting per-node
evidence counts, gap analysis (required specs with zero accepted records),
and submission rate, over a rolling window. Advisory policy warns when the
coverage ratio falls below the target in `policy/analytics.yaml`.
Evidence coverage is read-only and advisory — it never submits or alters
an evidence record.

**Rolling window** — the time span a derivation or analytics command covers,
counted backwards from today. The default is controlled by
`default_window_days` in `policy/analytics.yaml` and may be overridden
per-invocation with `--days`. A rolling window is advisory context for a
derivation; it never affects node states, evidence records, or progress.

**Soft data threshold** — the minimum number of sessions in the rolling
window (`min_sessions_for_full_data` in `policy/analytics.yaml`) below
which an analytics command prefixes its output with a limited-data
advisory. The threshold is a data-quality warning only; it never blocks
output or changes exit codes.

## Mentor voice (v1.x)

**Mentor section** — one rendered block of the Mentor-voice output: a
heading plus its lines, the typed shape that every read-only command and
view renders. The canonical section headings are `Brief`, `Where to
learn`, `How to proceed`, `Do this next`, and `Context`. The dispatch
(`mentor.prose.brief_for(state, facts, perspective)`) is state-keyed
(one branch per NodeState), not a string-template engine — future voice
tuning is a per-state edit, not a template rewrite.

**Node facts** — the uniform tuple every Mentor section consumes
(`mentor.prose.NodeFacts`): node, state, specs, records, gate presence,
resource lines, unsatisfied prereqs, unlocked-by, blockers, open-session
flag, and titles map. Constructing one is the caller's job; the prose
module reads only these fields, never the joined view directly, so it
stays pure of I/O and easy to test.

**Overdue review** — a scheduled Review past its `scheduled_for` date.
Derived, never stored (per the existing definition), with one canonical
predicate (`execution.overdue.overdue_reviews`) shared by every surface
(today, report, listings, suggest, analytics, web, advisory). The wall
clock is read through one funnel (`execution.overdue.utc_today`) that
honors the dispatcher's `Context.clock` override so midnight-UTC
transitions cannot turn a passing test red.
