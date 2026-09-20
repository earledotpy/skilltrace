# Archived — templates (scaffold-era human checklists)

Original paths: `evidence_templates/` (4) + `session_templates/` (6) — 10 markdown forms
Archived to: `archive/scaffold-v0.1/templates/` preserving subfolders (`evidence_templates/`, `session_templates/`)
Date archived: 2026-08-21 (T4 #55 resolution, executed in T5 #56)
Reason: templates are human authoring aids, not engine data — zero engine load-bearingness (T1 inventory `template-aid`, T4 grill). `evidence_templates/checklist_evidence_template.md:19` conflicts with `CONTEXT.md:EvidenceRecord` (acceptance frozen at submission via gate/manual review, not post-hoc checklist); `session_templates/standard_session_template.md:34` duplicates `execution/sessions.yaml` + `session_work.yaml` but is never read by `skilltrace session close`. Engine truth is `policy/workload.yaml:39-45` (`micro:15/standard:45/deep:90`) via `execution/templates.py:28`; learner workflow is `USER_GUIDE.md:51-54` (`skilltrace start/work/evidence submit`). Archiving removes Session-template label vs. markdown conflation without needing a `CONTEXT.md` edit.

Discoverable via `git log --follow` and this directory; not linked from `USER_GUIDE.md` (would falsely advertise workflow).

See: Map #51, T4 #55, T1 `research/scaffold-inventory.md@bd9b5b8`, ADR 0005.

Contents:
- `evidence_templates/`: `checklist_evidence_template.md`, `code_evidence_template.md`, `problem_set_evidence_template.md`, `technical_summary_template.md`
- `session_templates/`: `micro_session_template.md`, `standard_session_template.md`, `deep_work_session_template.md`, `blocker_template.md`, `remediation_template.md`, `review_template.md`
