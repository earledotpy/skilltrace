# Top-10 shortlist similarity evidence matrix

**Research date:** 2026-09-03
**Scope:** the ranked top-10 shortlist in
`docs/resources/learning-engines-comparison.md`, audited against SkillTrace at
`HEAD` `61f54164a50ed76b2481f270cb6abc2841e26265`. Every shortlist pin was
re-verified on 2026-09-03 as still the default-branch tip (urnote uses
`master`; developer-roadmap uses `master`).

**Method:** Primary sources only — repository source, tests, and first-party
metadata read from the pinned commits via the GitHub API; no blog posts or
vendor summaries. Every source citation uses the complete
`owner/repo@full-commit:path:Lx-Ly` form (with no implied or abbreviated
repository, revision, or path). READMEs are cited only where they establish
identity, provenance, or content layout.

## Provenance resolutions

### Numo = `mohaneddz/Numo` (original work, not a fork)

- GitHub metadata: `fork:false`, no `parent`/`source`; created 2026-03-24;
  owner `mohaneddz` (Mohaned-Dz, account created 2021-02-24). Root commit
  `d63c79761262cedfcdc3f89f7a1fba67ef0e5984` ("- Plan 1 implementation",
  authored by "Mohaned", 2026-03-25, one day after repo creation).
- Package identity at the pin is `"name": "numo"`, private Tauri 2 + React 18
  + TypeScript desktop app
  (`mohaneddz/Numo@9569c4d27329981c7bf537de36e4776095d6c27e:package.json:1-38`).
- Disambiguation: this is **not** the Ruby `numo` numerical-computing
  ecosystem; the repo description and stack are a Duolingo-style
  language-learning desktop app (description field retrieved via
  `gh api repos/mohaneddz/Numo`, 2026-09-03).

### learn-faster-kit: `hluaguo/learn-faster-kit` == former `cheukyin175/learn-faster-kit` (account rename)

- Pinned `pyproject.toml` lists author Hugo Lau <cheukyin175@gmail.com> and
  Homepage/Repository/Issues URLs pointing at
  `github.com/cheukyin175/learn-faster-kit`
  (`hluaguo/learn-faster-kit@c0168f30f87e488b5230dbd387fe2904f7fdf538:pyproject.toml:11-13,39-42`).
- The old path still redirects: `gh api repos/cheukyin175/learn-faster-kit`
  resolves to repo id **1093331589**, identical to
  `gh api repos/hluaguo/learn-faster-kit` — same repository, renamed owner
  (`hluaguo` profile name "Hugo, CY LAU" matches the pyproject author).
  `users/cheukyin175` itself now 404s.
- Root commit `7646e9e91786e496e2a7166cf7164ae54798a031` ("feat: initial
  commit - Learn FASTER uvx tool", Hugo Lau, 2025-11-10, same day the repo
  was created). `fork:false`; 34 of 38 commits by `hluaguo`. Conclusion:
  original work by one author under a renamed account; the shortlist URL is
  the canonical current identity.

## Evidence matrix

| Repo (pin = tip) | Strongest verified features | More efficient than SkillTrace | Additive adoption idea | Caveat |
|---|---|---|---|---|
| `nagisanzenin/engram` | FSRS-4.5 transitions cap relearning dose (`nagisanzenin/engram@0590eb8f008680acbfb5aaa4dbc73bf63ca643dd:scripts/engram.py:180-272`); static checks find probe/rubric gaps (`nagisanzenin/engram@0590eb8f008680acbfb5aaa4dbc73bf63ca643dd:scripts/engram.py:783-798`). | Atomic temp-file replacement and corrupt-JSON quarantine make hand-edited-state recovery safer (`nagisanzenin/engram@0590eb8f008680acbfb5aaa4dbc73bf63ca643dd:scripts/engram.py:287-327`). | Add author-facing, non-mutating warnings where an ArtifactSpec rubric demands criteria its probe does not ask. | FSRS, IO, CLI, analytics, and embedded self-tests share one 12,676-line script (`nagisanzenin/engram@0590eb8f008680acbfb5aaa4dbc73bf63ca643dd:scripts/engram.py:1-12676`). |
| `ankitects/anki` | FSRS-6 trains parameters from revision logs (`ankitects/anki@20c475f110c44899b91546906ce876976d9a52d7:rslib/src/scheduler/fsrs/params.rs:81-108`); manual rescheduling preserves intervals (`ankitects/anki@20c475f110c44899b91546906ce876976d9a52d7:rslib/src/scheduler/reviews.rs:22-81`). | `"50-70!"` assigns each card a uniformly sampled due day, avoiding deferral clumps (`ankitects/anki@20c475f110c44899b91546906ce876976d9a52d7:rslib/src/scheduler/reviews.rs:91-122,138-161`). | Apply jitter only to policy-layer review recommendations; never mutate asserted progress. | Its due-date tests exercise only the non-FSRS branch (`ankitects/anki@20c475f110c44899b91546906ce876976d9a52d7:rslib/src/scheduler/reviews.rs:260-307`). |
| `mohaneddz/Numo` | Modality-specific mastery records retain strength, lapses, latency, hint rate, interval, and ease (`mohaneddz/Numo@9569c4d27329981c7bf537de36e4776095d6c27e:src/services/curriculum/masteryStore.ts:21-45`); its SM-2 variant clamps ease and weights hints (`mohaneddz/Numo@9569c4d27329981c7bf537de36e4776095d6c27e:src/services/curriculum/masteryStore.ts:108-130`). | A deterministic planner reserves review steps, warms up first, and supplies a task rationale (`mohaneddz/Numo@9569c4d27329981c7bf537de36e4776095d6c27e:src/services/curriculum/sessionPlanner.ts:76-83,100-122,131-172`). | Policy-only session shaping: interleave derived-due reviews and explain their rank while `edges.yaml` remains the locking authority. | Misses mutate and demote mastery in a settings-backed JSON cache (`mohaneddz/Numo@9569c4d27329981c7bf537de36e4776095d6c27e:src/services/curriculum/masteryStore.ts:142-218`), violating monotonic asserted progress. |
| `hluaguo/learn-faster-kit` | `init_project()` creates `.learning/` without clobbering root instructions (`hluaguo/learn-faster-kit@c0168f30f87e488b5230dbd387fe2904f7fdf538:src/learn_faster/cli/installer.py:196-235`); JSON `llm_directive` supplies a composable next action (`hluaguo/learn-faster-kit@c0168f30f87e488b5230dbd387fe2904f7fdf538:src/learn_faster/templates/shared/scripts/review_scheduler.py:47-56,101-112`). | A single installer bootstraps a project-local workspace (`hluaguo/learn-faster-kit@c0168f30f87e488b5230dbd387fe2904f7fdf538:src/learn_faster/cli/installer.py:196-235`). | Include an optional advisory `next_action` in JSON output, naming a read-only or learner-initiated command only. | “Repetition” is a static day ladder and progress is text plus counters, not FSRS/SM-2 or durable evidence (`hluaguo/learn-faster-kit@c0168f30f87e488b5230dbd387fe2904f7fdf538:src/learn_faster/templates/shared/scripts/review_scheduler.py:12-16,63-113`). |
| `S-Sigdel/vimhjkl` | It machine-grades real Vim state and keystroke efficiency (`S-Sigdel/vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/grader.py:258-305,311-425,429-505`); a separate mastery axis gates new skills (`S-Sigdel/vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/engine.py:39-55,301-326`). | Objective buffer/cursor/register checks and `par/actual` efficiency eliminate self-attestation (`S-Sigdel/vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/grader.py:278-282`). | Add an optional external-checker ArtifactSpec whose recorded exit result is advisory evidence; passing stays an explicit learner command. | A miss automatically demotes a Leitner box (`S-Sigdel/vimhjkl@501762feecd0aa1c2f04089ba2f94177159b730e:src/vimhjkl/store.py:185-193`), which SkillTrace forbids. |
| `SYuan03/Skill-Anything` | Seven typed parsers feed map-reduce LLM generation (`SYuan03/Skill-Anything@4c83b8e73dccd897db6cecc1d5e6bbd987baf80a:skill_anything/engine.py:122-138,278-354`); `SkillPack` supports quizzes, flashcards, exercises, and learning paths (`SYuan03/Skill-Anything@4c83b8e73dccd897db6cecc1d5e6bbd987baf80a:skill_anything/models.py:186-240`). | It bulk-ingests sources and caches SHA-256 prompt results to avoid repeat model cost (`SYuan03/Skill-Anything@4c83b8e73dccd897db6cecc1d5e6bbd987baf80a:skill_anything/generators/_concurrent.py:41-68,131-223`). | Generate draft nodes and candidate edges for human review as seed data only. | Quiz outcomes are in-memory and flashcard grades are self-reported; neither gates progress (`SYuan03/Skill-Anything@4c83b8e73dccd897db6cecc1d5e6bbd987baf80a:skill_anything/interactive/quiz_runner.py:23,152`). |
| `mnemosyne-proj/mnemosyne` | The scheduler interface supports queue rebuilding, sister avoidance, and dry-run grading (`mnemosyne-proj/mnemosyne@ff4f61e84bea0d6928c29b7798f0f88b90938a0a:mnemosyne/libmnemosyne/scheduler.py:17-135`); a cramming scheduler proves the seam (`mnemosyne-proj/mnemosyne@ff4f61e84bea0d6928c29b7798f0f88b90938a0a:mnemosyne/libmnemosyne/schedulers/cramming.py:12-30`). | Dry runs preview side-effect-free intervals and plugins can scale them (`mnemosyne-proj/mnemosyne@ff4f61e84bea0d6928c29b7798f0f88b90938a0a:mnemosyne/libmnemosyne/schedulers/SM2_mnemosyne.py:377-388,487-488,495-496`). | Add `review --dry-run` to preview derived recommendations without event or state mutation. | Core code duplicates a method definition and has a grade-0 fact/card queue mismatch (`mnemosyne-proj/mnemosyne@ff4f61e84bea0d6928c29b7798f0f88b90938a0a:mnemosyne/libmnemosyne/scheduler.py:121,195`; `mnemosyne-proj/mnemosyne@ff4f61e84bea0d6928c29b7798f0f88b90938a0a:mnemosyne/libmnemosyne/schedulers/SM2_mnemosyne.py:210-212`). |
| `rr-/drill` | The fixed 11-rung scheduler walks full answer history (`rr-/drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/scheduler.py:6-18,28-40`); export/import preserves decks, cards, tags, and history (`rr-/drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/cmd/export.py:20-46`). | A wrong answer is shuffle-requeued within the same session (`rr-/drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/cmd/review.py:112-125`). | Requeue a failed work item as a new immutable attempt in the same session, without touching asserted progress. | Typed answers are assigned to an ORM field that does not exist, and SQLite is authoritative (`rr-/drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/cmd/review.py:70`; `rr-/drill@a3ba4a6610c1f1b7d0fa19ecb6aa8b36626dbea0:drillsrs/db.py:15-21,37-49`). |
| `nilbuild/developer-roadmap` | Topic files pair readable slugs with opaque immutable node IDs (`nilbuild/developer-roadmap@82441f97180f9a36f11b1fe348c65010978c9156:readme.md:148-166`); typed roadmap records contain nodes and edges (`nilbuild/developer-roadmap@82441f97180f9a36f11b1fe348c65010978c9156:scripts/lib/official-roadmap.ts:21-48`). | This scales a rename-safe content/graph-identity seam across many contributor-edited files (`nilbuild/developer-roadmap@82441f97180f9a36f11b1fe348c65010978c9156:readme.md:150-158`). | Add a read-only filename validator for `<human-slug>@<immutable-node-id>.md`; keep edges authoritative. | Repository content syncs to an external database/API rather than remaining Markdown/YAML truth (`nilbuild/developer-roadmap@82441f97180f9a36f11b1fe348c65010978c9156:scripts/sync-repo-to-database.ts:114-145,182-248`). |
| `urnote/urnote` | Question headings become scheduled items with hidden status IDs (`urnote/urnote@f22e7d4b755bc2fac2ea22a425ca17265ac07073:note/module/markdown/title_pat.py:6-64`; `urnote/urnote@f22e7d4b755bc2fac2ea22a425ca17265ac07073:note/module/markdown/filehandler.py:97-215`); one-character grades drive SuperMemo updates (`urnote/urnote@f22e7d4b755bc2fac2ea22a425ca17265ac07073:note/utils/review_algorithm.py:71-168`). | Any Markdown question heading is authorable without node schema or hierarchy (`urnote/urnote@f22e7d4b755bc2fac2ea22a425ca17265ac07073:note/module/markdown/filehandler.py:163-180`). | Write derived inline readiness annotations during sync while retaining state in `graph/state.yaml`. | Regex in-place edits reject malformed commands and are destructive (`urnote/urnote@f22e7d4b755bc2fac2ea22a425ca17265ac07073:note/module/markdown/filehandler.py:172-199`; `urnote/urnote@f22e7d4b755bc2fac2ea22a425ca17265ac07073:note/infrastructure/error.py:18-29`). |

## Cross-cutting observations

- **Verification authority:** vimhjkl is the only shortlist repo with
  machine-verified evidence; Skill-Anything and learn-faster-kit self-report;
  the SRS cores (Anki, Mnemosyne, drill, urnote) trust learner grades. None
  combine objective gates with SkillTrace's human-only acceptance authority.
- **Backward-moving state is the norm:** vimhjkl and Numo explicitly demote
  progress on misses; SkillTrace's monotonic asserted progress remains
  distinctive.
- **Closest end-to-end analogue:** engram (local JSON state, receipts, FSRS,
  concept map) — but monolithic and self-testing rather than layered.

## Gaps and unverified items

- **Anki:** queue builder internals and `service/` layer not read; FSRS
  branches beyond `again` in `states/review.rs` not fully traced.
- **Mnemosyne:** plugin runtime activation path and Android/JS scripting
  surface not fetched.
- **drill / urnote:** no test suites exist (drill) or partial coverage
  (urnote DB layer); behavior verified from source only, not executed.
- **Skill-Anything:** parser internals, SKILL.md exporter schema, and
  LLM-output quality not verifiable from source.
- **Numo:** engine/progression internals beyond curriculum services were out
  of scope; vitest suite not executed.
- **vimhjkl:** test suite not executed (requires vim/nvim);
  curriculum-generation scripts under `build/passes/` not audited.
- **developer-roadmap:** roadmap JSON is not committed at the pin; the typed
  shape was verified from first-party maintainer sync tooling instead.
