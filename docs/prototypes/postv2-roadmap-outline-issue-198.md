<!-- ============================================================
     PROTOTYPE — throwaway outline. NOT production documentation.
     Wayfinder ticket: G-DocShape #198 (map #191)
     Question under test: the document shape of docs/POST_V2_ROADMAP.md
     Content inputs: G-Slots #196 (slot table, Shipped reconciliation,
     v2.1 carry annotation) and G-Beyond #197 (Beyond roster).
     Everything rendering-shaped here is sketch; final wording is
     handoff. React, decide, delete. Lives only on branch
     prototype/postv2-roadmap-outline-issue-198.
     ============================================================ -->

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
([#191](https://github.com/earledotpy/skilltrace/issues/191)) is
the trail of decisions that produced the table.

Domain terms are defined in
[`CONTEXT.md`](../CONTEXT.md) (Learner, Compound value, Roadmap
anchor, etc.). Structural decisions are recorded in
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

## Version slots

The slot table, output of G-Slots
([#196](https://github.com/earledotpy/skilltrace/issues/196)),
with ROI (L × C → combined) from the locked G-ROI rubric
([#99](https://github.com/earledotpy/skilltrace/issues/99)) and
the **Enables** column capturing the compound-value chain.

| Slot | Theme | ROI (L, C → combined) | Enables | Acceptance |
|---|---|---|---|---|
| **v2.1** | Adaptive sequencing + retention overlay (FSRS) — *carried fixed from POST_V1 verbatim per map [#191](https://github.com/earledotpy/skilltrace/issues/191): unshipped as of v2.0.0; binds to the v1.6 event log + v1.5 retention model; advisory-only* | **M** (M, M) | closes the long arc | retention overlay bound to v1.6 event log; advisory-only |
| **v2.2** | Provenance & graph-impact diagnostics — bounded gate-run receipts (immutable, optional fields: normalized command identity, root-relative inputs, tool/version, exit class, output hashes; secrets/unbounded logs excluded) + read-only pre-release graph-impact diagnostic (derived lock/unlock flips, recommendation changes, dangling refs, no-op edges) | **M** (M, M) | future gate-runner extension when a Phase 4/5 seed artifact needs it; trustworthy pre-release verification of curriculum edits | theme + ROI, plus: receipt fields immutable + optional; unrunnable gate = no record; receipt never passes/masters; diagnostic read-only, `edges.yaml`-only, asserted states immutable, never blocks a human action; pytest green |

*(The locked table also has v2.3 verification-hygiene and v2.4
interface-sublayer rows — elided from this outline.)*

### Phase-mapping sidebar

The post-v2 application-version slots above are a **version
sequence**, not a re-labeling of the AI-curriculum phases in
[`docs/roadmap/phase-*.md`](./roadmap/). The bridge is:

- v2.1's adaptive-sequencing feature can use Phase 3 / Phase 4
  agent recommendations as an input, but the application slot
  is independent of the curriculum phase.

This sidebar is the only place this doc references the
`docs/roadmap/phase-*.md` files; the application slot list and
the curriculum phase list are tracked separately.

### How to use this doc

Who this doc is for, and what each reader does with it
(human or agent): the next-slot picker (human or agent) reads
[Version slots](#version-slots); readers reconstructing why the
table looks the way it does read the map + tickets under
[References](#references); nobody dispatches
engines from this file.

### Beyond this roadmap

Items explicitly out of scope for the version-slot sequence in
this document. Each is either ruled out by a current design
boundary (and stays out while that boundary holds) or deferred
past the slot sequence. Re-opening any item is a separate
future effort, not a slot-table edit.

*(Grouped rendering example:)*

*Restated, never slots (hard boundaries — carried from POST_V1 unchanged):*

- **Auto-master / auto-pass** — forbidden by the v1 hard
  boundary (`AGENTS.md`, `CONTEXT.md` Hard boundary); not
  re-openable while the boundary holds.

*Deferred (re-open on the named trigger):*

- **Diagnostic analytics (learner-facing)** — "why am I stuck / why recommended" primitives, distinct from v1.6's operational event-log analytics **and** from v2.2's pre-release graph-impact diagnostic; re-opens if diagnostic-as-a-primitive is wanted.

*Holding contracts (listed so the boundary stays visible; not
deferred work):*

### References

- [`docs/spec-tier1-serve.md`](./spec-tier1-serve.md) (v1.4 spec)
- [`docs/spec-tier2-retention-analytics.md`](./spec-tier2-retention-analytics.md) (v1.5 spec)
- [`docs/skilltrace-application-roadmap.md`](./skilltrace-application-roadmap.md)
  (v1 application plan; its post-v1 section already points at
  POST_V1 — POST_V2 joins that pointer trail when it lands)

### Out of scope for the outline

Q&A mapping: each numbered decision → where it is exercised
above; final answers go in the G-DocShape #198 resolution, not
here.

1. **Columns verbatim** → the two table rows.
2. **Shipped style** → the v2.0.0 line.
3. **Phase-mapping sidebar** → its section above.
4. **Beyond semantics + `reference_only` citation** → the
   sidebar's single reference and the Beyond bullets.

