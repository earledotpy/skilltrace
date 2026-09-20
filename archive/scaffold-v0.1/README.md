# Archived — Scaffold v0.1 History (read-only)

This directory is the read-only archive of Initial SkillTrace candidate scaffold artifacts, retired per **ADR 0005** (2026-08-21) and **ADR 0002** (2026-07-02). No engine code reads from `archive/`; `archive/` is preserved for history and for post-v1 dashboard design fresh from usage (POST_V1 backlog v1.4).

Archived via `git mv` (so `git log --follow <path>` traces renames). Byte-identical moves in the first commit; provenance annotations added in the second.

## What lives here and why

| Path | Original path | Reason |
|---|---|---|
| `interface/` (4 YAML: `cards.yaml:46`, `commands.yaml:526`, `state.yaml:12`, `views.yaml:311`) | `interface/` | 6-layer scaffold layer cut — 6→5 layers per ADR 0002; CLI is self-describing via `src/skilltrace/` dispatcher; 51 stranded `compiler` refs. |
| `generation_manifest.json` | `generation_manifest.json` | v0.1 6-layer manifest (`layer:6D`, `command_count:19`, `execution_seed_files:6`) — orphan, 0 inbound refs per T1 `research/scaffold-inventory.md@bd9b5b8` (`compiler` retirement v0.4, `src/skilltrace/__init__.py:4`). |
| `web-app-vision/reference-research-document.md:353` | `docs/reference-research-document.md` | Web-app vision synthesis (5-pillar framework + interface gap Phases B–E, truncated `gh` tool-call at line 351) — post-v1 scope (PRD:52 Non-goals, ADR 0002). |
| `web-app-vision/decision-tickets/t1..t5` | `docs/agents/decision-ticket-t*.md` (5) | Pre-wayfinder local-markdown decision tickets superseded by GitHub wayfinder map #51 + tickets #52–#56. |
| `templates/evidence_templates/:4` | `evidence_templates/` | Human checklists (`checklist`, `code`, `problem_set`, `technical_summary`) — zero engine load; `policy/workload.yaml:39-45` is truth via `execution/templates.py:28`; `USER_GUIDE.md` workflow is `skilltrace start/work/evidence submit`. |
| `templates/session_templates/:6` | `session_templates/` | `micro`, `standard`, `deep`, `blocker`, `remediation`, `review` forms — `CONTEXT.md:Session` opaque labels; archived to remove label-vs-form conflation. |
| `examples/:3` | `examples/` | Illustrative `python -m compiler.*` flows (18 `compiler` hits) — superseded by `USER_GUIDE.md` + `docs/RUNBOOK.md` + `src/skilltrace` CLI; no engine load. |
| `schemas/` | `schemas/` | Pydantic/ `compiler` claim (`schemas/README.md:5`) — truth is `docs/SCHEMA_REFERENCE.md` (frozen); no engine load. |
| `research/` | `research/` | `ai-engineering-agentic-roadmap-research.md` — superseded by `docs/reference-research-document.md` + canonical `docs/roadmap/*`. |
| `issues/:17` | `issues/` | Local file-based issue specs `0001`–`0016` + `README.md` — superseded by GitHub `wayfinder:*` tracker per `docs/agents/issue-tracker.md`. |

## Provenance headers

Each archived `interface/*.yaml` carries a header:

```yaml
# ARCHIVED — scaffold-legacy per ADR 0002 (2026-07-02) + ADR 0005 (2026-08-21)
# Original path: interface/<filename>
# Archived to: archive/scaffold-v0.1/interface/<filename>
# Reason: interface layer cut from v1 (6→5 layers); CLI self-describing; preserved for v1.4 dashboard reference
# See: docs/adr/0002-cut-interface-layer-from-v1.md, docs/adr/0005-scaffold-retirement.md, Map #51, T1 research/scaffold-inventory.md@bd9b5b8
```

`generation_manifest.json` left byte-identical (strict JSON); provenance lives here. `web-app-vision/` and `templates/` each have their own `README.md` with the same dates + map/ticket links.

## Not here

*   `docs/ai-engineering-roadmap.md` — kept as thin index (scope note at line 3-5) to canonical `docs/roadmap/*` (reference_only per `docs/curriculum-authoring.md:12-13`); annexes `docs/resources/*:3` stay live.
*   Live docs: `docs/skilltrace-application-roadmap.md`, `docs/curriculum-authoring.md`, `docs/SCHEMA_REFERENCE.md` (frozen), `docs/adr/0001-0005`, `CONTEXT.md`, `AGENTS.md`, `README.md`.

## How to find history

```bash
git log --follow -- archive/scaffold-v0.1/interface/commands.yaml
git log --follow -- archive/scaffold-v0.1/web-app-vision/reference-research-document.md
git log --follow -- archive/scaffold-v0.1/templates/evidence_templates/checklist_evidence_template.md
```

See ADR 0005 for the full decision and the `release/manifest.yaml` + `release/tests.yaml` companion edits.
