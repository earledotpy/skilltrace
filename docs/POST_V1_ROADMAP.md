# Post-v1 Roadmap

Pick the next version slot from the table; read the linked spec
and tickets before writing the new doc's slot. Out-of-scope items
are signposted in **Beyond this roadmap** — re-opening any of
them is a separate effort, not a slot-table edit.

## Purpose

This is the **post-v1 application plan** for SkillTrace
(v1.0.0+). It lists shipped versions, names the next six version
slots in order, and rules out items that the version-slot
sequence does not address. It is signposting, not spec: per-slot
specs live in their own `docs/spec-<slot>.md` and the wayfinder
map ([#95](https://github.com/earledotpy/skilltrace/issues/95)) is the trail of decisions that
produced the table.

Domain terms are defined in [`CONTEXT.md`](../CONTEXT.md) (Learner,
Compound value, ROAM, etc.). Structural decisions are recorded in
[`docs/adr/`](./adr/).

## Shipped

One line per shipped version, in order. The list is closed; new
shipped entries are append-only.

- **v1.0.0** — SkillTrace v1.0.0 stable release.
- **v1.4** — Tier 1 (Web UI + `skilltrace serve`, via
  [#62](https://github.com/earledotpy/skilltrace/issues/62));
  spec: [`docs/spec-tier1-serve.md`](./spec-tier1-serve.md).
- **v1.5** — Tier 2 (FSRS retention analytics, retro-numbered
  via G-Retro [#103](https://github.com/earledotpy/skilltrace/issues/103) from "unversioned" via map
  [#86](https://github.com/earledotpy/skilltrace/issues/86));
  spec: [`docs/spec-tier2-retention-analytics.md`](./spec-tier2-retention-analytics.md).

## Version slots

The slot table, output of G-Slot
([#100](https://github.com/earledotpy/skilltrace/issues/100)), with ROI (L × C → combined) from the
locked G-ROI rubric ([#99](https://github.com/earledotpy/skilltrace/issues/99)) and the **Enables**
column capturing the compound-value chain.

| Slot | Theme | ROI (L, C → combined) | Enables | Acceptance |
|---|---|---|---|---|
| **v1.6** | Event-log analytics v1: study velocity, blockers by domain, review completion, evidence coverage | **H** (H, H) | v2.0 (portfolio data), v2.1 (adaptive input) | theme + ROI |
| **v1.7** | Resource web-verification + stale-resource replacement | **M** (M, M) | (hygiene; no slot depends on it) | theme + ROI |
| **v1.8** | Phase 2 ML seed graph — MLCC, Andrew Ng **ML Specialization** (*Python*, not legacy Octave), ISLP (Python edition), Kaggle Learn. *No FastAPI/Docker — re-slotted to v1.9 per R-Phase2ML ([#97](https://github.com/earledotpy/skilltrace/issues/97)).* | **M** (M, H) | v1.9 (Phase 3 builds on classical ML) | seed graph exports; all 4 sources verified; ≥ 1 capstone integration |
| **v1.9** | Phase 3 LLM/agents/MCP seed graph — HF Agents Course, DSPy, LangGraph, smolagents, LlamaIndex, MCP (promoted to first-class per R-Phase3Agentic ([#98](https://github.com/earledotpy/skilltrace/issues/98))), Microsoft Agent Framework (replaces AutoGen), +OpenAI Agents SDK, +PydanticAI. **+ FastAPI + Docker Engine / Podman / Rancher Desktop / Finch / Colima** as a deployment primer (Docker Desktop *not* the default — see free-first doctrine absorbed into G-ROI). *Strictly Phase 3; see phase-mapping sidebar.* | **M** (M, H) | v2.1 (adaptive can use agent recommendations) | seed graph exports; all 9 sources verified; deployment primer works on free-first toolchain |
| **v2.0** | Portfolio builder + GitHub project report (one release) | **M** (M, H) | external sharing of work | theme + ROI |
| **v2.1** | Adaptive sequencing + retention overlay (FSRS) | **M** (M, M) | closes the long arc | retention overlay bound to v1.6 event log; advisory-only |

### Phase-mapping sidebar

The post-v1 application-version slots above are a **version
sequence**, not a re-labeling of the AI-curriculum phases in
[`docs/roadmap/phase-*.md`](./roadmap/). The bridge is:

- v1.8 ships **Phase 2** seed-graph content (classical ML).
- v1.9 ships **Phase 3** seed-graph content (LLM / agents / MCP)
  + a deployment primer that the Phase 3 + Phase 4 graph
  actually needs.
- v2.1's adaptive-sequencing feature can use Phase 3 / Phase 4
  agent recommendations as an input, but the application slot
  is independent of the curriculum phase.

This sidebar is the only place this doc references the
`docs/roadmap/phase-*.md` files; the application slot list and
the curriculum phase list are tracked separately.

## Beyond this roadmap

Items explicitly out of scope for the version-slot sequence in
this document. Each is either ruled out by a current design
boundary (and stays out while that boundary holds) or deferred
past the slot sequence. Re-opening any item is a separate
future effort, not a slot-table edit.

- **Auto-master / auto-pass** — forbidden by the v1 hard
  boundary (`AGENTS.md`, `CONTEXT.md` Hard boundary); not
  re-openable while the boundary holds.
- **LLM-graded evidence** — AI is never an acceptance authority
  (v1 hard boundary, `CONTEXT.md` Acceptance authority); not
  re-openable while the boundary holds.
- **Cloud sync / server-side engine** — local-first by design
  (`CONTEXT.md` Export + Serve are derived views, never truth);
  re-opens if multi-device learner UX is added.
- **Diagnostic analytics** — distinct from v1.6's operational
  event-log analytics; re-opens if diagnostic-as-a-primitive is
  wanted.
- **Elo / BKT-style mastery modeling** — mastery state is
  permanent by design (`CONTEXT.md` Node states); re-opens if
  mastery stops being permanent.
- **Generative AI tutoring** — engine treats AI as advisory
  only (`CONTEXT.md` Advisory annotation); re-opens if an
  AI-as-authority path is ever added.
- **Badge issuance** — no badge primitive in the engine;
  re-opens if external-sharing / portfolio needs them (post-v2.0).
- **Multi-curriculum + PKM integrations (Tier 3)** — long-horizon;
  MC-1 and PKM-1 fold into Tier 1 polish (v0.9.0-rc1) per
  R-Tier3 ([#96](https://github.com/earledotpy/skilltrace/issues/96)); MC-2, MC-3, PKM-2, and PKM-4 await
  the PKM-ecosystem rewrite settling or fresh user-demand
  evidence; PKM-3 is provisional pending the
  S-Tier3-PKMPluginAuthor ([#106](https://github.com/earledotpy/skilltrace/issues/106)) maintainer reply.

**Not in this list (already ruled elsewhere).** Multi-learner /
multi-user is already a glossary ruling (`CONTEXT.md:1-8` —
single-learner-by-design; a second learner forks the curriculum
without the progress store). Naming it again in the post-v1
doc would restate a glossary ruling, not add a new one.

## References

- [`docs/spec-tier1-serve.md`](./spec-tier1-serve.md) (v1.4 spec)
- [`docs/spec-tier2-retention-analytics.md`](./spec-tier2-retention-analytics.md) (v1.5 spec)
- [`docs/skilltrace-application-roadmap.md`](./skilltrace-application-roadmap.md) (v1 application plan;
  post-v1 section is replaced by a pointer to this doc — see
  the "Post-v1 backlog" line in that file's "v1.0.0 final" row)
- [`CONTEXT.md`](../CONTEXT.md) (ubiquitous language)
- [`docs/adr/`](./adr/) (structural decisions; no slot
  decision warrants a new ADR as of this writing)
- Wayfinder map
  ([#95](https://github.com/earledotpy/skilltrace/issues/95)) and the G-ROI
  ([#99](https://github.com/earledotpy/skilltrace/issues/99)), G-Slot
  ([#100](https://github.com/earledotpy/skilltrace/issues/100)), G-Beyond
  ([#101](https://github.com/earledotpy/skilltrace/issues/101)), G-Doc-Shape
  ([#102](https://github.com/earledotpy/skilltrace/issues/102)) tickets for the trail of decisions.
