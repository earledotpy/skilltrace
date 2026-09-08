# Post-v2 Roadmap

Pick the next version slot from the table; read the linked spec
and tickets before writing the new doc's slot. Out-of-scope items
are signposted in **Beyond this roadmap** — re-opening any of
them is a separate effort, not a slot-table edit.

## Purpose

This is the **post-v2 application plan** for SkillTrace
(v2.0.0+). It lists shipped versions, names the next four version
slots in order, and rules out items that the version-slot
sequence does not address. It is signposting, not spec: per-slot
specs live in their own `docs/spec-<slot>.md`, written when each
slot ships, and the wayfinder map
([#191](https://github.com/earledotpy/skilltrace/issues/191)) is the trail of decisions that
produced the table.

Domain terms are defined in [`CONTEXT.md`](../CONTEXT.md) (Learner,
Compound value, Roadmap anchor, etc.). Structural decisions are recorded in
[`docs/adr/`](./adr/).

## Shipped

One line per shipped version, in order. The list is closed; new
shipped entries are append-only. Each shipped entry carries a
verification note.

- **v1.0.0** — SkillTrace v1.0.0 stable release.
- **v1.4** — Tier 1 (Web UI + `skilltrace serve`, via
  [#62](https://github.com/earledotpy/skilltrace/issues/62));
  spec: [`docs/spec-tier1-serve.md`](./spec-tier1-serve.md).
- **v1.5** — Tier 2 (FSRS retention analytics, retro-numbered
  via G-Retro [#103](https://github.com/earledotpy/skilltrace/issues/103) from "unversioned" via map
  [#86](https://github.com/earledotpy/skilltrace/issues/86));
  spec: [`docs/spec-tier2-retention-analytics.md`](./spec-tier2-retention-analytics.md).
- **v2.0.0** — Slots v1.6 (event-log analytics) + v1.7
  (resource web-verification) + v1.8 (Phase 2 ML seed graph) +
  v1.9 (Phase 3 agent seed graph + deployment primer) + v2.0
  (Portfolio builder); verified on the merged tree (100 nodes /
  157 edges / 45 resources, full suite + all per-slot gates
  green) via
  [#183](https://github.com/earledotpy/skilltrace/issues/183)–
  [#190](https://github.com/earledotpy/skilltrace/issues/190).
- **v2.1.0** — Adaptive sequencing + retention overlay (FSRS):
  retention-urgency sequencing from below-threshold prerequisite
  retention pressure, advisory agent-signal factor, delay-aware
  per-node retention model (seeds `policy.recommendation.default_v0_7`
  + `policy.retention.default_v1_0`), `suggest reviews` retention
  section, `retention status --node-id`; verified on the merged tree
  (full suite green; v2.1 §7 functional gates exit 0 on seed, safety
  + doc gates green); spec:
  [`docs/spec-v2.1-adaptive-sequencing.md`](./spec-v2.1-adaptive-sequencing.md).

## Version slots

The slot table, output of G-Slots
([#196](https://github.com/earledotpy/skilltrace/issues/196)), with ROI (L × C → combined) from the
locked G-ROI rubric ([#99](https://github.com/earledotpy/skilltrace/issues/99)) and the **Enables**
column capturing the compound-value chain.

| Slot | Theme | ROI (L, C → combined) | Enables | Acceptance |
|---|---|---|---|---|
| **v2.1** | Adaptive sequencing + retention overlay (FSRS) — *carried fixed from POST_V1 verbatim per map [#191](https://github.com/earledotpy/skilltrace/issues/191): shipped as v2.1.0; binds to the v1.6 event log + v1.5 retention model; advisory-only* | **M** (M, M) | closes the long arc | retention overlay bound to v1.6 event log; advisory-only |
| **v2.2** | Provenance & graph-impact diagnostics — bounded gate-run receipts (immutable, optional fields: normalized command identity, root-relative inputs, tool/version, exit class, output hashes; secrets/unbounded logs excluded) + read-only pre-release graph-impact diagnostic (derived lock/unlock flips, recommendation changes, dangling refs, no-op edges) | **M** (M, M) | future gate-runner extension when a Phase 4/5 seed artifact needs it; trustworthy pre-release verification of curriculum edits | theme + ROI, plus: receipt fields immutable + optional; unrunnable gate = no record; receipt never passes/masters; diagnostic read-only, `edges.yaml`-only, asserted states immutable, never blocks a human action; pytest green |
| **v2.3** | Verification-hygiene hardening: polite batch sweeps — per-host rate limiting, `robots.txt` respect, 429 backoff — over the existing `check-resource`/registry seam. *Scheduling automation re-deferred with named trigger; deep-verification ruled Beyond (see Beyond list).* | **M** (M, M) | (hygiene; no slot depends on it) | theme + ROI, plus: offline-fixture gates for bucket/backoff/`robots.txt` behavior; safety assertions extending the v1.7 posture (polite sweep still never writes `last_verified`, never clears `broken`, appends no new event shapes); policy seed keys validate under `validate policy`; pytest green |
| **v2.4** | Tier 1 interface sublayer (ADR 0007): Python-derived View/Card vocabulary over the dispatcher registry — card-composed, de-CLI-flavoured daily screens; import-time + request-time validated | **M** (M, M) | future Tier 1 polish; no POST_V2 slot depends on it | theme + ROI, plus: sublayer import-validated (serve refuses to start on inconsistency); request-time gating omits engine-refused actions; no hand-declared YAML; existing Tier 1 route surface unchanged; pytest green |

All four slots score M (M, M), so ROI does not order them; the sequence is set by the
carry-verbatim lock (v2.1 first) plus two asymmetries: v2.2's gate-run receipts are
immutable, so freezing the schema early is the value, and its diagnostic half gives
release-time visibility exactly when the v2.x train runs; v2.3 hygiene follows on
cost-minimal grounds (smallest, touches nothing downstream); v2.4 interface closes
(no slot depends on it, no time window, most new surface). Full rationale lives on
[G-Slots](https://github.com/earledotpy/skilltrace/issues/196).

### Phase-mapping sidebar

The post-v2 application-version slots above are a **version
sequence**, not a re-labeling of the AI-curriculum phases in
[`docs/roadmap/phase-*.md`](./roadmap/). The bridge is:

- v2.1's adaptive-sequencing feature can use Phase 3 / Phase 4
  agent recommendations as an input, but the application slot
  is independent of the curriculum phase.

This sidebar is the only place this doc references the
`docs/roadmap/phase-*.md` files; the application slot list and
the curriculum phase list are tracked separately. Curriculum
phase files are `reference_only` anchors that never control
locking or recommendation (`CONTEXT.md` Roadmap anchor).

### How to use this doc

The next-slot picker (human or agent) reads [Version slots](#version-slots).
Readers reconstructing why the table looks this way read the map + tickets under
[References](#references). Nobody dispatches engines from this file.

## Beyond this roadmap

Items explicitly out of scope for the version-slot sequence in
this document. Each is either ruled out by a current design
boundary (and stays out while that boundary holds) or deferred
past the slot sequence. Re-opening any item is a separate
future effort, not a slot-table edit. Once v2.4 ships, every item
below opens as candidacy for whatever follows; that discussion
happens after v2.4 is implemented.

*Restated, never slots (hard boundaries — carried from POST_V1 unchanged):*

- **Auto-master / auto-pass** — forbidden by the v1 hard
  boundary (`AGENTS.md`, `CONTEXT.md` Hard boundary); not
  re-openable while the boundary holds.
- **LLM-graded evidence** — AI is never an acceptance authority
  (v1 hard boundary, `CONTEXT.md` Acceptance authority); not
  re-openable while the boundary holds.

*Boundary-gated (re-open only if the boundary itself changes):*

- **Cloud sync / server-side engine** — local-first by design
  (`CONTEXT.md`: Export + Serve are derived views, never truth);
  re-opens if multi-device learner UX is added.
- **Elo / BKT-style mastery modeling** — mastery state is
  permanent by design (`CONTEXT.md` Node states); re-opens if
  mastery stops being permanent.
- **Generative AI tutoring** — the engine treats AI as advisory
  only (`CONTEXT.md` Advisory annotation); re-opens if an
  AI-as-authority path is ever added.

*Deferred (re-open on the named trigger):*

- **Diagnostic analytics (learner-facing)** — "why am I stuck /
  why recommended" primitives, distinct from v1.6's operational
  event-log analytics **and** from v2.2's pre-release
  graph-impact diagnostic; re-opens if diagnostic-as-a-primitive
  is wanted.
- **Practice profiles + prompt extraction** — protocols as opaque
  advisory session-template values, prompt extraction as
  disposable derived output, strictly advisory (never
  gate/evidence/pass-master authority) per R-Practice
  ([#195](https://github.com/earledotpy/skilltrace/issues/195));
  re-opens post-v2.1, once the retention overlay has produced
  enough data to sequence practice.
- **Badge issuance** — no badge primitive in the engine;
  re-opens if a portfolio consumer demands one.
- **Multi-curriculum + PKM integrations (Tier 3)** — MC-1, MC-2,
  MC-3, PKM-2, PKM-3, PKM-4; re-opens on the PKM-ecosystem
  rewrite settling or fresh user-demand evidence; PKM-3 is
  additionally provisional pending maintainer replies (outreach
  prep complete per
  [#106](https://github.com/earledotpy/skilltrace/issues/106); a
  non-reply after the response window is itself a sizing signal).
- **Phase 4/5 + capstone seed graphs** — consumers of this
  sequence's seams (gate-run receipts, graph-impact diagnostics,
  later practice profiles over the v2.1 overlay); re-opens as a
  post-POST_V2 "adaptable ideas/features/functionality" effort —
  a future version is not pre-ruled — but they are never engine
  slots in this sequence.
- **Full gate-runner / scheduler-queue** — v2.2 ships only the
  bounded receipt + read-only diagnostic (R-Provenance
  [#194](https://github.com/earledotpy/skilltrace/issues/194));
  re-opens when a concrete Phase 4/5 seed artifact needs
  automated gate runs — the receipts are the precondition.
- **Verification-sweep scheduling automation** — sweeps stay
  manual in v1.7/v2.3; re-opens when unattended sweeps are
  actually wanted: demonstrated manual-sweep cadence, a
  downstream slot needing scheduled checks, or serve/today
  background-sweep work. Doctrine rider: whatever schedules only
  ever flags (`broken`), never asserts `last_verified`.
- **Resource deep-verification (cert metadata, content-hash
  drift)** — only cert-*metadata* inspection and hash-drift
  detection are new (implicit TLS validation already exists in
  `check_url`); re-opens on evidence of content drift harming
  study (an incident a content-hash check would have caught) or
  a host/publisher requiring pinned-content verification.

*Holding contracts (listed so the boundary stays visible; not deferred work):*

- **Single-writer CLI/serve write path** — every UI action is a
  dispatcher-mediated command appending one audit event; re-opens
  only if a surface ever needs a second write path — an
  ADR-gated change, never a slot.
- **Sync conflict matrix** — the written precondition for any
  sync transport (research rank 3); re-opens when cloud sync
  re-opens — it is transport's gate.
- **Plugin capabilities** — no third-party capability surface in
  the engine; re-opens with Tier 3 integrations.

**Not in this list (already ruled elsewhere).** Multi-learner /
multi-user is already a glossary ruling (`CONTEXT.md:1-8` —
single-learner-by-design; a second learner forks the curriculum
without the progress store). Naming it again in the post-v2
doc would restate a glossary ruling, not add a new one.

## References

- [`docs/spec-tier1-serve.md`](./spec-tier1-serve.md) (v1.4 spec)
- [`docs/spec-tier2-retention-analytics.md`](./spec-tier2-retention-analytics.md) (v1.5 spec)
- Per-slot specs for v1.6–v2.0 shipped with their slots; specs
  for v2.1+ are written when each slot ships (slot-row only
  until then, per G-Slots).
- [`docs/skilltrace-application-roadmap.md`](./skilltrace-application-roadmap.md) (v1 application plan;
  its post-v1 section already points at POST_V1 — POST_V2 joins
  that pointer trail when it lands)
- [`CONTEXT.md`](../CONTEXT.md) (ubiquitous language)
- [`docs/adr/`](./adr/) (structural decisions; this map's only
  ADR interaction is ADR 0007, which v2.4 implements as-written —
  no new ADR from this map)
- Wayfinder map
  ([#191](https://github.com/earledotpy/skilltrace/issues/191)) and the G-Interface
  ([#192](https://github.com/earledotpy/skilltrace/issues/192)), G-Hygiene
  ([#193](https://github.com/earledotpy/skilltrace/issues/193)), R-Provenance
  ([#194](https://github.com/earledotpy/skilltrace/issues/194)), R-Practice
  ([#195](https://github.com/earledotpy/skilltrace/issues/195)), G-Slots
  ([#196](https://github.com/earledotpy/skilltrace/issues/196)), G-Beyond
  ([#197](https://github.com/earledotpy/skilltrace/issues/197)), G-DocShape
  ([#198](https://github.com/earledotpy/skilltrace/issues/198)) tickets for the trail of decisions,
  plus the locked G-ROI rubric ([#99](https://github.com/earledotpy/skilltrace/issues/99)).
