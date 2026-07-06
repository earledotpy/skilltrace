# Curriculum authoring guide

How to author SkillTrace curriculum — nodes, edges, gates, and resources — so
that every addition meets the production bar without re-deriving the design
session that set it (grilling, 2026-07-06; see issue #14). This is doctrine for
*seed data*, not engine behavior. Nothing here changes the ubiquitous language
in `CONTEXT.md`; it records the editorial rules the engine cannot enforce.

The curriculum is designed **destination-backward** from the learner's stated
destination — a working AI/ML engineer-practitioner. Topic depth serves where
the learner is going, not an outside document's month plan. The old AI learning
roadmap is `reference_only`: a candidate-topic checklist and `roadmap_anchors`
metadata, never a structure to transcribe.

## Node grain

One node is the **smallest skill that can be independently evidenced by one
artifact**, sized to roughly **30–90 minutes of effort**. This is the grain the
session-fit scoring assumes and the grain a single ArtifactSpec can prove.

- Too big: if proving the skill needs two unrelated artifacts, it is two nodes.
- Too small: if the artifact is trivial to produce for anyone who can read the
  title, fold it into its neighbor.
- Depth is a budget. Spend nodes where the destination is load-bearing
  (statistics/probability, linear algebra go deep — 6–8 nodes); keep shallow
  bands shallow (arithmetic, calculus intuition, CLI, Git, visualization,
  communication — 2–4 nodes). Node-count targets are design guidance, not a
  validator rule.

## Edges: the minimal-locking test

`graph/edges.yaml` is the sole source of node relationships. There are three
edge types; the choice between hard and soft is the single most consequential
authoring decision, because **a `hard_prerequisite` is the only wall** — it
locks the target until the source is `passed`/`mastered`. Soft prerequisites
and remediation edges never lock; they only inform recommendation.

**The test — apply it to every hard edge:**

> Strip the source competence entirely — imagine it learned *nowhere*. Is the
> target's artifact still coherent to produce?
>
> - **No** → the source is *constitutive* of the target. Use `hard_prerequisite`.
> - **Merely harder, slower, or unmotivated** → the source is pedagogical
>   ordering. Use `soft_prerequisite`.

The "outside knowledge" framing matters: we do **not** hard-lock just because
our node is the teaching path. A learner who already has the source competence
(from anywhere) can pass the source node quickly and unlock the target — so a
hard edge on a genuinely constitutive dependency still respects prior learning.
Hard-lock only when the competence itself is a true prerequisite regardless of
where it was learned.

**Constitutive vs infrastructural vs packaging** — the three lines authors trip on:

- *Constitutive* (hard): the source competence is exercised inside the target's
  artifact. Solving `ax + b = c` manipulates a variable expression; a conditional
  branches on values held in variables; reading a CSV opens and reads a file.
- *Infrastructural* (soft): the source is a one-time precondition satisfiable
  outside SkillTrace, not a competence re-exercised in the target. Having a
  working Python environment lets you *run* variable code, but a learner who
  already has Python installed can start variables cold — so
  `environment → variables` is soft.
- *Packaging* (soft): the source is a parallel deliverable bundled with the
  target, not what makes it work. A portfolio project is hard-edged only from
  the nodes that *mechanically enable* it (the code skills it is built from);
  versioning it in Git or writing its README are packaging, so those edges are
  soft.

Expected shape: hard edges form **short chains inside genuinely cumulative
bands**; most cross-band scaffolding is soft. Every hard edge's `reason` must
state *why the target is incoherent without the source* — not "builds on" or
"helps with", which are soft-edge language. When auditing an existing edge, hold
it to the same test and demote it (with an updated reason) if it fails.

## Gates: the honesty rule

Every node has exactly one ValidationGate (`evidence/validation_gates.yaml`)
with one of two authorities:

- **`manual`** — a human judges the evidence. The default. Use it wherever
  judgment is the substance: math reasoning, writing, projects, consolidation.
- **`objective`** — a command exiting 0 *is* the pass bar. Use it only where a
  computer genuinely can check the skill: running the artifact script or its
  tests, interrogating a Git repository artifact. Roughly 15–20 code/Git nodes.

**Never author an objective gate whose command checks a proxy** — file exists,
line count, a grep for a keyword. If the honest check needs judgment, the gate
is `manual`. A gate that pretends a proxy is the skill is worse than an honest
manual gate. Objective commands are authored for and smoke-tested on the
learner's actual environment (Windows) so they work at submission time.

AI review is never an acceptance authority; it may attach advisory commentary
only. Passing and mastering are explicit learner commands (see the safety rules
in `CLAUDE.md`).

**Authoring an objective gate (the shipped-checker pattern).** The gate runner
(`commands/submit.py`) runs the gate's `command` as `shlex.split(command)` →
`subprocess.run(argv)` with `shell=False`, no cwd override, and no substitution
of the submitted `--location`. The contract that follows from that:

- **A checker ships; the solution does not.** Put a checker at
  `evidence/checks/<node_id>_check.py` and point the gate `command` at
  `python evidence/checks/<node_id>_check.py`. The learner writes their solution
  to a fixed path under `evidence/artifacts/` (gitignored — the seed carries
  checkers, never solutions), which the checker resolves *relative to its own
  `__file__`*, not the cwd. Name that path in the node body and mirror it in the
  spec's `expected_location_hint` / `example_filename` so the hashed `--location`
  and the checked file coincide. Set the spec's `minimum_count: 1`.
- **Forward slashes only.** `shlex.split` is POSIX; a backslash is an escape and
  eats the path. Python and Git both accept `/` on Windows.
- **The checker verifies stated behavior, never a proxy.** Exercise the actual
  functions (or interrogate the actual repo with `git rev-parse`/`log`/`ls-tree`)
  and compare against the contract the node body states. A file-exists or
  line-count check is the proxy the honesty rule forbids.
- **Decide the verdict with an explicit `raise SystemExit`, never `assert`.**
  `python -O` / `PYTHONOPTIMIZE` strips `assert`, which would make the checker
  exit 0 for a *wrong* solution and silently accept anything. The shared
  `evidence/checks/_loader.py` exposes `check(cond, msg)` for exactly this.
- **Smoke-test both directions on the real environment before shipping.** On a
  disposable copy (never the real repo — a real submit writes an evidence record
  and an audit event), submit a correct solution (→ ACCEPTED) *and* a deliberately
  wrong one (→ REJECTED). The wrong-case rejection is what proves the gate
  discriminates rather than passing vacuously.

A shipped-test objective gate is inherently game-able by hardcoding to the
visible cases; that is acceptable for a single honest self-learner. The honesty
rule governs the *author* (ship no proxy), not adversarial-proofing the learner.

## Resources

The LearningResource registry (`graph/resources.yaml`) is authored at
**per-material grain**: one entry per course, book, doc site, or video series,
with a stable **root URL**. Chapter- and unit-level deep links live in the
node body's *Study pointers* section, not the registry — this keeps the
registry small (~30–45 entries) and slow to rot while nodes still say where to
start. Each node carries **1–3** supporting resources: enough for a study path,
few enough to avoid choice paralysis.

Selection criteria, in priority order:

1. **Free-first** — every primary resource is free. No paid materials.
2. **Provider URL-stability over novelty** — prefer providers whose links
   outlive fashions.
3. **Modality matched to the node's gate** — runnable exercises for
   objective-gated code nodes; worked problems with answers for manual-gated
   math nodes.
4. **Honest claims or no entry** — `cost`, `free_tier`, `certificate`, and
   `license` are filled from the provider's actual current terms observed
   during a web pass, never assumed.

**Verification is human, not machine.** An agent may draft resource entries and
a verification worksheet (claims filled from live pages, uncertainties flagged),
but the learner clicks through and personally runs the `verify-resource`
command block. An agent never runs `verify-resource` — held in the spirit of
the pass/master boundary. Entries the learner does not get to ship *honestly
unverified* (warned, never blocking); the 180-day staleness window catches them
later. A seed that lies is worse than one that admits what it hasn't checked.

## The lean node template

A node markdown file is **pure curriculum**: identity, description, effort, and
honest anchor metadata. State lives in the progress store and relationships in
`edges.yaml` (ADR 0001). Frontmatter carries exactly these keys:

```yaml
id: <namespace>.<topic>_NN        # immutable; the suffix is a sequence, not a version
title: <imperative skill name>
summary: <one sentence — what the learner can do>
domain: <broad area>
track: foundational | core | consolidation | portfolio | remediation
roadmap_anchors:                  # only where a genuine old-roadmap counterpart exists
  - phase: phase_0
    phase_label: <label>
    month_range: "1-3"
    roadmap_topic: <topic>
    source_role: reference_only   # required on every anchor
estimated_effort:
  min_minutes: <int>
  max_minutes: <int>
micro_session_fit:                # MUST be consistent with min_minutes (see below)
  can_fit_15_min: <bool>
  can_fit_30_min: <bool>
  requires_long_block: <bool>
tags: [ ... ]
created_at: <date>
updated_at: <date>
```

**Do not** carry `mastery_policy`, `competency_dimensions`, or a legacy `level`
field. `mastery_policy` was a shadow gate that could contradict the real
ValidationGate; `competency_dimensions` was never read — its self-review role
belongs to the gate's acceptance summary. The node loader tolerates unknown
keys, so these are an editorial rule, not a load error; the seed-acceptance
suite (`tests/seed`) enforces their absence.

**Effort / session-fit consistency.** `micro_session_fit` is derived from
`estimated_effort.min_minutes` and must never claim a window the node cannot
fit:

| condition            | `can_fit_15_min` | `can_fit_30_min` | `requires_long_block` |
| -------------------- | ---------------- | ---------------- | --------------------- |
| `min_minutes <= 15`  | true             | true             | false                 |
| `16 <= min <= 30`    | false            | true             | false                 |
| `min_minutes > 30`   | false            | false            | true                  |

A "long block" here means *longer than the 30-minute micro-session ceiling* —
the node cannot be finished in either micro window. Session-fit scoring rests on
honest effort claims, so a 45-minute node does not advertise that it fits a
15-minute session.

**Body** — three sections only:

```markdown
# <title>

## Learning target

<what the learner will be able to do — usually the summary, expanded>

## Study pointers

<deep links into the registered resources: which chapter/unit to start with>

## Notes

<optional authoring notes; never learner state>
```

Empty `Evidence` / `Blockers` / `Reflection` shadow sections are gone — they
invited state into curriculum files. Evidence lives in the evidence layer;
blockers and reflection in the execution layer.

## Namespaces

Node IDs are immutable and name the topic truthfully forever. Bands are
dot-separated namespaces; author within the established set and mint a new one
only for a genuinely new band:

- Existing: `math.arithmetic.*`, `math.algebra.*`, `math.functions.*`,
  `programming.python.*`, `tooling.cli.*`, `tooling.git.*`, `data.csv.*`,
  `data.pandas.*`, `communication.*`, `portfolio.project.*`.
- Minted for the foundations rebuild: `math.statistics.*` (probability is part
  of this band, not a separate one), `math.linear_algebra.*`, `math.calculus.*`
  (named for the topic — depth is a curriculum choice that can deepen later, so
  not `calculus_intuition`), `data.visualization.*`, `consolidation.*`.

**A node's namespace says what the skill *is*; `track` and edges say what role
it *plays*.**

- **Remediation nodes get no namespace of their own.** A remediation node is an
  ordinary node homed in its natural domain (e.g. `math.arithmetic.fractions_01`)
  with `track: remediation`; its remediation role lives entirely in its edge
  type (`remediation`) and track label. Seed remediation few, at predictable
  fracture points; author the rest lazily from real Blockers.
- **`consolidation.*` earns a namespace** because a consolidation node is
  inherently cross-band — no single domain would be a truthful home. Weighted
  2.0 (above portfolio) so a standing nudge counteracts racing ahead without
  integrating.

## Tracks and weights

Five tracks, weighted in `policy/recommendation.yaml`. `track` names are opaque
to the engine (decision 18): a node's track is looked up in the weight map, and
an unmapped track scores 0 with a warning — so every track in use must be
mapped.

| track           | weight | role                                              |
| --------------- | ------ | ------------------------------------------------- |
| `foundational`  | 3.0    | the load-bearing foundations                      |
| `core`          | 2.0    | reserved for the post-foundations tranche         |
| `consolidation` | 2.0    | integration checkpoints; nudged above portfolio   |
| `portfolio`     | 1.0    | portfolio projects                                |
| `remediation`   | 0.5    | sinks at rest until an active remediation edge lifts it |
