# T1 — Classified Scaffold Inventory (research throwaway)

**Branch:** `research/scaffold-inventory` | **Parent map:** #51 | **Ticket:** #52
**Date:** 2026-08-21 | **Repo:** `C:\skilltrace` (commit `main` HEAD at time of inventory)
**Mandate:** Table of every top-level path + every `docs/*` file (ticket says 38, repo has **39** on this branch) classified as `engine layer / curriculum seed / docs / scaffold-legacy / template-aid / release-artifact` with one-line provenance and reference counts for `compiler`, `interface/`, `generation_manifest`.

> Throwaway research artifact — decision lives in #52. File disposition (keep / keep-as-index / archive to `archive/scaffold-v0.1/`) follows T2/T3/T4.

---

## 0. Global reference counts (source of truth for per-row `refs` column)

Counts exclude `.git/`, `__pycache__/`, `.pytest_cache/` (numbers with those dirs in parentheses). Method: `python` walk counting `str.count(term)` in file text.

| Term | Total occurrences | Files containing term | Representative holders |
|------|-------------------|-----------------------|------------------------|
| `compiler` | **111** (122 incl. pycache) | **14** (25 incl. pycache) | `interface/commands.yaml` (51), `release/tests.yaml` (15), `release/smoke_tests.yaml` (8), `examples/interface_command_registry.md` (7), `examples/example_session_command_flow.md` (6), `examples/policy_command_flow.md` (5), `issues/0009` (5), `release/WORKFLOW.md` (4), `docs/skilltrace-application-roadmap.md` (3), `release/manifest.yaml` (2), `issues/0001` (2), `AGENTS.md` (1), `schemas/README.md` (1), `src/skilltrace/__init__.py` (1) |
| `interface/` | **2** | **2** | `docs/adr/0002-cut-interface-layer-from-v1.md` (1), `release/manifest.yaml` (1) — literal `interface/` path string only |
| `interface` (without slash, for context) | 111 | 35 | includes `interface/` + mentions in `docs/reference-research-document.md` (13), `interface/*.yaml` themselves, ADRs, roadmap phases, `archive/*.md` etc. |
| `generation_manifest` | **0** | **0** | The file `generation_manifest.json` exists at top level but contains no self-reference string; no other file greps for the name |

> Implication: the `compiler` vocabulary is fully stranded — zero implementation remains outside `src/skilltrace/`; only `interface/` + `schemas/` + `examples/` + `release/` + `archive` still carry it. `generation_manifest` is an orphan file (zero inbound refs).

---

## 1. Top-level path inventory

27 entries at repo root (20 dirs + 7 files ignoring `.git`, `.pytest_cache`). Sorted alphabetically; `class` is one of the six ticket values.

| # | Top-level path | Kind | Class | One-line provenance | Refs (`compiler` / `interface/` / `generation_manifest`) in this path's own files | Notes / sharpened question for T2-T4 |
|---|---|---|---|---|---|---|
| 1 | `.gitignore` | file | `release-artifact` | Repo hygiene, not engine/curriculum; standard git artifact | 0/0/0 | keep |
| 2 | `AGENTS.md` | file | `docs` | Repo working conventions (invariants, layers, scaffold cut per ADR 0002) — agent-facing docs | 1/0/0 | keep; references `compiler/` historically |
| 3 | `CONTEXT.md` | file | `docs` | **Ubiquitous language** — canonical glossary per `docs/adr/*` & `docs/skilltrace-application-roadmap.md:12` | 0/0/0 | keep (frozen glossary) |
| 4 | `README.md` | file | `docs` | Entry-point docs; points to `docs/INSTALL.md` + `src/skilltrace` CLI | 0/0/0 (mentions `interface` once generically) | keep |
| 5 | `generation_manifest.json` | file | `scaffold-legacy` | v0.1 scaffold manifest (`version: v0.1.0-rc1`, `layer: 6D`, `command_count: 19`, `execution_seed_files: 6`) — the `compiler`'s output record; zero inbound refs | 0/0/0 self | **Archive to `archive/scaffold-v0.1/generation_manifest.json`** — preserve history per #51 preference |
| 6 | `pyproject.toml` | file | `release-artifact` | PEP 517 build metadata for the `skilltrace` installable package (`src/skilltrace`) | 0/0/0 | keep; `primary_interface = cli` confirms ADR 0002 |
| 7 | `requirements.txt` | file | `release-artifact` | Pins `PyYAML>=6.0`; only runtime dep per `SCHEMA_REFERENCE.md` | 0/0/0 | keep (or fold into pyproject; not blocking) |
| 8 | `archive/` | dir (11 files) | `scaffold-legacy` | Pre-v0.4 framework docs (`skill-graph-*.md`, `.pdf`, prototype `reports_design_issue_31.*`) — scaffold history | 0/0/0 (3 generic `interface` mentions in archived frameworks) | keep as-is; candidate target for `archive/scaffold-v0.1/` consolidation (TBD T2) |
| 9 | `data/` | dir (1 file) | `release-artifact` | `data/export.md` — **disposable export** regenerated from files; `CONTEXT.md:Export` says Markdown/YAML are sole source of truth | 0/0/0 | keep dir (generated, `.gitignore`-candidate if not already); not curriculum |
| 10 | `docs/` | dir (39 files) | `docs` | Canonical docs layer (see §2) | — | see §2; `docs/roadmap/*` declared canonical per #51 notes |
| 11 | `evidence/` | dir (46 files incl. artifacts/ + .pyc) | `engine layer` (evidence) + `curriculum seed` data inside | `evidence/artifact_specs.yaml`, `evidence/gates.yaml`, `evidence/evidence_records.yaml`, `evidence/assessment_attempts.yaml` are **seed + live**; `examples/` under it are sample artifacts | 0/0/0 | keep; one of 5 engine layers per roadmap §1 & AGENTS.md invariants |
| 12 | `evidence_templates/` | dir (4 files) | `template-aid` **uncertain** — flagged in #51 as open (T4) | Advisory templates for creating evidence artifacts (`code`, `checklist`, `problem_set`, `technical_summary`) — not referenced by engine code; `CONTEXT.md:EvidenceRecord` says submission is judged by gate/manual review, not template | 0/0/0 | **T4 grill:** keep / thin to 1 canonical example / archive to `archive/scaffold-v0.1/evidence_templates/` |
| 13 | `examples/` | dir (3 files) | `scaffold-legacy` | `example_session_command_flow.md`, `interface_command_registry.md`, `policy_command_flow.md` — illustrative flows referencing `compiler` (5-7 hits each); `interface_command_registry.md` is Layer-4 registry that ADR 0002 cut | 18/0/0 | **Archive** — contradicts ADR 0002; preserve in `archive/scaffold-v0.1/examples/` |
| 14 | `execution/` | dir (6 files) | `engine layer` (execution) | `sessions.yaml`, `session_work.yaml`, `blockers.yaml`, `reviews.yaml`, `remediation_actions.yaml`, `events.yaml` — execution layer per roadmap; event log audit-only | 0/0/0 | keep; one of 5 engine layers |
| 15 | `graph/` | dir (84 files: 81 nodes + edges + resources + state) | `curriculum seed` (+ one live file) | `graph/nodes/*.md` (81), `graph/edges.yaml` (sole truth per AGENTS.md invariants), `graph/resources.yaml` (29 verified) are **curriculum seed**; `graph/state.yaml` is **engine progress store** per ADR 0001 | 0/0/0 | keep; split-view: seed vs. `state.yaml` belongs to engine but lives here by ADR 0001 |
| 16 | `interface/` | dir (4 files) | `scaffold-legacy` | `commands.yaml` (19 commands, 51 `compiler` hits), `views.yaml`, `cards.yaml`, `state.yaml` — **cut** per `docs/adr/0002:26-32` ("removed, not stubbed"; CLI self-describing) | 79/0/0 (incl. generic `interface` hits in its own YAML) | **Archive to `archive/scaffold-v0.1/interface/`** per #51 preference — preserve scaffold history; do not reintroduce |
| 17 | `issues/` | dir (17 files) | `template-aid` | V0 slice issue specs (`0001-` …) — plan docs, not engine; useful provenance for ADR context | 7/0/0 (`0001` 2, `0009` 5) | **Archive or keep 1 index** — T2 decides; currently scaffold planning history |
| 18 | `policy/` | dir (7 files) | `engine layer` (policy) but values are `curriculum seed` | 6 YAML policy files + docs; hard boundaries enforced as engine constants per ADR 0004, advisory values are seed per `CONTEXT.md:Advisory policy` | 0/0/0 | keep; one of 5 engine layers; values are seed data |
| 19 | `release/` | dir (31 files) | `release-artifact` | `manifest.yaml`, `criteria.yaml`, `tests.yaml` (15 compiler refs), `smoke_tests.yaml`, `WORKFLOW.md`, `release_candidate.yaml`, `criteria.yaml`, `test_results.yaml`, `test_outputs/`, `smoke_outputs/`, `skilltrace-v1.0.0-release-assets.zip` — release layer (5th engine layer) but contents are artifacts | 29/1/0 | keep; shape to final v1.0 shape — strip `compiler` refs from `tests.yaml`/`manifest.yaml` when interface-layer tests removed |
| 20 | `research/` | dir (1 file) | `docs` (reference research) | `research/ai-engineering-agentic-roadmap-research.md` — pre-v1 research; superseded by `docs/reference-research-document.md` + `docs/roadmap/*` | 0/0/0 | **Archive** or thin — T2 research-elements ticket owns this |
| 21 | `schemas/` | dir (2 files: README + __init__.py) | `scaffold-legacy` | `schemas/README.md` describes "Pydantic models + bundled compiler uses lightweight runtime validators so package can run with only PyYAML" — engine now has no Pydantic, no compiler; schema truth is `docs/SCHEMA_REFERENCE.md` (frozen) | 1/0/0 | **Archive** — keep only `SCHEMA_REFERENCE.md`; `schemas/` is orphaned compiler-era artifact |
| 22 | `scripts/` | dir (2 files) | `release-artifact` | `exit_gate_v03.py`, `exit_gate_v04.py` — RC validation helpers (invoke `src/skilltrace` validators) | 0/0/0 | keep if release gating still uses them; otherwise archive after v1.0 |
| 23 | `session_templates/` | dir (6 files) | `template-aid` **uncertain** — flagged open (T4) | Templates for sessions/blocks/reviews (`micro`, `standard`, `deep`, `blocker`, `remediation`, `review`) — `CONTEXT.md:Session` says template is opaque label, advisory only; engine supports but doesn't require them | 0/0/0 | **T4 grill:** keep / thin to 2 (micro+standard) / archive — currently 6 files is heavy |
| 24 | `src/` | dir (320 files: 100+ .py + pycache) | `engine layer` (implementation) | Installable `skilltrace` CLI package — the 5-layer engine implementation; `compiler/` retired in v0.4 per `src/skilltrace/__init__.py:4` | 1/0/0 | keep; the engine |
| 25 | `tests/` | dir (227 files) | `release-artifact` (validation) | Per-layer `pytest` suites — RC exit-gate validation; never read by engine | 0/0/0 | keep |

**Summary counts:** `engine layer` 5 dirs + `src/` = 6 | `curriculum seed` (graph seed, part of evidence/policy values) = 1 dir flagged hybrid | `scaffold-legacy` = 5 (`generation_manifest.json`, `interface/`, `examples/`, `schemas/`, part of `archive/`+`research/`) | `template-aid` = 3 (`evidence_templates/`, `session_templates/`, `issues/`) with 2 uncertain | `docs` = 3 dirs/files | `release-artifact` = 6

---

## 2. `docs/*` file inventory — 39 files (ticket scope says 38; extra is `docs/agents/domain.md` vs. earlier tally)

| # | File | Class | One-line provenance | Refs in file (`compiler` / `interface/` / `generation_manifest`) | Disposition hint (T2/T3/T4 decides) |
|---|---|---|---|---|---|
| 1 | `docs/skilltrace-application-roadmap.md` | `docs` — **canonical roadmap** | **The** 5-layer engine roadmap; `source_role: reference_only` for AI roadmap per line 12-13; halves seed vs. engine per AGENTS.md | 3 / 0 / 0 | **keep — canonical** per #51 |
| 2 | `docs/adr/0001-separate-progress-store.md` | `docs` (ADR — decision) | ADR 0001 accepted: learner progress in `graph/state.yaml`, not node frontmatter — invariant in AGENTS.md | 0 / 0 / 0 | keep (frozen) |
| 3 | `docs/adr/0002-cut-interface-layer-from-v1.md` | `docs` (ADR — decision) | ADR 0002 accepted: 6→5 layers, `interface/` removed not stubbed; `validate_interface` + layer-4 release check removed | 0 / 1 / 0 | keep; the authority for archiving `interface/` |
| 4 | `docs/adr/0003-acceptance-frozen-at-submission.md` | `docs` (ADR) | ADR 0003: evidence acceptance frozen at submission; supersession/annotation derived, never mutation | 0 / 0 / 0 | keep |
| 5 | `docs/adr/0004-hard-boundaries-are-engine-constants.md` | `docs` (ADR) | ADR 0004: hard boundaries in code (`automation_boundary.yaml` must agree), not policy-file-authoritative | 0 / 0 / 0 | keep |
| 6 | `docs/SCHEMA_REFERENCE.md` | `docs` — **frozen** | Frozen v1.0 schema (3rd session consulter per #51); unknown keys tolerated; only forbidden keys rejected | 0 / 0 / 0 | keep (frozen) |
| 7 | `docs/curriculum-authoring.md` | `docs` (doctrine) | Curriculum-authoring doctrine for seed data; destination-backward; `roadmap_anchors` `reference_only` per §1 | 0 / 0 / 0 | keep |
| 8 | `docs/PRD.md` | `docs` | Product requirements (problem, product def) — drives 5-layer engine | 0 / 0 / 0 | keep |
| 9 | `docs/SAFETY_BOUNDARIES.md` | `docs` | Safety rules (hard boundaries narrative) — mirrors `CONTEXT.md` + ADR 0004 | 0 / 0 / 0 | keep (or fold into SCHEMA_REFERENCE; currently distinct) |
| 10 | `docs/USER_GUIDE.md` | `docs` | User guide for single-learner CLI daily use (`today`, `next`, `health`, `report`) | 0 / 0 / 0 | keep |
| 11 | `docs/RUNBOOK.md` | `docs` | Daily study loop runbook (operational reference) | 0 / 0 / 0 | keep |
| 12 | `docs/INSTALL.md` | `docs` | Fresh-clone install (Python ≥3.14, PyYAML only) | 0 / 0 / 0 | keep |
| 13 | `docs/INSTALL_WINDOWS.md` | `docs` | Windows-specific install notes (encoding, console) | 0 / 0 / 0 | keep (or fold into INSTALL.md per T3 API surface decision) |
| 14 | `docs/CHANGELOG.md` | `docs` | Condensed v0.1.0-rc1 → v1.0.0 milestone log | 0 / 0 / 0 | keep |
| 15 | `docs/RELEASE_NOTES.md` | `docs` | v1.0.0 release notes (post-v1 backlog pointer) | 0 / 0 / 0 | keep |
| 16 | `docs/RELEASE_SHORT.md` | `docs` | Short changelog for v1.0.0 tag/release | 0 / 0 / 0 | keep or fold into RELEASE_NOTES (thin) |
| 17 | `docs/POST_V1_BACKLOG.md` | `docs` | Tiered post-v1 backlog (web UI, dashboard per ADR 0002 deferral) — out-of-scope guard | 0 / 0 / 0 (generic `interface` 1) | keep |
| 18 | `docs/ai-engineering-roadmap.md` | `scaffold-legacy` / `docs` hybrid — **flagged for T4** | AI Engineering Roadmap v1.0 (Aug 2026, 380h agentic-coding emphasis) — original **curriculum seed** exemplar; `CONTEXT.md` + `curriculum-authoring.md:12-13` declare it `reference_only` seed, not engine; now superseded by `docs/roadmap/*` as canonical per #51 | 0 / 0 / 0 | **T4 grill:** keep-as-index in `docs/roadmap/README.md` or archive to `archive/scaffold-v0.1/` — do not keep as parallel roadmap |
| 19 | `docs/curriculum-verification-worksheet.md` | `release-artifact` (sitting record) | Resource verification sitting record (29 resources verified 2026-07-10, 1012 pytest pass, events committed) — historical evidence of `graph/resources.yaml` verification | 0 / 0 / 0 | **archive** after v1.0 (keep until v1 ships for audit; then `archive/scaffold-v0.1/`) |
| 20 | `docs/reference-research-document.md` | `scaffold-legacy` (synthesis) | Synthesized "5-Pillar framework vision + current build + interface gap + mobile-first web app path" — pre-T1 research synthesis; contains 13 `interface` mentions as historical synthesis, not canonical docs | 0 / 13 generic `interface` / 0 | **Archive** — T2 research-elements decides; duplicates `research/` + ADR 0002 history |
| 21 | `docs/roadmap/phase-0-prerequisites.md` | `curriculum seed` (+ `docs`) | Canonical roadmap phase 0 (40h, Python/Git/SQL) — seed data served by engine | 0 / 0 / 0 | **keep — canonical** per #51 |
| 22 | `docs/roadmap/phase-1-math-foundations.md` | `curriculum seed` | Canonical phase 1 (math foundations) | 0 / 0 / 0 | keep — canonical |
| 23 | `docs/roadmap/phase-2-classical-ml.md` | `curriculum seed` | Canonical phase 2 (classical ML) | 0 / 0 / 0 | keep — canonical |
| 24 | `docs/roadmap/phase-3-deep-learning.md` | `curriculum seed` | Canonical phase 3 (deep learning) | 0 / 1 generic `interface` / 0 | keep — canonical |
| 25 | `docs/roadmap/phase-4-agentic-ai.md` | `curriculum seed` | Canonical phase 4 (agentic AI) | 0 / 0 / 0 | keep — canonical |
| 26 | `docs/roadmap/phase-5-specializations.md` | `curriculum seed` | Canonical phase 5 (specializations) | 0 / 3 generic `interface` / 0 | keep — canonical |
| 27 | `docs/roadmap/capstone-projects.md` | `curriculum seed` | Canonical capstone projects (deployed agentic apps) | 0 / 0 / 0 | keep — canonical |
| 28 | `docs/resources/agentic-frameworks-comparison.md` | `docs` (reference) | Reference: agentic framework comparison (Last Verified Aug 2026) — supports roadmap phase 4 | 0 / 0 / 0 | keep — part of roadmap reference docs |
| 29 | `docs/resources/certification-roadmap.md` | `docs` (reference) | Reference: certification roadmap | 0 / 0 / 0 | keep |
| 30 | `docs/resources/free-compute-guide.md` | `docs` (reference) | Reference: free compute guide | 0 / 0 / 0 | keep |
| 31 | `docs/maintenance/quarterly-review-checklist.md` | `docs` (process) | Process: quarterly roadmap resource review cadence; `last_verified` staleness per `CONTEXT.md:Verified` | 0 / 0 / 0 | keep — process doc, not engine |
| 32 | `docs/agents/issue-tracker.md` | `template-aid` (agent skill aid) | Agent skill: issue-tracker workflow (`gh` CLI) per `docs/agents/*.md` domain-docs setup | 0 / 0 / 0 | keep (agent wiring; not user docs) |
| 33 | `docs/agents/triage-labels.md` | `template-aid` | Agent skill: 5 canonical triage labels (`eeds-triage` … `wontfix`) | 0 / 0 / 0 | keep |
| 34 | `docs/agents/domain.md` | `template-aid` | Agent skill: single-context domain-docs layout (`CONTEXT.md` + `docs/adr/`) | 0 / 1 generic `interface` / 0 | keep — this is the "38 vs 39" extra file; keep with agent docs |
| 35 | `docs/agents/decision-ticket-t1-interface-type.md` | `template-aid` | Wayfinder decision ticket T1 (interface type) — prior scaffold decision history | 0 / 5 generic `interface` / 0 | **archive** after map closes — wayfinder ticketing doc, not v1 docs |
| 36 | `docs/agents/decision-ticket-t2-research-elements.md` | `template-aid` | Wayfinder decision ticket T2 (research elements) | 0 / 2 generic `interface` / 0 | archive after map closes |
| 37 | `docs/agents/decision-ticket-t3-api-surface.md` | `template-aid` | Wayfinder decision ticket T3 (engine API surface) | 0 / 3 generic `interface` / 0 | archive after map closes |
| 38 | `docs/agents/decision-ticket-t4-roadmap-integration.md` | `template-aid` | Wayfinder decision ticket T4 (roadmap integration) — owns `evidence_templates`/`session_templates` grill | 0 / 4 generic `interface` / 0 | archive after map closes |
| 39 | `docs/agents/decision-ticket-t5-synthesis-timing.md` | `template-aid` | Wayfinder decision ticket T5 (synthesis timing) | 0 / 8 generic `interface` / 0 | archive after map closes |

> Totals: `docs` canonical 17 + `curriculum seed` 7 (roadmap phases) + `scaffold-legacy` hybrid 2-3 + `template-aid` 8 (incl. 5 wayfinder tickets) + `release-artifact` 1 (worksheet) = 39. Remove wayfinder ticket docs from the v1.0 docs surface and the count drops to 34 user-facing docs — which is the expected post-T1 shape.

---

## 3. Focus: the two uncertain areas

### `evidence_templates/` (4 files) — `template-aid`, open question per #51

- Files: `checklist_evidence_template.md`, `code_evidence_template.md`, `problem_set_evidence_template.md`, `technical_summary_template.md`
- Each is a small markdown form (Node / Date / Work / Accepted? checklist) — **not referenced by any engine code** (`src/skilltrace` never imports them; submission is via `skilltrace submit` + gate/manual review per `CONTEXT.md:EvidenceRecord`).
- Engine consequence of removing them: **none** — templates are advisory for the human; evidence is recorded as `EvidenceRecord` regardless of template.
- Provenance: scaffold-era aids (pre-v0.5), duplicated by `docs/curriculum-authoring.md` guidance on artifact specs.
- **Recommendation for T4:** **Thin to 1** canonical example (e.g., `code_evidence_template.md` as inclusive example) in `examples/`-replacement or inline in `docs/USER_GUIDE.md`; archive the other 3 to `archive/scaffold-v0.1/evidence_templates/`. Rationale: reduce scaffold surface without removing the ergonomic aid entirely.

### `session_templates/` (6 files) — `template-aid`, open question per #51

- Files: `blocker_template.md`, `deep_work_session_template.md`, `micro_session_template.md`, `remediation_template.md`, `review_template.md`, `standard_session_template.md`
- Each mirrors a `CONTEXT.md` execution concept (`Session` opaque label, `Blocker`, `RemediationAction`, `Review`) — engine attaches **no meaning** to template names; durations are seed presets, advisory only.
- Engine code reference: `src/skilltrace/execution/templates.py` exists but is template-aid formatting only; engine lifecycle (`sessions.py`, `work.py`, `blockers.py`, `reviews.py`) does not require these markdown templates.
- Provenance: scaffold-era session aids; partially redundant with `docs/RUNBOOK.md` daily loop.
- **Recommendation for T4:** **Thin to 2** (`micro_session_template.md` + `standard_session_template.md`) retained to honor the two dominant session lengths in `policy/recommendation.yaml`; archive the other 4 to `archive/scaffold-v0.1/session_templates/`. Alternative full-archive is acceptable — T4 grill to decide thin vs. archive.

---

## 4. Cross-cutting deltas already verified in this inventory

- **Interface layer cut (ADR 0002) is complete in code, not in repo surface:** `src/skilltrace` has no `interface/` import; `pyproject.toml` declares `primary_interface = cli`; but `interface/*.yaml` + `examples/interface_command_registry.md` + `schemas/README.md` + `release/tests.yaml` still carry `compiler` vocabulary. Inventory confirms archive scope.
- **`docs/roadmap/*` is canonical (7 files, ~80 KB)** — `docs/ai-engineering-roadmap.md` is the only competing roadmap artifact (6 KB, `reference_only` per curriculum-authoring); it should not duplicate `docs/roadmap/*`. `research/ai-engineering-agentic-roadmap-research.md` is similarly superseded.
- **`generation_manifest.json` zero inbound refs:** confirms it became orphaned when `compiler/` retired in v0.4 (`src/skilltrace/__init__.py:4`); safe to archive without GREP migration.
- **No schema drift:** `docs/SCHEMA_REFERENCE.md` frozen; `schemas/` is not that reference — archiving `schemas/` does not affect validation.
- **5 wayfinder decision-ticket docs (`docs/agents/decision-ticket-t*.md`)** are the bulk of `template-aid` in docs — they are map-internal planning, not v1 docs surface; inventory isolates them for post-map archival.

---

## 5. What T2/T3/T4 will decide (sharpens per #51 "Not yet specified")

| Open question | Options | Owned by | Inventory input |
|---|---|---|---|
| `interface/` archive sub-path | `archive/scaffold-v0.1/interface/` vs `archive/scaffold-v0.1/interface-layer/` | Map (pre-T2) | Recommend `interface/` (matches source dir name; `generation_manifest.json` alongside as `archive/scaffold-v0.1/generation_manifest.json`) |
| `ai-engineering-roadmap.md` disposition | Index at `docs/roadmap/README.md` vs fold into `docs/roadmap/*` intro vs archive | T4 | Recommend keep-as-index (1 page, links to 7 phases) then archive original |
| `evidence_templates/` | keep / thin-to-1 / archive | T4 | Thin-to-1 (see §3) |
| `session_templates/` | keep / thin-to-2 / archive | T4 | Thin-to-2 (see §3) |
| `reference-research-document.md` + `research/` + `schemas/` + `examples/` | archive vs keep-as-reference | T2 (research elements) | Archive all 4 clusters to `archive/scaffold-v0.1/` — zero engine load-bearingness verified |

---

## 6. Sources consulted

- `CONTEXT.md` (ubiquitous language; `Export`, `Verified`, `Roadmap anchor` `reference_only`, `Session` template opaque, 5 states)
- `AGENTS.md` (invariants: edges.yaml sole truth, progress store derivation, 5 layers, interface cut, scaffold retiring)
- `docs/skilltrace-application-roadmap.md` (v1 five layers; reference_only doctrine; 5-layer list)
- `docs/adr/0001`..`0004` (progress store, interface cut, acceptance frozen, hard-boundaries constants)
- `docs/curriculum-authoring.md:12-13` (`roadmap_anchors` `reference_only` requirement)
- `docs/SCHEMA_REFERENCE.md` (frozen schema; forbidden keys only)
- `pyproject.toml`, `src/skilltrace/__init__.py:4` (compiler retired v0.4), `generation_manifest.json` (v0.1 6-layer manifest)
- `interface/*.yaml`, `examples/*.md`, `schemas/README.md`, `release/*.yaml`, `issues/*.md` (grep counts)
- `evidence_templates/*.md`, `session_templates/*.md` (content shape for T4)
- GitHub issues #51 (map) + #52 (this ticket)

---

*Generated for wayfinder ticket #52. Next: post branch URL + file link as issue comment, then let T2/T3/T4 resolve file-by-file keep/archive decisions.*
