# ADR 0005 — Retire scaffold artifacts to archive/scaffold-v0.1/

Date: 2026-08-21
Status: accepted

## Context

After ADR 0002 cut the interface layer (6→5 layers), four clusters of scaffold-era artifacts remained at the repo surface:

*   `interface/` (4 YAML, 111 `compiler` refs stranded)
*   `generation_manifest.json` (orphan, 0 inbound refs per T1 inventory `research/scaffold-inventory.md@bd9b5b8`)
*   `docs/reference-research-document.md:353` + 5 local `docs/agents/decision-ticket-t*.md` (web-app vision, pre-wayfinder)
*   `evidence_templates/:4` + `session_templates/:6` (human checklists, zero engine load — `policy/workload.yaml:39-45` is truth via `execution/templates.py:28`)
*   `examples/:3` (`compiler` command flows) + `schemas/` (Pydantic claim, truth is `docs/SCHEMA_REFERENCE.md` frozen) + `research/` + `issues/` (local-markdown tracker, superseded by GitHub `wayfinder:*`)

Leaving them at top level made `v1.0.0` ship unexplained placeholders, contradicting the map destination: *every top-level folder and every `docs/*` file declared, no unexplained placeholders — docs consistent with the 5-layer engine, scaffold history preserved*. The grilling for T5 (#56) confirmed: learner has no live use for `evidence_templates/`/`session_templates/` or `examples/` flows and prefers an ADR for the freeze.

Three disposition models were considered:

1.  **Archive via `git mv` to `archive/scaffold-v0.1/`** (preserve history, `git log --follow` intact, one `archive/` subtree per `Map #51` Notes preference `preserve scaffold history in archive/`).
2.  **Delete** — loses v0.1 6-layer manifest + interface card/view history needed for post-v1 dashboard design fresh from usage (ADR 0002 Consequences, `docs/POST_V1_BACKLOG.md` v1.4) and the 5-pillar synthesis.
3.  **Keep in place / thin to one** — leaves a 6-layer surface contradicting `AGENTS.md:47` (`v1 has five layers`) and invites drift between `interface/commands.yaml:51` registry and `src/skilltrace/` dispatcher; markdown templates conflate `Session` opaque label (`CONTEXT.md:197-199`) with a work-log form.

## Decision

Model 1. `git mv` (not copy) every scaffold cluster to `archive/scaffold-v0.1/`:

```
archive/scaffold-v0.1/
  README.md
  interface/ (cards.yaml, commands.yaml, state.yaml, views.yaml)
  generation_manifest.json
  web-app-vision/reference-research-document.md + decision-tickets/t1..t5 + README.md
  templates/evidence_templates/ (4) + templates/session_templates/ (6) + templates/README.md
  examples/ (3) + schemas/ (README + __init__.py) + research/ (1) + issues/ (17)
```

Byte-identical moves in the first commit, provenance headers + `README.md` stubs + doc-consistency edits in the second. No CONTEXT edit — retirement is an engine-layer/doc-surface fact, not a ubiquitous-language term. `docs/ai-engineering-roadmap.md:51-71` stays as thin index to canonical `docs/roadmap/*` (reference_only per `docs/curriculum-authoring.md:12-13`); annexes `docs/resources/*:3` stay live.

Companion edits (same effort, not a separate ADR):

*   `release/manifest.yaml:23-26` remove `interface/` (and `schemas/`/`compiler/`/`examples/`) required-path entries; bump `python_min_version: 3.11 → 3.14` to match `pyproject.toml:9`.
*   `release/tests.yaml:32-41` remove `test.interface.validate` and replace `python -m compiler.*` with `skilltrace` CLI equivalents (or move legacy tests to archive).
*   `release/criteria.yaml:2-5` `criterion.layers.present` 6→5 layers, drop `criterion.interface.valid`.
*   `AGENTS.md:60-63` Repo layout + `README.md:46-49` Layers already declare 5 layers; polish adds `archived at archive/scaffold-v0.1/` pointer.
*   `docs/ai-engineering-roadmap.md:1-8` header gains one-sentence `reference_only` scope note linking `roadmap/*` + `CURRICULUM_AUTHORING.md`.
*   `schemas/README.md:5` updated to `Schema contract lives in docs/SCHEMA_REFERENCE.md (frozen); schemas/ archived`.

## Consequences

*   `v1.0.0` ships 5 layers with no scaffold placeholders; `archive/scaffold-v0.1/` is read-only history (pre-v0.4 framework docs pattern continues). `git log --follow` traces renames.
*   `skilltrace validate graph/evidence/execution/policy/resources` + `pytest` + `skilltrace health` remain green; scaffold removal has zero engine coupling (T1 verified).
*   Post-v1 dashboard (POST_V1 backlog v1.4) can mine `interface/cards.yaml:46` + `views.yaml:311` and `web-app-vision/` as input, but not as spec.
*   If a future curriculum needs any archived aid, it is a human `git mv` back plus an ADR revisit — friction is intentional.

See: ADR 0002, Map #51, T1 #52 (`research/scaffold-inventory.md`), T2 #53, T3 #54, T4 #55, T5 #56.
