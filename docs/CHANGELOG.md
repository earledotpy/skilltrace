# Changelog

This changelog summarizes notable changes and milestones from v0.1.0-rc1 through v1.0.0.

All notable changes are condensed from the project's release notes and release artifacts.

## v1.0.0 (2026)
- Finalized v1 release: version bump to 1.0.0, annotated tag and GitHub release created.
- Release assets attached: release manifest, test results, full release artifact zip.
- Release hardening: YAML/frontmatter schema freeze; Windows fresh-clone install verified; schema reference and release docs completed (INSTALL, RUNBOOK, USER_GUIDE, SAFETY_BOUNDARIES, POST_V1_BACKLOG, SCHEMA_REFERENCE).
- All release validation tests passed; automation checks for forbidden automation (pass/master/delete) enforced.

## v0.9.0-rc1
- Daily-use polish and Mentor-voice outputs: `today`, enriched `next`, `node` detail, `report` family.
- Stdlib-pure rendering via `src/skilltrace/render.py` (no rich/ANSI dependence).
- Command aliases: `st`, `submit`, `close`.
- Prototypes and design docs for output and reports.

## v0.8.0-rc1
- Production-grade seed graph (81 nodes, 124 edges, verified resources).
- Backfilled prior learning (Khan Academy algebra nodes) with safety rules for retrospective records.
- Seed acceptance test suite and verified resources registry.

## v0.7.0-rc1
- Resource registry and verification workflow implemented.
- `skilltrace resources` and resource-reporting commands added.

## v0.6.0-rc1
- Policy engine: hard boundaries enforced (no AI-only pass/master/delete/no hard-prerequisite override).
- Advisory policies for recommendation weights, workload, remediation pressure.
- `skilltrace master` and check-automation commands.

## v0.5.0-rc1
- Execution workflow: sessions, session work items, blockers, remediation actions, reviews, audit event log.

## v0.4.0-rc1
- Evidence model: ArtifactSpec, ValidationGate, EvidenceRecord, supersede model, pass eligibility semantics.

## v0.3.0-rc1
- Graph core and CLI packaging; installable `skilltrace` package and console entry point.
- SkillNode and GraphEdge schema constraints; readiness sync and recommendation engine.

## v0.2.0-rc1
- Foundational operational docs (CONTEXT.md, CLAUDE.md) and PRD; ADRs added.

## v0.1.0-rc1
- Scaffold baseline and initial generated candidate.

---

Notes:
- This changelog is a concise, human-friendly summary. For full decision history, see the linked issues in `docs/RELEASE_NOTES.md` and the repository's issue tracker.
