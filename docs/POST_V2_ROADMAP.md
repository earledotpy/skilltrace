# Post-v2 Roadmap

Pick the next version slot from the table; read the linked spec
and tickets before writing the new doc's slot. Out-of-scope items
are signposted in **Beyond this roadmap** — re-opening any of
them is a separate effort, not a slot-table edit.

## Purpose

This is the **post-v2 application plan** for SkillTrace
(v2.0.0+). It lists shipped versions and the planned version sequence
through the **v3.0.0** capability milestone, and rules out items that
sequence does not address. It is signposting, not spec: per-slot
specs live in their own `docs/spec-<slot>.md`, written when each
slot ships. The original wayfinder map and the
[Map — v3.0.0 frontier: extend POST_V2 slots + adjudicate Beyond](https://github.com/earledotpy/skilltrace/issues/275)
carry the decision trail under [References](#references).
`POST_V3_ROADMAP.md` appears only when v3.0.0 ships, superseding this doc
by the POST_V1 → POST_V2 precedent; it is not written by this effort.

Domain terms are defined in [`CONTEXT.md`](../CONTEXT.md) (Learner,
Roadmap anchor, etc.). Structural decisions are recorded in
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
- **v2.2.0** — Provenance & graph-impact diagnostics (R-Provenance
  [#194](https://github.com/earledotpy/skilltrace/issues/194)):
  gate-run receipts on objective-gate evidence records (exact argv, input
  paths, exit class, optional exit code + output hashes), and the
  read-only `graph impact` advisory comparing the working tree against a
  git-ref baseline (flips, asserted-standing, recommendation diffs, dangling
  references, no-op edges); verified on the merged tree (full suite green,
  v2.2 §7 functional gates exit 0 on seed, safety + doc gates green);
  spec:
  [`docs/spec-v2.2-provenance-impact.md`](./spec-v2.2-provenance-impact.md).

- **v2.3.0** — Verification-hygiene hardening: polite batch sweeps
  (G-Hygiene [#193](https://github.com/earledotpy/skilltrace/issues/193)):
  nominal per-host spacing, one `robots.txt` fetch per host with
  fail-open, and bounded 429-only backoff over the existing
  `check-resource`/registry seam, with the `polite_sweep.yaml` seed
  validated under `validate policy`; sweeps stay manual (scheduling
  re-deferred) and purely read-only (never sets `last_verified`, never
  clears or writes `broken`, emits no event); verified on the merged tree
  (affected suites green, whole-repo sweep green modulo one pre-existing
  `test_cli.py` registry gap fixed in the same change); spec:
  [`docs/spec-v2.3-polite-sweep.md`](./spec-v2.3-polite-sweep.md).

- **v2.4.0** — Preference-driven, de-CLI-flavoured interface sublayer
  (map [#208](https://github.com/earledotpy/skilltrace/issues/208)):
  the ADR 0007 sublayer (`src/skilltrace/web/interface/`) — View/Card/
  Command/Active-view-state over the live dispatcher registry, import-time
  + serve-boot validation — plus the P3 card-stack Today, the `NextAction`
  typed fact with the days-practiced mirror, human controls, one analytics
  theme per page, structural omission for walled actions, and the P3.1
  forbidden-vocabulary translation seam; tier-0 zero-JS throughout
  (no ADR 0008; the no-`<script>` gate is release-tested); verified on the
  merged tree (web + interface suites green, CLI byte-identity captured on
  `today`/`next`/`node`); spec:
  [`docs/spec-v2.4-interface-sublayer.md`](./spec-v2.4-interface-sublayer.md).

## Version slots

The slot table combines [G-Slots](https://github.com/earledotpy/skilltrace/issues/196)
with [G-SlotsV3 — sequence the post-v2.4 slot table through v3.0.0](https://github.com/earledotpy/skilltrace/issues/281).
ROI (L × C → combined) follows the locked
[G-ROI rubric](https://github.com/earledotpy/skilltrace/issues/99); **Enables**
captures the compound-value chain. The post-v2.4 posture is criterion-led
with an ROI floor: each feature slot must independently clear the rubric,
not ride the criterion at L. The terminal row is an exit gate, not a
scored feature, so its ROI is **—**.

| Slot | Theme | ROI (L, C → combined) | Enables | Acceptance |
|---|---|---|---|---|
| **v2.1** | Adaptive sequencing + retention overlay (FSRS) — *carried fixed from POST_V1 verbatim per map [#191](https://github.com/earledotpy/skilltrace/issues/191): shipped as v2.1.0; binds to the v1.6 event log + v1.5 retention model; advisory-only* | **M** (M, M) | closes the long arc | retention overlay bound to v1.6 event log; advisory-only |
| **v2.2** | Provenance & graph-impact diagnostics — bounded gate-run receipts (immutable, optional fields: normalized command identity, root-relative inputs, tool/version, exit class, output hashes; secrets/unbounded logs excluded) + read-only pre-release graph-impact diagnostic (derived lock/unlock flips, recommendation changes, dangling refs, no-op edges) | **M** (M, M) | future gate-runner extension when a Phase 4/5 seed artifact needs it; trustworthy pre-release verification of curriculum edits | theme + ROI, plus: receipt fields immutable + optional; unrunnable gate = no record; receipt never passes/masters; diagnostic read-only, `edges.yaml`-only, asserted states immutable, never blocks a human action; pytest green |
| **v2.3** | Verification-hygiene hardening: polite batch sweeps — per-host rate limiting, `robots.txt` respect, 429 backoff — over the existing `check-resource`/registry seam. *Scheduling automation re-deferred with named trigger; deep-verification ruled Beyond (see Beyond list).* | **M** (M, M) | (hygiene; no slot depends on it) | theme + ROI, plus: offline-fixture gates for bucket/backoff/`robots.txt` behavior; safety assertions extending the v1.7 posture (polite sweep still never writes `last_verified`, never clears `broken`, appends no new event shapes); policy seed keys validate under `validate policy`; pytest green |
| **v2.4** | Preference-driven, de-CLI-flavoured Tier 1 interface direction over the ADR 0007 sublayer (audit-informed; prototypes validated): Python-derived View/Card vocabulary, card-composed daily screens, locked design direction (P1-Evolve base + P3 card-stack Today) + palette/type/spacing tokens, tier-0 zero-JS interaction posture; import-time + request-time validated | **M** (M, M) | future Tier 1 polish; no POST_V2 slot depends on it | theme + ROI, plus: sublayer import-validated (serve refuses to start on inconsistency); request-time gating splits structural (action omitted, wall still rendered) from judgment (live with advisory text) per ADR 0007 Amendment 2026-09-11; route surface restructurable downward only per G-RouteSurface (no new top-level view; table normative in spec-tier1-serve §C); design direction + palette per G-Direction (P1-Evolve base over every surface, P3 card-stack Today — ≤4 card-level blocks, one CTA, zero tables, no `<details>` on the primary path); interaction posture tier 0 per G-JS (no JS budget — no ADR 0008, ADR 0006 unamended; the sublayer emits no `<script>`, a grep-able gate); no hand-declared YAML; hard boundaries carried verbatim; pytest green |
| **v2.5** | Phase 4/5 + capstone seed graphs — curriculum seed data only: authors nodes/edges/resources (+ policy values), never engine behavior | **M** (M, H) | gives the criterion day its substance; first real load for v2.2 gate-run receipts; portfolio content | theme + ROI, plus: seed validation fails loudly on bad seeds; write path hardened in the same slot — atomic temp-file writes + corrupt-file quarantine, single-writer serialization contract honored; authored nodes carry none of the forbidden frontmatter keys; hard boundaries carried verbatim; pytest green |
| **v2.6** | Honest mirrors & honest-progress surfaces — nine-item cluster: root-cause prerequisite trace on repeated failure; rigor-as-avoidance visibility report; confidence self-report as an execution fact; scheduler-transparency surface for the retention overlay; honesty display contract; non-punitive overdue/backlog-mercy surface; what-moved-today summary; eligibility-coverage metric with explicit denominator; self-grading-norms copy rule + delayed-feedback-as-repair stance | **M** (M, M) | closes toward the criterion's visibility bar (retention pressure, blocker/remediation state, provenance-bearing evidence visible on the day) | theme + ROI, plus: every surface a read-only mirror or advisory copy rule over already-computed facts — no new authority, nothing gates or blocks, asserted progress untouched; the honesty display contract is the shared invariant the other eight render under; pytest green |
| **v3.0.0** | Capability milestone — the live study day through the non-CLI surfaces (planned-day surface test), plus the consolidation rider; truncates the sequence when met | **—** | — | *v3.0.0 ships when, on the live graph, the learner can see, work, and close a full study day entirely through the non-CLI surfaces — today → work → evidence → session close — with retention review pressure, blocker/remediation state, and provenance-bearing evidence visible on that day, and the consolidation rider holds: (1) deprecated v2.x schema/doc surfaces migrated or formally sunset (the known candidate is the pre-v0.3 node-frontmatter migration), (2) `archive/scaffold-v0.1` and interface-layer history confirmed fully settled per ADR 0005, (3) full suite + all per-slot gates green on the merged tree per the established verification convention.* |

The original four slots score M (M, M), so ROI does not order them; their sequence is set by the
carry-verbatim lock (v2.1 first) plus two asymmetries: v2.2's gate-run receipts are
immutable, so freezing the schema early is the value, and its diagnostic half gives
release-time visibility exactly when the v2.x train runs; v2.3 hygiene follows on
cost-minimal grounds (smallest, touches nothing downstream); v2.4 interface closes
(no slot depends on it, no time window, most new surface). Full rationale lives on
[G-Slots](https://github.com/earledotpy/skilltrace/issues/196).

The new feature slots also score M; criterion-led ordering puts **v2.5**
first for study-day substance, write-path durability, and the earliest
receipt-backed gate-runner re-check. **v2.6** is the cost-minimal close
toward the visibility bar, touching nothing downstream; **v3.0.0** terminates.
Single-writer serialization, atomic writes + quarantine, and fail-loudly
validation are folded into v2.5 acceptance, not separate slots. The nine
honesty items remain one v2.6 cluster. Full rationale and ROI audit live on
[G-SlotsV3 — sequence the post-v2.4 slot table through v3.0.0](https://github.com/earledotpy/skilltrace/issues/281).

The terminal criterion is verbatim from
[G-V3 criterion — what must be true for v3.0.0 to ship](https://github.com/earledotpy/skilltrace/issues/276)
and immutable since G-SlotsV3 closed. It is a deterministic **planned-day
surface test**, not proof of an actual lived study day: no learner cadence,
date, numeric floor, or individual feature is required. The full planned
path above truncates at the first completed slot satisfying the criterion;
v3.0.0 may ship early without erasing history. If the last listed slot leaves
it unmet, the next map extends the sequence, never rewords the criterion.

The consolidation rider was already approximately satisfied at sequencing:
G-SlotsV3 recorded 0/100 graph node files with forbidden frontmatter, settled
archive history per ADR 0005, and merged-tree verification as standing
convention. These conditions are **verified at exit**, not new work or a slot.

### Phase-mapping sidebar

The post-v2 application-version slots above are a **version
sequence**, not a re-labeling of the AI-curriculum phases in
[`docs/roadmap/phase-*.md`](./roadmap/). The bridge is:

- v2.1's adaptive-sequencing feature can use Phase 3 / Phase 4
  agent recommendations as an input, but the application slot
  is independent of the curriculum phase. The v2.5 seed-graph
  slot authors curriculum *files* under `graph/`; it is not a
  curriculum-phase application slot either.

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
future effort, not a slot-table edit. The post-v2.4 adjudication is
[G-Beyond verdicts — graduate, defer, or reject each Beyond item](https://github.com/earledotpy/skilltrace/issues/280):
five rejects, seven defers, one graduate. **Phase 4/5 + capstone seed
graphs graduated to v2.5** and are no longer deferred here; portable
evidence locator and default-deny share-profile extensions are two
additional defers from G-SlotsV3. The later Tier 3 and advisory-AI
resolutions below do not silently add slots.

*Restated, never slots (hard boundaries — carried from POST_V1 unchanged):*

- **Auto-master / auto-pass** — rejected: passing and mastering are explicit learner commands, never automated (`CONTEXT.md` Hard boundary); never re-opened by this effort.
- **LLM-graded evidence** — rejected: AI is never an acceptance authority (`CONTEXT.md` Acceptance authority); never re-opened by this effort.

*Boundary-gated (re-open only if the boundary itself changes):*

- **Cloud sync / server-side engine** — rejected: the local-first
  boundary holds; files are truth, Export and Serve never are.
  The multi-device learner-UX trigger is unmet; no ADR work is named.
- **Elo / BKT-style mastery modeling** — rejected: its trigger would
  repeal the never-demotion safety rule, not respond to a world change.
  The v2.1 retention overlay already surfaces shaky retention without
  revoking mastery.
- **Generative AI tutoring** — rejected: the AI-as-authority trigger
  is a hard boundary this effort never re-opens. The separate
  [G-AdvisoryAI — can a free cloud API or small local model power the Mentor advisory seam?](https://github.com/earledotpy/skilltrace/issues/283)
  permits an optional **Advisory model**, not an authority or a slot:
  local-first, restricted cloud payload of derived curriculum-metadata
  facts only, silent static-Mentor fallback. It stays an eligible candidate
  requiring an explicit roadmap decision; no placeholder row is added.
  The glossary term landed before wiring via
  [T-AdvisoryModelTerm — add the Advisory model glossary term to CONTEXT.md](https://github.com/earledotpy/skilltrace/issues/286).

*Deferred (re-open on the named trigger):*

- **Diagnostic analytics (learner-facing)** — defer. Trigger: a first
  real blocker or failed assessment attempt (friction to diagnose),
  **or learner demand for the primitive**. Friction-shaped, not
  day-count-shaped. These "why am I stuck / why recommended" primitives
  are distinct from operational analytics and pre-release graph impact.
  [P-DiagnosticsSim — simulate the learner-facing diagnostic surface on fixture data](https://github.com/earledotpy/skilltrace/issues/285)
  links the throwaway simulation; whether it is *wanted* is the
  learner's call on reading it — the demand branch trips as a new
  verdict on [G-Beyond verdicts — graduate, defer, or reject each Beyond item](https://github.com/earledotpy/skilltrace/issues/280),
  never an automatic slot.
- **Practice profiles + prompt extraction** — defer. Trigger: a first
  real review backlog (reviews accumulating under retention pressure).
  R-MineBeyond found no reviews: a sequencing layer on an empty model
  builds nothing. Protocols remain opaque advisory session-template values;
  extracted prompts are disposable output, never acceptance authority.
- **Badge issuance** — defer. Trigger: a concrete portfolio consumer
  demands a badge primitive. R-MineBeyond found zero passed/mastered nodes
  and no evidenced consumer despite the shipped portfolio — leaning reject
  while demand stays nil.
- **Multi-curriculum + PKM integrations (Tier 3)** — deferred, with
  directed triggers per
  [R-Tier3Contactless — size MC/PKM integration from public sources, no outreach](https://github.com/earledotpy/skilltrace/issues/284)
  and the learner's follow-up on G-RoadmapWrite:
  **MC-1/MC-2** retain their fresh-user-demand trigger and M/L scores;
  neither requires a PKM. **MC-3** is no-go by construction under the
  single-learner glossary, not a deferred build. **PKM-2/PKM-3** re-open
  on fresh user demand: PKM-2's one-way-projection precondition improves,
  and PKM-3's engine-owned approval needs no upstream work, discharging
  the maintainer-reply dependency. **PKM-4** keeps the ecosystem-settling
  or fresh-demand trigger; its round-trip precondition worsens as the
  ecosystem moves toward one-way projections. The contactless go/no-go
  pre-read is complete, a sizing input to re-opening discussion, not
  graduation; outreach tests only the in-vault variant, not demand.
  Caveat (learner, 2026-09-16): no PKM is in use, so PKM demand is nil,
  not merely untripped. The learner explicitly kept PKM-2/3/4 deferred,
  not rejected. Any future vault integration must respect **one writer
  per path**, with SkillTrace-owned paths namespaced and watcher-ignored.
  PKM-1 already shipped inside Tier 1 as `serve`.
- **Full gate-runner / scheduler-queue** — defer. Trigger: a concrete
  Phase 4/5 seed artifact whose objective gates are hand-run often
  enough to automate; the first real evidence record with receipts in
  active use is the earliest re-check (v2.5's receipt load is the
  earliest such re-check).
- **Verification-sweep scheduling automation** — defer. Trigger
  unchanged (disjunction): demonstrated manual-sweep cadence, a
  downstream slot needing scheduled checks, or serve/today
  background-sweep work. Doctrine rider: whatever schedules only
  ever flags (`broken`), never asserts `last_verified`.
- **Resource deep-verification (cert metadata, content-hash
  drift)** — defer. Trigger: a content-drift incident a hash check
  would have caught, or a host/publisher requiring pinned-content
  verification. If it ever trips: the cert-metadata slice first
  (structured fields over existing license prose); hash-drift
  detection needs a stored baseline the registry lacks —
  schema-adjacent, not a slot.
- **Portable evidence locator** — defer until a second external consumer of evidence records beyond the portfolio export exists (G-SlotsV3); no consumer yet justifies the contract.
- **Default-deny share profile extensions** — defer until a second sharing/export surface demands a privacy posture (G-SlotsV3); the existing portfolio Share profile remains in force.

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
  until then, per G-Slots). v2.3 ships
  [`docs/spec-v2.3-polite-sweep.md`](./spec-v2.3-polite-sweep.md);
  v2.4 ships
  [`docs/spec-v2.4-interface-sublayer.md`](./spec-v2.4-interface-sublayer.md).
- [`docs/skilltrace-application-roadmap.md`](./skilltrace-application-roadmap.md) (v1 application plan;
  its post-v1 section already points at POST_V1 — POST_V2 joins
  that pointer trail when it lands)
- [`CONTEXT.md`](../CONTEXT.md) (ubiquitous language)
- [`docs/adr/`](./adr/) (structural decisions; ADR 0007 governs the
  interface sublayer; no new ADR from the v3.0.0 frontier map).
  The carried v2.4 entries record the original zero-JS release posture;
  [ADR 0008](./adr/0008-inline-progressive-enhancement-posture.md)
  subsequently accepted the narrowly capped chart-tooltip grant.
- The original wayfinder map
  ([#191](https://github.com/earledotpy/skilltrace/issues/191)) and its
  [G-Interface](https://github.com/earledotpy/skilltrace/issues/192),
  [G-Hygiene](https://github.com/earledotpy/skilltrace/issues/193),
  [R-Provenance](https://github.com/earledotpy/skilltrace/issues/194),
  [R-Practice](https://github.com/earledotpy/skilltrace/issues/195),
  [G-Slots](https://github.com/earledotpy/skilltrace/issues/196),
  [G-Beyond](https://github.com/earledotpy/skilltrace/issues/197),
  [G-DocShape](https://github.com/earledotpy/skilltrace/issues/198)
  tickets — the POST_V2 table + Beyond trail.
- [Map — v3.0.0 frontier: extend POST_V2 slots + adjudicate Beyond](https://github.com/earledotpy/skilltrace/issues/275)
  and its
  [G-V3 criterion — what must be true for v3.0.0 to ship](https://github.com/earledotpy/skilltrace/issues/276),
  [R-MineBeyond — evidence brief on each deferred Beyond candidate](https://github.com/earledotpy/skilltrace/issues/277),
  [R-MineDocsArchive — candidacy sweep of docs/ and archive/](https://github.com/earledotpy/skilltrace/issues/278),
  [G-BoundaryGated — cloud sync, Elo/BKT, generative tutoring: do any re-open?](https://github.com/earledotpy/skilltrace/issues/279),
  [G-Beyond verdicts — graduate, defer, or reject each Beyond item](https://github.com/earledotpy/skilltrace/issues/280),
  [G-SlotsV3 — sequence the post-v2.4 slot table through v3.0.0](https://github.com/earledotpy/skilltrace/issues/281),
  [G-AdvisoryAI — can a free cloud API or small local model power the Mentor advisory seam?](https://github.com/earledotpy/skilltrace/issues/283),
  [R-Tier3Contactless — size MC/PKM integration from public sources, no outreach](https://github.com/earledotpy/skilltrace/issues/284),
  [P-DiagnosticsSim — simulate the learner-facing diagnostic surface on fixture data](https://github.com/earledotpy/skilltrace/issues/285),
  [T-AdvisoryModelTerm — add the Advisory model glossary term to CONTEXT.md](https://github.com/earledotpy/skilltrace/issues/286)
  tickets — the post-v2.4 sequence and Beyond adjudication trail,
  plus the locked G-ROI rubric ([#99](https://github.com/earledotpy/skilltrace/issues/99)).
